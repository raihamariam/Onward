-- Onward — Phase 4: Impact Graph. Run once in the Supabase SQL Editor,
-- after 0001-0003 (same reason as before: no CLI/DB-wire access is
-- available to this environment — see CLAUDE.md and every prior migration).
--
-- Design: a single generic adjacency-list table (`dependencies`) with
-- typed, directional edges is the ONLY place organisational relationships
-- live — not a graph database (CLAUDE.md §1 already rejects one: the graph
-- here is a handful of nodes, 2-4 hops deep; a Postgres recursive CTE
-- answers every traversal question we need). `locations` and `events` are
-- plain node tables holding only their own attributes, with NO foreign key
-- to each other — "what depends on what" has exactly one source of truth
-- (the edge table), never split between FK columns and edge rows.
--
-- Deliberately minimal, matching Phase 2/3's own minimalism: only what the
-- Impact Engine needs. Technicians, inventory, spare equipment, and
-- alternative rooms are Phase 5 (Recovery) — CLAUDE.md §20 — not added here.

-- ---------------------------------------------------------------------------
-- locations: rooms/sites/bays — a node type in the dependency graph, not
-- itself a recovery resource (an alternate room for recovery is Phase 5).
-- No capacity/status columns — nothing in Phase 4 needs them; adding them
-- now would be building ahead of need.
-- ---------------------------------------------------------------------------
create table if not exists locations (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- events: any scheduled operation with timing + an affected population —
-- generic enough to model a lecture, a shipment, a breakfast service, or a
-- peak checkout window without a domain-specific table per vertical (see
-- the Phase 4 brief's cross-industry extensibility requirement).
-- required_capability is what this operation needs to succeed (e.g.
-- "AV_PROJECTION") — matched against incident_intelligence.required_capability
-- to phrase "service_at_risk"; nullable because not every event depends on
-- a specific capability.
-- ---------------------------------------------------------------------------
create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  starts_at timestamptz not null,
  ends_at timestamptz,
  attendee_count integer,
  required_capability text,
  status text not null default 'scheduled'
    check (status in ('scheduled', 'in_progress', 'completed', 'cancelled')),
  created_at timestamptz not null default now()
);

create index if not exists idx_events_starts_at on events (starts_at);

-- ---------------------------------------------------------------------------
-- dependencies: typed, directional edges — the Impact Graph itself. Generic
-- source/dependency (type, id) pairs so the same table models
-- asset -> location, location -> event, or (for other verticals, unbuilt
-- now) asset -> event directly, with no schema change.
--
-- `dependency_id` is null only for 'capability' edges — a capability isn't
-- a row in any table, it's a leaf fact carried in impact_metadata (e.g.
-- {"capability": "AV_PROJECTION"}), matched against an event's own
-- required_capability column rather than requiring a second traversal hop.
--
-- No DB-level uniqueness constraint on the edge tuple: a duplicate edge is
-- redundant, not unsafe (the traversal/RPC below is idempotent to
-- duplicates), and enforcing one would need an awkward null-coalescing
-- expression index purely to make ON CONFLICT usable in the seed script —
-- not worth it at this scale. Compare `actions.action_key` (Phase 5, not
-- yet built), which DOES need a real uniqueness guarantee because it
-- gates real-world side effects; this table only gates a read.
-- ---------------------------------------------------------------------------
create table if not exists dependencies (
  id uuid primary key default gen_random_uuid(),
  source_type text not null check (source_type in ('asset', 'location', 'event')),
  source_id uuid not null,
  dependency_type text not null check (dependency_type in ('asset', 'location', 'event', 'capability')),
  dependency_id uuid,
  relationship text not null,
  criticality text not null default 'medium' check (criticality in ('low', 'medium', 'high')),
  impact_metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  constraint dependency_id_required_unless_capability
    check (dependency_type = 'capability' or dependency_id is not null)
);

create index if not exists idx_dependencies_source on dependencies (source_type, source_id);

-- ---------------------------------------------------------------------------
-- operational_impact: the persisted output of /impact/calculate. Kept
-- separate from incident_intelligence for the same reason intelligence is
-- kept separate from incidents (0002's own comment) — "what was reported"
-- (incidents), "what Onward inferred" (incident_intelligence), and "what
-- Onward computed from real state" (this table) are three different kinds
-- of truth and stay in three tables, never merged. 1:1 on incident_id.
-- affected_operations/dependency_path/warnings are stored as the
-- already-computed jsonb the engine returned — not re-derivable raw
-- organisational data, so no duplication concern (CLAUDE.md Phase 4 task
-- item 8).
-- ---------------------------------------------------------------------------
create table if not exists operational_impact (
  incident_id uuid primary key references incidents (id),
  schema_version text not null default '1.0',
  asset_id uuid not null references assets (id),
  impact_known boolean not null,
  impact_level text not null check (impact_level in ('none', 'low', 'medium', 'high', 'critical')),
  minutes_until_impact integer,
  service_at_risk text,
  affected_operations jsonb not null default '[]',
  dependency_path jsonb not null default '[]',
  warnings jsonb not null default '[]',
  reason text,
  calculated_at timestamptz not null,
  created_at timestamptz not null default now()
);

alter table locations enable row level security;
alter table events enable row level security;
alter table dependencies enable row level security;
alter table operational_impact enable row level security;

drop policy if exists "public read access" on locations;
create policy "public read access" on locations
  for select to anon, authenticated using (true);

drop policy if exists "public read access" on events;
create policy "public read access" on events
  for select to anon, authenticated using (true);

drop policy if exists "public read access" on dependencies;
create policy "public read access" on dependencies
  for select to anon, authenticated using (true);

drop policy if exists "public read access" on operational_impact;
create policy "public read access" on operational_impact
  for select to anon, authenticated using (true);

-- ---------------------------------------------------------------------------
-- get_dependency_chain: the one place the recursive traversal SQL lives
-- (CLAUDE.md §11) — WF-03 calls this once per incident via PostgREST's RPC
-- endpoint (POST /rest/v1/rpc/get_dependency_chain) instead of re-deriving
-- the graph walk in an n8n Code node, or decision-engine re-querying
-- Postgres itself (which it structurally cannot do — CLAUDE.md §0.3).
-- decision-engine's job is downstream and genuinely different: interpreting
-- the returned edges into meaning (filtering finished/cancelled events,
-- time math, ranking, explaining) — not a second traversal of the same
-- graph.
--
-- Guards against cycles/runaway traversal two ways: the depth cap (mirrors
-- CLAUDE.md §11's own example, `WHERE i.depth < 6`) and a `visited` array
-- of edge ids, so even a misconfigured self-referencing edge cannot loop
-- forever inside one query. decision-engine's own traversal (app/impact/
-- service.py) re-applies an equivalent bound independently — it never
-- trusts its input to already be safe, belt and suspenders.
--
-- Returns a single jsonb OBJECT of shape {"edges": [...]} (via jsonb_agg
-- wrapped in jsonb_build_object, `returns jsonb`, not `returns table(...)`)
-- rather than a bare array — a top-level JSON array in an HTTP response
-- gets split into one n8n item per element, which would make an
-- asset-with-no-dependencies (a legitimate, common case — Phase 4 gate
-- scenario F) produce ZERO items and silently skip every downstream node
-- in WF-03. Wrapping in an object guarantees exactly one n8n item every
-- time, whose `.edges` field is the (possibly empty) array — no
-- zero-items-skips-the-workflow footgun to design around in n8n itself.
-- ---------------------------------------------------------------------------
create or replace function get_dependency_chain(
  p_source_type text,
  p_source_id uuid,
  p_max_depth integer default 6
) returns jsonb
language sql
stable
as $$
  with recursive chain as (
    select
      d.id, d.source_type, d.source_id, d.dependency_type, d.dependency_id,
      d.relationship, d.criticality, d.impact_metadata,
      1 as depth,
      array[d.id] as visited
    from dependencies d
    where d.source_type = p_source_type and d.source_id = p_source_id

    union all

    select
      d.id, d.source_type, d.source_id, d.dependency_type, d.dependency_id,
      d.relationship, d.criticality, d.impact_metadata,
      c.depth + 1,
      c.visited || d.id
    from dependencies d
    join chain c
      on d.source_type = c.dependency_type
     and d.source_id = c.dependency_id
    where c.depth < p_max_depth
      and not (d.id = any (c.visited))
  )
  select jsonb_build_object(
    'edges',
    coalesce(
      jsonb_agg(
        jsonb_build_object(
          'source_type', source_type,
          'source_id', source_id,
          'dependency_type', dependency_type,
          'dependency_id', dependency_id,
          'relationship', relationship,
          'criticality', criticality,
          'impact_metadata', impact_metadata,
          'depth', depth
        )
        order by depth
      ),
      '[]'::jsonb
    )
  )
  from chain;
$$;

grant execute on function get_dependency_chain(text, uuid, integer) to anon, authenticated;
