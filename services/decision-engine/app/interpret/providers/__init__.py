from __future__ import annotations

import os

from app.interpret.providers.base import InterpretationProvider

__all__ = ["InterpretationProvider", "get_provider"]


def get_provider() -> InterpretationProvider:
    """Which model backs incident interpretation. Defaults to Groq
    (qwen/qwen3.8-27b) — CLAUDE.md §5's zero-spend-runtime principle still
    applies, Groq is just the provider whose free tier is actually usable
    at this project's iteration pace (Gemini's ~20 requests/day proved too
    low, see gemini.py). Set MODEL_PROVIDER=gemini or =anthropic to use
    either alternative instead; nothing else in this codebase needs to
    change to do that — both remain fully implemented, just not active.
    Raises RuntimeError if the selected provider's API key isn't
    configured — callers (interpret_incident) turn that into a safe,
    review-flagged fallback rather than letting it crash a request."""
    selected = os.environ.get("MODEL_PROVIDER", "groq").lower()

    if selected == "groq":
        from app.interpret.providers.groq_provider import GroqProvider

        return GroqProvider()
    if selected == "gemini":
        from app.interpret.providers.gemini import GeminiProvider

        return GeminiProvider()
    if selected == "anthropic":
        from app.interpret.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider()

    raise ValueError(
        f"Unknown MODEL_PROVIDER: {selected!r} (expected 'groq', 'gemini', or 'anthropic')"
    )
