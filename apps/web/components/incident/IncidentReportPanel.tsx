"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";
import { formatClockTime } from "@/lib/onward/formatting";

export function IncidentReportPanel({ vm }: { vm: OnwardViewModel }) {
  const incident = vm.incident;

  return (
    <div className="rounded-xl border border-panel-border bg-panel p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">Incident Report</h2>
      </div>

      {!incident ? (
        <p className="mt-4 text-sm text-text-muted">No active incident.</p>
      ) : (
        <>
          <div className="mt-3 rounded-lg border border-panel-border-strong bg-panel-elevated p-4">
            <p className="text-sm italic text-text-primary">&ldquo;{incident.description}&rdquo;</p>
            <p className="mt-2 text-[11px] text-text-muted">
              Reported via {incident.source === "qr" ? "QR" : incident.source} · {formatClockTime(incident.reported_at)}
            </p>
          </div>

          <div className="mt-4 space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] uppercase tracking-wide text-text-muted">Asset</p>
                <p className="mt-1 text-sm font-medium text-text-primary">{vm.asset?.code}</p>
                <p className="text-xs text-text-secondary">{vm.asset?.name}</p>
              </div>
              <div className="text-right">
                <p className="text-[11px] uppercase tracking-wide text-text-muted">Location</p>
                <p className="mt-1 text-sm font-medium text-text-primary">{vm.asset?.location}</p>
              </div>
            </div>

            {incident.media_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={incident.media_url}
                alt="Incident evidence"
                className="h-28 w-full rounded-lg border border-panel-border-strong object-cover"
              />
            ) : (
              <div className="flex h-20 items-center justify-center rounded-lg border border-dashed border-panel-border-strong text-text-muted">
                <svg viewBox="0 0 24 24" fill="none" className="h-7 w-7" stroke="currentColor" strokeWidth={1.5}>
                  <rect x="3" y="4" width="18" height="14" rx="2" />
                  <path d="M8 21h8" strokeLinecap="round" />
                </svg>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
