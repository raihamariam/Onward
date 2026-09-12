"""Unit tests for the Impact Engine (Phase 4).

All fixtures are synthetic and in-memory — calculate_impact is a pure
function, so these tests don't need Postgres, n8n, or a model provider.
Real-data evidence (does the actual seeded ECON301 scenario behave this way
against real Supabase state via WF-03) is the Phase 4 live gate, run
separately once database/migrations/0004_impact_graph.sql has been applied.

Cases map directly to the Phase 4 task's required dynamic-behaviour tests:
  A. baseline — asset -> location -> event, starts soon, people affected
  B. same chain, event moved later -> urgency drops
  C. dependency edge removed -> the event no longer appears
  D. participant count changes -> output reflects the new value
  E. one asset, multiple downstream operations -> all represented
  F. no known dependency -> impact_known is False, nothing fabricated
  G. cyclic/malformed relationship -> bounded, safe, no crash
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.impact.service import calculate_impact
from app.schemas.impact import DependencyEdge, EventState, ImpactRequest, LocationState

NOW = datetime(2026, 3, 5, 9, 0, 0, tzinfo=UTC)

ASSET_ID = "asset-av-204"
LOCATION_ID = "loc-room-312"
EVENT_ID = "event-econ301"


def minutes_from_now(minutes: int) -> datetime:
    return NOW + timedelta(minutes=minutes)


def supports_edge(location_id: str = LOCATION_ID, criticality: str = "high") -> DependencyEdge:
    return DependencyEdge(
        source_type="asset",
        source_id=ASSET_ID,
        dependency_type="location",
        dependency_id=location_id,
        relationship="supports",
        criticality=criticality,
    )


def hosts_edge(
    event_id: str = EVENT_ID, location_id: str = LOCATION_ID, criticality: str = "high"
) -> DependencyEdge:
    return DependencyEdge(
        source_type="location",
        source_id=location_id,
        dependency_type="event",
        dependency_id=event_id,
        relationship="hosts",
        criticality=criticality,
    )


def make_event(
    event_id: str = EVENT_ID,
    code: str = "ECON301",
    name: str = "ECON301 Lecture",
    starts_in_minutes: int = 10,
    ends_in_minutes: int | None = 60,
    attendee_count: int | None = 84,
    required_capability: str | None = "AV_PROJECTION",
    status: str = "scheduled",
) -> EventState:
    return EventState(
        id=event_id,
        code=code,
        name=name,
        starts_at=minutes_from_now(starts_in_minutes),
        ends_at=minutes_from_now(ends_in_minutes) if ends_in_minutes is not None else None,
        attendee_count=attendee_count,
        required_capability=required_capability,
        status=status,
    )


def make_request(**overrides) -> ImpactRequest:
    base = dict(
        incident_id="incident-1",
        asset_id=ASSET_ID,
        asset_code="AV-204",
        now=NOW,
        dependency_edges=[supports_edge(), hosts_edge()],
        locations=[LocationState(id=LOCATION_ID, code="ROOM-312", name="Room 3.12")],
        events=[make_event()],
    )
    base.update(overrides)
    return ImpactRequest(**base)


# --- A. Baseline: lecture starting soon, real dependency chain -------------


def test_baseline_lecture_soon_is_high_urgency():
    result = calculate_impact(make_request())
    assert result.impact_known is True
    assert result.impact_level == "critical"  # 10 minutes out, within the critical band
    assert result.minutes_until_impact == 10
    assert len(result.affected_operations) == 1
    op = result.affected_operations[0]
    assert op.people_affected == 84
    assert op.code == "ECON301"
    assert result.dependency_path == [
        "AV-204",
        "supports Room 3.12",
        "hosts ECON301",
        "serves 84 attendees",
    ]
    assert result.service_at_risk == "AV_PROJECTION for ECON301 Lecture"


# --- B. Same chain, event moved later --------------------------------------


def test_event_moved_later_lowers_urgency():
    soon = calculate_impact(make_request())
    later = calculate_impact(
        make_request(events=[make_event(starts_in_minutes=1500, ends_in_minutes=1560)])
    )
    assert soon.impact_level == "critical"
    assert later.impact_level == "low"
    assert later.minutes_until_impact == 1500
    soon_people = soon.affected_operations[0].people_affected
    later_people = later.affected_operations[0].people_affected
    assert soon_people == later_people


def test_medium_band_between_high_and_low():
    result = calculate_impact(
        make_request(events=[make_event(starts_in_minutes=600, ends_in_minutes=660)])
    )
    assert result.impact_level == "medium"


# --- C. Dependency edge removed ---------------------------------------------


def test_dependency_removed_event_no_longer_appears():
    result = calculate_impact(make_request(dependency_edges=[supports_edge()]))
    assert result.impact_known is True
    assert result.impact_level == "none"
    assert result.affected_operations == []
    assert "ECON301" not in "".join(result.dependency_path)


# --- D. Participant count changes -------------------------------------------


def test_participant_count_change_is_reflected():
    result = calculate_impact(make_request(events=[make_event(attendee_count=250)]))
    assert result.affected_operations[0].people_affected == 250
    assert "serves 250 attendees" in result.dependency_path


def test_missing_participant_count_handled_gracefully():
    result = calculate_impact(make_request(events=[make_event(attendee_count=None)]))
    assert result.affected_operations[0].people_affected is None
    assert not any("attendees" in step for step in result.dependency_path)


# --- E. Multiple downstream dependencies ------------------------------------


def test_one_location_hosting_two_events_reports_both():
    evening = make_event(
        event_id="event-econ301-evening",
        code="ECON301-EVENING",
        starts_in_minutes=540,
        ends_in_minutes=600,
        attendee_count=30,
    )
    evening_edge = hosts_edge(event_id="event-econ301-evening")
    result = calculate_impact(
        make_request(
            dependency_edges=[supports_edge(), hosts_edge(), evening_edge],
            events=[make_event(), evening],
        )
    )
    codes = {op.code for op in result.affected_operations}
    assert codes == {"ECON301", "ECON301-EVENING"}
    # Sorted soonest-first; overall level driven by the most urgent one.
    assert result.affected_operations[0].code == "ECON301"
    assert result.impact_level == "critical"


def test_asset_branching_into_two_locations():
    other_location = "loc-checkout-3"
    other_event = "event-peak-checkout"
    result = calculate_impact(
        make_request(
            dependency_edges=[
                supports_edge(),
                hosts_edge(),
                supports_edge(location_id=other_location),
                hosts_edge(event_id=other_event, location_id=other_location),
            ],
            locations=[
                LocationState(id=LOCATION_ID, code="ROOM-312", name="Room 3.12"),
                LocationState(id=other_location, code="CHECKOUT-3", name="Checkout Lane 3"),
            ],
            events=[
                make_event(),
                make_event(
                    event_id=other_event,
                    code="PEAK-CHECKOUT",
                    name="Peak Checkout Window",
                    starts_in_minutes=20,
                    attendee_count=120,
                    required_capability="POS_PROCESSING",
                ),
            ],
        )
    )
    codes = {op.code for op in result.affected_operations}
    assert codes == {"ECON301", "PEAK-CHECKOUT"}


# --- F. No known dependency --------------------------------------------------


def test_no_dependency_edges_does_not_fabricate_impact():
    result = calculate_impact(make_request(dependency_edges=[]))
    assert result.impact_known is False
    assert result.impact_level == "none"
    assert result.affected_operations == []
    assert result.minutes_until_impact is None


def test_edges_present_but_none_start_at_this_asset():
    edge_fields = {**supports_edge().model_dump(), "source_id": "some-other-asset"}
    unrelated_edge = DependencyEdge(**edge_fields)
    result = calculate_impact(make_request(dependency_edges=[unrelated_edge]))
    assert result.impact_known is False


# --- G. Cyclic / malformed dependency data ----------------------------------


def test_self_referencing_cycle_is_bounded_not_infinite():
    cyclic_edge = DependencyEdge(
        source_type="asset",
        source_id=ASSET_ID,
        dependency_type="asset",
        dependency_id=ASSET_ID,
        relationship="depends_on",
    )
    result = calculate_impact(make_request(dependency_edges=[cyclic_edge]))
    assert result.impact_known is True
    assert "cyclic_dependency_detected" in result.warnings
    assert result.affected_operations == []


def test_edge_missing_dependency_id_is_skipped_safely():
    broken_edge = DependencyEdge(
        source_type="asset",
        source_id=ASSET_ID,
        dependency_type="location",
        dependency_id=None,
        relationship="supports",
    )
    result = calculate_impact(make_request(dependency_edges=[broken_edge]))
    assert result.impact_known is True
    assert result.impact_level == "none"
    assert any("missing dependency_id" in w for w in result.warnings)


def test_edge_pointing_at_unresolvable_event_degrades_safely():
    ghost_edge = hosts_edge(event_id="ghost-event")
    result = calculate_impact(
        make_request(dependency_edges=[supports_edge(), ghost_edge], events=[])
    )
    assert result.impact_known is True
    assert result.impact_level == "none"
    assert any(w.startswith("missing_referenced_event") for w in result.warnings)


def test_long_chain_beyond_max_hops_is_bounded():
    edges = [supports_edge()]
    locations = [LocationState(id=LOCATION_ID, code="ROOM-312", name="Room 3.12")]
    prev_location = LOCATION_ID
    for i in range(10):
        next_location = f"loc-chain-{i}"
        edges.append(
            DependencyEdge(
                source_type="location",
                source_id=prev_location,
                dependency_type="location",
                dependency_id=next_location,
                relationship="adjacent_to",
            )
        )
        locations.append(LocationState(id=next_location, code=f"CHAIN-{i}", name=f"Chain Room {i}"))
        prev_location = next_location
    edges.append(hosts_edge(location_id=prev_location))

    result = calculate_impact(make_request(dependency_edges=edges, locations=locations))
    assert "max_traversal_depth_reached" in result.warnings
    assert result.affected_operations == []  # the event is beyond the hop cap


# --- Event lifecycle: completed / cancelled / stale ------------------------


def test_completed_event_excluded():
    result = calculate_impact(make_request(events=[make_event(status="completed")]))
    assert result.impact_level == "none"
    assert result.affected_operations == []


def test_cancelled_event_excluded():
    result = calculate_impact(make_request(events=[make_event(status="cancelled")]))
    assert result.impact_level == "none"


def test_event_past_its_end_time_excluded_even_if_status_stale():
    stale = make_event(starts_in_minutes=-120, ends_in_minutes=-60, status="scheduled")
    result = calculate_impact(make_request(events=[stale]))
    assert result.impact_level == "none"
    assert result.affected_operations == []


def test_in_progress_event_is_immediate_urgency():
    ongoing = make_event(starts_in_minutes=-10, ends_in_minutes=30, status="in_progress")
    result = calculate_impact(make_request(events=[ongoing]))
    assert result.impact_level == "critical"
    assert result.affected_operations[0].minutes_until_start == 0
