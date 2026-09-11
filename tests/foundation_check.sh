#!/usr/bin/env bash
# Phase 1 foundation check: proves the web app and decision-engine are both
# reachable at the same time. Does not exercise any business logic — there
# isn't any yet. Run each service in its own terminal first:
#
#   cd apps/web && npm run dev
#   cd services/decision-engine && uv run uvicorn app.main:app --port 8000
#
# Then run this script.
set -euo pipefail

WEB_URL="${WEB_URL:-http://127.0.0.1:3000/api/health}"
ENGINE_URL="${ENGINE_URL:-http://127.0.0.1:8000/health}"

check() {
  local name="$1" url="$2"
  echo "checking $name ($url)"
  local body
  body="$(curl -sf "$url")" || { echo "FAIL: $name unreachable"; exit 1; }
  echo "  -> $body"
}

check "web" "$WEB_URL"
check "decision-engine" "$ENGINE_URL"

echo "PASS: both services reachable"
