"""Gemini Developer API — kept as the manual fallback provider (set
MODEL_PROVIDER=gemini), not the active default. Groq (qwen/qwen3.8-27b) is
active instead because Gemini's real free-tier daily quota proved too low
for this project's actual development/live-gate pace — see below. Gemini
stays in the codebase specifically *because* of that failure mode: it's a
small (~90 lines), correct, already-tested second option if Groq itself
becomes rate-limited or unavailable during a demo, at effectively zero
maintenance cost (one class, behind the same interface, changed with one
env var). CLAUDE.md §5's zero-spend-runtime principle governs both.

Model: gemini-3-flash-preview. Free-tier limits are project/key-specific —
published figures (blog posts said 1,500 requests/day) did not match what
this project actually got from the API: a live Phase 3 gate run hit a real
429 RESOURCE_EXHAUSTED after ~20 calls in a few minutes, with the API's own
error body naming the limit explicitly: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`,
quotaValue 20. Treat the error response as ground truth over any
documentation when reasoning about free-tier capacity — a hackathon demo
plans its live-call budget around ~20/day per model on a fresh key, not the
higher published number. This is exactly why the retry-then-safe-fallback
behavior in interpret_incident() exists: quota exhaustion is a real,
expected failure mode at this tier, not an edge case, and it's also why
Groq (a materially higher usable budget) is the active provider now.

Data-handling rule, not just documentation: Google's unpaid-tier terms
permit using submitted content (including human review) to improve their
products. Onward must therefore only ever send synthetic/non-sensitive
hackathon data through this provider — never real user reports. See
CLAUDE.md §7 and database/seed/0001_seed_assets.sql for what "synthetic"
means here.
"""

from __future__ import annotations

import base64
import binascii
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
            try:
                image_bytes = base64.b64decode(image_base64, validate=True)
            except (binascii.Error, ValueError) as e:
                logger.warning("Unsupported/malformed image_base64: %s", e)
                return None
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image_media_type))

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
