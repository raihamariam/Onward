"use client";

import type { ActionType, ExecutionAction as ExecutionActionData } from "@/lib/onward/types";
import { ACTION_LABEL } from "@/lib/onward/formatting";

const ICONS: Record<ActionType, React.ReactNode> = {
  resource_reservation: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <path d="M4 21V6l8-3 8 3v15" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 21v-6h6v6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  calendar_update: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" strokeLinecap="round" />
    </svg>
  ),
  work_order: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <path d="M14.7 6.3a4 4 0 0 1-5.4 5.4L4 17v3h3l5.3-5.3a4 4 0 0 1 5.4-5.4l-3 3-2-2 3-3Z" strokeLinejoin="round" />
    </svg>
  ),
  slack_notify: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <rect x="9" y="2" width="6" height="8" rx="2" />
      <rect x="9" y="14" width="6" height="8" rx="2" />
      <rect x="2" y="9" width="8" height="6" rx="2" />
      <rect x="14" y="9" width="8" height="6" rx="2" />
    </svg>
  ),
  gmail_notify: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m4 7 8 6 8-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  inventory_decrement: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <rect x="3" y="4" width="18" height="14" rx="2" />
      <path d="M8 21h8" strokeLinecap="round" />
    </svg>
  ),
};

type Phase = "pending" | "processing" | "completed" | "failed";

export function ExecutionAction({
  type,
  phase,
  data,
}: {
  type: ActionType;
  phase: Phase;
  data: ExecutionActionData | null;
}) {
  const toneClasses: Record<Phase, string> = {
    pending: "border-panel-border-strong text-text-muted",
    processing: "border-status-green-border bg-status-green-bg text-status-green onward-pulse",
    completed: "border-status-green-border bg-status-green-bg text-status-green",
    failed: "border-status-red-border bg-status-red-bg text-status-red",
  };

  return (
    <div className={`flex min-w-[150px] flex-1 flex-col gap-2 rounded-lg border p-3 ${toneClasses[phase]}`}>
      <span className="flex h-7 w-7 items-center justify-center rounded-md bg-black/20">{ICONS[type]}</span>
      <p className="text-xs font-semibold text-text-primary">{ACTION_LABEL[type]}</p>
      <p className="flex items-center gap-1.5 text-[11px] font-medium">
        {phase === "pending" && "Pending"}
        {phase === "processing" && (
          <>
            <span className="h-1.5 w-1.5 rounded-full bg-status-green" /> Processing
          </>
        )}
        {phase === "completed" && (
          <>
            <span>✓</span> Completed
          </>
        )}
        {phase === "failed" && (
          <>
            <span>✕</span> Failed
          </>
        )}
      </p>
      {data?.error && phase === "failed" && (
        <p className="truncate text-[10px] text-status-red/80" title={data.error}>
          {data.error}
        </p>
      )}
    </div>
  );
}
