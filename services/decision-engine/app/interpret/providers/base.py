"""The provider boundary. Swapping which model answers incident
interpretation means writing one new class here and adding one line to
get_provider() — nothing in service.py, the schema, or the retry/validation/
review-policy logic changes."""

from __future__ import annotations

from abc import ABC, abstractmethod


class InterpretationProvider(ABC):
    name: str  # the specific model id, e.g. "gemini-3-flash-preview"
    provider_id: str  # short identifier stored in IncidentIntelligence.provider

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        context_text: str,
        image_base64: str | None,
        image_media_type: str | None,
    ) -> dict | None:
        """One request. Returns a raw dict matching ModelOutput's shape, or
        None on any failure (auth, network, timeout, unparseable response).
        Never raises — service.py treats None uniformly as "this attempt
        failed, maybe retry" regardless of what actually went wrong inside
        a specific provider."""
        raise NotImplementedError
