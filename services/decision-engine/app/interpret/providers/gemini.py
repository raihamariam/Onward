"""Gemini Developer API — the default provider (CLAUDE.md §7: Onward's
runtime must incur zero additional spend, so it runs on Google's free,
rate-limited Gemini tier rather than a paid API or the Anthropic
subscription this session itself runs on).

Model: gemini-3-flash-preview. Free-tier limits (checked Sept 2026): 10
requests/minute, 250k tokens/minute, 1,500 requests/day — far more than a
hackathon needs. Chosen over gemini-3.1-flash-lite (higher RPM/lower
quality trade-off we don't need, since RPD isn't our constraint) and over
gemini-2.5-flash (lower daily cap, same tier of capability).

Data-handling rule, not just documentation: Google's unpaid-tier terms
permit using submitted content (including human review) to improve their
products. Onward must therefore only ever send synthetic/non-sensitive
hackathon data through this provider — never real user reports. See
CLAUDE.md §7 and database/seed/0001_seed_assets.sql for what "synthetic"
means here.
"""

from __future__ import annotations

import base64
import json
import logging
import os

from google import genai
from google.genai import errors, types

from app.interpret.providers.base import InterpretationProvider
from app.schemas.incident import ModelOutput

logger = logging.getLogger(__name__)


class GeminiProvider(InterpretationProvider):
    name = "gemini-3-flash-preview"
    provider_id = "gemini"

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self._client = genai.Client(api_key=key)

    def complete(
        self,
        system_prompt: str,
        context_text: str,
        image_base64: str | None,
        image_media_type: str | None,
    ) -> dict | None:
        parts = [types.Part.from_text(text=context_text)]
        if image_base64 and image_media_type:
            parts.append(
                types.Part.from_bytes(
                    data=base64.b64decode(image_base64), mime_type=image_media_type
                )
            )

        try:
            response = self._client.models.generate_content(
                model=self.name,
                contents=[types.Content(role="user", parts=parts)],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=ModelOutput,
                ),
            )
        except errors.APIError as e:
            logger.warning("Gemini call failed: %s", e)
            return None
        except Exception as e:  # network/transport failures below the SDK's own error types
            logger.warning("Gemini call failed unexpectedly: %s: %s", type(e).__name__, e)
            return None

        text = getattr(response, "text", None)
        if not text:
            return None
        try:
            return json.loads(text)
        except ValueError:
            logger.warning("Gemini response was not valid JSON despite response_mime_type")
            return None
