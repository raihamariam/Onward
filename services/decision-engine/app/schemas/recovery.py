"""Shared contract for recovery planning — the Phase 5 output.

Recovery answers "what can the organisation realistically do to preserve
the operation?" using real resource state (technicians, inventory,
alternate locations) fetched by n8n, never AI. See CLAUDE.md §0.3/§12 and
the Phase 5 task brief for why this stays a deterministic pure function:
hard constraints first, ranking only among plans that already passed them,
no execution, no approval.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

ResourceStatus = Literal["available", "unavailable"]
PlanType = Literal["repair_via_technician", "replace_asset", "relocate_operation"]
RunStatus = Literal["plans_available", "no_feasible_plan"]

# Ordinal, not a weight — used only to break ties between feasible plans
# with identical estimated_recovery_minutes. Lower means less disruptive to
# the organisation: fixing the broken asset in place disturbs nothing else;
# relocating an entire operation is the most disruptive option available.
# This replaces the vault's 0.45-weighted "continuity" term (see Phase 5
# report's Architectural decisions) with a plain, explainable integer.
DISRUPTION_RANK: dict[PlanType, int] = {
    "repair_via_technician": 0,
    "replace_asset": 1,
    "relocate_operation": 2,
}


class TechnicianState(BaseModel):
    id: str
    name: str
    skills: list[str] = Field(default_factory=list)
    status: ResourceStatus = "available"
    eta_minutes: int | None = None


class InventoryItemState(BaseModel):
    id: str
    name: str
    compatible_capability: str
    quantity: int = 0
    status: ResourceStatus = "available"
    setup_minutes: int | None = None


class AlternateLocationState(BaseModel):
    id: str
    code: str
    name: str
    capacity: int | None = None
    capabilities: list[str] = Field(default_factory=list)
    transfer_minutes: int | None = None
    status: ResourceStatus = "available"


class RecoveryRequest(BaseModel):
    incident_id: str
    # Two DIFFERENT vocabularies, both trusted context, never re-derived or
    # guessed here — conflating them was a real bug caught in design review
    # (see the Phase 5 report's Architectural decisions):
    #   incident_capability: the REPAIR skill a technician/replacement needs
    #     (incident_intelligence.required_capability, e.g. "AV_SUPPORT") —
    #     matched against technicians.skills and inventory.compatible_capability.
    #   operation_capability: what the threatened OPERATION itself needs to
    #     proceed (operational_impact's affected event's own
    #     required_capability, e.g. "AV_PROJECTION") — matched against
    #     alternate_locations.capabilities. A relocation candidate doesn't
    #     care what broke or what skill would fix it; it cares whether the
    #     alternate room already has a working equivalent.
    incident_capability: str | None = None
    operation_capability: str | None = None
    people_affected: int | None = None
    # Minutes until the threatened operation is disrupted (operational_
    # impact.minutes_until_impact) — the hard deadline every candidate is
    # measured against. None means no known time pressure.
    deadline_minutes: int | None = None
    now: datetime = Field(default_factory=lambda: datetime.now(UTC))
    technicians: list[TechnicianState] = Field(default_factory=list)
    inventory: list[InventoryItemState] = Field(default_factory=list)
    alternate_locations: list[AlternateLocationState] = Field(default_factory=list)


class ConstraintResult(BaseModel):
    name: str
    passed: bool
    detail: str


class RecoveryPlan(BaseModel):
    plan_type: PlanType
    # Which real resource row this candidate came from — traceability, not
    # a hallucinated reference (e.g. {"technician_id": "..."}).
    resource_ref: dict = Field(default_factory=dict)
    feasible: bool
    estimated_recovery_minutes: int | None = None
    disruption_rank: int
    rank: int | None = None
    is_recommended: bool = False
    constraints: list[ConstraintResult] = Field(default_factory=list)
    reason: str | None = None


class RecoveryResult(BaseModel):
    schema_version: str = "1.0"
    incident_id: str
    status: RunStatus
    reason: str | None = None
    plans: list[RecoveryPlan] = Field(default_factory=list)
    # Short deterministic hash over the resource state actually considered —
    # lets a later reader detect that real state has moved on since this was
    # computed, without event-sourcing (Phase 5 task item #15).
    state_fingerprint: str
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
