"""Phase 11 demo preflight — one concise PASS/FAIL report before going live.

Read-only wherever possible. The two exceptions, both deliberate and
harmless:

  - WF-01 / WF-05a are probed with a deliberately INVALID payload (missing
    a required field). Both webhooks validate input before touching
    Supabase, so this reliably reaches the real webhook and gets a real
    400 response -- proving the workflow is published and reachable --
    without creating an incident, an approval, or any other row.
  - Groq is checked with exactly one minimal (5-token) real completion
    call. This is a genuine API call (the task's own "check Groq once"),
    kept to the smallest possible request.

Calendar / Slack / Gmail credentials live only in n8n's own credential
store (per CLAUDE.md Sec.15) -- this script has no independent way to
verify them without either sending a real message/event (which the task
says not to do just for preflight) or duplicating a credential outside
n8n (which this project deliberately never does). Those three rows are
reported as INFO, not a guessed PASS/FAIL, with a note on how to get a
real answer when it matters.

WF-02/03/04's own workflow activation isn't independently pingable (no
public trigger, sub-workflow only) -- this script instead verifies the
decision-engine compute endpoint each one depends on, which is a stateless
pure function call with zero Supabase side effects.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

FRONTEND_URL = "https://onward-smoky.vercel.app/"
ECON301_EVENT_ID = "b8010afd-6215-4c4c-a59f-a85ecfdedca9"
ECON301_EVENING_EVENT_ID = "8692c129-75f2-4d1d-8ae4-6b2442c97112"
ROOM_208_ID = "35e3a65c-617d-4f4d-a7c2-2f682246195b"
AV204_ASSET_ID = "24939e33-7cf8-470c-95ca-9783fd0e11f1"

results: list[tuple[str, bool | None, str]] = []  # (label, True/False/None=INFO, detail)


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


def http(method: str, url: str, headers: dict | None = None, body: dict | None = None, timeout: int = 12):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return None, str(e.reason)


def check(label: str, passed: bool | None, detail: str = ""):
    results.append((label, passed, detail))


def main() -> int:
    env = load_env(ENV_PATH)
    base = env.get("SUPABASE_URL", "").rstrip("/")
    pub = env.get("SUPABASE_PUBLISHABLE_KEY", "")
    secret = env.get("SUPABASE_SECRET_KEY", "")
    incident_webhook = env.get("INCIDENT_WEBHOOK_URL", "")
    approval_webhook = env.get("APPROVAL_WEBHOOK_URL", "")
    decision_engine_public = env.get("DECISION_ENGINE_PUBLIC_URL", "")
    groq_key = env.get("GROQ_API_KEY", "")

    # Frontend
    status, _ = http("GET", FRONTEND_URL)
    check("Frontend", status == 200, f"HTTP {status}")

    # Decision engine local
    status, _ = http("GET", "http://localhost:8000/health")
    check("Decision engine (local)", status == 200, f"HTTP {status}")

    # Decision engine public (tunnel)
    if decision_engine_public:
        status, _ = http("GET", decision_engine_public.rstrip("/") + "/health")
        check("Decision engine (public tunnel)", status == 200, f"HTTP {status} -- {decision_engine_public}")
    else:
        check("Decision engine (public tunnel)", None, "DECISION_ENGINE_PUBLIC_URL not set in .env")

    # Supabase
    if base and pub:
        status, _ = http("GET", f"{base}/rest/v1/assets?limit=1", {"apikey": pub, "Authorization": f"Bearer {pub}"})
        check("Supabase", status == 200, f"HTTP {status}")
    else:
        check("Supabase", False, "SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY missing")

    # WF-01: harmless invalid-payload probe (expect 400, creates nothing)
    if incident_webhook:
        status, body = http("POST", incident_webhook, {"Content-Type": "application/json"}, {"asset_code": "AV-204"})
        check("WF-01 (Incident Intake)", status == 400, f"HTTP {status} (expect 400 invalid_request)")
    else:
        check("WF-01 (Incident Intake)", False, "INCIDENT_WEBHOOK_URL missing")

    # WF-02/03/04: decision-engine compute path each one calls (pure, stateless, no Supabase writes)
    if decision_engine_public:
        de = decision_engine_public.rstrip("/")
        status, _ = http("POST", de + "/incident/interpret", {"Content-Type": "application/json"},
                          {"incident_id": "00000000-0000-0000-0000-000000000000", "description": "preflight probe",
                           "image_base64": None, "image_media_type": None,
                           "asset_context": {"code": "AV-204", "name": "Epson Projector", "location": "Room 3.12", "status": "active", "prior_incidents": []}})
        check("WF-02 compute path (/incident/interpret)", status == 200, f"HTTP {status}")

        status, _ = http("POST", de + "/impact/calculate", {"Content-Type": "application/json"},
                          {"incident_id": "00000000-0000-0000-0000-000000000000", "asset_id": "x", "asset_code": "AV-204",
                           "required_capability": None, "dependency_edges": [], "locations": [], "events": []})
        check("WF-03 compute path (/impact/calculate)", status == 200, f"HTTP {status}")

        status, _ = http("POST", de + "/recovery/plan", {"Content-Type": "application/json"},
                          {"incident_id": "00000000-0000-0000-0000-000000000000", "incident_capability": None,
                           "operation_capability": None, "people_affected": None, "deadline_minutes": None,
                           "technicians": [], "inventory": [], "alternate_locations": []})
        check("WF-04 / WF-05 compute path (/recovery/plan)", status == 200, f"HTTP {status}")
    else:
        check("WF-02 compute path (/incident/interpret)", None, "no public decision-engine URL configured")
        check("WF-03 compute path (/impact/calculate)", None, "no public decision-engine URL configured")
        check("WF-04 / WF-05 compute path (/recovery/plan)", None, "no public decision-engine URL configured")

    # WF-05a: harmless invalid-payload probe (expect 400, creates nothing)
    if approval_webhook:
        status, body = http("POST", approval_webhook, {"Content-Type": "application/json"}, {"incident_id": "x"})
        check("WF-05a (Recovery Approval)", status == 400, f"HTTP {status} (expect 400 invalid_request)")
    else:
        check("WF-05a (Recovery Approval)", False, "APPROVAL_WEBHOOK_URL missing")

    # Groq: exactly one minimal real call
    if groq_key:
        try:
            import groq  # type: ignore
            client = groq.Groq(api_key=groq_key)
            resp = client.chat.completions.create(model="qwen/qwen3.8-27b", messages=[{"role": "user", "content": "say OK"}], max_tokens=5)
            check("Groq availability", True, resp.choices[0].message.content or "")
        except ImportError:
            check("Groq availability", None, "groq package not installed in this Python env -- run from services/decision-engine's venv (uv run) to check")
        except Exception as e:  # noqa: BLE001 -- reporting any failure as FAIL is the point here
            check("Groq availability", False, f"{type(e).__name__}: {str(e)[:150]}")
    else:
        check("Groq availability", False, "GROQ_API_KEY missing")

    # Calendar / Slack / Gmail: credentials live only in n8n, not independently checkable here
    check("Onward Demo Calendar", None, "credentials live in n8n only -- verify via a real run, or ask Claude Code to check with n8n MCP access")
    check("Slack", None, "credentials live in n8n only -- same as above")
    check("Gmail", None, "credentials live in n8n only -- same as above")

    # ECON301 timing
    if base and pub:
        status, body = http("GET", f"{base}/rest/v1/events?id=eq.{ECON301_EVENT_ID}&select=starts_at,attendee_count",
                             {"apikey": pub, "Authorization": f"Bearer {pub}"})
        try:
            row = json.loads(body)[0]
            from datetime import datetime, timezone
            starts_at = datetime.fromisoformat(row["starts_at"].replace("Z", "+00:00"))
            minutes_out = (starts_at - datetime.now(timezone.utc)).total_seconds() / 60
            fresh = 0 < minutes_out < 60 and row["attendee_count"] == 84
            check("ECON301 timing", fresh, f"starts in {minutes_out:.1f} min, {row['attendee_count']} attendees (run tests/prepare_demo.py if stale)")
        except Exception:
            check("ECON301 timing", False, f"could not read event row (HTTP {status})")
    else:
        check("ECON301 timing", False, "Supabase not configured")

    # Room 2.08 available
    if base and pub:
        status, body = http("GET", f"{base}/rest/v1/locations?id=eq.{ROOM_208_ID}&select=status",
                             {"apikey": pub, "Authorization": f"Bearer {pub}"})
        try:
            row = json.loads(body)[0]
            check("Room 2.08 available", row["status"] == "available", f"status={row['status']}")
        except Exception:
            check("Room 2.08 available", False, f"could not read location row (HTTP {status})")

    # AV-204 active
    if base and pub:
        status, body = http("GET", f"{base}/rest/v1/assets?id=eq.{AV204_ASSET_ID}&select=status",
                             {"apikey": pub, "Authorization": f"Bearer {pub}"})
        try:
            row = json.loads(body)[0]
            check("AV-204 active", row["status"] == "active", f"status={row['status']}")
        except Exception:
            check("AV-204 active", False, f"could not read asset row (HTTP {status})")

    print("ONWARD DEMO PREFLIGHT\n")
    width = max(len(label) for label, _, _ in results)
    all_pass = True
    for label, passed, detail in results:
        tag = "PASS" if passed is True else "FAIL" if passed is False else "INFO"
        if passed is False:
            all_pass = False
        print(f"{label.ljust(width)}  {tag}   {detail}")

    print()
    print("PASS overall" if all_pass else "FAIL -- one or more checks failed, see above")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
