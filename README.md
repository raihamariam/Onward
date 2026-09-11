# Onward — Team Unity

An AI operational-response layer that turns physical-world incidents into
coordinated business recovery. *When the physical world breaks, the business
keeps moving.*

Full product thesis, architecture, component responsibilities, data model,
build order, and Claude Code operating rules live in **[`CLAUDE.md`](./CLAUDE.md)**
— read that before touching anything here. Original product/system context is
preserved in `ONWARD_MASTER_MEMORY_VAULT.md` for history; it is not the
operating instructions.

## Repository layout

```
apps/web/                  Next.js incident UI + ops dashboard
services/decision-engine/  FastAPI — stateless interpretation/impact/recovery logic
database/                  Supabase Postgres schema, migrations, seed data
n8n/exports/                Version-controlled snapshots of the live n8n workflows
knowledge/                 Manuals/procedures/safety docs for pgvector retrieval
tests/                     Cross-service integration and end-to-end checks
```

## Local development

```bash
# web app
cd apps/web && npm run dev              # http://localhost:3000

# decision-engine
cd services/decision-engine && uv run uvicorn app.main:app --reload --port 8000
uv run pytest                           # tests
uv run ruff check .                     # lint

# prove both are up together
bash tests/foundation_check.sh
```

Copy `.env.example` to `.env` and fill in real values — see that file for
what's required and which credentials are still blockers (Supabase project,
Anthropic key, Calendar/Slack/Gmail).

## Current phase

**Phase A — system build.** See `CLAUDE.md` §3 and §17 for the milestone
list and Definition of Done. Demo/presentation work does not start until
that gate is met.
