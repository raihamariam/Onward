-- Onward — Phase 11: demo-session marker for the live Command View.
-- Run in the Supabase SQL Editor after 0008_command_view_rls.sql.
--
-- Problem this solves: apps/web's Command View (app/page.tsx) previously
-- followed "whichever incident is newest in the whole incidents table" —
-- so after rehearsals, reopening the presentation screen on competition day
-- would show whatever stale test incident happened to be last, with an
-- expired operational window, instead of a clean SYSTEM READY state.
--
-- This table holds exactly one thing: when the current demo session
-- started. tests/prepare_demo.py inserts a new row (via the secret key)
-- each time the team prepares for a rehearsal or the real run.
-- app/api/incident-state/route.ts reads the most recent row (via the
-- publishable key) and only ever follows an incident reported_at AFTER
-- that timestamp — so historical incidents remain fully intact in the
-- database (nothing is deleted, per CLAUDE.md's audit-trail requirements)
-- but the live screen never accidentally re-surfaces one.
--
-- No incident data is destroyed by this migration or by preparing a demo
-- session — this is purely a "where do we start looking" marker.

create table if not exists demo_sessions (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists idx_demo_sessions_started_at on demo_sessions (started_at desc);

alter table demo_sessions enable row level security;

-- Read-only for the frontend (publishable key) — same convention as every
-- other table apps/web reads. Writes go through tests/prepare_demo.py using
-- the secret key, same as every other operator/seed script in this repo;
-- no insert/update/delete policy is added for anon/authenticated, so this
-- table cannot be mutated from the browser or any public endpoint.
drop policy if exists "public read access" on demo_sessions;
create policy "public read access" on demo_sessions for select to anon, authenticated using (true);
