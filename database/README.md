# database/

Supabase Postgres schema and seed data. Empty in Phase 1 by design — there is
no Supabase project to apply anything to yet (see root `.env.example`).

- `migrations/` — plain numbered `.sql` files (`0001_init.sql`, ...), applied
  via `psql` or the Supabase SQL editor. No ORM/migration framework needed at
  this scale.
- `seed/` — seed script(s) for the small university world described in
  `CLAUDE.md` §17 (M1): 3 assets, 3 rooms, 2 technicians, a few events,
  dependency edges, a few knowledge chunks.
- `schema.sql` — added in Phase 2 (M1), matching the tables in `CLAUDE.md`
  §10.

Do not add tables here speculatively. The table list in `CLAUDE.md` §10 is
the contract — extend it there first if a real need appears.
