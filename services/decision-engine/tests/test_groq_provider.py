"""Provider-specific tests for GroqProvider — things that can only be
exercised at this layer (response parsing, empty/malformed content) rather
than through the FakeProvider-based orchestration tests in
test_interpret.py. The Groq client itself is mocked (patched at
construction) so these run with no network call and no API key.

Real behavior against the live API (structured output actually validating,
genuine image understanding, real provider errors/rate limits) is proven
by the Phase 3 live gate (tests/incident_intelligence_check.py), not here.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.interpret.providers.groq_provider import GroqProvider


def make_response(content: str | None):
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


VALID_PAYLOAD = {
    "incident_type": "power_failure",
    "symptoms": ["device does not power on"],
    "visual_observations": [],
    "severity": "high",
    "safety_risk": False,
    "confidence": 0.9,
    "likely_faults": [],
    "required_capability": "AV_SUPPORT",
    "requires_human_review": False,
    "review_reason": None,
    "evidence_conflict": False,
}


def test_valid_structured_response_parses():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = make_response(json.dumps(VALID_PAYLOAD))
    with patch("app.interpret.providers.groq_provider.groq.Groq", return_value=mock_client):
        provider = GroqProvider(api_key="test-key-not-real")
        result = provider.complete("system", "context", None, None)
    assert result == VALID_PAYLOAD
    # forced json_schema mode was actually requested, not left to prompting alone
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["response_format"]["type"] == "json_schema"
    assert kwargs["response_format"]["json_schema"]["strict"] is True


def test_multimodal_request_includes_image_content_block():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = make_response(json.dumps(VALID_PAYLOAD))
    with patch("app.interpret.providers.groq_provider.groq.Groq", return_value=mock_client):
        provider = GroqProvider(api_key="test-key-not-real")
        provider.complete("system", "context", "ZmFrZWJhc2U2NA==", "image/jpeg")
    _, kwargs = mock_client.chat.completions.create.call_args
    user_content = kwargs["messages"][1]["content"]
    image_blocks = [b for b in user_content if b["type"] == "image_url"]
    assert len(image_blocks) == 1
    assert image_blocks[0]["image_url"]["url"] == "data:image/jpeg;base64,ZmFrZWJhc2U2NA=="


def test_empty_choices_returns_none():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(choices=[])
    with patch("app.interpret.providers.groq_provider.groq.Groq", return_value=mock_client):
        provider = GroqProvider(api_key="test-key-not-real")
        result = provider.complete("system", "context", None, None)
    assert result is None


def test_malformed_json_content_returns_none():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = make_response("not valid json {")
    with patch("app.interpret.providers.groq_provider.groq.Groq", return_value=mock_client):
        provider = GroqProvider(api_key="test-key-not-real")
        result = provider.complete("system", "context", None, None)
    assert result is None


def test_api_error_returns_none_not_raises():
    import groq as groq_module

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = groq_module.APIConnectionError(
        request=MagicMock()
    )
    with patch("app.interpret.providers.groq_provider.groq.Groq", return_value=mock_client):
        provider = GroqProvider(api_key="test-key-not-real")
        result = provider.complete("system", "context", None, None)
    assert result is None


def test_missing_api_key_raises_runtime_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    try:
        GroqProvider()
    except RuntimeError as e:
        assert "GROQ_API_KEY" in str(e)
    else:
        raise AssertionError("expected RuntimeError")
