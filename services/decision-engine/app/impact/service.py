"""Impact Engine — pure function: dependency traversal -> operational impact.

No AI, no I/O, no database connection (CLAUDE.md §0.3). n8n's WF-03 fetches
the asset's dependency subgraph via the get_dependency_chain Postgres RPC
(database/migrations/0004_impact_graph.sql) plus every location/event row,
and hands it all in as JSON; this module walks that graph in memory to
answer "what does this asset's failure threaten right now," deterministically.

The recursive graph *fetch* already happened in SQL (one query, one place —
see the migration for why). What happens here is different: interpreting
the returned edges into meaning — which paths still lead to a real,
current-or-upcoming operation, how urgent each one is, how to explain the
chain in plain language. That's business logic, not a second traversal, so
it belongs in the same place the rest of Onward's deterministic rules live.
"""

from __future__ import annotations

from app.schemas.impact import (
    MAX_TRAVERSAL_HOPS,
    AffectedOperation,
    DependencyEdge,
    EventState,
    ImpactLevel,
    ImpactRequest,
    ImpactResult,
    LocationState,
)

_LEVEL_RANK: dict[ImpactLevel, int] = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

# Time-based urgency, in minutes until the operation starts (or already
# underway). Deterministic thresholds, not model-tunable — timing is a
# fact read from `events.starts_at`, not an interpretation (CLAUDE.md "AI
# vs deterministic logic").
_URGENCY_CRITICAL_MINUTES = 15
_URGENCY_HIGH_MINUTES = 60
_URGENCY_MEDIUM_MINUTES = 24 * 60

Node = tuple[str, str]


def _max_level(a: ImpactLevel, b: ImpactLevel) -> ImpactLevel:
    return a if _LEVEL_RANK[a] >= _LEVEL_RANK[b] else b


def _time_urgency(minutes_until_start: int, in_progress: bool) -> ImpactLevel:
    if in_progress or minutes_until_start <= _URGENCY_CRITICAL_MINUTES:
        return "critical"
    if minutes_until_start <= _URGENCY_HIGH_MINUTES:
        return "high"
    if minutes_until_start <= _URGENCY_MEDIUM_MINUTES:
        return "medium"
    return "low"


def _resolve_display_name(
    dependency_type: str,
    dependency_id: str,
    locations_by_id: dict[str, LocationState],
    events_by_id: dict[str, EventState],
) -> str | None:
    # Locations are shown by human name ("Room 3.12"); events by their
    # stable code ("ECON301") — matches the explainability example in the
    # Phase 4 brief and keeps the path readable without over-long event names.
    if dependency_type == "location":
        loc = locations_by_id.get(dependency_id)
        return loc.name if loc else None
    if dependency_type == "event":
        ev = events_by_id.get(dependency_id)
        return ev.code if ev else None
    return None


def _evaluate_event(
    edge: DependencyEdge, event: EventState, now, path_so_far: list[str]
) -> AffectedOperation | None:
    """None means "not currently a real impact" — finished, cancelled, or
    otherwise no longer relevant. Never fabricated; every non-None result
    traces to real fields on a real `events` row."""
    if event.status in ("completed", "cancelled"):
        return None
    if event.ends_at is not None and now > event.ends_at:
        return None

    in_progress = event.status == "in_progress" or event.starts_at <= now
    minutes_until_start = max(0, int((event.starts_at - now).total_seconds() // 60))

    # Urgency tracks real timing only — a structurally "high-criticality"
    # dependency whose next booking is tomorrow must still read as low
    # urgency (Phase 4 brief's own example). The edge's static criticality
    # is preserved in the dependency graph for later phases (e.g. recovery
    # prioritization) but does not floor Phase 4's headline urgency signal.
    level = _time_urgency(minutes_until_start, in_progress)

    path = path_so_far
    if event.attendee_count is not None:
        path = path_so_far + [f"serves {event.attendee_count} attendees"]

    return AffectedOperation(
        id=event.id,
        code=event.code,
        name=event.name,
        starts_at=event.starts_at,
        minutes_until_start=minutes_until_start,
        people_affected=event.attendee_count,
        required_capability=event.required_capability,
        criticality=level,
        dependency_path=path,
    )


def _service_at_risk_text(op: AffectedOperation) -> str:
    if op.required_capability:
        return f"{op.required_capability} for {op.name}"
    return f"operation continuity: {op.name}"


def calculate_impact(req: ImpactRequest) -> ImpactResult:
    locations_by_id = {loc.id: loc for loc in req.locations}
    events_by_id = {ev.id: ev for ev in req.events}

    adjacency: dict[Node, list[DependencyEdge]] = {}
    for edge in req.dependency_edges:
        adjacency.setdefault((edge.source_type, edge.source_id), []).append(edge)

    warnings: list[str] = []
    operations: list[AffectedOperation] = []
    reached_any_edge = False

    start_node: Node = ("asset", req.asset_id)
    start_path = [req.asset_code or req.asset_id]
    frontier: list[tuple[Node, list[str]]] = [(start_node, start_path)]
    visited: set[Node] = {start_node}

    hop = 0
    while frontier and hop < MAX_TRAVERSAL_HOPS:
        hop += 1
        next_frontier: list[tuple[Node, list[str]]] = []
        for node, path in frontier:
            for edge in adjacency.get(node, []):
                reached_any_edge = True

                if edge.dependency_type == "capability":
                    # Leaf fact, not a traversable node — the matching
                    # event already carries its own required_capability
                    # column; nothing further to walk from here.
                    continue

                if edge.dependency_id is None:
                    warnings.append(f"edge missing dependency_id: {edge.relationship}")
                    continue

                target: Node = (edge.dependency_type, edge.dependency_id)
                if target in visited:
                    warnings.append("cyclic_dependency_detected")
                    continue
                visited.add(target)

                display_name = _resolve_display_name(
                    edge.dependency_type, edge.dependency_id, locations_by_id, events_by_id
                )
                if display_name is None:
                    warnings.append(f"missing_referenced_{edge.dependency_type}:{edge.dependency_id}")
                    continue

                new_path = path + [f"{edge.relationship} {display_name}"]

                if edge.dependency_type == "event":
                    op = _evaluate_event(edge, events_by_id[edge.dependency_id], req.now, new_path)
                    if op is not None:
                        operations.append(op)

                next_frontier.append((target, new_path))

        frontier = next_frontier

    if frontier:
        warnings.append("max_traversal_depth_reached")

    if not reached_any_edge:
        return ImpactResult(
            incident_id=req.incident_id,
            asset_id=req.asset_id,
            impact_known=False,
            impact_level="none",
            warnings=warnings,
            reason="no registered dependency for this asset",
        )

    if not operations:
        reason = (
            "dependency chain known but some referenced data was missing or malformed"
            if warnings
            else "dependency chain known but no current or upcoming operation is affected"
        )
        return ImpactResult(
            incident_id=req.incident_id,
            asset_id=req.asset_id,
            impact_known=True,
            impact_level="none",
            warnings=warnings,
            reason=reason,
        )

    operations.sort(key=lambda op: op.minutes_until_start)
    overall_level: ImpactLevel = "none"
    for op in operations:
        overall_level = _max_level(overall_level, op.criticality)

    top = operations[0]
    return ImpactResult(
        incident_id=req.incident_id,
        asset_id=req.asset_id,
        impact_known=True,
        impact_level=overall_level,
        minutes_until_impact=top.minutes_until_start,
        service_at_risk=_service_at_risk_text(top),
        affected_operations=operations,
        dependency_path=top.dependency_path,
        warnings=warnings,
    )
