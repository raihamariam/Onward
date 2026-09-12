"use client";

import { useState } from "react";
import type { OnwardViewModel } from "@/lib/onward/view-model";
import { findConstraint, planLabelWithResource } from "@/lib/onward/formatting";

export function RecoveryExplanation({ vm }: { vm: OnwardViewModel }) {
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRejected, setShowRejected] = useState(false);

  if (!vm.hasPlans || vm.noFeasiblePlan || !vm.recommendedPlan) return null;

  const plan = vm.recommendedPlan;
  const capacityConstraint = findConstraint(plan, "capacity");
  const timeConstraint = findConstraint(plan, "time_window");
  const capabilityConstraint = findConstraint(plan, "capability");
  const availabilityConstraint = findConstraint(plan, "location_status") ?? findConstraint(plan, "technician_status") ?? findConstraint(plan, "inventory_status");
  const candidateLocation = plan.resource_ref?.location_id
    ? vm.candidateLocations.find((l) => l.id === plan.resource_ref!.location_id)
    : null;

  const rows: { label: string; value: string }[] = [];
  if (timeConstraint) rows.push({ label: "Transfer time", value: `${plan.estimated_recovery_minutes} minutes` });
  if (vm.impact?.minutes_until_impact !== null && vm.impact?.minutes_until_impact !== undefined) {
    rows.push({
      label: "Within recovery window",
      value: `${plan.estimated_recovery_minutes} < ${Math.round(vm.impact.minutes_until_impact)} min`,
    });
  }
  if (capacityConstraint) {
    rows.push({
      label: "Capacity",
      value: candidateLocation?.capacity != null ? `${candidateLocation.capacity} / ${vm.impact?.affected_operations?.[0]?.people_affected ?? "—"}` : capacityConstraint.detail,
    });
  }
  if (capabilityConstraint) rows.push({ label: "Capability", value: capabilityConstraint.passed ? "Available" : "Unavailable" });
  if (availabilityConstraint) rows.push({ label: "Availability", value: availabilityConstraint.passed ? "Yes" : "No" });

  async function decide(decision: "approved" | "rejected") {
    setDeciding(true);
    setError(null);
    try {
      const res = await fetch("/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ incident_id: vm.incident!.id, plan_id: plan.id, decision }),
      });
      const body = await res.json();
      if (!res.ok) setError(body.message ?? "The decision could not be recorded.");
    } catch {
      setError("Could not reach Onward.");
    } finally {
      setDeciding(false);
    }
  }

  const rejectedPlans = vm.plans.filter((p) => p.id !== plan.id);

  return (
    <div className="rounded-xl border border-status-green-border bg-panel p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">Why this plan?</h2>
        <span className="rounded-full bg-status-green-bg px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-status-green">
          Recommended
        </span>
      </div>
      <p className="mt-2 text-base font-semibold text-text-primary">{planLabelWithResource(plan)}</p>

      <ul className="mt-3 space-y-2">
        {rows.map((r) => (
          <li key={r.label} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1.5 text-text-secondary">
              <span className="text-status-green">✓</span>
              {r.label}
            </span>
            <span className="font-medium text-text-primary">{r.value}</span>
          </li>
        ))}
      </ul>

      {!vm.isDecided ? (
        <>
          <button
            onClick={() => decide("approved")}
            disabled={deciding}
            className="mt-4 w-full rounded-lg bg-status-green py-2.5 text-sm font-semibold text-panel transition disabled:opacity-50"
          >
            {deciding ? "Recording decision…" : "✓ Approve Recovery"}
          </button>
          <button
            onClick={() => decide("rejected")}
            disabled={deciding}
            className="mt-2 w-full rounded-lg border border-panel-border-strong py-2.5 text-sm font-medium text-text-secondary transition hover:text-text-primary disabled:opacity-50"
          >
            Reject
          </button>
          {error && <p className="mt-2 text-xs text-status-red">{error}</p>}
        </>
      ) : vm.isRejected ? (
        <div className="mt-4 rounded-lg border border-status-red-border bg-status-red-bg p-3 text-center text-sm font-semibold text-status-red">
          Recovery rejected — no consequential actions executed
        </div>
      ) : (
        <div className="mt-4 rounded-lg border border-status-green-border bg-status-green-bg p-3 text-center text-sm font-semibold text-status-green">
          Approved by {vm.approval?.decided_by}
        </div>
      )}

      {rejectedPlans.length > 0 && (
        <button
          onClick={() => setShowRejected(true)}
          className="mt-3 w-full rounded-lg bg-panel-elevated py-2 text-xs font-medium text-text-secondary transition hover:text-text-primary"
        >
          Why not the other options?
        </button>
      )}

      {showRejected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6"
          onClick={() => setShowRejected(false)}
        >
          <div
            className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-xl border border-panel-border-strong bg-panel-elevated p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text-primary">Other options considered</h3>
              <button onClick={() => setShowRejected(false)} className="text-text-muted hover:text-text-primary">
                ✕
              </button>
            </div>
            <div className="mt-3 space-y-4">
              {rejectedPlans.map((p) => (
                <div key={p.id} className="border-t border-panel-border pt-3 first:border-0 first:pt-0">
                  <p className="text-sm font-medium text-text-primary">{planLabelWithResource(p)}</p>
                  <ul className="mt-1.5 space-y-1">
                    {(p.constraints ?? []).map((c) => (
                      <li key={c.name} className="flex items-start gap-2 text-xs">
                        <span className={c.passed ? "text-status-green" : "text-status-red"}>{c.passed ? "✓" : "✕"}</span>
                        <span className="text-text-secondary">
                          <span className="capitalize text-text-primary">{c.name.replace(/_/g, " ")}</span> — {c.detail}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
