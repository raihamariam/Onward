"""Phase 11 demo preparation — the one controlled action before a rehearsal
or the real competition run.

Prepares exactly the locked demo scenario's organisational state and then
starts a new demo session so the Command View (apps/web/app/page.tsx) shows
a clean SYSTEM READY, ignoring any older incidents already in the database.

What this script does (all via the Supabase secret key, same as every other
operator/seed script in this repo):

1. Pushes ECON301 (the correct, 84-attendee event — never ECON301-EVENING)
   forward so it starts ~13 minutes from now, reproducing the locked
   scenario's deadline pressure.
2. Restores Room 2.08 and Room 1.01 to "available".
3. Restores the two AV_SUPPORT technicians (Jordan Lee, Alex Rivera) to
   their expected ETA/status.
4. Restores the spare projector inventory to quantity 2 / available.
5. Confirms AV-204 is "active" (fixes it if some earlier test left it
   otherwise).
6. Inserts a new demo_sessions row — this is the ONLY thing that changes
   what the live Command View shows; every incident reported before this
   timestamp stays exactly where it is, nothing is deleted.

Safe to re-run any number of times (idempotent): every write here sets a
known-good value, it never depends on the previous state. Requires
database/migrations/0009_demo_sessions.sql to have been applied — if the
demo_sessions table doesn't exist yet, this script says so and stops
without silently skipping the session reset.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

# Real IDs, established across Phases 4-10 — see database/seed/*.sql.
ECON301_EVENT_ID = "b8010afd-6215-4c4c-a59f-a85ecfdedca9"  # 84 attendees — the locked scenario. NOT ECON301-EVENING.
ROOM_208_ID = "35e3a65c-617d-4f4d-a7c2-2f682246195b"
ROOM_101_ID = "c8c38300-ab4a-4bb1-82ea-09b4b0f9fda2"
JORDAN_LEE_ID = "ea83f662-453f-4713-89de-e7363330c777"
ALEX_RIVERA_ID = "5484a203-c149-4468-9849-a3ed767ff5f8"
SPARE_PROJECTOR_ID = "23afdfb2-1c04-4c29-aa4f-9885058286d2"
AV204_ASSET_ID = "24939e33-7cf8-470c-95ca-9783fd0e11f1"

DEADLINE_MINUTES = 13
EVENT_DURATION_MINUTES = 60


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


def request(method: str, url: str, key: str, body: dict | None = None) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def patch(base: str, key: str, table: str, row_id: str, fields: dict) -> bool:
    status, body = request("PATCH", f"{base}/rest/v1/{table}?id=eq.{row_id}", key, fields)
    ok = status in (200, 204)
    print(f"  {'OK' if ok else 'FAIL'}  {table}/{row_id[:8]}... -> {fields}  (HTTP {status})")
    if not ok:
        print(f"        {body[:200]}")
    return ok


def main() -> int:
    env = load_env(ENV_PATH)
    base = env.get("SUPABASE_URL", "").rstrip("/")
    secret = env.get("SUPABASE_SECRET_KEY", "")
    if not base or not secret:
        print("FAIL: SUPABASE_URL / SUPABASE_SECRET_KEY missing from .env")
        return 1

    now = datetime.now(timezone.utc)
    starts_at = now + timedelta(minutes=DEADLINE_MINUTES)
    ends_at = starts_at + timedelta(minutes=EVENT_DURATION_MINUTES)

    print("=== Onward demo preparation ===")
    print(f"now (UTC): {now.isoformat()}")
    print(f"ECON301 will start at: {starts_at.isoformat()}  (~{DEADLINE_MINUTES} min from now)")
    print()

    print("1. ECON301 timing (NOT ECON301-EVENING):")
    ok = patch(base, secret, "events", ECON301_EVENT_ID, {
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
    })

    print("2. Room availability:")
    ok &= patch(base, secret, "locations", ROOM_208_ID, {"status": "available"})
    ok &= patch(base, secret, "locations", ROOM_101_ID, {"status": "available"})

    print("3. Technician state:")
    ok &= patch(base, secret, "technicians", JORDAN_LEE_ID, {"status": "available", "eta_minutes": 45})
    ok &= patch(base, secret, "technicians", ALEX_RIVERA_ID, {"status": "available", "eta_minutes": 28})

    print("4. Replacement inventory:")
    ok &= patch(base, secret, "inventory", SPARE_PROJECTOR_ID, {"status": "available", "quantity": 2})

    print("5. AV-204 asset:")
    ok &= patch(base, secret, "assets", AV204_ASSET_ID, {"status": "active"})

    print("6. Starting new demo session (Command View will now show SYSTEM READY):")
    status, body = request("POST", f"{base}/rest/v1/demo_sessions", secret, {"started_at": now.isoformat()})
    if status in (200, 201):
        print(f"  OK  demo_sessions row created -> {body}")
    else:
        print(f"  FAIL  HTTP {status}: {body[:300]}")
        if status == 404 or "relation" in body.lower():
            print("  -> database/migrations/0009_demo_sessions.sql has not been applied yet.")
            print("     Run it in the Supabase SQL Editor, then re-run this script.")
        ok = False

    print()
    if ok:
        print("PASS: demo prepared. Open https://onward-smoky.vercel.app/ -- it should read SYSTEM READY.")
        return 0
    print("FAIL: one or more preparation steps failed -- see above before starting the demo.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
