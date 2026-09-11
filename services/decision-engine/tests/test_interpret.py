"""Unit tests for incident interpretation orchestration.

A FakeProvider stands in for whichever real model backs interpretation —
these tests prove the validation/retry/fallback/policy logic is correct,
independent of any specific SDK (Gemini, Anthropic, or whatever comes
next). That's the point of the provider abstraction: this file doesn't
change when the active provider does.

Real model-quality evidence (does it actually classify well, handle
genuinely ambiguous/conflicting real-world input) is the Phase 3 live gate
test (tests/incident_intelligence_check.py at the repo root), which needs
a real GEMINI_API_KEY and is run separately.
"""

from __future__ import annotations

import pytest

from app.interpret.providers.base import InterpretationProvider
from app.interpret.service import interpret_incident
from app.schemas.incident import AssetContext, InterpretRequest

ASSET = AssetContext(code="AV-204", name="Epson Projector", location="Room 3.12", status="active")


class FakeProvider(InterpretationProvider):
    """Returns each of `results` in order, one per call. A `dict` is a
    successful response; `None` simulates any provider-side failure
    (network, auth, timeout, unparseable output) — matches the real
    contract in InterpretationProvider.complete."""

    name = "fake-model"
    provider_id = "fake"

    def __init__(self, *results: dict | None):
        self._results = list(results)
        self.call_count = 0

    def complete(self, system_prompt, context_text, image_base64, image_media_type):
        self.call_count += 1
        return self._results.pop(0)


def make_request(description: str, **kwargs) -> InterpretRequest:
    return InterpretRequest(
        incident_id="11111111-1111-1111-1111-111111111111",
        description=description,
        asset_context=ASSET,
        **kwargs,
    )


HIGH_CONFIDENCE_PAYLOAD = {
    "incident_type": "power_failure",
    "symptoms": ["device does not power on"],
    "visual_observations": [],
    "severity": "high",
    "safety_risk": False,
    "confidence": 0.91,
    "likely_faults": [{"code": "POWER_SUPPLY_FAILURE", "confidence": 0.74}],
    "required_capability": "AV_SUPPORT",
    "requires_human_review": False,
    "evidence_conflict": False,
}


def test_clear_text_incident_classified_confidently():
    provider = FakeProvider(HIGH_CONFIDENCE_PAYLOAD)
    result = interpret_incident(make_request("projector won't turn on"), provider=provider)
    assert result.incident_type == "power_failure"
    assert result.requires_human_review is False
    assert result.confidence == pytest.approx(0.91)
    assert result.safety_risk is False
    assert result.model == "fake-model"
    assert result.provider == "fake"


def test_low_confidence_forces_review_even_if_model_says_no():
    payload = {**HIGH_CONFIDENCE_PAYLOAD, "confidence": 0.3, "requires_human_review": False}
    provider = FakeProvider(payload)
    result = interpret_incident(make_request("something seems off maybe"), provider=provider)
    assert result.requires_human_review is True
    assert "confidence" in result.review_reason


def test_safety_signal_forces_review_and_sets_flag():
    payload = {
        **HIGH_CONFIDENCE_PAYLOAD,
        "safety_risk": True,
        "requires_human_review": False,
        "confidence": 0.95,
    }
    provider = FakeProvider(payload)
    result = interpret_incident(make_request("sparks coming from the panel"), provider=provider)
    assert result.safety_risk is True
    assert result.requires_human_review is True
    assert "safety" in result.review_reason


def test_evidence_conflict_forces_review():
    payload = {**HIGH_CONFIDENCE_PAYLOAD, "evidence_conflict": True, "requires_human_review": False}
    provider = FakeProvider(payload)
    result = interpret_incident(
        make_request(
            "the screen is flickering",
            image_base64="Zm9v",
            image_media_type="image/jpeg",
        ),
        provider=provider,
    )
    assert result.requires_human_review is True
    assert "conflict" in result.review_reason


def test_malformed_output_retries_then_falls_back_safely():
    provider = FakeProvider({"incident_type": "power_failure"}, {"incident_type": "power_failure"})
    result = interpret_incident(make_request("won't turn on"), provider=provider)
    assert result.requires_human_review is True
    assert result.incident_type == "unknown"
    assert result.confidence == 0.0
    assert provider.call_count == 2


def test_malformed_output_then_valid_retry_succeeds():
    provider = FakeProvider({"incident_type": "power_failure"}, HIGH_CONFIDENCE_PAYLOAD)
    result = interpret_incident(make_request("won't turn on"), provider=provider)
    assert result.incident_type == "power_failure"
    assert result.requires_human_review is False


def test_provider_error_retries_then_falls_back_safely():
    provider = FakeProvider(None, None)
    result = interpret_incident(make_request("won't turn on"), provider=provider)
    assert result.requires_human_review is True
    assert "model call failed" in result.review_reason
    assert provider.call_count == 2


def test_provider_error_then_success_on_retry():
    provider = FakeProvider(None, HIGH_CONFIDENCE_PAYLOAD)
    result = interpret_incident(make_request("won't turn on"), provider=provider)
    assert result.incident_type == "power_failure"
    assert result.requires_human_review is False


def test_insufficient_evidence_forces_review():
    payload = {
        **HIGH_CONFIDENCE_PAYLOAD,
        "incident_type": "unknown",
        "symptoms": [],
        "confidence": 0.9,
        "requires_human_review": False,
    }
    provider = FakeProvider(payload)
    result = interpret_incident(make_request("something is wrong"), provider=provider)
    assert result.requires_human_review is True
    assert "insufficient evidence" in result.review_reason


def test_missing_default_provider_api_key_degrades_safely_instead_of_crashing(monkeypatch):
    """Groq is the active default provider (Phase 3 provider substitution)."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    result = interpret_incident(make_request("won't turn on"))  # no provider injected
    assert result.requires_human_review is True
    assert "GROQ_API_KEY" in result.review_reason


def test_missing_provider_api_key_degrades_safely_instead_of_crashing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("MODEL_PROVIDER", "gemini")
    result = interpret_incident(make_request("won't turn on"))  # no provider injected
    assert result.requires_human_review is True
    assert "GEMINI_API_KEY" in result.review_reason


def test_model_provider_env_var_switches_provider(monkeypatch):
    """Proves the abstraction is actually swappable, not just theoretically
    so: switching MODEL_PROVIDER changes which key get_provider() demands,
    with zero other code changes."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    result = interpret_incident(make_request("won't turn on"))
    assert result.requires_human_review is True
    assert "ANTHROPIC_API_KEY" in result.review_reason


def test_never_invents_operational_facts():
    """The schema itself has no field capable of carrying an operational
    fact — this asserts that invariant structurally, not just by prompt."""
    from app.schemas.incident import IncidentIntelligence

    fields = set(IncidentIntelligence.model_fields.keys())
    forbidden_terms = {"availability", "inventory", "schedule", "capacity", "cost", "technician"}
    for field in fields:
        assert not any(term in field.lower() for term in forbidden_terms), field
