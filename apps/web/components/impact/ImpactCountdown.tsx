"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";
import { formatClockTime, formatCountdown } from "@/lib/onward/formatting";

export function ImpactCountdown({ vm }: { vm: OnwardViewModel }) {
  if (!vm.hasImpact) return null;

  const op = vm.impact!.affected_operations?.[0];
  const minutes = vm.impact!.minutes_until_impact;
  const known = vm.impactKnown && minutes !== null;

  return (
    <div className="rounded-lg border border-status-red-border bg-status-red-bg p-4 text-center">
      {known ? (
        <>
          <p className="font-mono text-4xl font-bold text-status-red">{formatCountdown(minutes)}</p>
          <p className="mt-1 text-[11px] font-bold uppercase tracking-wide text-status-red">Until impact</p>
          {op?.starts_at && (
            <p className="mt-2 text-[11px] text-text-secondary">Starts at {formatClockTime(op.starts_at)}</p>
          )}
        </>
      ) : (
        <>
          <p className="text-2xl font-bold text-text-secondary">—:—</p>
          <p className="mt-1 text-[11px] font-bold uppercase tracking-wide text-text-muted">Window unknown</p>
        </>
      )}
    </div>
  );
}
