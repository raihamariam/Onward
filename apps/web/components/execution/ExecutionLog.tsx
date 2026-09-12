"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";
import { ACTION_LABEL, formatClockTime, truncateReference } from "@/lib/onward/formatting";
import type { ActionType } from "@/lib/onward/types";

export function ExecutionLog({ vm }: { vm: OnwardViewModel }) {
  return (
    <div className="rounded-xl border border-panel-border bg-panel p-5">
      <h2 className="text-sm font-semibold text-text-primary">Live Execution Log</h2>

      {!vm.isApproved || vm.executionActions.length === 0 ? (
        <p className="mt-3 text-xs text-text-muted">
          {vm.isApproved ? "Waiting for the first action to complete…" : (
            <>
              No actions yet.
              <br />
              Execution events will appear here after approval.
            </>
          )}
        </p>
      ) : (
        <ul className="mt-3 space-y-2.5">
          {vm.executionActions.map((a) => (
            <li key={a.action_type} className="flex items-center justify-between text-sm">
              <div>
                <p className="font-medium text-text-primary">{ACTION_LABEL[a.action_type as ActionType] ?? a.action_type}</p>
                <p className="text-[10px] text-text-muted">
                  {formatClockTime(a.executed_at)}
                  {a.external_reference && <> · {truncateReference(a.external_reference)}</>}
                </p>
              </div>
              <span className={`text-xs font-semibold ${a.status === "completed" ? "text-status-green" : "text-status-red"}`}>
                {a.status === "completed" ? "Completed" : "Failed"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
