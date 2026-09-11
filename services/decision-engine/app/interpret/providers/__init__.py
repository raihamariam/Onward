from __future__ import annotations

import os

from app.interpret.providers.base import InterpretationProvider

__all__ = ["InterpretationProvider", "get_provider"]


def get_provider() -> InterpretationProvider:
    """Which model backs incident interpretation. Defaults to the free
    Gemini tier (CLAUDE.md §7 — zero-spend runtime requirement). Set
    MODEL_PROVIDER=anthropic to use the Anthropic-backed alternative
    instead; nothing else in this codebase needs to change to do that.
    Raises RuntimeError if the selected provider's API key isn't
    configured — callers (interpret_incident) turn that into a safe,
    review-flagged fallback rather than letting it crash a request."""
    selected = os.environ.get("MODEL_PROVIDER", "gemini").lower()

    if selected == "gemini":
        from app.interpret.providers.gemini import GeminiProvider

        return GeminiProvider()
    if selected == "anthropic":
        from app.interpret.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider()

    raise ValueError(f"Unknown MODEL_PROVIDER: {selected!r} (expected 'gemini' or 'anthropic')")
