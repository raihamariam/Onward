# Onward demo runbook

One controlled action prepares the demo. Nothing here requires remembering
database IDs or writing SQL.

## Before each rehearsal / the real run

```bash
uv run --project services/decision-engine python tests/demo_preflight.py
uv run --project services/decision-engine python tests/prepare_demo.py
```

`demo_preflight.py` is read-only (plus two harmless invalid-payload probes
to WF-01/WF-05a and one minimal Groq call) — safe to run as often as you
like. If it reports `ECON301 timing: FAIL`, that's expected before you've
run `prepare_demo.py` yet.

`prepare_demo.py` resets exactly the locked scenario's organisational state
(ECON301 timing, Room 2.08/1.01, technicians, spare projector, AV-204) and
starts a new demo session. It is idempotent — safe to re-run. **It never
touches `ECON301-EVENING` and never deletes any incident, execution, or
audit row.**

After it prints `PASS`, open `https://onward-smoky.vercel.app/` — it must
read `SYSTEM READY`, regardless of how many old incidents exist in
Supabase.

## Running the demo

1. Lecturer scans the AV-204 QR → `/report/AV-204` → submits.
2. The Command View locks onto that incident automatically (no manual
   action) and follows it through to completion.
3. Judge approves or rejects on screen — this calls the real WF-05a
   through `/api/approve`. Nothing is simulated.

## If the judge rejects

The screen honestly shows `RECOVERY REJECTED` — zero consequential actions
ran, by design (proven in Phase 6/7). **Never overwrite or re-decide a
rejection.** Instead:

1. Say: *"That live decision correctly stopped here — Onward recommends,
   humans decide. We'll continue with an equivalent prepared incident to
   show the execution path."*
2. Open `https://onward-smoky.vercel.app/?incident=<backup_incident_id>`
   on the presentation screen — this is the documented override, unrelated
   to the locked-on live incident.
3. Prepare a backup incident id before the demo by running the real flow
   once yourself (submit → approve) and noting the `incident_id` the
   `/report/AV-204` success screen shows.

## Resetting for another rehearsal

Just re-run `prepare_demo.py` again. A new demo session starts, the
Command View automatically drops any old lock (even mid-display) and
returns to `SYSTEM READY` on its own — no page needs to be closed, no
record needs to be deleted.

## If the Cloudflare tunnel restarts

The tunnel URL is ephemeral and decision-engine's public reachability
depends on it (`DECISION_ENGINE_PUBLIC_URL` in `.env`). If
`demo_preflight.py` reports the public tunnel check as `FAIL`:

1. Confirm exactly one `uvicorn` and one `cloudflared` process are running
   (`Get-CimInstance Win32_Process | Where-Object { $_.Name -match
   'uvicorn.exe|cloudflared.exe' }` in PowerShell).
2. If `cloudflared` isn't running: `cloudflared tunnel --url
   http://localhost:8000` and note the new `https://*.trycloudflare.com`
   URL it prints.
3. Update `DECISION_ENGINE_PUBLIC_URL` in `.env` to the new URL.
4. The matching n8n HTTP-request nodes (WF-02 "Call Decision Engine", WF-03
   "Call Decision Engine", WF-04 "Call Decision Engine", WF-05 "Recompute
   Fingerprint") each need their `url` field updated to the new tunnel and
   republished — this needs Claude Code's n8n access, or manual editing in
   the n8n UI. Do not touch any other part of those workflows.
5. Re-run `demo_preflight.py` to confirm.

## Groq

Free-tier rate limiting is real and has happened during development. Check
it exactly once with `demo_preflight.py` before going live — don't fire
extra calls "just to be sure." If it fails during the actual competition
run, the system's existing safe fallback takes over automatically
(`GENERAL_MAINTENANCE`, `requires_human_review: true`, confidence `0`) —
the UI shows this honestly, it never claims a confident AI result that
didn't happen. Note: with the fallback active, repair/replace candidates
won't appear on the recovery screen (only relocate options) — this is
correct, deterministic behaviour, not a bug (see Phase 10/11 diagnosis).

## What preflight cannot check on its own

Calendar / Slack / Gmail credentials live only in n8n's credential store —
`demo_preflight.py` reports these as `INFO`, not a guessed pass. Ask
Claude Code to verify them directly (it has n8n access) if you need a real
answer before going on stage.
