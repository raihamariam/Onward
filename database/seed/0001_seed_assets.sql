-- Onward — Phase 2 seed data. Run after 0001_init.sql, in the Supabase SQL
-- Editor. Idempotent (ON CONFLICT DO NOTHING on the unique `code`), safe to
-- re-run.
--
-- Three assets, not one, and not all "active" — the gate test needs a
-- second active asset to prove the flow isn't hardcoded to a single record,
-- and an inactive one to prove the inactive-asset rejection path for real.
insert into assets (code, name, location, status) values
  ('AV-204', 'Epson Projector', 'Room 3.12', 'active'),
  ('POS-07', 'Point of Sale Terminal', 'Checkout Lane 3', 'active'),
  ('HVAC-12', 'Rooftop HVAC Unit', 'Mechanical Room B', 'inactive')
on conflict (code) do nothing;
