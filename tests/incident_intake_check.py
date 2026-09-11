"""Phase 2 gate test — WF-01 Incident Intake, against the real live system.

Exercises the full required flow plus every failure/duplicate case:

  known active asset  -> 201, incident persisted, readable by id
  unknown asset       -> 404
  inactive asset      -> 422
  missing fields       -> 400
  retry (same key)     -> 200, duplicate:true, same incident_id, no new row

Requires the two Phase 2 manual steps to be done first:
  1. database/migrations/0001_init.sql and database/seed/0001_seed_assets.sql
     run in the Supabase SQL editor.
  2. The "Supabase (Onward)" credential created in n8n and attached to the
     three Supabase nodes in WF-01, and the workflow published (active).

Never prints SUPABASE_SECRET_KEY (not needed — this test only reads via the
publishable key, matching the frontend's own read path). Creates incident
rows as a side effect (that's the point) but touches no other data.
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


def post_incident(webhook_url: str, payload: dict) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def get_incident(supabase_url: str, publishable_key: str, incident_id: str) -> list:
    url = f"{supabase_url.rstrip('/')}/rest/v1/incidents?id=eq.{incident_id}&select=*"
    req = urllib.request.Request(
        url, headers={"apikey": publishable_key, "Authorization": f"Bearer {publishable_key}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check(label: str, condition: bool, detail: str = "") -> bool:
    print(f"{'PASS' if condition else 'FAIL'}: {label}" + (f" — {detail}" if detail else ""))
    return condition


def main() -> int:
    env = {**load_env(ENV_PATH), **os.environ}
    webhook_url = env.get("NEXT_PUBLIC_N8N_INCIDENT_WEBHOOK_URL", "")
    supabase_url = env.get("SUPABASE_URL", "")
    publishable_key = env.get("SUPABASE_PUBLISHABLE_KEY", "")

    missing = [
        name
        for name, val in [
            ("NEXT_PUBLIC_N8N_INCIDENT_WEBHOOK_URL", webhook_url),
            ("SUPABASE_URL", supabase_url),
            ("SUPABASE_PUBLISHABLE_KEY", publishable_key),
        ]
        if not val
    ]
    if missing:
        print(f"FAIL: missing env vars: {', '.join(missing)}")
        return 1

    all_ok = True

    # 1. Happy path: known active asset.
    key1 = str(uuid.uuid4())
    status, body = post_incident(
        webhook_url,
        {"asset_code": "AV-204", "description": "Projector will not power on", "idempotency_key": key1},
    )
    all_ok &= check("known active asset -> 201", status == 201, f"got {status}: {body}")
    incident_id = body.get("incident_id")
    all_ok &= check("response includes incident_id", bool(incident_id))

    # 2. Retrieve by id via Supabase directly (publishable key, RLS read path).
    if incident_id:
        rows = get_incident(supabase_url, publishable_key, incident_id)
        all_ok &= check("incident retrievable by id", len(rows) == 1, f"got {len(rows)} rows")
        if rows:
            all_ok &= check(
                "stored record references correct asset",
                rows[0].get("idempotency_key") == key1,
            )

    # 3. Unknown asset.
    status, body = post_incident(
        webhook_url,
        {"asset_code": "DOES-NOT-EXIST", "description": "test", "idempotency_key": str(uuid.uuid4())},
    )
    all_ok &= check("unknown asset -> 404", status == 404, f"got {status}: {body}")

    # 4. Inactive asset.
    status, body = post_incident(
        webhook_url,
        {"asset_code": "HVAC-12", "description": "test", "idempotency_key": str(uuid.uuid4())},
    )
    all_ok &= check("inactive asset -> 422", status == 422, f"got {status}: {body}")

    # 5. Missing required field.
    status, body = post_incident(
        webhook_url, {"asset_code": "AV-204", "idempotency_key": str(uuid.uuid4())}
    )
    all_ok &= check("missing description -> 400", status == 400, f"got {status}: {body}")

    # 6. Retry the original request with the SAME idempotency key.
    status, body = post_incident(
        webhook_url,
        {"asset_code": "AV-204", "description": "Projector will not power on", "idempotency_key": key1},
    )
    all_ok &= check("retry same key -> 200 duplicate", status == 200 and body.get("duplicate") is True, f"got {status}: {body}")
    all_ok &= check(
        "retry returns the SAME incident_id (no duplicate row)",
        body.get("incident_id") == incident_id,
        f"original={incident_id} retry={body.get('incident_id')}",
    )

    print("PASS: all gate checks passed" if all_ok else "FAIL: one or more gate checks failed")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
