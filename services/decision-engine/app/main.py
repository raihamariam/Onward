"""Onward decision-engine.

Stateless FastAPI service. No database connection — n8n fetches all resource
state and passes it in as JSON. Endpoints added so far:

  POST /incident/interpret   (Phase 3)

Still to come:

  POST /impact/calculate     (Phase 4)
  POST /recovery/plan        (Phase 4)
"""

from fastapi import FastAPI

from app.env import load_repo_root_env
from app.interpret.service import interpret_incident
from app.schemas.incident import IncidentIntelligence, InterpretRequest

load_repo_root_env()

app = FastAPI(title="Onward Decision Engine")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "onward-decision-engine"}


@app.post("/incident/interpret", response_model=IncidentIntelligence)
def incident_interpret(req: InterpretRequest) -> IncidentIntelligence:
    return interpret_incident(req)
