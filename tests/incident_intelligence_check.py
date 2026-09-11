"""Phase 3 gate test — Incident Intelligence, against the real live system.

Requires GROQ_API_KEY to be set wherever decision-engine is running (the
active provider — see CLAUDE.md §5/§7 zero-spend-runtime rule; local .env
is enough for local runs, a deployed/tunneled instance needs it in its own
environment). Only ever run this against synthetic/non-sensitive data — a
free-tier provider's terms typically permit using submitted content to
improve their products. Exercises decision-engine's /incident/interpret
directly — the same call WF-02 makes — so it proves real model behavior
independent of whether WF-02 itself is reachable from n8n Cloud yet.

Cases A-F match the Phase 3 task's required gate test:
  A. clear text -> confident structured power-failure classification
  B. different wording, same underlying problem -> same semantic class
  C. image + text -> the image itself must materially change the result
     (same neutral text, two different real fixture images; not a
     text-only request with an unused image)
  D. weak/ambiguous evidence -> requires_human_review = true
  E. safety signal -> safety_risk = true (and requires_human_review = true)
  F. conflicting text/image -> requires_human_review / evidence_conflict,
     not false certainty

Also asserts none of the outputs contain any operational-fact field —
structurally, not just by inspection (mirrors test_interpret.py's
test_never_invents_operational_facts, run here against real model output).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
# Phrases, not bare words: "technician" alone collides with the legitimately
# permitted required_capability field (e.g. "AV Technician" is a role name,
# not an invented fact). What's actually forbidden is asserting operational
# STATE — a specific technician being available, a specific schedule slot,
# a specific stock count — not naming the kind of skill needed.
FORBIDDEN_PHRASES = {
    "technician available",
    "technician is available",
    "in stock",
    "inventory count",
    "next available",
    "scheduled for",
    "authorized by",
    "authorised by",
}


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


def fixture_b64(name: str) -> str:
    return base64.b64encode((FIXTURES / name).read_bytes()).decode()


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
    leaked = [t for t in FORBIDDEN_PHRASES if t in flat]
    return check(f"{label}: no operational-fact phrases leaked", not leaked, f"found: {leaked}")


def main() -> int:
    env = {**load_env(ENV_PATH), **os.environ}
    base_url = env.get("DECISION_ENGINE_URL", "http://127.0.0.1:8000")
    provider = env.get("MODEL_PROVIDER", "groq").lower()
    required_key = "GEMINI_API_KEY" if provider == "gemini" else "GROQ_API_KEY"
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
    all_ok &= check("Case A: confident, no review needed", body.get("requires_human_review") is False)
    all_ok &= assert_no_operational_facts("Case A", body)
    case_a_type = body.get("incident_type", "")

    # Case B — different wording, should land on a similar class to Case A
    # (compared loosely — a real model won't always produce byte-identical
    # category strings, so this checks for a shared keyword rather than
    # exact equality).
    status, body_b = interpret(base_url, request("nothing happens when I press the button"))
    all_ok &= check("Case B: HTTP 200", status == 200, f"got {status}: {body_b}")
    case_b_type = body_b.get("incident_type", "")
    shared_word = bool(set(case_a_type.lower().replace("_", " ").split()) & set(case_b_type.lower().replace("_", " ").split()))
    all_ok &= check(
        "Case B: semantically similar class to Case A", shared_word, f"A={case_a_type!r} B={case_b_type!r}"
    )
    all_ok &= assert_no_operational_facts("Case B", body_b)

    # Case C — the image must MATERIALLY change the result. Same neutral
    # text against two different real (synthetic but visually distinct)
    # fixture images: fixtures/damaged.jpg (sparks/arcing imagery) vs
    # fixtures/calm.jpg (plain, nothing alarming). If the image weren't
    # actually being read, both calls would produce the same output.
    neutral_text = "Please assess the equipment shown in the photo."
    status_c1, body_c1 = interpret(
        base_url, request(neutral_text, image_base64=fixture_b64("damaged.jpg"), image_media_type="image/jpeg")
    )
    status_c2, body_c2 = interpret(
        base_url, request(neutral_text, image_base64=fixture_b64("calm.jpg"), image_media_type="image/jpeg")
    )
    all_ok &= check("Case C: both calls HTTP 200", status_c1 == 200 and status_c2 == 200)
    materially_different = (
        body_c1.get("safety_risk") != body_c2.get("safety_risk")
        or body_c1.get("severity") != body_c2.get("severity")
        or body_c1.get("visual_observations") != body_c2.get("visual_observations")
    )
    all_ok &= check(
        "Case C: image content materially changes the result",
        materially_different,
        f"damaged={body_c1.get('safety_risk')}/{body_c1.get('severity')} "
        f"calm={body_c2.get('safety_risk')}/{body_c2.get('severity')}",
    )
    all_ok &= assert_no_operational_facts("Case C (damaged)", body_c1)
    all_ok &= assert_no_operational_facts("Case C (calm)", body_c2)

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

    # Case F — conflicting modalities: confident text claim contradicted by
    # a calm real image (the same "calm.jpg" used above, which shows no
    # damage at all).
    status, body = interpret(
        base_url,
        request(
            "The projector's lamp has completely burned out and melted — "
            "definitely needs a full lamp replacement, no other explanation.",
            image_base64=fixture_b64("calm.jpg"),
            image_media_type="image/jpeg",
        ),
    )
    all_ok &= check("Case F: HTTP 200", status == 200, f"got {status}: {body}")
    all_ok &= check(
        "Case F: does not assert false certainty",
        body.get("requires_human_review") is True or body.get("evidence_conflict") is True,
        f"got requires_human_review={body.get('requires_human_review')} evidence_conflict={body.get('evidence_conflict')}",
    )
    all_ok &= assert_no_operational_facts("Case F", body)

    # Reliability: malformed image data must degrade safely, not crash.
    status, body = interpret(
        base_url, request("test", image_base64="not-valid-base64-###", image_media_type="image/jpeg")
    )
    all_ok &= check(
        "Malformed image_base64 degrades safely (HTTP 200, review-flagged)",
        status == 200 and body.get("requires_human_review") is True,
        f"got {status}: {body}",
    )

    print("PASS: all Phase 3 gate checks passed" if all_ok else "FAIL: one or more gate checks failed")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
