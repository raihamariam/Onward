"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";
import { formatClockTime, planLabelWithResource } from "@/lib/onward/formatting";

function Row({ label, value, tone }: { label: string; value: string; tone?: "green" | "amber" | "red" }) {
  const toneClass = tone === "green" ? "text-status-green" : tone === "amber" ? "text-status-amber" : tone === "red" ? "text-status-red" : "text-text-primary";
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-text-muted">{label}</span>
      <span className={`font-medium ${toneClass}`}>{value}</span>
    </div>
  );
}

export function SystemTruthPanel({ vm }: { vm: OnwardViewModel }) {
  if (!vm.hasIncident) return null;

  const op = vm.impact?.affected_operations?.[0];
  const approvalTone = !vm.isDecided ? "amber" : vm.isRejected ? "red" : "green";
  const approvalLabel = !vm.isDecided ? "Pending" : vm.isRejected ? "Rejected" : "Approved";

  const executionTone = vm.isCompleted ? "green" : vm.isFailed ? "red" : vm.isPartial ? "amber" : undefined;
  const operationStatus = vm.isCompleted
    ? "Recovered"
    : vm.isPartial
    ? "Partially recovered"
    : vm.isFailed
    ? "Recovery failed"
    : vm.isExecuting
    ? "Coordinating"
    : "—";

  const recommendedLocation = vm.recommendedPlan?.resource_ref?.location_id
    ? vm.candidateLocations.find((l) => l.id === vm.recommendedPlan!.resource_ref!.location_id)
    : null;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-panel-border bg-panel p-5">
        <h2 className="text-sm font-semibold text-text-primary">System Truth</h2>
        <div className="mt-3 space-y-2.5">
          {vm.hasIntelligence && <Row label="AI confidence" value={`${Math.round(vm.intelligence!.confidence * 100)}%`} />}
          {op && <Row label="People affected" value={String(op.people_affected)} />}
          {vm.impact?.minutes_until_impact != null && (
            <Row label="Recovery window" value={`${Math.round(vm.impact.minutes_until_impact)} minutes`} />
          )}
          {vm.recommendedPlan && <Row label="Recommended plan" value={planLabelWithResource(vm.recommendedPlan)} tone="green" />}
          {vm.hasPlans && <Row label="Approval status" value={approvalLabel} tone={approvalTone} />}
          {vm.isApproved && (
            <Row label="Execution progress" value={`${vm.completedActionCount} / ${vm.totalExpectedActionCount}`} tone={executionTone} />
          )}
          {vm.isExecutionTerminal && <Row label="Operation status" value={operationStatus} tone={executionTone} />}
        </div>
      </div>

      <div className="rounded-xl border border-panel-border bg-panel p-5">
        <h2 className="text-sm font-semibold text-text-primary">Related Information</h2>
        <div className="mt-3 space-y-3">
          {op && (
            <div>
              <p className="text-sm font-medium text-text-primary">{op.name}</p>
              {op.starts_at && <p className="text-xs text-text-muted">Starts {formatClockTime(op.starts_at)}</p>}
            </div>
          )}
          {vm.originLocation && (
            <div>
              <p className="text-sm font-medium text-text-primary">{vm.originLocation.name}</p>
              {vm.originLocation.capacity != null && (
                <p className="text-xs text-text-muted">Capacity: {vm.originLocation.capacity}</p>
              )}
            </div>
          )}
          {recommendedLocation && (
            <div>
              <p className="text-sm font-medium text-text-primary">{recommendedLocation.name}</p>
              <p className="text-xs text-text-muted">
                Capacity: {recommendedLocation.capacity ?? "—"} · <span className="capitalize">{recommendedLocation.status}</span>
              </p>
            </div>
          )}
          <div>
            <p className="text-sm font-medium text-text-primary">{vm.asset?.code}</p>
            <p className="text-xs text-text-muted">
              {vm.workOrders.length > 0
                ? vm.workOrders[0].description
                : vm.recommendedPlan
                ? "Work order will be created"
                : "No maintenance action yet"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
