"""Onward decision-engine.

Stateless FastAPI service. No database connection — n8n fetches all resource
state and passes it in as JSON. Endpoints:

  POST /incident/interpret   (Phase 3)
  POST /impact/calculate     (Phase 4)
  POST /recovery/plan        (Phase 5)
"""

from fastapi import FastAPI

from app.env import load_repo_root_env
from app.impact.service import calculate_impact
from app.interpret.service import interpret_incident
from app.recovery.service import plan_recovery
from app.schemas.impact import ImpactRequest, ImpactResult
from app.schemas.incident import IncidentIntelligence, InterpretRequest
from app.schemas.recovery import RecoveryRequest, RecoveryResult

load_repo_root_env()

app = FastAPI(title="Onward Decision Engine")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "onward-decision-engine"}


@app.post("/incident/interpret", response_model=IncidentIntelligence)
def incident_interpret(req: InterpretRequest) -> IncidentIntelligence:
    return interpret_incident(req)


@app.post("/impact/calculate", response_model=ImpactResult)
def impact_calculate(req: ImpactRequest) -> ImpactResult:
    return calculate_impact(req)


@app.post("/recovery/plan", response_model=RecoveryResult)
def recovery_plan(req: RecoveryRequest) -> RecoveryResult:
    return plan_recovery(req)
