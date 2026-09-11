# CLAUDE.md — Onward (Team Unity)

Operating manual for every Claude Code session working in this repository. Source memory lives in `ONWARD_MASTER_MEMORY_VAULT.md` — that file is preserved history, not instructions. This file is the instructions. If the two conflict, this file wins for *how to build*; the vault still wins for *what the product means*.

---

## 0. How this file relates to the vault

This architecture was derived from the vault by critically re-evaluating it, not by copying it. Where this file diverges from the vault, it is deliberate. The three changes that matter most:

1. **The Claude call moves into the decision-engine service, not into an n8n node.** The vault had n8n calling Claude directly inside WF‑02. Instead, the FastAPI service owns the prompt, the forced structured-output schema, and the validate‑or‑retry logic, as versioned, unit-testable Python. n8n still triggers it and still owns *when* it happens — orchestration stays in n8n — but the fragile, hard-to-diff, hard-to-unit-test part (prompt + schema enforcement) lives in code that can be tested with mocked API responses. n8n node configuration cannot be unit tested; a Python function can.
2. **There is no agent in this system.** The vault already resisted multi-agent hype, but still called its AI step an "agent." It isn't one — it never loops, never chooses its own tools, never takes multiple turns. It is a single-shot, schema-forced LLM function call: `interpret_incident(inputs) -> IncidentReport`. Calling it a function instead of an agent is not a rename for its own sake — it changes how you build and test it (fixture-in, schema-out, no tool-loop failure modes to defend against).
3. **The decision-engine service is stateless.** It never touches Postgres. n8n fetches all resource state (asset rows, dependency edges, event data, technician/inventory/room availability, retrieved knowledge chunks) and passes it as JSON. This makes every endpoint a pure function: same input, same output, trivially testable with `pytest`, no database mocking required. It also means the "AI interprets, Python validates reality, n8n orchestrates, Postgres stores truth" separation from the vault is actually enforced by the code structure, not just stated as a principle.

Everything else below either keeps the vault's decisions (they were sound) or explains a change with a reason. Do not re-introduce something this file removed without re-reading why it was removed (see §1).

---

## 1. Rejected alternatives (read before "improving" the architecture)

A future session, or a well-meaning refactor, will be tempted to add one of these. Each was considered and explicitly rejected. Re-adding one requires a new, real requirement — not familiarity or hype.

| Considered | Rejected because |
|---|---|
| **LangChain / LangGraph** for the incident-interpretation step | It's a single forced-schema LLM call, not a chain or a graph. LangChain adds an abstraction layer over the Anthropic SDK that makes the call harder to unit test and debug, for zero functional gain at this scope. |
| **MCP server exposing our own tools** (RAG search, asset lookup) to the model | Only one client ever calls these tools — our own decision-engine process. MCP earns its cost when multiple independent clients need a shared, standardized tool surface, or when you're consuming someone else's MCP server. Here it would just be a protocol wrapper around a function call. |
| **Agentic tool-use loop** (model decides when to retrieve, when to ask a clarifying question) | Retrieval is cheap and the corpus is tiny — always retrieve top‑k, every time, deterministically, before the model runs. Clarification-needed is just a field in the structured output (`requires_human_review`), not a tool the model invokes. A loop adds unpredictable latency and a new failure mode (the model never stops looping) for no behavior we actually need. |
| **Neo4j / dedicated graph database** for the Impact Graph | The graph is a handful of nodes, 2–4 hops deep. A Postgres recursive CTE over an adjacency table answers every traversal we need and keeps "Postgres is the one source of organizational truth" true, which matters for both reliability and the Track 2 story. A second database with its own query language and ops burden buys nothing at this scale. |
| **Pinecone / Weaviate / Qdrant** for vector search | pgvector inside the same Postgres instance handles a few hundred knowledge chunks without breaking a sweat, and keeps the audit/observability story ("one database holds the truth") intact. A separate vector store is a second thing to keep in sync and monitor. |
| **OR-tools / a real constraint solver** for recovery planning | We evaluate 2–5 hand-generated candidate plans against a handful of boolean/numeric constraints (capacity, time window, availability, safety). That's a few `if` statements per candidate, not a CSP. A solver is the right tool when the search space is combinatorial; ours isn't. |
| **Kubernetes, Kafka, RabbitMQ, a service mesh, Redis** | No component here needs independent horizontal scaling, a message bus, or a cache faster than a Postgres row lookup, at hackathon scale or at the "first few real customers" scale this needs to demo a path toward. Each would be infrastructure with no job. |
| **Docker/docker-compose for local dev** | Two lightweight processes (`npm run dev`, `uv run uvicorn`) start in seconds natively on the dev machine. Containerizing them adds Dockerfiles, a compose file, and a rebuild step to every iteration for zero reliability gain at this stage — reconsider only when deploying, if the target platform needs it. |
| **Poetry / pip-tools for the decision-engine** | `uv` was already available in this environment and does dependency resolution, locking (`uv.lock`), and venv management faster and with fewer moving parts than Poetry. No reason to add a second, slower tool that does the same job. |
| **`instructor` library** for structured Claude output | Genuinely useful for exactly this problem (validated-Pydantic-object-from-LLM-call with retry) — but it wraps the Anthropic SDK client directly, and our Claude call already lives in one place (decision-engine's `/incident/interpret`) where we control the retry loop explicitly in ~20 lines. Adding a dependency to save 20 lines of code we need to fully understand anyway (for the safety/confidence branching) isn't worth it. Reconsider if the retry/validation logic grows materially more complex. |

If you find yourself reaching for one of these, first ask: *what breaks without it, specifically, in this system, at this scale* — not "is it good practice in general."

---

## 2. Project identity

**Team:** Team Unity
**Project:** Onward
**Thesis:** Onward is an AI operational-response layer that turns physical-world incidents into coordinated business recovery. *When the physical world breaks, the business keeps moving.* We don't automate fixing what broke — we automate everything that needs to happen **because** it broke.
**Central object:** the operation, not the work order.
**Primary hackathon track:** Track 2 — Best Business Use Case & End-to-End Integration. Track 1 (Creativity & Innovation) is a secondary strength that falls out of Track 2 work; do not optimize for it separately.
**Non-negotiable shape of the product:**

```
physical incident → operational impact → feasible recovery → coordinated execution
```

If the system ever collapses to `photo → AI diagnosis → work order`, it has failed conceptually, regardless of how well that narrower thing works. Every build decision should be checked against this shape.

Demo narrative, pitch timing, judge-interaction design, and market positioning are preserved in full in `ONWARD_MASTER_MEMORY_VAULT.md` (§§3, 5, 9, 10, 24, 25). That material is real and will be used — it is deliberately not duplicated here because this file governs the current phase, and the current phase is not demo work.

---

## 3. Current phase

**Phase A — System build. Active now.**

Phase B — demo/presentation (UI polish, pitch rehearsal, judge-interaction scripting, staging) does not start until every item in the Definition of Done (§16) is true. If you are asked to make the dashboard "look better" or "more impressive" before that gate is met, push back and point to this section — polish on a system that doesn't yet work end-to-end is wasted effort and actively risks the demo.

---

## 4. Product invariants (never change these without the user explicitly asking)

- The core loop stays: incident → **impact** (what does this threaten) → **feasible recovery** (what can we actually do) → **coordinated execution** (n8n changes real systems) → **audit**. Do not simplify away the impact or recovery steps.
- The recovery recommendation must be **computed from real data**, never hardcoded. If `if projector_broken: recommend Room 2.08` ever appears anywhere, that is a bug, not a shortcut. The test for this: changing a single row in the seed data (room availability, technician ETA, event capacity) must be able to change which plan wins, with no code change.
- AI interprets ambiguous, multimodal, messy reality. It never invents operational facts — inventory counts, room capacity, technician availability, event timing, cost, or authorization. Those come from the database, always.
- Consequential actions (moving people, spending money, changing a schedule, cancelling something) require human approval before execution. Safety-risk incidents (sparks, smoke, gas, high voltage, dangerous machinery, medical-equipment risk) never receive automated repair suggestions — they escalate immediately.
- n8n is the orchestration layer end to end. It is not being replaced by a bigger Python backend or by giving the LLM more autonomy. If a future session is tempted to move sequencing logic out of n8n and into code "for reliability," that is backwards — see §5.
- Real integrations must actually do the thing claimed. If a screen says "Calendar updated," a calendar event must exist. No fake success animations.

---

## 5. Technical principles

**AI vs. deterministic logic.** AI's job is understanding: turning a photo + a spoken sentence + asset context into a structured, typed incident. Everything downstream of that — is this room available, is this technician free, does this plan fit in the time window, what does this actually cost — is deterministic code reading real state. The test for "should this be an LLM call": *does answering it require understanding ambiguous human input, or does it require reading a fact that exists in a database?* If it's the latter, it is not an LLM's job, ever, even "just this once for the demo."

**Zero-spend runtime (decided in Phase 3).** Onward's *running system* must not bill against any paid API or against the Anthropic subscription this development session itself runs on — those are two separate things, and conflating them was the mistake to avoid. The model provider behind incident interpretation is swappable (`app/interpret/providers/`, `MODEL_PROVIDER` env var) specifically so the runtime can sit on a free tier (Gemini, by default) while development tooling (this Claude Code session) remains unaffected. A free tier's terms typically permit the provider to use submitted content to improve their products — so only synthetic/non-sensitive hackathon data (the seeded assets, test incident descriptions) may ever be sent to it; this is a hard rule, not a preference, until a paid tier or a provider with different terms is deliberately chosen.

**Real data over hallucinated state.** Every number that appears in a recovery plan (ETA, capacity, distance, cost) must trace back to a database row. If the seed data doesn't have it, the plan can't use it — fix the seed data, don't let the model fill the gap.

**Dynamic recovery over hardcoding.** The recovery engine generates and scores candidates from live resource state. It is allowed to produce the "obviously right" answer for the canonical demo scenario, but it must produce a *different* answer when the underlying data changes, and that must be provable with a test (see §16, §17).

**n8n's orchestration role.** n8n decides *what happens next* and *when*, calls the services that decide *what is true* and *what is possible*, and is the only layer that talks to external real-world systems (Calendar, Slack, Gmail, Supabase). Business logic (is this plan valid, what does it score) does not belong in n8n Code nodes — that logic goes in the decision-engine service, where it can be unit tested. n8n's job is sequencing, retries, fan-out/fan-in, and the approval pause — not computation.

**Human approval boundaries.** Approval is required before any action that moves people, spends money, changes a booking/schedule, or acts on a safety-risk incident. Approval is not required to *compute* a recommendation, only to *execute* one. Low-confidence AI output and safety-flagged incidents both route to a human before any recovery plan is even proposed for approval — they don't get to the approval gate, they get to a different, earlier escalation state.

**Reliability over architecture theatre.** Every component added to this system must answer "what breaks, specifically, without this" (§1 gives the answers for the ones we rejected). A boring, well-tested Postgres table beats a clever new subsystem every time at this scale.

---

## 6. Final architecture

```
                     USER / PHYSICAL WORLD
                             │
                   QR + PHOTO + VOICE/TEXT
                             │
                             ▼
                    NEXT.JS WEB / PWA  (Vercel)
                             │
                             ▼
                        n8n  (WF-01 intake)
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
          SUPABASE STORAGE          SUPABASE POSTGRES
          photo / audio             incident row created
                 └───────────┬───────────┘
                             ▼
                n8n  (WF-02 intelligence)
        fetch asset context + prior incidents (pgvector deferred, §7)
                             │
                             ▼
        DECISION-ENGINE SERVICE  /incident/interpret
        (model call lives HERE, behind a swappable
         provider — forced structured output,
         Pydantic-validated, one retry on
         invalid schema, confidence + safety flags)
                             │
                             ▼
                n8n  (WF-03 impact)
        fetch dependency edges + event + people data
                             │
                             ▼
        DECISION-ENGINE SERVICE  /impact/calculate
        (pure function: dependency traversal → impact)
                             │
                             ▼
                n8n  (WF-04 recovery)
        fetch technicians + inventory + rooms + resources
                             │
                             ▼
        DECISION-ENGINE SERVICE  /recovery/plan
        (pure function: candidates → constraints →
         ranked, explained plans)
                             │
                             ▼
                     APPROVAL GATE
              n8n Wait node + resume webhook
                             │
                             ▼
                n8n  (WF-05 execution, parallel,
                       idempotent, retried)
       ┌──────────┬─────────┼─────────┬──────────┐
       ▼          ▼         ▼         ▼          ▼
   Calendar     Slack     Gmail   work_order   room/
                                              inventory
                             │                 (Supabase
                             ▼                stand-ins)
                n8n  (WF-06 resolution/audit)
                             │
                             ▼
                 audit_log + asset history
                 OPERATION CONTINUES
```

Four real components, everything else is an integration:

```
Next.js  —  n8n  —  decision-engine (FastAPI)  —  Supabase (Postgres+Storage+pgvector)
```

---

## 7. Component responsibilities

| Layer | Owns | Does not own |
|---|---|---|
| **Frontend (Next.js/Vercel)** | QR-driven incident report UI, photo/audio capture, ops dashboard (impact view, plan comparison, approve/reject), status polling | Any business logic, any direct write to Calendar/Slack/Gmail, any decision about which plan is best |
| **n8n** | Sequencing (WF-01…06), all calls to external real-world systems, retries/timeouts on those calls, the approval wait/resume, fan-out/fan-in for parallel execution, assembling request payloads for the decision-engine from Postgres reads | Computing scores, validating recovery-plan feasibility, running the model call, storing anything n8n itself considers "the record" (Postgres is the record) |
| **AI/model layer (Gemini 3 Flash by default, inside decision-engine)** | Interpreting text+image+trusted-asset-context into a structured `IncidentIntelligence` (`app/schemas/incident.py`) via one forced-schema call — symptoms, category, severity, safety risk, confidence, review flag; explaining a chosen plan in plain language for the UI/demo (later). Provider is swappable (`app/interpret/providers/`, `MODEL_PROVIDER` env var — `gemini` default, `anthropic` available); §5's zero-spend-runtime principle governs the default, not a hard dependency on any one vendor | Deciding room capacity, technician availability, inventory counts, event timing, whether a plan is valid, or anything requiring "the current state of the world" — enforced structurally: no field in the schema can hold an operational fact (see `test_never_invents_operational_facts`) |
| **Decision-engine (FastAPI)** | `/incident/interpret` (Phase 3), `/impact/calculate`, `/recovery/plan` (Phase 4) — all pure, stateless, unit-tested functions; owns the shared Pydantic schemas that are the contract between every stage | Any database connection, any external API besides the active model provider's, any orchestration/sequencing decision |
| **Data layer (Supabase Postgres)** | System-of-record for assets, locations, incidents, incident_intelligence, dependencies, events, technicians, inventory, resources, recovery_plans, actions, audit_log — the single source of organizational truth | — |
| **Retrieval (Supabase pgvector)** | *Deferred as of Phase 3* — no manuals/procedures exist yet to index (`knowledge/` is empty), so there is nothing to retrieve; building the pipeline now would be infrastructure with no content. Trusted context for interpretation is deterministic instead: the asset row + its prior incidents (already-existing tables), fetched by n8n and passed in. Revisit only once real manuals/knowledge documents actually exist. | Ever being treated as a source of truth for inventory, schedules, or availability, whenever it is eventually built |
| **Storage (Supabase Storage)** | Incident photos (Phase 3: public `incident-media` bucket, created via the Storage REST API — not SQL, so this one wasn't blocked on the SQL-editor limitation), audio clips, manual source documents | — |
| **Integrations (n8n nodes)** | Google Calendar, Slack, Gmail — real writes, real reads for verification | Business decisions about *whether* to act (that's the approval gate) |
| **Observability** | n8n execution history (per-node input/output, free and built-in), `audit_log`/`actions` tables (durable, queryable, the thing you show a judge), decision-engine structured stdout logs (captured by the host platform) | A dedicated metrics/tracing stack — not justified at this scale |

---

## 8. Agent strategy

**Onward has zero autonomous agents.** This is a deliberate conclusion, not a default (see §1 for why an agentic tool-loop was considered and rejected).

The AI component is one **single-shot, schema-forced interpretation function**: `interpret_incident(photo, text, asset_context, retrieved_chunks) -> IncidentReport`. It runs once per incident, does not choose its own tools, does not take multiple turns, and cannot invoke anything that changes state.

- **What it can use:** the multimodal input it's given, plus context that n8n pre-fetched and handed to it (asset row, dependency summary, top-k retrieved chunks). It does not call tools itself.
- **What it must never control:** any write to Postgres, any external API call (Calendar/Slack/Gmail), which recovery plan is chosen, whether a plan is "valid," or whether an action executes. It produces one JSON object and returns.
- **If a future need arises** for the model to take multiple steps or choose actions dynamically, that is a new requirement to bring to the user before building — do not add it speculatively because "an agent could handle this better." Re-justify against §1's reasoning first.

---

## 9. n8n architecture

Six workflows, each a clear contract with an exit condition. Keep them modular — do not collapse into one workflow, and do not let any of them do another's job.

| Workflow | Input | Responsibility | Exit condition |
|---|---|---|---|
| **WF-01 Incident intake** | Webhook (asset code, description, idempotency key, source) | Validate payload, resolve registered asset by `assets.code`, reject unknown/inactive assets, dedupe on `idempotency_key`, create `incidents` row | A valid incident row exists, referencing a real asset, and duplicate submissions with the same idempotency key produce no second row |
| **WF-02 Incident intelligence** | `incident_id` (via Execute Workflow Trigger, called by WF-01) | Fetch incident + asset + prior incidents for that asset as trusted context, call decision-engine `/incident/interpret`, persist to `incident_intelligence` | A valid `IncidentIntelligence` row exists for the incident, or a clean `incident_not_found` / `decision_engine_unreachable` / `intelligence_persist_failed` terminal state — never left ambiguous |
| **WF-03 Operational impact** | Validated incident | Fetch dependency edges + event data from Postgres, call `/impact/calculate` | An `ImpactResult` (affected event, people affected, minutes remaining, criticality) exists and is stored |
| **WF-04 Recovery planning** | Incident + impact | Fetch technicians/inventory/rooms/resources from Postgres, call `/recovery/plan`, store all candidates (not just the winner), enter the approval gate | A ranked, explained set of feasible plans exists, or an explicit `no_recovery_available` state is set |
| **Approval gate** (inside WF-04/05 boundary) | Recommended plan | n8n Wait node pauses the execution; a resume webhook (hit by the ops dashboard's Approve/Reject/Choose-other action) continues it | Execution resumes only on an explicit human decision, never on a timeout defaulting to "approved" |
| **WF-05 Recovery execution** | Approved plan | Parallel, idempotent, retried writes to Calendar/Slack/Gmail/work_orders/inventory/room reservation, each recorded as an `actions` row keyed by `{incident_id}:{action_type}:{target_id}` | Every planned action has a terminal status (`succeeded`/`failed`), overall execution is `complete` or `partial`, never silently missing |
| **WF-06 Resolution & audit** | Execution results | Update incident status, update asset/maintenance history, write `audit_log`, close out | The incident has one final, traceable state |

**Reads vs. writes (decided in Phase 2):** the vault and §6 leave the read path implicit. Writes — anything that creates or changes a row — go exclusively through n8n, using the Supabase **secret key** in n8n's own credential store (bypasses RLS, matching n8n's role as the only writer). Reads that just display state — an incident's status, its detail page — go **directly from `apps/web` to Supabase's Data API**, server-side, using the **publishable key**, protected by a public-`SELECT`-only RLS policy (`database/migrations/0001_init.sql`). This isn't a violation of "n8n orchestrates" — reads aren't orchestration, and round-tripping every status check through an n8n webhook would be slower and adds no safety. Never give the publishable key `INSERT`/`UPDATE`/`DELETE` access via RLS — if a future read path needs to trigger a write, that write still goes through n8n.

**WF-02 is implemented and live-gate-tested** (Phase 3): workflow id `fMQ15943GzYcH6bw`, exported at `n8n/exports/wf02-incident-intelligence.json`, **published and active**. It is a **sub-workflow, not a public endpoint** — it uses an Execute Workflow Trigger, not a webhook, and is invoked by WF-01 (a fire-and-forget `Execute Sub-workflow` node added to WF-01, `waitForSubWorkflow: false`, so intake's response latency and shape are unaffected either way). Verified live: submitting a real incident through WF-01's webhook reliably fires WF-02 (`mode: "integrated"` in `search_workflow_executions`), and a duplicate (same `idempotency_key`) resubmission does not — WF-01's own "Already Recorded?" branch short-circuits before ever reaching the node that triggers WF-02, so idempotency holds at the orchestration layer, not just inside WF-02's own "Already Interpreted?" check. Two things worth knowing before touching either workflow again:
- **A workflow with only an Execute Workflow Trigger cannot be run via the `execute_workflow` MCP tool** — that tool only drives Schedule/Webhook/Form/Chat triggers. To test WF-02 directly (not via WF-01), either add a temporary second trigger or exercise it by submitting a real incident through WF-01's webhook and then reading `search_workflow_executions`/`get_workflow_execution` for WF-02's id.
- **`update_workflow` (used for WF-01's additive change) creates a new draft version — it does not republish the live one.** `get_workflow_details` distinguishes `versionId` (draft) from `activeVersionId` (what's actually running); they can differ after an edit. Check both before assuming an edit is live, and remember publishing is still gated on the user's explicit go-ahead each time (§9 below), same as any other consequential n8n action.

**Image evidence is carried through WF-01 → WF-02 → decision-engine** (Phase 3, third pass). Intake never receives raw image bytes: the client uploads to the public `incident-media` Supabase Storage bucket first (created via the Storage REST API — `POST /storage/v1/bucket`, not SQL, so it wasn't blocked by the SQL-editor limitation) and submits the resulting URL as `media_url`, a small string, not a payload. `incidents.media_url` is nullable and optional — the entire text-only path is byte-for-byte unchanged when it's absent. Inside WF-02, `Has Media?` branches on it; when present, `Fetch Image` downloads it, `Extract Base64` converts it to a base64 string, `Finalize Image Fields` pairs that with the mime type, and all three possible tails (real image / fetch failed / no media) converge on `Call Decision Engine` with the exact same `{image_base64, image_media_type}` shape — the field decision-engine's `InterpretRequest` already expected from the start, so **decision-engine itself needed zero changes**. Two real bugs surfaced building this, both fixed and worth knowing if this graph is touched again:
- **Item multiplication**: `Has Media?` sat downstream of `Fetch Prior Incidents`, which returns up to 5 items — without `executeOnce: true`, everything downstream ran once per prior incident instead of once for the actual current one. Fixed with `executeOnce: true` on `Has Media?` alone (it then emits exactly one item, so nothing downstream needs the setting too).
- **`{{ $binary.data.data }}` does not resolve to base64 in this instance.** This n8n instance stores binary data in `filesystem-v2` mode; a bare expression reference to `.data` returns the storage-mode marker, not lazily-loaded content (confirmed live — not a tool-display artifact). The fix is the dedicated **Extract from File** node (`n8n-nodes-base.extractFromFile`, `binaryToPropery` operation) — built specifically to produce base64 regardless of binary storage backend. `.mimeType` is plain metadata (not lazily loaded) and reads fine via a bare expression.

**n8n Cloud → local decision-engine connectivity (dev/gate-testing only):** a free **Cloudflare Quick Tunnel** (`cloudflared tunnel --url http://localhost:8000` — no account, no signup, prints an ephemeral `*.trycloudflare.com` URL). Paste `<that url>/incident/interpret` into WF-02's "Call Decision Engine" node for the duration of a gate-test session; it changes every time the tunnel restarts, so it's never committed anywhere. This is explicitly a **dev/testing bridge, not production connectivity** — exposing a local port to the public internet is a real action with real exposure, so Claude Code will not start a tunnel (or any similar port-forwarding) without the user's explicit go-ahead in that moment, same as any other consequential action; a blocked attempt at this is expected behavior, not a bug to route around. The real production path is still deploying decision-engine somewhere with a stable URL (Railway/Render, per §16) — the tunnel only exists to make Phase 3 gate-testable before that deployment happens.

**Stable asset identifiers:** `assets.code` (e.g. `AV-204`) is the public, human-facing identifier intake resolves against — never the internal `uuid` primary key. This is what a QR code will encode later (`/report?asset=<code>`); the intake contract was built against `code` from the start specifically so adding real QR codes never requires touching the resolution logic, only wiring a QR image to a URL Next.js already serves at `apps/web/app/report/page.tsx`.

**WF-01 is implemented, live, and image-aware** (Phase 2, extended Phase 3): workflow id `2LTZ0WR1nIjRqlaU`, exported at `n8n/exports/wf01-incident-intake.json`. It validates required fields, resolves the asset by `code`, rejects unknown (404) and inactive (422) assets, checks `idempotency_key` for an existing row before inserting (200 + `duplicate: true` on replay, never a second row), stores an optional `media_url`, and returns 201 with the persisted incident on success, or 500 if the Supabase write itself fails. It fires WF-02 (fire-and-forget) on every successful insert.

**Building n8n workflows in this environment:** this Claude Code session has direct MCP access to the connected n8n workspace (`mcp__claude_ai_n8n__*` tools — `create_workflow_from_code`, `update_workflow`, `validate_workflow`, `test_workflow`, `search_workflows`, etc.). Prefer these tools over hand-editing JSON blindly — `validate_workflow` and `test_workflow` exist specifically to catch mistakes before they're live. However: **never call `publish_workflow`, `execute_workflow` (against real Slack/Calendar/Gmail credentials), or `archive_workflow`/deletion tools without the user's explicit go-ahead in that moment**, even though the tools are available — the same rule that governs any other consequential, hard-to-reverse action in this project. Export a JSON snapshot of finished workflows into `n8n/exports/` for version control after they're validated, so the repo has a durable copy independent of the live n8n instance.

---

## 10. Data model

Supabase Postgres. Core tables (target design — see below for what's actually implemented):

| Table | Purpose |
|---|---|
| `assets` | Registered physical equipment (id, type, location, manuals ref) |
| `locations` | Rooms/sites, including capacity and AV/equipment status |
| `incidents` | Every reported issue: raw input, structured `IncidentReport`, status |
| `maintenance_history` | Past faults and repairs per asset |
| `dependencies` | Adjacency edges: `source_type, source_id, dependency_type, dependency_id, relationship, criticality, impact_metadata (jsonb)` — this is the Impact Graph |
| `events` | Classes/bookings/events: time, attendee count, room, requirements |
| `technicians` | Staff skills + current availability |
| `inventory` | Parts/replacement assets: quantity, location |
| `resources` | Alternate rooms/assets usable as recovery options |
| `recovery_plans` | Every generated candidate for an incident, with constraint results and score, not just the winner |
| `work_orders` | Maintenance jobs created from an incident |
| `actions` | Every executed (or attempted) action, unique on `action_key`, with status |
| `audit_log` | Append-only record of what happened and why, for every incident |
| `knowledge_chunks` | Manual/procedure/history text chunks + embedding vector, for pgvector retrieval |

`actions.action_key` carries a **unique constraint** in the schema — idempotency is enforced by the database, not by application-level "best effort" checks. An insert with a duplicate key is a no-op, not a new row.

**Implemented so far:** `assets` and `incidents` (Phase 2, `database/migrations/0001_init.sql`), plus `incident_intelligence` (Phase 3, `0002_incident_intelligence.sql`) — deliberately minimal each time; everything else above is the target shape for later phases, not built ahead of need. Two differences from the table above, both intentional: `assets` has a `code` column (the stable public identifier, see §9) in addition to `id`; `incidents.idempotency_key` carries its own unique constraint directly (simpler than `actions.action_key` since intake has no separate action-dispatch step yet). `incident_intelligence` is keyed 1:1 on `incident_id` (primary key, not a separate uuid) — exactly one AI interpretation per incident, kept in its own table so "what the user reported" (`incidents`) and "what Onward inferred" (`incident_intelligence`) are never merged into one row. All three tables have RLS enabled with a public-`SELECT`-only policy — see §9's reads-vs-writes split.

---

## 11. Impact Graph design

Representation: an adjacency-list table (`dependencies`) with typed edges (`relationship`, `criticality`) and a flexible `impact_metadata jsonb` column for edge-specific facts (e.g., "this room seats 96," "this event has 84 attendees"), rather than a graph database. The graph here is small and shallow (2–4 hops); a recursive CTE over one table answers every traversal question we need:

```sql
WITH RECURSIVE impact AS (
  SELECT source_type, source_id, dependency_type, dependency_id, relationship, criticality, impact_metadata, 1 AS depth
  FROM dependencies WHERE source_type = 'asset' AND source_id = :asset_id
  UNION ALL
  SELECT d.source_type, d.source_id, d.dependency_type, d.dependency_id, d.relationship, d.criticality, d.impact_metadata, i.depth + 1
  FROM dependencies d JOIN impact i ON d.source_id = i.dependency_id
  WHERE i.depth < 6
)
SELECT * FROM impact ORDER BY depth;
```

n8n runs this query (or an equivalent Supabase call) and hands the resulting chain, plus the joined `events`/attendee data, to `/impact/calculate`, which turns it into the `ImpactResult` (affected event, people affected, minutes remaining, criticality) — pure computation, no I/O in that function.

---

## 12. Recovery engine

`/recovery/plan` is a pure function: `(incident, impact, resource_state) -> ranked, explained plans`.

1. **Candidate generation.** A small registry of recovery strategies keyed by `incident_type`/`required_capability` (e.g., `repair_via_technician`, `replace_asset`, `relocate_operation`). For a given incident, generate one candidate per applicable strategy using the resource state n8n provided (nearest available technician, nearest available replacement, nearest available alternate room/resource).
2. **Constraint validation.** Each candidate is checked against explicit, named constraints (time window, capacity, availability, safety) and each check records `{name, passed, detail}` — e.g., `{"name": "time_window", "passed": false, "detail": "ETA 28min > 13min available"}`. A candidate that fails any hard constraint is marked infeasible and excluded from ranking, but kept in the response with its failure reasons — this is what lets the system explain "why not Plan A" during the demo and in the audit trail.
3. **Ranking.** Feasible candidates only are scored:
   `PlanScore = 0.45·continuity + 0.30·speed + 0.15·cost_efficiency + 0.10·low_disruption`
   Weights are tunable, not sacred — but constraint checking always happens *before* scoring, so an infeasible plan can never outrank a feasible one.
4. **No feasible plan** is a valid, explicit output (`feasible: false`, all candidates with reasons) — not an error, not a silent fallback. n8n routes this to a `no_recovery_available` escalation state.

---

## 13. Integration strategy (real, for Track 2)

Must genuinely work, not be simulated:

- **Google Calendar** — real event creation/update on a real calendar.
- **Slack** — real message to a real channel/user.
- **Gmail** — real email sent.
- **Supabase Postgres** — real row writes (work orders, room reservations, inventory decrements).

For systems we don't have access to (CMMS, ERP, university room-booking software), Supabase tables are functional stand-ins, and this is stated plainly in the demo, not hidden: *"Supabase represents the facilities backend in this prototype. In deployment, this adapter would connect to the organization's existing CMMS/ERP/booking system."* Never show a "✓ updated" state for an action that didn't really happen.

---

## 14. Reliability strategy

- **Retries** — n8n's built-in retry-on-fail with exponential backoff on every external call (Calendar, Slack, Gmail, decision-engine). Reasonable per-call timeouts (e.g., 10s for integrations, 45s for the interpretation call, which does the model-provider round trip).
- **Idempotency** — enforced by the `actions.action_key` unique constraint (§10) and by incident-level idempotency keys on WF-01 intake. Retried or duplicated requests never produce duplicate calendar events, emails, Slack messages, or work orders.
- **Timeouts & fallbacks** — if the interpretation call fails or times out after one retry, the incident routes to human review with the raw input attached, rather than blocking. If recovery planning finds zero feasible plans, that's an explicit escalation state, not a crash.
- **Partial failure** — WF-05's parallel actions are independent; if Slack fails but Calendar succeeds, overall status is `partial`, both outcomes are recorded, and the failure is visible in the dashboard/audit — no rollback of the succeeded action, because actions are additive and idempotent, not transactional.
- **Schema validation** — every incident, impact result, and recovery plan is a Pydantic model with strict validation at the decision-engine boundary; nothing downstream ever consumes unvalidated shape.
- **Dead-end states** — every incident terminates in one of a fixed, named set of statuses: `resolved`, `no_recovery_available`, `escalated_unsafe`, `escalated_low_confidence`, `rejected_by_approver`, `failed_partial`. An incident is never left with an undefined or ambiguous status.

**Two real defects found and fixed during the Phase 3 live gate (both worth remembering):**
- **decision-engine never actually loaded `.env`.** `os.environ.get(...)` only sees real process env vars; nothing loaded the repo-root `.env` into the process, so `GEMINI_API_KEY` sat in the file, unused, while the running server correctly (if unhelpfully) fell back to `"...is not configured"` on every call. Fixed with `app/env.py` — a same-pattern-as-elsewhere-in-this-repo `.env` parser, called once at `main.py` import time, real environment variables always winning over the file (inert in any real deployment). **Restarting decision-engine is required after editing `.env`** — it's read once, not watched.
- **Malformed `image_base64` crashed the request** (`base64.b64decode()` ran outside `GeminiProvider.complete()`'s try/except, so a decode error propagated as a raw 500 instead of the designed safe fallback). Fixed by decoding inside its own try/except, returning `None` like every other provider failure. Regression test: `services/decision-engine/tests/test_gemini_provider.py`.

Both were caught specifically *because* the gate was run against the real system instead of trusting mocked tests alone — mocked tests can't catch "the real process never saw the key" or "the real SDK call happens outside the try block."

---

## 15. Security/safety boundaries

- Secrets live only in environment variables / the n8n credential store — never committed, never hardcoded.
- Every trust boundary validates input before it touches the database (webhook payload shape-checked before any `incidents` insert; decision-engine requests/responses are Pydantic-validated).
- Integration credentials are scoped narrowly (a dedicated Slack bot token with only the needed channel scopes, a dedicated Calendar resource/service account) — not personal accounts.
- Any action that moves people, spends money, changes a schedule, or responds to a safety-risk incident requires explicit human approval before execution; there is no timeout-based auto-approve.
- Safety-flagged incidents (`safety_risk = true`) never receive automated repair guidance — they go straight to human escalation, full stop.
- `audit_log` is append-only from the application's perspective (no update/delete paths in app logic) so it remains a trustworthy record of what actually happened.

---

## 16. Repository structure

**Tooling, locked in Phase 1:** `apps/web` uses npm (whatever `create-next-app` sets up — no yarn/pnpm, no benefit at this scale). `services/decision-engine` uses `uv` for venv + dependency locking (`uv sync`, `uv run ...`) and `ruff` for lint — not pip/poetry/flake8/black, see §1. No Docker in local dev, see §1.

```
onward/
├── apps/
│   └── web/                    Next.js incident UI + ops dashboard
│       ├── app/
│       ├── components/
│       └── lib/
│
├── services/
│   └── decision-engine/         FastAPI, stateless, pure-function service
│       ├── app/
│       │   ├── schemas/         Shared Pydantic contracts (IncidentIntelligence, ImpactResult, RecoveryPlan)
│       │   ├── interpret/        Provider-agnostic orchestration + retry/confidence/safety logic
│       │   │   └── providers/    One class per model provider (gemini.py default, anthropic_provider.py)
│       │   ├── impact/           Dependency traversal → impact calculation
│       │   └── recovery/         Candidate generation + constraints + scoring
│       └── tests/
│
├── database/
│   ├── migrations/
│   ├── seed/                    Small university world seed data
│   └── schema.sql
│
├── n8n/
│   └── exports/                 Version-controlled JSON snapshots (canonical source is the live n8n workspace)
│
├── knowledge/
│   ├── manuals/
│   ├── procedures/
│   └── safety/
│
├── tests/                       Cross-service integration + end-to-end scripts
│
├── CLAUDE.md
├── ONWARD_MASTER_MEMORY_VAULT.md
└── README.md
```

---

## 17. Build order

Seven milestones. Do not add more without a real reason — this list already covers the whole loop once.

**M0 — Foundation.** Repo skeleton, Supabase project + empty schema, n8n workspace reachable, decision-engine deployed with a `/health` endpoint, secrets wired via env vars. *Exit:* web app deploys, `/health` returns 200, n8n can reach Supabase and the decision-engine, no secrets in git. *Test:* a smoke script hits both health endpoints; `git log -p` review confirms no committed secrets.

**M1 — Data model & seeded world.** Full schema + migrations + a seed script producing the small university world (3 assets, 3 rooms, 2 technicians, a few events, dependency edges, a few knowledge chunks). *Exit:* the recursive CTE (§11) returns the correct multi-hop chain for the seeded asset. *Test:* a pytest/SQL test asserting the traversal result, and a second assertion that changing one seed row changes the result.

**M2 — Incident intake.** Next.js report page (asset resolved from QR param), upload to Supabase Storage, WF-01 webhook validates and creates the incident row, idempotency key enforced. *Exit:* a real QR scan → real submission → a real Postgres row with attachment URLs; a duplicate submission with the same key produces no second row. *Test:* an integration test posts the same payload twice and asserts one row.

**M3 — Incident intelligence.** WF-02 fetches asset context + pgvector top-k, calls `/incident/interpret`, branches on confidence/safety. *Exit:* the same photo+text reliably produces a valid `IncidentReport`; ambiguous input sets `requires_human_review`; a safety keyword routes to escalation without any repair suggestion. *Test:* a fixture table (happy path, ambiguous, unsafe, malformed image) each asserted against its expected branch.

**M4 — Impact & recovery (the differentiator).** `/impact/calculate` and `/recovery/plan` fully implemented as pure, unit-tested functions; WF-03/WF-04 wire real Postgres queries into them. *Exit:* changing one seed value (room availability, technician ETA) measurably changes the recommended plan, provably without touching code. *Test:* pytest cases mirroring the projector/room example, plus a negative test that flips Room 2.08's availability and asserts a different plan wins.

**M5 — End-to-end execution with approval.** Full WF-01→06 chain connected; approval gate via Wait node + resume webhook; WF-05 executes real Calendar/Slack/Gmail/DB actions in parallel, idempotently, with retries; WF-06 writes the audit trail. *Exit:* one live incident flows start to finish, a human approves, and Calendar/Slack/Gmail genuinely change — verified independently, not just "success" in an n8n log. *Test:* an end-to-end script that submits an incident, approves it via the resume webhook, then independently reads back the Calendar event, the Slack message, and confirms the email was sent, the `audit_log` rows exist, and re-submitting the same incident does not duplicate any action.

**M6 — Reliability hardening.** Explicitly exercise every failure path: no feasible plan, an integration API failure, a duplicate submit, a rejected approval, low confidence, an unsafe incident. *Exit:* every scenario resolves to one of the named dead-end states (§14) with a correct audit trail, none of them crash or hang. *Test:* one automated test per scenario, run together as a suite before any demo work starts.

---

## 18. Testing strategy

- **Unit** — every decision-engine function (`interpret`, `impact`, `recovery`) is a pure function tested with `pytest` and fixture inputs; the model provider is swapped for a `FakeProvider` test double for these tests (see `app/interpret/providers/base.py`), never a specific SDK mock — so the tests don't change when the active provider does. Schema tests confirm Pydantic models reject malformed data.
- **Integration** — n8n workflows tested with `mcp__claude_ai_n8n__test_workflow` (available directly in this environment) against fixture payloads, without touching real Slack/Calendar/Gmail credentials where avoidable.
- **Workflow-level** — `validate_workflow` before any `publish_workflow` (which itself always requires explicit human confirmation, per §9).
- **End-to-end** — the M5 script: real submission → real approval → independently-verified real side effects → audit trail — is the test that actually proves Track 2 readiness. Re-run it as a regression check after any change to WF-01…06 or the decision-engine contracts.

---

## 19. Definition of Done (before Phase B / demo work starts)

- [ ] Registered asset lookup works from a real QR scan
- [ ] Incident submission works, with idempotency enforced
- [ ] Multimodal incident intelligence works and is schema-validated
- [ ] Impact calculation is driven by real dependency data, not hardcoded
- [ ] Recovery candidates are generated dynamically and change when data changes
- [ ] Constraint validation runs before scoring, always
- [ ] Approval gate genuinely pauses and resumes execution
- [ ] Google Calendar, Slack, and Gmail integrations genuinely change real state
- [ ] Supabase writes (work orders, reservations, inventory) genuinely persist
- [ ] Audit log captures every incident's full decision + execution trail
- [ ] Duplicate requests are provably safe (no duplicate actions)
- [ ] No-feasible-plan, low-confidence, unsafe, and integration-failure paths all resolve to defined states
- [ ] The M5 end-to-end test passes on demand, repeatably

Only when every box above is true does demo/presentation work begin.

---

## 20. Deferred scope (explicitly not now)

Predictive maintenance, IoT telemetry (NFC/RFID/BLE), computer-vision asset recognition, a native mobile app, multi-industry configuration, advanced analytics dashboards, enterprise RBAC/SSO, real CMMS/ERP connectors, ML-based optimization or learning loops, any multi-agent or agentic-tool-loop architecture, demo choreography/animation. These are legitimate future directions for Onward beyond the hackathon — they are not this build's job, and adding any of them now is scope creep against the Definition of Done in §19.

---

## 21. Claude Code operating rules

- **Inspect before changing.** Read the current state of the relevant code/schema/workflow before editing it. Do not assume the repo matches this file's description if it's been a while — verify.
- **Explain important architectural changes.** If you're about to deviate from §6–§14, say so and why, in the same way §1 explains this file's deviations from the vault. Don't silently drift.
- **Test after implementing.** Every milestone in §17 names its own test — run it. Don't mark a milestone done on "it looks right."
- **Avoid speculative rewrites.** Don't refactor working code to "improve" it without a concrete failure or requirement driving the change.
- **Avoid uncontrolled scope expansion.** If a task starts pulling in something from §20, stop and check with the user before continuing.
- **Challenge weak assumptions** — including your own. If a design decision here seems wrong given something you've since learned about the actual data or constraints, raise it explicitly rather than quietly working around it.
- **Prefer evidence over confidence.** "The test passed" beats "this should work." For anything touching real integrations (Calendar/Slack/Gmail), verify the real side effect independently, not just the n8n execution status.
- **Preserve repository consistency.** Follow the structure in §16; keep the decision-engine stateless (§0); keep business logic out of n8n Code nodes (§5).
- **n8n MCP tools are available in this environment** (§9) — use them for building/validating/testing workflows, but never call anything with a real, hard-to-reverse side effect (`publish_workflow`, `execute_workflow` against live credentials, archive/delete) without the user's explicit go-ahead in that moment, exactly as with any other consequential action.
