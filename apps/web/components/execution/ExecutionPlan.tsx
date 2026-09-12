"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";
import type { ActionType } from "@/lib/onward/types";
import { ExecutionAction } from "./ExecutionAction";

export function ExecutionPlan({ vm }: { vm: OnwardViewModel }) {
  if (!vm.recommendedPlan || vm.expectedActionTypes.length === 0) return null;

  const byType = new Map(vm.executionActions.map((a) => [a.action_type, a]));

  return (
    <div className="rounded-xl border border-panel-border bg-panel p-5">
      <h2 className="text-sm font-semibold text-text-primary">
        Execution Plan {!vm.isApproved && <span className="font-normal text-text-muted">(awaiting approval)</span>}
      </h2>
      <p className="mt-0.5 text-xs text-text-muted">
        {vm.isApproved ? "These real actions are being coordinated." : "These actions will be executed after approval."}
      </p>

      <div className="mt-4 flex items-stretch gap-2 overflow-x-auto">
        {vm.expectedActionTypes.map((type, i) => {
          const actionType = type as ActionType;
          const data = byType.get(actionType) ?? null;
          const phase = !vm.isApproved
            ? "pending"
            : data
            ? data.status === "completed"
              ? "completed"
              : "failed"
            : "processing";
          return (
            <div key={type} className="flex items-center gap-2">
              <ExecutionAction type={actionType} phase={phase} data={data} />
              {i < vm.expectedActionTypes.length - 1 && (
                <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 shrink-0 text-text-muted" stroke="currentColor" strokeWidth={2}>
                  <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
