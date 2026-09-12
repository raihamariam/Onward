-- Onward — Phase 10: minimal RLS re-open for the live Command View.
-- Run in the Supabase SQL Editor after 0007_tighten_execution_rls.sql.
--
-- 0007 correctly locked anon/publishable reads on all six Phase 6 tables
-- because, at the time, nothing in apps/web read any of them. That has now
-- changed: the Command View (apps/web/app/page.tsx, via
-- app/api/incident-state/route.ts) needs to show live execution progress
-- during the demo -- reserve/calendar/work-order/notification checklist
-- items ticking off as execution_actions rows complete, and the final
-- "OPERATION RECOVERED" screen reading work_orders/resource_reservations.
-- It also needs to know whether a plan has been approved/rejected yet.
--
-- Scope is deliberately narrow: only the five tables the Command View
-- actually reads get a policy. `audit_log` is NOT reopened -- nothing in
-- the current frontend reads it (per CLAUDE.md's "keep public read only
-- where the real frontend genuinely needs it" convention, same reasoning
-- 0007 itself used). If a future audit-trail view is built, add a scoped
-- policy for exactly that table at that point, not preemptively here.
--
-- This does not touch write access anywhere: n8n's WF-05a/WF-05 continue
-- writing with the Supabase SECRET key, which bypasses RLS entirely
-- regardless of what anon/authenticated policies exist. This migration
-- only affects what the publishable-key reader (apps/web, server-side) can
-- see.

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
