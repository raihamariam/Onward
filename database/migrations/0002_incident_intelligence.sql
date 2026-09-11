-- Onward — Phase 3: incident_intelligence. Run once in the Supabase SQL
-- Editor, after 0001_init.sql (same reason as before: no SQL execution path
-- is available to this environment).
--
-- Kept separate from `incidents` on purpose: `incidents` is what the user
-- reported, verbatim; this table is what Onward inferred. One row per
-- incident (1:1), never merged into the incidents row itself, so a future
-- auditor (or this codebase) can always tell the two apart.

create table if not exists incident_intelligence (
  incident_id uuid primary key references incidents (id),
  schema_version text not null default '1.0',
  incident_type text not null,
  symptoms jsonb not null default '[]',
  visual_observations jsonb not null default '[]',
  severity text not null check (severity in ('low', 'medium', 'high', 'critical')),
  safety_risk boolean not null default false,
  confidence numeric not null check (confidence >= 0 and confidence <= 1),
  likely_faults jsonb not null default '[]',
  required_capability text not null,
  requires_human_review boolean not null default false,
  review_reason text,
  evidence_conflict boolean not null default false,
  model text not null,
  provider text not null default 'anthropic',
  interpreted_at timestamptz not null,
  created_at timestamptz not null default now()
);

alter table incident_intelligence enable row level security;

drop policy if exists "public read access" on incident_intelligence;
create policy "public read access" on incident_intelligence
  for select
  to anon, authenticated
  using (true);
