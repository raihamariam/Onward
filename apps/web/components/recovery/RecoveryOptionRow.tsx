"use client";

import type { Plan } from "@/lib/onward/types";
import { planLabelWithResource, reasonForPlan, statusLabelForPlan } from "@/lib/onward/formatting";

export function RecoveryOptionRow({ plan, onView }: { plan: Plan; onView: (plan: Plan) => void }) {
  const status = statusLabelForPlan(plan);
  const toneClasses = {
    recommended: "text-status-green",
    feasible: "text-text-secondary",
    rejected: "text-status-red",
  }[status.tone];

  return (
    <tr
      className={`border-b border-panel-border last:border-0 ${
        plan.is_recommended ? "bg-status-green-bg" : ""
      }`}
    >
      <td className="py-2.5 pl-3 text-sm font-medium text-text-primary">
        {planLabelWithResource(plan)}
        {plan.is_recommended && <span className="ml-2 inline-block h-1.5 w-1.5 rounded-full bg-status-green align-middle" />}
      </td>
      <td className="py-2.5 text-sm text-text-secondary">{plan.estimated_recovery_minutes} min</td>
      <td className={`py-2.5 text-sm font-medium ${toneClasses}`}>
        <span className="inline-flex items-center gap-1.5">
          {status.tone === "recommended" ? (
            <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5" stroke="currentColor" strokeWidth={2.5}>
              <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          ) : status.tone === "rejected" ? (
            <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5" stroke="currentColor" strokeWidth={2.5}>
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8v5M12 16h.01" strokeLinecap="round" />
            </svg>
          ) : null}
          {status.label}
        </span>
      </td>
      <td className="py-2.5 text-sm text-text-muted">{reasonForPlan(plan)}</td>
      <td className="py-2.5 pr-3 text-right">
        <button
          onClick={() => onView(plan)}
          className="rounded-md border border-panel-border-strong px-3 py-1 text-xs font-medium text-text-secondary transition hover:border-text-secondary hover:text-text-primary"
        >
          View
        </button>
      </td>
    </tr>
  );
}
