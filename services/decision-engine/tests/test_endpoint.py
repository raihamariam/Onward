"""Confirms the HTTP wiring for POST /incident/interpret, independent of the
interpretation logic itself (covered in test_interpret.py) and independent
of which provider is active (patches get_provider, not an SDK client)."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from tests.test_interpret import HIGH_CONFIDENCE_PAYLOAD, FakeProvider

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
    with patch(
        "app.interpret.service.get_provider",
        return_value=FakeProvider(HIGH_CONFIDENCE_PAYLOAD),
    ):
        res = client.post("/incident/interpret", json=PAYLOAD)

    assert res.status_code == 200
    body = res.json()
    assert body["incident_type"] == "power_failure"
    assert body["incident_id"] == PAYLOAD["incident_id"]
    assert body["requires_human_review"] is False


def test_incident_interpret_rejects_malformed_request():
    res = client.post("/incident/interpret", json={"description": "missing required fields"})
    assert res.status_code == 422
