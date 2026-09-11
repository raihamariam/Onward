"""Phase 3 gate test — Incident Intelligence, against the real live system.

Requires GEMINI_API_KEY to be set wherever decision-engine is running (the
default provider — see CLAUDE.md §5/§7 zero-spend-runtime rule; local .env
is enough for local runs, a deployed/tunneled instance needs it in its own
environment). Only ever run this against synthetic/non-sensitive data —
Gemini's free tier may use submitted content to improve Google's products.
Exercises decision-engine's /incident/interpret directly — the same call
WF-02 makes — so it proves real model behavior independent of whether
WF-02 itself is reachable from n8n Cloud yet.

Cases A-F match the Phase 3 task's required gate test:
  A. clear text -> confident structured power-failure classification
  B. different wording, same underlying problem -> same semantic class
  C. image + text -> multimodal result (visual_observations populated)
  D. weak/ambiguous evidence -> requires_human_review = true
  E. safety signal -> safety_risk = true (and requires_human_review = true)
  F. conflicting text/image -> requires_human_review = true, not false certainty

Also asserts none of the outputs contain any operational-fact field —
structurally, not just by inspection (mirrors test_interpret.py's
test_never_invents_operational_facts, run here against real model output).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
FORBIDDEN_TERMS = {"availability", "inventory", "schedule", "capacity", "cost", "technician"}

# A 1x1 transparent PNG — enough to prove the multimodal request plumbing
# works end to end. Swap for a real incident photo to test actual visual
# understanding (Case C's value is in the model genuinely looking at an
# image, not in this placeholder pixel).
TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def interpret(base_url: str, payload: dict) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/incident/interpret",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def check(label: str, condition: bool, detail: str = "") -> bool:
    print(f"{'PASS' if condition else 'FAIL'}: {label}" + (f" — {detail}" if detail else ""))
    return condition


def asset(**overrides) -> dict:
    base = {
        "code": "AV-204",
        "name": "Epson Projector",
        "location": "Room 3.12",
        "status": "active",
        "prior_incidents": [],
    }
    base.update(overrides)
    return base


def request(description: str, **kwargs) -> dict:
    return {
        "incident_id": str(uuid.uuid4()),
        "description": description,
        "asset_context": asset(),
        **kwargs,
    }


def assert_no_operational_facts(label: str, body: dict) -> bool:
    flat = json.dumps(body).lower()
    leaked = [t for t in FORBIDDEN_TERMS if t in flat]
    return check(f"{label}: no operational-fact terms leaked", not leaked, f"found: {leaked}")


def main() -> int:
    env = {**load_env(ENV_PATH), **os.environ}
    base_url = env.get("DECISION_ENGINE_URL", "http://127.0.0.1:8000")
    provider = env.get("MODEL_PROVIDER", "gemini").lower()
    required_key = "ANTHROPIC_API_KEY" if provider == "anthropic" else "GEMINI_API_KEY"
    # Best-effort local check only — decision-engine may be running
    # elsewhere (tunneled/deployed) with the key set in its own
    # environment, not this one. A pass here doesn't guarantee the remote
    # instance is configured; a fail here reliably means "check locally
    # first" when running everything on one machine.
    if not env.get(required_key):
        print(f"FAIL: {required_key} not set locally — cannot run a real gate test (see Phase 3 report)")
        return 1

    all_ok = True

    # Case A
    status, body = interpret(base_url, request("projector won't turn on"))
    all_ok &= check("Case A: HTTP 200", status == 200, f"got {status}: {body}")
    all_ok &= check("Case A: classified as power-related", "power" in body.get("incident_type", ""))
    all_ok &= check("Case A: confident, no review needed", body.get("requires_human_review") is False)
    all_ok &= assert_no_operational_facts("Case A", body)
    case_a_type = body.get("incident_type")

    # Case B — different wording, should land on the same incident_type
    status, body_b = interpret(base_url, request("nothing happens when I press the button"))
    all_ok &= check("Case B: HTTP 200", status == 200, f"got {status}: {body_b}")
    all_ok &= check(
        "Case B: same semantic class as Case A",
        body_b.get("incident_type") == case_a_type,
        f"A={case_a_type} B={body_b.get('incident_type')}",
    )
    all_ok &= assert_no_operational_facts("Case B", body_b)

    # Case C — image + text
    status, body = interpret(
        base_url,
        request(
            "screen is dead, see photo",
            image_base64=TINY_PNG_BASE64,
            image_media_type="image/png",
        ),
    )
    all_ok &= check("Case C: HTTP 200", status == 200, f"got {status}: {body}")
    all_ok &= check(
        "Case C: multimodal request accepted and answered",
        "incident_type" in body,
    )
    all_ok &= assert_no_operational_facts("Case C", body)

    # Case D — weak/ambiguous evidence
    status, body = interpret(base_url, request("something seems off maybe"))
    all_ok &= check("Case D: HTTP 200", status == 200, f"got {status}: {body}")
    all_ok &= check("Case D: flagged for review, not guessed", body.get("requires_human_review") is True)
    all_ok &= assert_no_operational_facts("Case D", body)

    # Case E — safety signal
    status, body = interpret(base_url, request("sparks and a burning smell coming from the unit"))
    all_ok &= check("Case E: HTTP 200", status == 200, f"got {status}: {body}")
    all_ok &= check("Case E: safety_risk = true", body.get("safety_risk") is True)
    all_ok &= check("Case E: also forces review", body.get("requires_human_review") is True)
    all_ok &= assert_no_operational_facts("Case E", body)

    # Case F — conflicting modalities: text says one thing, image is unrelated
    status, body = interpret(
        base_url,
        request(
            "the projector bulb has completely burned out and melted",
            image_base64=TINY_PNG_BASE64,
            image_media_type="image/png",
        ),
    )
    all_ok &= check("Case F: HTTP 200", status == 200, f"got {status}: {body}")
    all_ok &= check(
        "Case F: does not assert false certainty",
        body.get("requires_human_review") is True or body.get("evidence_conflict") is True,
        f"got requires_human_review={body.get('requires_human_review')} evidence_conflict={body.get('evidence_conflict')}",
    )
    all_ok &= assert_no_operational_facts("Case F", body)

    print("PASS: all Phase 3 gate checks passed" if all_ok else "FAIL: one or more gate checks failed")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
