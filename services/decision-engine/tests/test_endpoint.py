"""Confirms the HTTP wiring for POST /incident/interpret, independent of the
interpretation logic itself (covered in test_interpret.py)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.interpret.service import TOOL_NAME
from app.main import app

client = TestClient(app)

PAYLOAD = {
    "incident_id": "11111111-1111-1111-1111-111111111111",
    "description": "projector won't turn on",
    "asset_context": {
        "code": "AV-204",
        "name": "Epson Projector",
        "location": "Room 3.12",
        "status": "active",
        "prior_incidents": [],
    },
}


def test_incident_interpret_endpoint_returns_valid_schema():
    fake_input = {
        "incident_type": "power_failure",
        "symptoms": ["device does not power on"],
        "visual_observations": [],
        "severity": "high",
        "safety_risk": False,
        "confidence": 0.9,
        "likely_faults": [],
        "required_capability": "AV_SUPPORT",
        "requires_human_review": False,
        "evidence_conflict": False,
    }
    fake_response = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", name=TOOL_NAME, input=fake_input)]
    )
    mock_anthropic_client = MagicMock()
    mock_anthropic_client.messages.create.return_value = fake_response

    with patch("app.interpret.service.anthropic.Anthropic", return_value=mock_anthropic_client):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-not-real"}):
            res = client.post("/incident/interpret", json=PAYLOAD)

    assert res.status_code == 200
    body = res.json()
    assert body["incident_type"] == "power_failure"
    assert body["incident_id"] == PAYLOAD["incident_id"]
    assert body["requires_human_review"] is False


def test_incident_interpret_rejects_malformed_request():
    res = client.post("/incident/interpret", json={"description": "missing required fields"})
    assert res.status_code == 422
