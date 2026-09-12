"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";
import { computeStage, type StageStatus } from "@/lib/onward/stage";

const STAGES: { label: string; sublabel: string }[] = [
  { label: "Incident", sublabel: "Received" },
  { label: "Understand", sublabel: "AI analysis" },
  { label: "Impact", sublabel: "Dependencies" },
  { label: "Recover", sublabel: "Find options" },
  { label: "Approve", sublabel: "Human decision" },
  { label: "Execute", sublabel: "Coordinate" },
  { label: "Completed", sublabel: "Continuity restored" },
];

function circleClasses(status: StageStatus): string {
  switch (status) {
    case "completed":
      return "border-status-green bg-status-green text-panel";
    case "active":
      return "border-status-green text-status-green onward-pulse";
    case "awaiting":
      return "border-status-amber text-status-amber onward-pulse-amber";
    case "rejected":
      return "border-status-red bg-status-red/20 text-status-red";
    case "partial":
      return "border-status-amber bg-status-amber/20 text-status-amber";
    case "failed":
      return "border-status-red bg-status-red/20 text-status-red";
    default:
      return "border-panel-border-strong text-text-muted";
  }
}

function labelClasses(status: StageStatus): string {
  if (status === "pending") return "text-text-muted";
  if (status === "rejected" || status === "failed") return "text-status-red";
  if (status === "partial") return "text-status-amber";
  if (status === "awaiting") return "text-status-amber";
  return "text-text-primary";
}

function connectorClasses(leftStatus: StageStatus): string {
  if (leftStatus === "completed") return "bg-status-green";
  if (leftStatus === "active" || leftStatus === "awaiting") return "bg-gradient-to-r from-status-green/60 to-panel-border-strong";
  return "bg-panel-border-strong";
}

export function StageTracker({ vm, compact = false }: { vm: OnwardViewModel; compact?: boolean }) {
  const { statuses } = computeStage(vm);

  return (
    <div className="flex flex-1 items-center gap-1 overflow-x-auto">
      {STAGES.map((stage, i) => {
        const status = statuses[i];
        const isLast = i === STAGES.length - 1;
        return (
          <div key={stage.label} className="flex items-center">
            <div className="flex items-center gap-2.5">
              <div
                className={`flex ${compact ? "h-8 w-8 text-xs" : "h-9 w-9 text-sm"} shrink-0 items-center justify-center rounded-full border-2 font-semibold transition-colors duration-300 ${circleClasses(status)}`}
              >
                {status === "completed" ? (
                  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={3}>
                    <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : status === "rejected" || status === "failed" ? (
                  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={3}>
                    <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              {!compact && (
                <div className="hidden leading-tight xl:block">
                  <p className={`text-sm font-semibold ${labelClasses(status)}`}>{stage.label}</p>
                  <p className="text-[11px] text-text-muted">
                    {status === "awaiting" ? "Awaiting decision" : status === "rejected" ? "Rejected" : status === "partial" ? "Partial" : status === "failed" ? "Failed" : stage.sublabel}
                  </p>
                </div>
              )}
            </div>
            {!isLast && <div className={`mx-2 h-px w-6 shrink-0 xl:w-10 ${connectorClasses(status)}`} />}
          </div>
        );
      })}
    </div>
  );
}
