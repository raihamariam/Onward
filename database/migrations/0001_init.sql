-- Onward — Phase 2 minimum schema: registered assets + incidents.
-- Run once in the Supabase SQL Editor (no CLI/DB-wire access is available
-- to this environment — see CLAUDE.md and the Phase 2 report for why).
--
-- Deliberately minimal: only what Incident Intake needs. Locations, events,
-- dependencies, technicians, inventory, recovery_plans, etc. are added when
-- the Impact Graph / Recovery Engine phases actually need them (CLAUDE.md
-- §10) — do not add them here speculatively.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- assets: registered physical equipment. `code` is the stable, human-facing
-- identifier (e.g. "AV-204") that a later QR code will encode and that
-- incident intake resolves against — not the internal uuid.
-- ---------------------------------------------------------------------------
create table if not exists assets (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  location text,
  status text not null default 'active' check (status in ('active', 'inactive', 'retired')),
  created_at timestamptz not null default now()
);

create index if not exists idx_assets_code on assets (code);

-- ---------------------------------------------------------------------------
-- incidents: what a user reported, verbatim. No AI-inferred fields belong
-- here (see CLAUDE.md §5 — "what the user reported" vs "what Onward
-- inferred" stay separate; inferred fields arrive in Phase 3 on a separate
-- table/columns, not by widening this one).
-- ---------------------------------------------------------------------------
create table if not exists incidents (
  id uuid primary key default gen_random_uuid(),
  asset_id uuid not null references assets (id),
  idempotency_key text not null unique,
  description text not null,
  media_url text,
  source text not null default 'web',
  status text not null default 'received' check (status in ('received', 'intake_complete', 'failed')),
  reported_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_incidents_asset_id on incidents (asset_id);
create index if not exists idx_incidents_idempotency_key on incidents (idempotency_key);

-- ---------------------------------------------------------------------------
-- Row Level Security: n8n writes using the secret key, which bypasses RLS
-- entirely (Supabase's service-role behavior) — no write policy is needed
-- or added for the anon/publishable role. The frontend reads directly with
-- the publishable key (CLAUDE.md's reads-vs-writes split), so both tables
-- get a public SELECT policy and nothing else.
-- ---------------------------------------------------------------------------
alter table assets enable row level security;
alter table incidents enable row level security;

drop policy if exists "public read access" on assets;
create policy "public read access" on assets
  for select
  to anon, authenticated
  using (true);

drop policy if exists "public read access" on incidents;
create policy "public read access" on incidents
  for select
  to anon, authenticated
  using (true);
