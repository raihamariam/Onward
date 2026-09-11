"""Incident interpretation — the only place this service talks to Anthropic.

Not an agent: one forced-tool-call request per incident, no loop, no tool
choice made by the model, no multi-turn conversation. See CLAUDE.md §8.
"""

from __future__ import annotations

import logging
import os
import time

import anthropic
from pydantic import ValidationError

from app.schemas.incident import (
    IncidentIntelligence,
    InterpretRequest,
    apply_review_policy,
    fallback_intelligence,
)

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024
MAX_PRIOR_INCIDENTS = 5

TOOL_NAME = "emit_incident_intelligence"

TOOL_SCHEMA = {
    "name": TOOL_NAME,
    "description": "Return the structured interpretation of a reported physical-asset incident.",
    "input_schema": {
        "type": "object",
        "properties": {
            "incident_type": {
                "type": "string",
                "description": "Short snake_case category, e.g. power_failure, display_issue, "
                "physical_damage, connectivity_issue, safety_hazard, unknown.",
            },
            "symptoms": {"type": "array", "items": {"type": "string"}},
            "visual_observations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Only from the image, if one was provided. Empty array if no image.",
            },
            "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            "safety_risk": {
                "type": "boolean",
                "description": "True for sparks, smoke, burning smell, exposed wiring, electrical "
                "arcing, or any other immediate physical danger described or shown.",
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "likely_faults": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["code", "confidence"],
                },
            },
            "required_capability": {
                "type": "string",
                "description": "e.g. AV_SUPPORT, ELECTRICAL, GENERAL_MAINTENANCE, SAFETY_TEAM.",
            },
            "requires_human_review": {
                "type": "boolean",
                "description": "True if the evidence is ambiguous, insufficient, or you are not "
                "confident in this classification.",
            },
            "review_reason": {
                "type": "string",
                "description": "Why review is needed. Required if requires_human_review is true, "
                "omit otherwise.",
            },
            "evidence_conflict": {
                "type": "boolean",
                "description": "True if the text description and the image appear to describe "
                "different problems.",
            },
        },
        "required": [
            "incident_type",
            "symptoms",
            "visual_observations",
            "severity",
            "safety_risk",
            "confidence",
            "likely_faults",
            "required_capability",
            "requires_human_review",
            "evidence_conflict",
        ],
    },
}

SYSTEM_PROMPT = """You interpret reported incidents about physical equipment for Onward, an \
operational-response system. You are shown a user's description (and sometimes a photo) of \
something that appears broken, plus trusted facts about the registered asset involved.

Your only job is understanding what appears to have happened. You must NEVER invent or assume:
- technician availability, room/resource availability, event schedules, inventory levels, \
capacity, cost, authorization, or any other operational fact. You do not have that information \
and are not being asked for it.

You MAY infer: symptoms, an incident category, visual observations (from an image only), \
severity, safety risk, likely fault classes with your confidence in each, the general kind of \
service capability needed, and your own confidence and uncertainty.

If the description is vague, if text and image seem to describe different problems, or if you \
are simply not confident, set requires_human_review to true and explain why in review_reason — \
do not guess a specific answer to appear certain. A wrong confident answer is worse than an \
honest "review this."

If there is any sign of immediate physical danger (sparks, smoke, burning smell, exposed wiring, \
electrical arcing, or similar), set safety_risk to true. Do not suggest how to fix or approach \
the equipment — classification only, never repair instructions.

Call the emit_incident_intelligence tool exactly once with your structured interpretation."""


def _build_user_content(req: InterpretRequest) -> list[dict]:
    asset = req.asset_context
    prior_lines = "\n".join(
        f"- {p.reported_at.isoformat()} ({p.status}): {p.description}"
        for p in asset.prior_incidents[:MAX_PRIOR_INCIDENTS]
    ) or "(none on record)"

    text = (
        f"Registered asset: {asset.code} — {asset.name}\n"
        f"Location: {asset.location or 'unknown'}\n"
        f"Asset status: {asset.status}\n"
        f"Prior incidents for this asset:\n{prior_lines}\n\n"
        f"User's report:\n{req.description}"
    )

    content: list[dict] = [{"type": "text", "text": text}]
    if req.image_base64 and req.image_media_type:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": req.image_media_type,
                    "data": req.image_base64,
                },
            }
        )
    return content


def _call_model(client: anthropic.Anthropic, content: list[dict]) -> dict | None:
    """One API call. Returns the tool_use input dict, or None on any failure
    (caller decides whether to retry)."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=[TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": TOOL_NAME},
            messages=[{"role": "user", "content": content}],
        )
    except (anthropic.APIConnectionError, anthropic.APITimeoutError, anthropic.APIStatusError) as e:
        logger.warning("Anthropic call failed: %s", e)
        return None

    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL_NAME:
            return dict(block.input)
    return None


def interpret_incident(
    req: InterpretRequest, client: anthropic.Anthropic | None = None
) -> IncidentIntelligence:
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            # Missing configuration is not a crash-worthy bug — it's the
            # same "can't trust an answer" situation as a provider outage,
            # and gets the same safe, review-flagged outcome.
            return apply_review_policy(
                fallback_intelligence(req.incident_id, "ANTHROPIC_API_KEY is not configured")
            )
        client = anthropic.Anthropic(api_key=api_key)
    content = _build_user_content(req)

    raw = _call_model(client, content)
    if raw is None:
        time.sleep(1)
        raw = _call_model(client, content)
    if raw is None:
        return apply_review_policy(
            fallback_intelligence(req.incident_id, "model call failed after retry")
        )

    try:
        intel = IncidentIntelligence(**raw, incident_id=req.incident_id, model=MODEL)
    except ValidationError as e:
        logger.warning("Model output failed schema validation, retrying once: %s", e)
        raw_retry = _call_model(client, content)
        if raw_retry is not None:
            try:
                intel = IncidentIntelligence(**raw_retry, incident_id=req.incident_id, model=MODEL)
            except ValidationError as e2:
                return apply_review_policy(
                    fallback_intelligence(
                        req.incident_id, f"model output failed validation twice: {e2}"
                    )
                )
        else:
            return apply_review_policy(
                fallback_intelligence(req.incident_id, "model output invalid; retry call failed")
            )

    return apply_review_policy(intel)
