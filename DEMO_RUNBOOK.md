# Onward demo runbook

One controlled action prepares the demo. Nothing here requires remembering
database IDs or writing SQL.

## Before each rehearsal / the real run

The decision-engine runs locally and its public dev tunnel (Cloudflare
Quick Tunnel) rotates URL every restart, which four n8n nodes depend on —
so start with the runtime hardening procedure, not `prepare_demo.py`
directly:

```bash
python tests/demo_runtime.py start
```

Ensures exactly one decision-engine process and exactly one fresh tunnel
are up, validates the tunnel is genuinely publicly reachable, and prints
the new URL. **Then** ask Claude Code: *"Update WF-02, WF-03, WF-04, and
WF-05's decision-engine HTTP node to `<the printed URL>` and republish all
four."* (Or edit the four HTTP nodes by hand in the n8n editor if Claude
Code isn't available — see "Runtime hardening: the tunnel-refresh
procedure" below for exactly which node in each workflow.)

```bash
python tests/demo_runtime.py finish
```

Re-checks health, then runs `demo_preflight.py` and `prepare_demo.py` for
you (see below for what each does), and confirms the public Command View
reads SYSTEM READY. Full details, safety rules, and the exact expected
output: see "Runtime hardening: the tunnel-refresh procedure" below.

If the tunnel is already known-good (e.g. earlier in the same session) and
you only need to reset the scenario's timing/state, the two underlying
scripts can still be run directly:

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

## Runtime hardening: the tunnel-refresh procedure

If `demo_preflight.py` reports the public tunnel check (or any of the
WF-02/03/04 compute-path checks) as `FAIL`, the Cloudflare Quick Tunnel has
gone stale — run the full procedure from the top of this document
(`tests/demo_runtime.py start`, then the n8n update, then `tests/
demo_runtime.py finish`). What `start` actually does, precisely:

1. **Decision engine.** Checks which process (if any) actually owns the
   listening socket on `:8000` — not a process-name guess, the real
   listener. Starts one (`uv run uvicorn app.main:app --host 0.0.0.0
   --port 8000`, no `--reload`) only if none is running. More than one
   listener is reported as a FAIL rather than silently picked between —
   that needs a human to look at it.
2. **Tunnel.** Finds every cloudflared process whose command line contains
   exactly `--url http://localhost:8000` (this project's decision-engine,
   nothing else), prints each one's pid/parent/start-time/command line,
   closes it (a Quick Tunnel URL can never be renewed — a stale one has to
   go before a fresh one starts), then starts exactly one new tunnel.
   **Safety rule, deliberate and non-negotiable:** it will never act on a
   cloudflared process for any other `--url`, or on any process that
   merely happens to contain the word "cloudflared" somewhere in its own
   text (this was an actual bug caught during development — the
   inspection query's own command line matched the search filter it was
   running, until the query was tightened to exclude `powershell.exe`).
3. **Validation.** Polls the new URL's `/health` with a public-DNS (1.1.1.1)
   fallback for the few seconds a brand-new `*.trycloudflare.com`
   subdomain sometimes needs before this network's local resolver catches
   up — a real, reproducible lag seen repeatedly here, not a tunnel
   problem.
4. Writes the URL into `.env`'s `DECISION_ENGINE_PUBLIC_URL` and stops.

**Then, the one step that isn't scriptable:** ask Claude Code to update
WF-02 "Call Decision Engine" (`/incident/interpret`), WF-03 "Call Decision
Engine" (`/impact/calculate`), WF-04 "Call Decision Engine"
(`/recovery/plan`), and WF-05 "Recompute Fingerprint" (`/recovery/plan`)
to the new URL and republish all four — this needs n8n's own access
(Claude Code's existing MCP connection), which is why this isn't a single
one-shot script; provisioning a separate n8n API credential just to avoid
that one manual step would mean adding a new access path, not reusing the
one that's already there. Without Claude Code, edit those same four nodes
by hand in the n8n editor. Do not touch any other part of any of the four
workflows.

Finally: `tests/demo_runtime.py finish` — re-checks health, runs
`demo_preflight.py`, runs `prepare_demo.py`, and confirms the public
Command View reads SYSTEM READY. Expect every row PASS (Groq may
legitimately read INFO — see below):

```
Local decision engine: PASS
Public tunnel: PASS
WF-02 URL: PASS
WF-03 URL: PASS
WF-04 URL: PASS
WF-05 URL: PASS
Groq: PASS/INFO
Supabase: PASS
ECON301: PASS
Room 2.08: PASS
Frontend: PASS
Command View: SYSTEM READY

ONWARD DEMO RUNTIME: READY
```

If anything reads FAIL, fix that one thing and re-run rather than
proceeding to record.

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
