"use client";

import { useState } from "react";
import type { OnwardViewModel } from "@/lib/onward/view-model";
import type { Plan } from "@/lib/onward/types";
import { RecoveryOptionRow } from "./RecoveryOptionRow";
import { planLabelWithResource } from "@/lib/onward/formatting";

const CHECKING = [
  "Technician availability",
  "Replacement inventory",
  "Alternate locations",
  "Capacity",
  "Capabilities",
  "Recovery window",
];

export function RecoveryOptions({ vm }: { vm: OnwardViewModel }) {
  const [viewing, setViewing] = useState<Plan | null>(null);

  if (!vm.hasImpact || !vm.impactKnown) return null;

  return (
    <div className="rounded-xl border border-panel-border bg-panel p-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">Recovery Options</h2>
          <p className="text-xs text-text-muted">Evaluating possible ways to maintain operation</p>
        </div>
        {vm.hasPlans && (
          <div className="flex items-center gap-1.5 rounded-md border border-panel-border-strong px-2.5 py-1 text-xs text-text-secondary">
            Sort by: Fastest feasible
            <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5" stroke="currentColor" strokeWidth={2}>
              <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        )}
      </div>

      {!vm.hasPlans ? (
        <div className="mt-4 rounded-lg border border-panel-border-strong bg-panel-elevated p-5">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-status-green onward-pulse" />
            <p className="text-sm font-semibold text-text-primary">Evaluating recovery options</p>
          </div>
          <p className="mt-1 mb-3 text-xs text-text-muted">Checking real resource state, not assumptions.</p>
          <ul className="grid grid-cols-2 gap-x-6 gap-y-1.5">
            {CHECKING.map((c) => (
              <li key={c} className="flex items-center gap-2 text-xs text-text-secondary">
                <span className="h-1 w-1 rounded-full bg-text-muted" />
                {c}
              </li>
            ))}
          </ul>
        </div>
      ) : vm.noFeasiblePlan ? (
        <div className="mt-4 rounded-lg border border-status-red-border bg-status-red-bg p-5 text-center">
          <p className="text-sm font-semibold text-status-red">No feasible recovery found</p>
          <p className="mt-1 text-xs text-text-secondary">Every candidate plan failed at least one hard constraint.</p>
        </div>
      ) : (
        <table className="mt-3 w-full border-collapse">
          <thead>
            <tr className="border-b border-panel-border text-left text-[11px] uppercase tracking-wide text-text-muted">
              <th className="pb-2 pl-3 font-medium">Option</th>
              <th className="pb-2 font-medium">Time</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 font-medium">Constraint / Reason</th>
              <th className="pb-2 pr-3" />
            </tr>
          </thead>
          <tbody>
            {vm.plans.map((p) => (
              <RecoveryOptionRow key={p.id} plan={p} onView={setViewing} />
            ))}
          </tbody>
        </table>
      )}

      {viewing && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6"
          onClick={() => setViewing(null)}
        >
          <div
            className="max-h-[80vh] w-full max-w-md overflow-y-auto rounded-xl border border-panel-border-strong bg-panel-elevated p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text-primary">{planLabelWithResource(viewing)}</h3>
              <button onClick={() => setViewing(null)} className="text-text-muted hover:text-text-primary">
                ✕
              </button>
            </div>
            <ul className="mt-3 space-y-2">
              {(viewing.constraints ?? []).map((c) => (
                <li key={c.name} className="flex items-start gap-2 text-sm">
                  <span className={c.passed ? "text-status-green" : "text-status-red"}>{c.passed ? "✓" : "✕"}</span>
                  <span className="text-text-secondary">
                    <span className="capitalize text-text-primary">{c.name.replace(/_/g, " ")}</span> — {c.detail}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
