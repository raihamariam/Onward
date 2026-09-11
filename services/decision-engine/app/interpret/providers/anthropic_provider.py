"""Not the active default — CLAUDE.md §7 requires a zero-spend runtime, and
this provider bills against the Anthropic API / this session's own
subscription. Kept as a working, tested alternative (set
MODEL_PROVIDER=anthropic) so the provider can be swapped back, or compared
against Gemini, without touching the interpretation contract or retry
logic in service.py."""

from __future__ import annotations

import logging
import os

import anthropic

from app.interpret.providers.base import InterpretationProvider

logger = logging.getLogger(__name__)

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


class AnthropicProvider(InterpretationProvider):
    name = "claude-sonnet-5"
    provider_id = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        self._client = anthropic.Anthropic(api_key=key)

    def complete(
        self,
        system_prompt: str,
        context_text: str,
        image_base64: str | None,
        image_media_type: str | None,
    ) -> dict | None:
        content: list[dict] = [{"type": "text", "text": context_text}]
        if image_base64 and image_media_type:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": image_base64,
                    },
                }
            )

        try:
            response = self._client.messages.create(
                model=self.name,
                max_tokens=1024,
                system=system_prompt,
                tools=[TOOL_SCHEMA],
                tool_choice={"type": "tool", "name": TOOL_NAME},
                messages=[{"role": "user", "content": content}],
            )
        except (
            anthropic.APIConnectionError,
            anthropic.APITimeoutError,
            anthropic.APIStatusError,
        ) as e:
            logger.warning("Anthropic call failed: %s", e)
            return None

        for block in response.content:
            if block.type == "tool_use" and block.name == TOOL_NAME:
                return dict(block.input)
        return None
