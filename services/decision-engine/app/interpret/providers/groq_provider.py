"""Groq — the active provider (Phase 3 provider substitution: Gemini's free
tier request quota proved too low for development/live-gate testing, ~20
requests/day per model on a fresh key — see gemini.py's docstring for the
live-verified evidence). Groq's free tier is materially more usable for
this project's iteration pace. CLAUDE.md §5's zero-spend-runtime principle
still applies; only the specific provider changed.

Model: qwen/qwen3.8-27b — vision-capable (accepts image + text; Groq's docs
list a 3-image-per-request, 20MB-per-image limit, well above what a single
incident photo needs) and supports strict `json_schema` structured outputs
(not just the looser `json_object` mode), so — same as `gemini.py` — the
response is schema-constrained by the API itself, not left to prompting
alone.

Uses Groq's official Python SDK (OpenAI-compatible interface) rather than
hand-rolled HTTP: it's already a proper typed client with its own
exception hierarchy (mirroring the pattern already used in `gemini.py`),
and Groq's API is not literally OpenAI's endpoint — routing an `openai`
SDK client at it would be compatibility code for a dependency this project
doesn't otherwise need, whereas `groq` is the correct, minimal,
purpose-built one.

Not the Anthropic subscription this development session itself runs on —
CLAUDE.md §5's zero-spend-runtime principle governs the choice of active
provider, not a hard dependency on any one vendor.

Live-observed limit (same "trust the real error over documentation" lesson
as gemini.py): the on-demand free tier enforces an output-tokens-per-minute
cap around 1000 OTPM for this model — a real 429 (`rate_limit_exceeded`,
`type: tokens`) surfaced during Phase 3 live-gate testing after several
consecutive calls each producing ~1,000-1,200 output tokens (this schema's
verbose `review_reason` field is the main driver). It's handled the same as
any other provider failure — retry once, then a safe fallback — but a demo
should pace live calls with this in mind rather than firing many in quick
succession.
"""

from __future__ import annotations

import json
import logging
import os

import groq

from app.interpret.providers.base import InterpretationProvider

logger = logging.getLogger(__name__)

RESPONSE_SCHEMA_NAME = "incident_intelligence"

# Mirrors app.schemas.incident.ModelOutput exactly. Hand-written rather
# than derived from Pydantic's model_json_schema(), because Groq/OpenAI-style
# strict mode has
# extra requirements Pydantic doesn't emit by default: every property must
# appear in `required` (nullable fields use a ["type", "null"] union rather
# than being omitted) and every object needs `additionalProperties: false`.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "incident_type": {"type": "string"},
        "symptoms": {"type": "array", "items": {"type": "string"}},
        "visual_observations": {"type": "array", "items": {"type": "string"}},
        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "safety_risk": {"type": "boolean"},
        "confidence": {"type": "number"},
        "likely_faults": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["code", "confidence"],
                "additionalProperties": False,
            },
        },
        "required_capability": {"type": "string"},
        "requires_human_review": {"type": "boolean"},
        "review_reason": {"type": ["string", "null"]},
        "evidence_conflict": {"type": "boolean"},
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
        "review_reason",
        "evidence_conflict",
    ],
    "additionalProperties": False,
}


class GroqProvider(InterpretationProvider):
    name = "qwen/qwen3.8-27b"
    provider_id = "groq"

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        self._client = groq.Groq(api_key=key)

    def complete(
        self,
        system_prompt: str,
        context_text: str,
        image_base64: str | None,
        image_media_type: str | None,
    ) -> dict | None:
        user_content: list[dict] = [{"type": "text", "text": context_text}]
        if image_base64 and image_media_type:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_media_type};base64,{image_base64}"},
                }
            )

        try:
            response = self._client.chat.completions.create(
                model=self.name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": RESPONSE_SCHEMA_NAME,
                        "strict": True,
                        "schema": RESPONSE_SCHEMA,
                    },
                },
            )
        except groq.APIError as e:
            logger.warning("Groq call failed: %s", e)
            return None
        except Exception as e:  # network/transport failures below the SDK's own error types
            logger.warning("Groq call failed unexpectedly: %s: %s", type(e).__name__, e)
            return None

        content = response.choices[0].message.content if response.choices else None
        if not content:
            return None
        try:
            return json.loads(content)
        except ValueError:
            logger.warning("Groq response was not valid JSON despite json_schema mode")
            return None
