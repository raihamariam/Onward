-- Onward — Phase 4 seed: the Impact Graph's minimum operational world.
-- Run after 0004_impact_graph.sql, in the Supabase SQL Editor. Builds on
-- the three assets already seeded in 0001_seed_assets.sql (AV-204, POS-07,
-- HVAC-12) — no new assets are created here.
--
-- Uses now() + interval so timestamps are always fresh relative to when you
-- run it — RE-RUN THIS SEED before a demo or a live-gate run to reset
-- ECON301's start time back to "urgent." Locations/events are idempotent
-- (ON CONFLICT on the unique `code`, refreshing timestamps on re-run so
-- reseeding actually resets urgency instead of being a silent no-op).
-- Dependency edges are guarded with NOT EXISTS instead of a DB unique
-- constraint — see 0004_impact_graph.sql's comment on `dependencies` for why.
--
-- Two independent chains prove the graph isn't projector-specific
-- (CLAUDE.md Phase 4 brief): AV-204 -> Room 3.12 -> two lectures (branching
-- + multi-event + timing variance in one scenario), and POS-07 -> Checkout
-- Lane 3 -> a peak checkout window (a second, unrelated vertical). HVAC-12
-- deliberately gets NO dependency edges, proving the "no known dependency"
-- path is real, not just untested theory (Phase 4 gate scenario F).

-- Locations
insert into locations (code, name) values
  ('ROOM-312', 'Room 3.12'),
  ('CHECKOUT-3', 'Checkout Lane 3')
on conflict (code) do nothing;

-- Events — ECON301 starts soon (critical urgency, <=15 min band);
-- ECON301-EVENING is the same room's next booking, hours later (proves
-- timing alone changes urgency — Phase 4 gate scenario B — with nothing
-- else about the asset or dependency changed).
insert into events (code, name, starts_at, ends_at, attendee_count, required_capability, status)
values
  ('ECON301', 'ECON301 Lecture', now() + interval '10 minutes', now() + interval '70 minutes', 84, 'AV_PROJECTION', 'scheduled'),
  ('ECON301-EVENING', 'ECON301 Evening Review Session', now() + interval '9 hours', now() + interval '10 hours', 30, 'AV_PROJECTION', 'scheduled'),
  ('PEAK-CHECKOUT', 'Peak Checkout Window', now() + interval '20 minutes', now() + interval '80 minutes', 120, 'POS_PROCESSING', 'scheduled')
on conflict (code) do update set
  starts_at = excluded.starts_at,
  ends_at = excluded.ends_at,
  attendee_count = excluded.attendee_count,
  required_capability = excluded.required_capability,
  status = excluded.status;

-- Dependencies — the Impact Graph itself.

insert into dependencies (source_type, source_id, dependency_type, dependency_id, relationship, criticality)
select 'asset', a.id, 'location', l.id, 'supports', 'high'
from assets a, locations l
where a.code = 'AV-204' and l.code = 'ROOM-312'
and not exists (
  select 1 from dependencies d
  where d.source_type = 'asset' and d.source_id = a.id
    and d.dependency_type = 'location' and d.dependency_id = l.id
    and d.relationship = 'supports'
);

insert into dependencies (source_type, source_id, dependency_type, dependency_id, relationship, criticality)
select 'location', l.id, 'event', e.id, 'hosts', 'high'
from locations l, events e
where l.code = 'ROOM-312' and e.code = 'ECON301'
and not exists (
  select 1 from dependencies d
  where d.source_type = 'location' and d.source_id = l.id
    and d.dependency_type = 'event' and d.dependency_id = e.id
    and d.relationship = 'hosts'
);

insert into dependencies (source_type, source_id, dependency_type, dependency_id, relationship, criticality)
select 'location', l.id, 'event', e.id, 'hosts', 'medium'
from locations l, events e
where l.code = 'ROOM-312' and e.code = 'ECON301-EVENING'
and not exists (
  select 1 from dependencies d
  where d.source_type = 'location' and d.source_id = l.id
    and d.dependency_type = 'event' and d.dependency_id = e.id
    and d.relationship = 'hosts'
);

insert into dependencies (source_type, source_id, dependency_type, dependency_id, relationship, criticality)
select 'asset', a.id, 'location', l.id, 'supports', 'medium'
from assets a, locations l
where a.code = 'POS-07' and l.code = 'CHECKOUT-3'
and not exists (
  select 1 from dependencies d
  where d.source_type = 'asset' and d.source_id = a.id
    and d.dependency_type = 'location' and d.dependency_id = l.id
    and d.relationship = 'supports'
);

insert into dependencies (source_type, source_id, dependency_type, dependency_id, relationship, criticality)
select 'location', l.id, 'event', e.id, 'hosts', 'high'
from locations l, events e
where l.code = 'CHECKOUT-3' and e.code = 'PEAK-CHECKOUT'
and not exists (
  select 1 from dependencies d
  where d.source_type = 'location' and d.source_id = l.id
    and d.dependency_type = 'event' and d.dependency_id = e.id
    and d.relationship = 'hosts'
);

-- HVAC-12: no dependency edges inserted for it, deliberately.
