"""Unit tests for incident interpretation.

The Anthropic client is always mocked here — these tests prove the
validation/retry/fallback/policy logic is correct, not that the live model
produces good classifications. That proof is the Phase 3 live gate test
(tests/incident_intelligence_check.py at the repo root), which requires a
real ANTHROPIC_API_KEY and is run separately.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic
import httpx
import pytest

from app.interpret.service import TOOL_NAME, interpret_incident
from app.schemas.incident import AssetContext, InterpretRequest

ASSET = AssetContext(code="AV-204", name="Epson Projector", location="Room 3.12", status="active")


def make_request(description: str, **kwargs) -> InterpretRequest:
    return InterpretRequest(
        incident_id="11111111-1111-1111-1111-111111111111",
        description=description,
        asset_context=ASSET,
        **kwargs,
    )


def fake_tool_response(payload: dict):
    block = SimpleNamespace(type="tool_use", name=TOOL_NAME, input=payload)
    return SimpleNamespace(content=[block])


def mock_client(*side_effects) -> MagicMock:
    client = MagicMock(spec=anthropic.Anthropic)
    client.messages.create.side_effect = list(side_effects)
    return client


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
    client = mock_client(fake_tool_response(HIGH_CONFIDENCE_PAYLOAD))
    result = interpret_incident(make_request("projector won't turn on"), client=client)
    assert result.incident_type == "power_failure"
    assert result.requires_human_review is False
    assert result.confidence == pytest.approx(0.91)
    assert result.safety_risk is False


def test_low_confidence_forces_review_even_if_model_says_no():
    payload = {**HIGH_CONFIDENCE_PAYLOAD, "confidence": 0.3, "requires_human_review": False}
    client = mock_client(fake_tool_response(payload))
    result = interpret_incident(make_request("something seems off maybe"), client=client)
    assert result.requires_human_review is True
    assert "confidence" in result.review_reason


def test_safety_signal_forces_review_and_sets_flag():
    payload = {
        **HIGH_CONFIDENCE_PAYLOAD,
        "safety_risk": True,
        "requires_human_review": False,
        "confidence": 0.95,
    }
    client = mock_client(fake_tool_response(payload))
    result = interpret_incident(make_request("sparks coming from the panel"), client=client)
    assert result.safety_risk is True
    assert result.requires_human_review is True
    assert "safety" in result.review_reason


def test_evidence_conflict_forces_review():
    payload = {**HIGH_CONFIDENCE_PAYLOAD, "evidence_conflict": True, "requires_human_review": False}
    client = mock_client(fake_tool_response(payload))
    result = interpret_incident(
        make_request(
            "the screen is flickering",
            image_base64="Zm9v",
            image_media_type="image/jpeg",
        ),
        client=client,
    )
    assert result.requires_human_review is True
    assert "conflict" in result.review_reason


def test_malformed_output_retries_then_falls_back_safely():
    bad = fake_tool_response({"incident_type": "power_failure"})  # missing required fields
    also_bad = fake_tool_response({"incident_type": "power_failure"})
    client = mock_client(bad, also_bad)
    result = interpret_incident(make_request("won't turn on"), client=client)
    assert result.requires_human_review is True
    assert result.incident_type == "unknown"
    assert result.confidence == 0.0
    assert client.messages.create.call_count == 2


def test_malformed_output_then_valid_retry_succeeds():
    bad = fake_tool_response({"incident_type": "power_failure"})
    good = fake_tool_response(HIGH_CONFIDENCE_PAYLOAD)
    client = mock_client(bad, good)
    result = interpret_incident(make_request("won't turn on"), client=client)
    assert result.incident_type == "power_failure"
    assert result.requires_human_review is False


def test_provider_error_retries_then_falls_back_safely():
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    client = MagicMock(spec=anthropic.Anthropic)
    client.messages.create.side_effect = [
        anthropic.APIConnectionError(request=req),
        anthropic.APIConnectionError(request=req),
    ]
    result = interpret_incident(make_request("won't turn on"), client=client)
    assert result.requires_human_review is True
    assert "model call failed" in result.review_reason
    assert client.messages.create.call_count == 2


def test_provider_error_then_success_on_retry():
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    client = MagicMock(spec=anthropic.Anthropic)
    client.messages.create.side_effect = [
        anthropic.APIConnectionError(request=req),
        fake_tool_response(HIGH_CONFIDENCE_PAYLOAD),
    ]
    result = interpret_incident(make_request("won't turn on"), client=client)
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
    client = mock_client(fake_tool_response(payload))
    result = interpret_incident(make_request("something is wrong"), client=client)
    assert result.requires_human_review is True
    assert "insufficient evidence" in result.review_reason


def test_missing_api_key_degrades_safely_instead_of_crashing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = interpret_incident(make_request("won't turn on"))  # no client injected
    assert result.requires_human_review is True
    assert "not configured" in result.review_reason


def test_never_invents_operational_facts():
    """The schema itself has no field capable of carrying an operational
    fact — this asserts that invariant structurally, not just by prompt."""
    from app.schemas.incident import IncidentIntelligence

    fields = set(IncidentIntelligence.model_fields.keys())
    forbidden_terms = {"availability", "inventory", "schedule", "capacity", "cost", "technician"}
    for field in fields:
        assert not any(term in field.lower() for term in forbidden_terms), field
