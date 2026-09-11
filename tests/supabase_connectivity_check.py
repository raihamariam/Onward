"""Phase 1 Supabase connectivity check — smallest safe test possible.

Confirms SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY / SUPABASE_SECRET_KEY in the
local .env are present and reach the live Supabase project's Data API.

Never prints credential values — only presence, length, and HTTP status
codes. Creates nothing: no tables, no schema, no rows. Parses .env with plain
string splitting (no `source`/shell eval) so a value containing shell
metacharacters can never be echoed or executed.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
REQUIRED = ["SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SECRET_KEY"]


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


def check_endpoint(url: str, api_key: str, label: str) -> bool:
    req = urllib.request.Request(
        url, headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"{label} -> HTTP {resp.status}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read(300).decode("utf-8", errors="replace")
        print(f"{label} -> HTTP {e.code} : {body}")
        if e.code == 401 and "Secret API key required" in body:
            # The schema-introspection root endpoint is intentionally
            # secret-key-only in Supabase's current key system. A
            # publishable key being scoped-rejected here (rather than
            # "invalid API key") is proof the key is valid and recognized,
            # not a connectivity failure.
            print("  (expected: this endpoint requires the secret key by design — key is valid)")
            return True
        # Any other 401/403 means the key itself was rejected as invalid.
        return e.code not in (401, 403)
    except urllib.error.URLError as e:
        print(f"{label} -> unreachable ({e.reason})")
        return False


def main() -> int:
    merged = {**load_env(ENV_PATH), **os.environ}

    missing = [k for k in REQUIRED if not merged.get(k)]
    for k in REQUIRED:
        v = merged.get(k, "")
        status = f"present ({len(v)} chars)" if v else "MISSING"
        print(f"{k}: {status}")

    if missing:
        print(f"FAIL: missing {', '.join(missing)}")
        return 1

    base = merged["SUPABASE_URL"].rstrip("/")
    ok_pub = check_endpoint(f"{base}/rest/v1/", merged["SUPABASE_PUBLISHABLE_KEY"], "Data API via publishable key")
    ok_secret = check_endpoint(f"{base}/rest/v1/", merged["SUPABASE_SECRET_KEY"], "Data API via secret key")

    if ok_pub and ok_secret:
        print("PASS: Supabase reachable with both provided keys")
        return 0
    print("FAIL: one or more keys did not reach a valid Supabase project")
    return 1


if __name__ == "__main__":
    sys.exit(main())
