-- Onward — Phase 6: Approval, Execution & Real Integrations. Run once in
-- the Supabase SQL Editor, after 0001-0005 (same reason as every prior
-- migration: no CLI/DB-wire access is available to this environment).
--
-- Full traceability chain this phase completes:
--   incident -> incident_intelligence -> operational_impact -> recovery_runs
--   -> recovery_plans -> approvals -> execution_runs -> execution_actions
-- plus work_orders (the broken asset's own maintenance concern, independent
-- of whichever recovery action was taken) and resource_reservations (the
-- real "room is now booked" record a relocate_operation plan produces).
-- audit_log is the flat, append-only, human-readable narrative across all
-- of the above (task item #15) — everything else here is normalized state;
-- audit_log is the story.

-- ---------------------------------------------------------------------------
-- approvals: one explicit human decision, permanently bound to exactly one
-- recovery_plans row. UNIQUE(plan_id) is what makes "impossible to
-- accidentally reuse for another plan" and "no duplicate approval" true at
-- the database level, not just in application logic — a second approval
-- attempt for the same plan is a constraint violation, not a race
-- condition to defend against in code.
-- ---------------------------------------------------------------------------
create table if not exists approvals (
  id uuid primary key default gen_random_uuid(),
  incident_id uuid not null references incidents (id),
  plan_id uuid not null references recovery_plans (id) unique,
  decision text not null check (decision in ('approved', 'rejected')),
  decided_by text not null,
  decided_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists idx_approvals_incident on approvals (incident_id);

-- ---------------------------------------------------------------------------
-- execution_runs: 1:1 with the approval that authorized it — mirrors
-- operational_impact/recovery_runs' own "one row per upstream decision"
-- pattern. Keying on approval_id (not a fresh uuid) makes "has this
-- approval already been executed" a plain primary-key lookup, the same
-- idempotency shape already used three times (WF-02/03/04).
-- ---------------------------------------------------------------------------
create table if not exists execution_runs (
  approval_id uuid primary key references approvals (id),
  incident_id uuid not null references incidents (id),
  plan_id uuid not null references recovery_plans (id),
  status text not null check (status in ('executing', 'completed', 'partially_completed', 'failed')),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- execution_actions: one row per attempted consequential action.
-- `action_key` is the real idempotency guard for the underlying EXTERNAL
-- side effect (CLAUDE.md §10/§14's existing pattern, e.g.
-- "{incident_id}:calendar:{plan_id}") — unique so a retry's upsert can
-- never create two rows for the same real-world action, but the row alone
-- doesn't stop a second real Slack/Calendar/Gmail call from firing; the
-- workflow always checks this table for an existing 'completed' row BEFORE
-- attempting the external call, never after.
-- ---------------------------------------------------------------------------
create table if not exists execution_actions (
  id uuid primary key default gen_random_uuid(),
  execution_run_id uuid not null references execution_runs (approval_id),
  incident_id uuid not null references incidents (id),
  action_key text not null unique,
  action_type text not null check (action_type in (
    'work_order', 'slack_notify', 'calendar_update', 'gmail_notify',
    'resource_reservation', 'inventory_decrement'
  )),
  status text not null check (status in ('completed', 'failed')),
  external_reference text,
  attempts integer not null default 1,
  error text,
  executed_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists idx_execution_actions_run on execution_actions (execution_run_id);

-- ---------------------------------------------------------------------------
-- work_orders: the broken asset's own maintenance concern, created for
-- EVERY executed plan regardless of type — moving the lecture or
-- replacing the projector doesn't fix AV-204 itself (task item #14).
-- ---------------------------------------------------------------------------
create table if not exists work_orders (
  id uuid primary key default gen_random_uuid(),
  incident_id uuid not null references incidents (id),
  asset_id uuid not null references assets (id),
  status text not null default 'open' check (status in ('open', 'assigned', 'completed')),
  assigned_technician_id uuid references technicians (id),
  description text not null,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- resource_reservations: the real Supabase-backed "this room is now
-- booked for this operation" record a relocate_operation plan produces —
-- the functional stand-in for a real room-booking system (CLAUDE.md §13),
-- stated plainly, not hidden behind a fake "booked" label with no backing
-- row.
-- ---------------------------------------------------------------------------
create table if not exists resource_reservations (
  id uuid primary key default gen_random_uuid(),
  incident_id uuid not null references incidents (id),
  location_id uuid not null references locations (id),
  reserved_at timestamptz not null default now(),
  source text not null default 'recovery_execution',
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- audit_log: append-only (no update/delete path in application logic —
-- CLAUDE.md §15), flat narrative across the whole incident lifecycle.
-- Everything else in this migration is normalized state a reviewer would
-- need to JOIN across six tables to reconstruct; this is the same story
-- pre-flattened into one ordered read.
-- ---------------------------------------------------------------------------
create table if not exists audit_log (
  id uuid primary key default gen_random_uuid(),
  incident_id uuid not null references incidents (id),
  event_type text not null,
  detail jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists idx_audit_log_incident on audit_log (incident_id, created_at);

alter table approvals enable row level security;
alter table execution_runs enable row level security;
alter table execution_actions enable row level security;
alter table work_orders enable row level security;
alter table resource_reservations enable row level security;
alter table audit_log enable row level security;

drop policy if exists "public read access" on approvals;
create policy "public read access" on approvals for select to anon, authenticated using (true);

drop policy if exists "public read access" on execution_runs;
create policy "public read access" on execution_runs for select to anon, authenticated using (true);

drop policy if exists "public read access" on execution_actions;
create policy "public read access" on execution_actions for select to anon, authenticated using (true);

drop policy if exists "public read access" on work_orders;
create policy "public read access" on work_orders for select to anon, authenticated using (true);

drop policy if exists "public read access" on resource_reservations;
create policy "public read access" on resource_reservations for select to anon, authenticated using (true);

drop policy if exists "public read access" on audit_log;
create policy "public read access" on audit_log for select to anon, authenticated using (true);
