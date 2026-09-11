# n8n/

Canonical workflow source is the connected n8n Cloud workspace itself, built
and edited via the `mcp__claude_ai_n8n__*` tools available in this Claude
Code environment (see `CLAUDE.md` §9).

`exports/` holds version-controlled JSON snapshots pulled after a workflow is
validated, so the repo has a durable copy independent of the live workspace.
Empty in Phase 1 — no workflows exist yet (confirmed via `search_workflows`/
`search_projects`: one personal project, zero workflows, zero folders).

Never call `publish_workflow`, `execute_workflow` against real credentials,
or any archive/delete tool without the user's explicit go-ahead in that
moment, regardless of how routine it seems.
