"""Shared contract for incident intelligence — the AI interpretation output.

This is the one place the schema is defined. n8n's WF-02 sends an
InterpretRequest and stores whatever comes back verbatim; nothing downstream
re-derives these fields.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]

# Confidence below this always forces human review, regardless of what the
# model itself decided — the model's own requires_human_review flag is a
# floor, not a ceiling; this is deterministic policy layered on top of a
# probabilistic call, not something we trust the model to self-police.
LOW_CONFIDENCE_THRESHOLD = 0.55


class PriorIncident(BaseModel):
    """One earlier incident for the same asset — trusted context, not RAG."""

    description: str
    reported_at: datetime
    status: str


class AssetContext(BaseModel):
    """Trusted, deterministic facts about the asset — never inferred."""

    code: str
    name: str
    location: str | None = None
    status: str
    prior_incidents: list[PriorIncident] = Field(default_factory=list)


class InterpretRequest(BaseModel):
    incident_id: str
    description: str
    image_base64: str | None = None
    image_media_type: str | None = None
    asset_context: AssetContext


class LikelyFault(BaseModel):
    code: str
    confidence: float = Field(ge=0, le=1)


class ModelOutput(BaseModel):
    """Exactly what a model provider is asked to produce — nothing this
    codebase computes itself (incident_id, which model/provider answered,
    when). Kept separate from IncidentIntelligence so every provider
    implementation validates against the same shape regardless of how it
    talks to its underlying API (see app/interpret/providers/)."""

    incident_type: str
    symptoms: list[str] = Field(default_factory=list)
    visual_observations: list[str] = Field(default_factory=list)
    severity: Severity
    safety_risk: bool
    confidence: float = Field(ge=0, le=1)
    likely_faults: list[LikelyFault] = Field(default_factory=list)
    required_capability: str
    requires_human_review: bool
    review_reason: str | None = None
    evidence_conflict: bool = False


class IncidentIntelligence(ModelOutput):
    """What the AI inferred, plus provenance. Never contains operational
    facts (availability, schedules, inventory, cost) — those don't exist at
    this layer."""

    schema_version: str = "1.0"
    incident_id: str
    model: str
    provider: str
    interpreted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def apply_review_policy(intel: IncidentIntelligence) -> IncidentIntelligence:
    """Deterministic floor on top of the model's own judgment. The model can
    ask for review; it cannot talk itself out of review when these hold."""
    reasons: list[str] = [intel.review_reason] if intel.review_reason else []

    if intel.safety_risk:
        reasons.append("safety risk detected")
    if intel.confidence < LOW_CONFIDENCE_THRESHOLD:
        reasons.append(f"confidence {intel.confidence:.2f} below {LOW_CONFIDENCE_THRESHOLD}")
    if intel.evidence_conflict:
        reasons.append("text and image evidence conflict")
    if intel.incident_type == "unknown" or not intel.symptoms:
        reasons.append("insufficient evidence to classify")

    if reasons:
        intel.requires_human_review = True
        intel.review_reason = "; ".join(dict.fromkeys(reasons))  # dedupe, keep order

    return intel


def fallback_intelligence(incident_id: str, reason: str) -> IncidentIntelligence:
    """Returned when the model call or its output can't be trusted at all —
    never raises past this point, always a valid, safe, review-flagged
    record. This is the "safely rejected" outcome for malformed output or a
    provider failure, not an exception bubbling into n8n."""
    return IncidentIntelligence(
        incident_id=incident_id,
        incident_type="unknown",
        symptoms=[],
        visual_observations=[],
        severity="high",
        safety_risk=False,
        confidence=0.0,
        likely_faults=[],
        required_capability="GENERAL_MAINTENANCE",
        requires_human_review=True,
        review_reason=reason,
        model="none",
        provider="none",
    )
