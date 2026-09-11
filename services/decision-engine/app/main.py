"""Onward decision-engine.

Stateless FastAPI service. No database connection — n8n fetches all resource
state and passes it in as JSON. Endpoints added in later phases:

  POST /incident/interpret   (Phase 3 — M3)
  POST /impact/calculate     (Phase 4 — M4)
  POST /recovery/plan        (Phase 4 — M4)

Only a health check exists in Phase 1.
"""

from fastapi import FastAPI

app = FastAPI(title="Onward Decision Engine")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "onward-decision-engine"}
