"""Incident interpretation — orchestration only. Which model actually
answers lives entirely behind app.interpret.providers; this module never
imports a specific SDK. Not an agent: one forced-schema request per
incident, no loop, no tool choice made by the model, no multi-turn
conversation. See CLAUDE.md §8.
"""

from __future__ import annotations

import logging
import time

from pydantic import ValidationError

from app.interpret.providers import InterpretationProvider, get_provider
from app.schemas.incident import (
    IncidentIntelligence,
    InterpretRequest,
    ModelOutput,
    apply_review_policy,
    fallback_intelligence,
)

logger = logging.getLogger(__name__)

MAX_PRIOR_INCIDENTS = 5

SYSTEM_PROMPT = """You interpret reported incidents about physical equipment for Onward, an \
operational-response system. You are shown a user's description (and sometimes a photo) of \
something that appears broken, plus trusted facts about the registered asset involved.

Your only job is understanding what appears to have happened. You must NEVER invent or assume:
- technician availability, room/resource availability, event schedules, inventory levels, \
capacity, cost, authorization, or any other operational fact. You do not have that information \
and are not being asked for it.

You MAY infer: symptoms, an incident category, visual observations (from an image only), \
severity, safety risk, likely fault classes with your confidence in each, and your own \
confidence and uncertainty.

required_capability must be a short UPPER_SNAKE_CASE tag naming the KIND of technician skill \
or spare-part category needed to address this — not a sentence or description. Pick the \
closest fit (e.g. AV_SUPPORT, POS_SUPPORT, ELECTRICAL, PLUMBING, HVAC_SUPPORT, IT_SUPPORT, \
NETWORK_SUPPORT); if truly nothing fits, use GENERAL_MAINTENANCE. This tag is matched \
literally against a fixed roster of real technician/inventory records downstream, so \
inventing a new or overly specific tag means no real resource will ever match it — when \
unsure between two plausible tags, prefer the more general one.

If the description is vague, if text and image seem to describe different problems, or if you \
are simply not confident, set requires_human_review to true and explain why in review_reason — \
do not guess a specific answer to appear certain. A wrong confident answer is worse than an \
honest "review this."

If there is any sign of immediate physical danger (sparks, smoke, burning smell, exposed wiring, \
electrical arcing, or similar), set safety_risk to true. Do not suggest how to fix or approach \
the equipment — classification only, never repair instructions.

Respond with your structured interpretation matching the required schema exactly."""


def _build_context_text(req: InterpretRequest) -> str:
    asset = req.asset_context
    prior_lines = "\n".join(
        f"- {p.reported_at.isoformat()} ({p.status}): {p.description}"
        for p in asset.prior_incidents[:MAX_PRIOR_INCIDENTS]
    ) or "(none on record)"

    return (
        f"Registered asset: {asset.code} — {asset.name}\n"
        f"Location: {asset.location or 'unknown'}\n"
        f"Asset status: {asset.status}\n"
        f"Prior incidents for this asset:\n{prior_lines}\n\n"
        f"User's report:\n{req.description}"
    )


def interpret_incident(
    req: InterpretRequest, provider: InterpretationProvider | None = None
) -> IncidentIntelligence:
    if provider is None:
        try:
            provider = get_provider()
        except (RuntimeError, ValueError) as e:
            # Missing/misconfigured provider is not a crash-worthy bug —
            # it's the same "can't trust an answer" situation as a
            # provider outage, and gets the same safe, review-flagged
            # outcome.
            return apply_review_policy(fallback_intelligence(req.incident_id, str(e)))

    context_text = _build_context_text(req)

    raw = provider.complete(SYSTEM_PROMPT, context_text, req.image_base64, req.image_media_type)
    if raw is None:
        time.sleep(1)
        raw = provider.complete(SYSTEM_PROMPT, context_text, req.image_base64, req.image_media_type)
    if raw is None:
        return apply_review_policy(
            fallback_intelligence(req.incident_id, "model call failed after retry")
        )

    model_output = _validate_or_retry(provider, req, context_text, raw)
    if model_output is None:
        return apply_review_policy(
            fallback_intelligence(req.incident_id, "model output failed validation twice")
        )

    intel = IncidentIntelligence(
        **model_output.model_dump(),
        incident_id=req.incident_id,
        model=provider.name,
        provider=provider.provider_id,
    )
    return apply_review_policy(intel)


def _validate_or_retry(
    provider: InterpretationProvider, req: InterpretRequest, context_text: str, raw: dict
) -> ModelOutput | None:
    try:
        return ModelOutput(**raw)
    except ValidationError as e:
        logger.warning("Model output failed schema validation, retrying once: %s", e)

    raw_retry = provider.complete(
        SYSTEM_PROMPT, context_text, req.image_base64, req.image_media_type
    )
    if raw_retry is None:
        return None
    try:
        return ModelOutput(**raw_retry)
    except ValidationError as e2:
        logger.warning("Model output failed validation on retry too: %s", e2)
        return None
