"""Recovery Engine — pure function: resource state -> ranked recovery plans.

No AI, no I/O (CLAUDE.md §0.3). n8n's WF-04 fetches current technicians,
inventory, and alternate-location state and hands it all in as JSON; this
module generates candidates, validates hard constraints deterministically,
and ranks only the plans that already passed them. See the Phase 5 report's
Architectural decisions for why ranking here is a plain two-key sort
(fastest feasible plan wins, ties broken by lowest disruption) rather than
a weighted score.
"""

from __future__ import annotations

import hashlib
import json

from app.schemas.recovery import (
    DISRUPTION_RANK,
    AlternateLocationState,
    ConstraintResult,
    InventoryItemState,
    RecoveryPlan,
    RecoveryRequest,
    RecoveryResult,
    TechnicianState,
)


def _fingerprint(req: RecoveryRequest) -> str:
    """Deterministic hash over exactly the resource + impact facts that
    feed candidate generation and constraint checks — lets a later reader
    detect real state has moved on since this was computed, without
    event-sourcing (Phase 5 task item #15)."""
    payload = {
        "incident_capability": req.incident_capability,
        "operation_capability": req.operation_capability,
        "people_affected": req.people_affected,
        "deadline_minutes": req.deadline_minutes,
        "technicians": sorted(
            [t.id, t.status, t.eta_minutes, sorted(t.skills)] for t in req.technicians
        ),
        "inventory": sorted(
            [i.id, i.status, i.quantity, i.setup_minutes] for i in req.inventory
        ),
        "alternate_locations": sorted(
            [loc.id, loc.status, loc.capacity, loc.transfer_minutes, sorted(loc.capabilities)]
            for loc in req.alternate_locations
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _time_window_constraint(
    estimated_minutes: int | None, deadline_minutes: int | None
) -> ConstraintResult:
    if estimated_minutes is None:
        return ConstraintResult(
            name="time_window", passed=False, detail="recovery time unknown"
        )
    if deadline_minutes is None:
        return ConstraintResult(
            name="time_window",
            passed=True,
            detail=f"{estimated_minutes} min, no deadline pressure",
        )
    passed = estimated_minutes <= deadline_minutes
    detail = f"{estimated_minutes} min {'<=' if passed else '>'} {deadline_minutes} min available"
    return ConstraintResult(name="time_window", passed=passed, detail=detail)


def _repair_candidate(tech: TechnicianState, req: RecoveryRequest) -> RecoveryPlan:
    constraints = [
        ConstraintResult(
            name="technician_capability",
            passed=True,
            detail=f"has {req.incident_capability}",
        ),
        ConstraintResult(
            name="technician_status",
            passed=tech.status == "available",
            detail=f"status is {tech.status}",
        ),
        _time_window_constraint(tech.eta_minutes, req.deadline_minutes),
    ]
    return RecoveryPlan(
        plan_type="repair_via_technician",
        resource_ref={"technician_id": tech.id, "name": tech.name},
        feasible=all(c.passed for c in constraints),
        estimated_recovery_minutes=tech.eta_minutes,
        disruption_rank=DISRUPTION_RANK["repair_via_technician"],
        constraints=constraints,
    )


def _replace_candidate(item: InventoryItemState, req: RecoveryRequest) -> RecoveryPlan:
    constraints = [
        ConstraintResult(
            name="inventory_status",
            passed=item.status == "available",
            detail=f"status is {item.status}",
        ),
        ConstraintResult(
            name="inventory_quantity",
            passed=item.quantity >= 1,
            detail=f"{item.quantity} in stock",
        ),
        _time_window_constraint(item.setup_minutes, req.deadline_minutes),
    ]
    return RecoveryPlan(
        plan_type="replace_asset",
        resource_ref={"inventory_id": item.id, "name": item.name},
        feasible=all(c.passed for c in constraints),
        estimated_recovery_minutes=item.setup_minutes,
        disruption_rank=DISRUPTION_RANK["replace_asset"],
        constraints=constraints,
    )


def _capacity_constraint(loc: AlternateLocationState, req: RecoveryRequest) -> ConstraintResult:
    if req.people_affected is None:
        return ConstraintResult(
            name="capacity", passed=False, detail="cannot verify capacity: attendee count unknown"
        )
    if loc.capacity is None:
        return ConstraintResult(
            name="capacity",
            passed=False,
            detail=f"capacity unknown, {req.people_affected} required",
        )
    passed = loc.capacity >= req.people_affected
    op = ">=" if passed else "<"
    return ConstraintResult(
        name="capacity", passed=passed, detail=f"{loc.capacity} {op} {req.people_affected}"
    )


def _capability_constraint(loc: AlternateLocationState, req: RecoveryRequest) -> ConstraintResult:
    if req.operation_capability is None:
        return ConstraintResult(
            name="capability", passed=True, detail="no specific capability required"
        )
    passed = req.operation_capability in loc.capabilities
    verb = "has" if passed else "missing"
    return ConstraintResult(
        name="capability", passed=passed, detail=f"{verb} {req.operation_capability}"
    )


def _relocate_candidate(loc: AlternateLocationState, req: RecoveryRequest) -> RecoveryPlan:
    constraints = [
        ConstraintResult(
            name="location_status",
            passed=loc.status == "available",
            detail=f"status is {loc.status}",
        ),
        _capacity_constraint(loc, req),
        _capability_constraint(loc, req),
        _time_window_constraint(loc.transfer_minutes, req.deadline_minutes),
    ]
    return RecoveryPlan(
        plan_type="relocate_operation",
        resource_ref={"location_id": loc.id, "code": loc.code, "name": loc.name},
        feasible=all(c.passed for c in constraints),
        estimated_recovery_minutes=loc.transfer_minutes,
        disruption_rank=DISRUPTION_RANK["relocate_operation"],
        constraints=constraints,
    )


def _generate_candidates(req: RecoveryRequest) -> list[RecoveryPlan]:
    plans: list[RecoveryPlan] = []

    # Without a known required capability we cannot safely match any
    # resource to it — no candidate is generated rather than guessing
    # (mirrors CLAUDE.md's "unknown should not silently become true").
    if req.incident_capability is not None:
        for tech in req.technicians:
            if req.incident_capability in tech.skills:
                plans.append(_repair_candidate(tech, req))
        for item in req.inventory:
            if item.compatible_capability == req.incident_capability:
                plans.append(_replace_candidate(item, req))

    for loc in req.alternate_locations:
        if loc.transfer_minutes is None:
            continue  # not a valid relocation target, not a candidate at all
        plans.append(_relocate_candidate(loc, req))

    return plans


def _rank_and_explain(plans: list[RecoveryPlan]) -> None:
    feasible_plans = [p for p in plans if p.feasible]
    feasible_plans.sort(
        key=lambda p: (
            p.estimated_recovery_minutes if p.estimated_recovery_minutes is not None else 10**9,
            p.disruption_rank,
        )
    )
    for i, plan in enumerate(feasible_plans, start=1):
        plan.rank = i

    if feasible_plans:
        winner = feasible_plans[0]
        winner.is_recommended = True
        winner_minutes = winner.estimated_recovery_minutes
        winner.reason = f"fastest feasible recovery option ({winner_minutes} min)"
        for plan in feasible_plans[1:]:
            delta = (plan.estimated_recovery_minutes or 0) - (winner_minutes or 0)
            plan.reason = (
                f"feasible, but {delta} min slower than the recommended plan"
                if delta > 0
                else "feasible, but more disruptive than the recommended plan"
            )

    for plan in plans:
        if not plan.feasible:
            failed = [c.name for c in plan.constraints if not c.passed]
            plan.reason = f"infeasible: failed {', '.join(failed)}"


def plan_recovery(req: RecoveryRequest) -> RecoveryResult:
    plans = _generate_candidates(req)
    _rank_and_explain(plans)
    feasible_count = sum(1 for p in plans if p.feasible)

    if not plans:
        status = "no_feasible_plan"
        reason = "no candidate recovery strategies apply to this incident's required capability"
    elif feasible_count == 0:
        status = "no_feasible_plan"
        reason = "all candidate recovery plans failed at least one hard constraint"
    else:
        status, reason = "plans_available", None

    return RecoveryResult(
        incident_id=req.incident_id,
        status=status,
        reason=reason,
        plans=plans,
        state_fingerprint=_fingerprint(req),
    )
