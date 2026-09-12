-- Onward — Phase 5: Recovery Intelligence resource model. Run once in the
-- Supabase SQL Editor, after 0001-0004 (same reason as every prior
-- migration: no CLI/DB-wire access is available to this environment).
--
-- Reuses `locations` and `assets` rather than duplicating concepts (task
-- instruction #2) — this migration only ADDS the columns locations needs to
-- serve as a relocation target, plus two genuinely new resource types
-- (technicians, inventory) that have no existing table to extend.
--
-- Deliberately minimal: no technician geolocation/routing (ETA is a direct,
-- mutable snapshot field, not derived from a distance calculation — matches
-- exactly what the Phase 5 brief's own live-gate scenario B mutates), no
-- N-by-N room-to-room travel-time matrix (transfer_minutes is a flat
-- per-location estimate, adequate at this scale), no technician shift
-- scheduling. Those are real future directions, not this phase's job.

-- ---------------------------------------------------------------------------
-- locations: add what's needed to serve as a recovery target. Capacity,
-- capabilities and transfer time are recovery-resource attributes (Phase 5,
-- CLAUDE.md §20 deferred them out of Phase 4 on purpose) — status here means
-- "is this room usable as a destination right now" (maintenance/closed),
-- distinct from an *asset's* status.
-- `capabilities` mirrors incident_intelligence.required_capability's
-- vocabulary (e.g. "AV_PROJECTION") so a relocation candidate's capability
-- constraint is a plain array-contains check, not a second classification
-- system.
-- `transfer_minutes` is null for a location that isn't a valid relocation
-- target (e.g. the room already hosting the operation, or a non-lecture
-- space) — candidate generation skips locations where it's null.
-- ---------------------------------------------------------------------------
alter table locations add column if not exists capacity integer;
alter table locations add column if not exists capabilities jsonb not null default '[]';
alter table locations add column if not exists transfer_minutes integer;
alter table locations add column if not exists status text not null default 'available'
  check (status in ('available', 'unavailable'));

-- ---------------------------------------------------------------------------
-- technicians: who can repair what, how fast. `skills` uses the same
-- capability vocabulary as required_capability/locations.capabilities.
-- `eta_minutes` is a direct snapshot (see header note) — real dispatch
-- systems would compute this from current technician location; that's a
-- real integration for a later phase, not a hackathon-scale requirement.
-- ---------------------------------------------------------------------------
create table if not exists technicians (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  skills jsonb not null default '[]',
  status text not null default 'available' check (status in ('available', 'unavailable')),
  eta_minutes integer,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- inventory: replacement assets/parts. `compatible_capability` matches the
-- same vocabulary — a spare projector's compatible_capability is
-- "AV_PROJECTION", generalizing to any vertical without a projector-specific
-- column.
-- ---------------------------------------------------------------------------
create table if not exists inventory (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  compatible_capability text not null,
  quantity integer not null default 0,
  status text not null default 'available' check (status in ('available', 'unavailable')),
  setup_minutes integer,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- recovery_runs: 1:1 per incident header — mirrors operational_impact and
-- incident_intelligence's own "separate table per kind of truth" pattern.
-- `state_fingerprint` is a short deterministic hash (computed by
-- decision-engine, a pure function, over exactly the resource facts that
-- were actually consulted) so a later reader can tell whether the
-- underlying resource state has moved on since this recommendation was
-- computed, without a full event-sourcing platform (task item #15).
-- ---------------------------------------------------------------------------
create table if not exists recovery_runs (
  incident_id uuid primary key references incidents (id),
  schema_version text not null default '1.0',
  status text not null check (status in ('plans_available', 'no_feasible_plan')),
  reason text,
  state_fingerprint text not null,
  calculated_at timestamptz not null,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- recovery_plans: every generated candidate, not just the winner (CLAUDE.md
-- §10) — infeasible plans are kept with their failing constraints so
-- "why not Plan A" is answerable from this table alone.
-- `resource_ref` is traceability: which real technician/inventory/location
-- row this candidate was generated from, so the plan is auditable back to
-- an actual resource, never a hallucinated one.
-- ---------------------------------------------------------------------------
create table if not exists recovery_plans (
  id uuid primary key default gen_random_uuid(),
  incident_id uuid not null references incidents (id),
  plan_type text not null check (plan_type in ('repair_via_technician', 'replace_asset', 'relocate_operation')),
  resource_ref jsonb not null default '{}',
  feasible boolean not null,
  estimated_recovery_minutes integer,
  disruption_rank integer not null,
  rank integer,
  is_recommended boolean not null default false,
  constraints jsonb not null default '[]',
  reason text,
  calculated_at timestamptz not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_recovery_plans_incident on recovery_plans (incident_id);

alter table technicians enable row level security;
alter table inventory enable row level security;
alter table recovery_runs enable row level security;
alter table recovery_plans enable row level security;

drop policy if exists "public read access" on technicians;
create policy "public read access" on technicians for select to anon, authenticated using (true);

drop policy if exists "public read access" on inventory;
create policy "public read access" on inventory for select to anon, authenticated using (true);

drop policy if exists "public read access" on recovery_runs;
create policy "public read access" on recovery_runs for select to anon, authenticated using (true);

drop policy if exists "public read access" on recovery_plans;
create policy "public read access" on recovery_plans for select to anon, authenticated using (true);
