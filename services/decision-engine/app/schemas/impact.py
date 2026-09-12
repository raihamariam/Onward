"""Shared contract for operational impact — the Phase 4 output.

Impact answers "what does this failure threaten downstream?" using real
dependency-graph state fetched by n8n (assets/locations/events + the edges
connecting them), never AI. See CLAUDE.md §0.3 (decision-engine is stateless
— n8n fetches state, this module computes on it), §11 (dependency traversal
lives here), and the Phase 4 task brief.

Deliberately excludes anything Phase 5 (Recovery) owns: no technician/
inventory/room-alternative fields exist anywhere in this contract.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

NodeType = Literal["asset", "location", "event"]
DependencyType = Literal["asset", "location", "event", "capability"]
EdgeCriticality = Literal["low", "medium", "high"]
ImpactLevel = Literal["none", "low", "medium", "high", "critical"]
EventStatus = Literal["scheduled", "in_progress", "completed", "cancelled"]

# Safety net independent of whatever bound the SQL CTE that produced these
# edges already applied (database/migrations/0004_impact_graph.sql caps at
# 6) — this module never trusts its input to already be safely bounded.
MAX_TRAVERSAL_HOPS = 6


class DependencyEdge(BaseModel):
    """One row from the `dependencies` table (or its get_dependency_chain
    RPC projection) — a typed, directional edge in the Impact Graph."""

    source_type: NodeType
    source_id: str
    dependency_type: DependencyType
    dependency_id: str | None = None
    relationship: str
    criticality: EdgeCriticality = "medium"
    impact_metadata: dict = Field(default_factory=dict)
    depth: int = 1


class EventState(BaseModel):
    """A row from `events` — real organisational state, never inferred."""

    id: str
    code: str
    name: str
    starts_at: datetime
    ends_at: datetime | None = None
    attendee_count: int | None = None
    required_capability: str | None = None
    status: EventStatus = "scheduled"


class LocationState(BaseModel):
    """A row from `locations` — identity only; capacity/status are Phase 5
    (recovery-resource) concerns and deliberately absent here."""

    id: str
    code: str
    name: str


class ImpactRequest(BaseModel):
    incident_id: str
    asset_id: str
    asset_code: str | None = None
    # From incident_intelligence (Phase 3), informational only — used to
    # phrase service_at_risk when it matches an event's own requirement;
    # never used to infer new operational facts.
    required_capability: str | None = None
    now: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dependency_edges: list[DependencyEdge] = Field(default_factory=list)
    locations: list[LocationState] = Field(default_factory=list)
    events: list[EventState] = Field(default_factory=list)


class AffectedOperation(BaseModel):
    type: Literal["event"] = "event"
    id: str
    code: str
    name: str
    starts_at: datetime
    minutes_until_start: int
    people_affected: int | None
    required_capability: str | None
    criticality: ImpactLevel
    dependency_path: list[str] = Field(default_factory=list)


class ImpactResult(BaseModel):
    schema_version: str = "1.0"
    incident_id: str
    asset_id: str
    # False only when nothing is known at all (no registered dependency, or
    # the graph couldn't be resolved). True whenever a real relationship
    # exists, even if nothing is *currently* at risk through it — those are
    # different facts and callers need to tell them apart.
    impact_known: bool
    impact_level: ImpactLevel
    minutes_until_impact: int | None = None
    service_at_risk: str | None = None
    affected_operations: list[AffectedOperation] = Field(default_factory=list)
    dependency_path: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    reason: str | None = None
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
