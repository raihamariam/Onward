-- Onward — Phase 6 follow-up: tighten RLS on the six tables 0006 just
-- added. Run in the Supabase SQL Editor after 0006_execution.sql.
--
-- 0006 gave all six the same "public read access" policy as every prior
-- table, matching this project's established pattern. On review: the
-- frontend (apps/web/app/incidents/[id]/page.tsx) reads only `incidents`
-- today — nothing anywhere in apps/web reads approvals, execution_runs,
-- execution_actions, work_orders, resource_reservations, or audit_log yet.
-- "Keep public read only where the real frontend genuinely needs it" means
-- none of these six currently qualify.
--
-- This does NOT affect any Phase 6 n8n functionality: WF-05a/WF-05 read
-- and write these tables using the Supabase SECRET key (n8n's own
-- credential), which bypasses RLS entirely regardless of what policies
-- exist for the anon/authenticated roles. Only a hypothetical
-- publishable-key reader (a future frontend page, or the anon key used
-- directly) is affected — and none exists yet for these tables.
--
-- Dropping the policy with RLS still enabled (already turned on in 0006)
-- means default-deny for anon/authenticated: no replacement policy is
-- added here. When a real ops-dashboard page is built to show approval/
-- execution status, add a scoped public-SELECT policy for exactly the
-- table(s) it reads at that point — matching every other table's existing
-- convention — rather than speculatively re-opening all six now.

drop policy if exists "public read access" on approvals;
drop policy if exists "public read access" on execution_runs;
drop policy if exists "public read access" on execution_actions;
drop policy if exists "public read access" on work_orders;
drop policy if exists "public read access" on resource_reservations;
drop policy if exists "public read access" on audit_log;
