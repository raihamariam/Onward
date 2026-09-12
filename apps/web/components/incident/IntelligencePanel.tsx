"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";

export function IntelligencePanel({ vm }: { vm: OnwardViewModel }) {
  if (!vm.hasIncident) return null;

  if (!vm.hasIntelligence) {
    return (
      <div className="mt-4 border-t border-panel-border pt-4">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-status-green onward-pulse" />
          <p className="text-sm font-semibold text-text-primary">Analysing incident…</p>
        </div>
        <p className="mt-1 text-xs text-text-muted">Groq is interpreting the report against asset context.</p>
      </div>
    );
  }

  const intel = vm.intelligence!;
  const isFallback = intel.provider === "none" || intel.confidence === 0;

  return (
    <div className="mt-4 border-t border-panel-border pt-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">AI Interpretation</h3>
        {isFallback ? (
          <span className="rounded-full bg-status-amber-bg px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-status-amber">
            Fallback classification
          </span>
        ) : (
          <span className="rounded-full bg-status-green-bg px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-status-green">
            Confirmed
          </span>
        )}
      </div>

      <dl className="mt-3 space-y-2 text-sm">
        <Row label="Incident type" value={intel.incident_type.replace(/_/g, " ")} capitalize />
        <Row label="Severity" value={intel.severity} valueClassName="text-status-amber capitalize" />
        <Row label="Required capability" value={intel.required_capability} />
        <Row label="Confidence" value={`${Math.round(intel.confidence * 100)}%`} />
        <Row label="Human review" value={intel.requires_human_review ? "Required" : "Not required"} />
        <Row label="Model" value={isFallback ? "None (fallback)" : `${intel.provider} / ${intel.model}`} />
      </dl>
      {intel.review_reason && isFallback && (
        <p className="mt-2 text-[11px] text-text-muted">{intel.review_reason}</p>
      )}
    </div>
  );
}

function Row({
  label,
  value,
  capitalize,
  valueClassName,
}: {
  label: string;
  value: string;
  capitalize?: boolean;
  valueClassName?: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-text-muted">{label}</dt>
      <dd className={`font-medium text-text-primary ${capitalize ? "capitalize" : ""} ${valueClassName ?? ""}`}>
        {value}
      </dd>
    </div>
  );
}
