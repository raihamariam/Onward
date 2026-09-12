"""Unit tests for the Recovery Engine (Phase 5).

All fixtures are synthetic and in-memory — plan_recovery is a pure
function, so these tests don't need Postgres, n8n, or a model provider.
Real-data evidence (does the seeded ECON301/AV-204 scenario behave this way
against real Supabase state via WF-04) is the Phase 5 live gate, run
separately.

Cases map directly to the Phase 5 task's required dynamic-behaviour tests:
  A. baseline — technician/replacement too slow, alternate room feasible
  B. technician becomes fast enough -> repair becomes feasible
  C. alternate room unavailable -> disappears from valid recommendations
  D. capacity failure -> room option rejected
  E. replacement becomes viable -> valid candidate
  F. all options infeasible -> no_feasible_plan
  G. multiple feasible options -> transparent ranking picks one
"""

from __future__ import annotations

from app.recovery.service import plan_recovery
from app.schemas.recovery import (
    AlternateLocationState,
    InventoryItemState,
    RecoveryRequest,
    TechnicianState,
)

TECH_ID = "tech-alex"
INV_ID = "inv-projector"
ROOM_208_ID = "loc-208"
ROOM_101_ID = "loc-101"


def technician(**overrides) -> TechnicianState:
    base = dict(
        id=TECH_ID, name="Alex Rivera", skills=["AV_SUPPORT"], status="available", eta_minutes=28
    )
    base.update(overrides)
    return TechnicianState(**base)


def inventory_item(**overrides) -> InventoryItemState:
    base = dict(
        id=INV_ID, name="Spare Epson Projector", compatible_capability="AV_SUPPORT",
        quantity=2, status="available", setup_minutes=19,
    )
    base.update(overrides)
    return InventoryItemState(**base)


def room_208(**overrides) -> AlternateLocationState:
    base = dict(
        id=ROOM_208_ID, code="ROOM-208", name="Room 2.08", capacity=96,
        capabilities=["AV_PROJECTION"], transfer_minutes=7, status="available",
    )
    base.update(overrides)
    return AlternateLocationState(**base)


def room_101(**overrides) -> AlternateLocationState:
    base = dict(
        id=ROOM_101_ID, code="ROOM-101", name="Room 1.01", capacity=50,
        capabilities=["AV_PROJECTION"], transfer_minutes=5, status="available",
    )
    base.update(overrides)
    return AlternateLocationState(**base)


def make_request(**overrides) -> RecoveryRequest:
    base = dict(
        incident_id="incident-1",
        incident_capability="AV_SUPPORT",
        operation_capability="AV_PROJECTION",
        people_affected=84,
        deadline_minutes=13,
        technicians=[technician()],
        inventory=[inventory_item()],
        alternate_locations=[room_208()],
    )
    base.update(overrides)
    return RecoveryRequest(**base)


def plan_of_type(result, plan_type):
    return next(p for p in result.plans if p.plan_type == plan_type)


# --- A. Baseline -------------------------------------------------------


def test_baseline_only_relocation_is_feasible():
    result = plan_recovery(make_request())
    assert result.status == "plans_available"
    repair = plan_of_type(result, "repair_via_technician")
    replace = plan_of_type(result, "replace_asset")
    relocate = plan_of_type(result, "relocate_operation")
    assert repair.feasible is False
    assert replace.feasible is False
    assert relocate.feasible is True
    assert relocate.is_recommended is True
    assert relocate.rank == 1


def test_infeasible_plans_carry_failure_reasons():
    result = plan_recovery(make_request())
    repair = plan_of_type(result, "repair_via_technician")
    assert "time_window" in repair.reason
    time_constraint = next(c for c in repair.constraints if c.name == "time_window")
    assert time_constraint.passed is False
    assert "28" in time_constraint.detail and "13" in time_constraint.detail


# --- B. Technician becomes fast enough -----------------------------------


def test_fast_technician_becomes_feasible_and_can_win():
    result = plan_recovery(make_request(technicians=[technician(eta_minutes=5)]))
    repair = plan_of_type(result, "repair_via_technician")
    relocate = plan_of_type(result, "relocate_operation")
    assert repair.feasible is True
    assert repair.estimated_recovery_minutes == 5
    # 5 min repair beats 7 min relocation -> repair should now be recommended.
    assert repair.is_recommended is True
    assert relocate.is_recommended is False
    assert repair.rank == 1
    assert relocate.rank == 2


# --- C. Alternate room unavailable ----------------------------------------


def test_unavailable_room_is_rejected():
    result = plan_recovery(make_request(alternate_locations=[room_208(status="unavailable")]))
    relocate = plan_of_type(result, "relocate_operation")
    assert relocate.feasible is False
    status_constraint = next(c for c in relocate.constraints if c.name == "location_status")
    assert status_constraint.passed is False
    assert result.status == "no_feasible_plan"


# --- D. Capacity failure ---------------------------------------------------


def test_insufficient_capacity_rejects_room():
    result = plan_recovery(make_request(alternate_locations=[room_101()]))  # capacity 50 < 84
    relocate = plan_of_type(result, "relocate_operation")
    assert relocate.feasible is False
    capacity_constraint = next(c for c in relocate.constraints if c.name == "capacity")
    assert capacity_constraint.passed is False
    assert "50" in capacity_constraint.detail and "84" in capacity_constraint.detail


def test_unknown_people_affected_fails_capacity_safely_not_silently_true():
    result = plan_recovery(make_request(people_affected=None))
    relocate = plan_of_type(result, "relocate_operation")
    capacity_constraint = next(c for c in relocate.constraints if c.name == "capacity")
    assert capacity_constraint.passed is False
    assert "unknown" in capacity_constraint.detail


# --- E. Replacement becomes viable -----------------------------------------


def test_fast_replacement_becomes_feasible():
    result = plan_recovery(make_request(inventory=[inventory_item(setup_minutes=10)]))
    replace = plan_of_type(result, "replace_asset")
    assert replace.feasible is True
    assert replace.estimated_recovery_minutes == 10


def test_out_of_stock_replacement_rejected_even_if_fast():
    result = plan_recovery(make_request(inventory=[inventory_item(setup_minutes=5, quantity=0)]))
    replace = plan_of_type(result, "replace_asset")
    assert replace.feasible is False
    qty_constraint = next(c for c in replace.constraints if c.name == "inventory_quantity")
    assert qty_constraint.passed is False


# --- F. No feasible option ---------------------------------------------------


def test_all_infeasible_yields_no_feasible_plan_without_fabrication():
    result = plan_recovery(
        make_request(alternate_locations=[room_208(status="unavailable")])
    )
    assert result.status == "no_feasible_plan"
    assert result.reason
    assert all(not p.is_recommended for p in result.plans)
    assert all(p.rank is None for p in result.plans)


def test_no_applicable_candidates_at_all_is_no_feasible_plan():
    result = plan_recovery(
        make_request(
            incident_capability="UNKNOWN_SKILL",
            technicians=[technician()],
            inventory=[inventory_item()],
            alternate_locations=[],
        )
    )
    assert result.status == "no_feasible_plan"
    assert result.plans == []


def test_unknown_incident_capability_generates_no_repair_or_replace_candidates():
    result = plan_recovery(make_request(incident_capability=None, alternate_locations=[]))
    assert result.plans == []
    assert result.status == "no_feasible_plan"


# --- G. Multiple feasible options -------------------------------------------


def test_multiple_feasible_plans_ranked_transparently_by_speed():
    result = plan_recovery(
        make_request(
            technicians=[technician(eta_minutes=10)],
            alternate_locations=[room_208(transfer_minutes=7)],
            deadline_minutes=30,
        )
    )
    repair = plan_of_type(result, "repair_via_technician")
    relocate = plan_of_type(result, "relocate_operation")
    assert repair.feasible and relocate.feasible
    # Relocation (7 min) is faster than repair (10 min) -> relocation wins.
    assert relocate.is_recommended is True
    assert relocate.rank == 1
    assert repair.rank == 2
    assert "slower" in repair.reason


def test_tie_in_recovery_time_broken_by_disruption_rank():
    result = plan_recovery(
        make_request(
            technicians=[technician(eta_minutes=7)],
            alternate_locations=[room_208(transfer_minutes=7)],
        )
    )
    repair = plan_of_type(result, "repair_via_technician")
    relocate = plan_of_type(result, "relocate_operation")
    assert repair.estimated_recovery_minutes == relocate.estimated_recovery_minutes == 7
    # Equal time -> lower disruption_rank (repair) wins the tie.
    assert repair.is_recommended is True
    assert relocate.is_recommended is False


# --- Traceability / explainability ------------------------------------------


def test_resource_ref_traces_to_real_resource_ids():
    result = plan_recovery(make_request())
    repair = plan_of_type(result, "repair_via_technician")
    replace = plan_of_type(result, "replace_asset")
    relocate = plan_of_type(result, "relocate_operation")
    assert repair.resource_ref["technician_id"] == TECH_ID
    assert replace.resource_ref["inventory_id"] == INV_ID
    assert relocate.resource_ref["location_id"] == ROOM_208_ID


def test_relocation_skipped_when_not_a_valid_target():
    result = plan_recovery(make_request(alternate_locations=[room_208(transfer_minutes=None)]))
    assert not any(p.plan_type == "relocate_operation" for p in result.plans)


# --- Stale-state fingerprint -------------------------------------------------


def test_fingerprint_stable_for_identical_input():
    r1 = plan_recovery(make_request())
    r2 = plan_recovery(make_request())
    assert r1.state_fingerprint == r2.state_fingerprint


def test_fingerprint_changes_when_resource_state_changes():
    r1 = plan_recovery(make_request())
    r2 = plan_recovery(make_request(technicians=[technician(eta_minutes=5)]))
    assert r1.state_fingerprint != r2.state_fingerprint


def test_fingerprint_unaffected_by_field_order_or_irrelevant_ids():
    """Same substantive state, different Python construction order -> same
    fingerprint. Proves the fingerprint reflects actual facts, not
    incidental representation details."""
    jordan = technician(id="t2", name="Jordan Lee")
    r1 = plan_recovery(make_request(technicians=[technician(), jordan]))
    r2 = plan_recovery(make_request(technicians=[jordan, technician()]))
    assert r1.state_fingerprint == r2.state_fingerprint


# --- No deadline pressure ----------------------------------------------------


def test_no_deadline_means_time_window_always_passes():
    result = plan_recovery(make_request(deadline_minutes=None))
    repair = plan_of_type(result, "repair_via_technician")
    time_constraint = next(c for c in repair.constraints if c.name == "time_window")
    assert time_constraint.passed is True
    assert repair.feasible is True
