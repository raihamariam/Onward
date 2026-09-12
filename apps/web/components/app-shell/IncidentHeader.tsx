"use client";

import { useEffect, useState } from "react";
import type { OnwardViewModel } from "@/lib/onward/view-model";
import { formatClockTime, formatCountdown } from "@/lib/onward/formatting";

function Chip({ icon, title, subtitle }: { icon: React.ReactNode; title: string; subtitle?: string }) {
  return (
    <div className="flex items-center gap-2 border-l border-panel-border pl-4">
      <span className="text-text-muted">{icon}</span>
      <div className="leading-tight">
        <p className="text-sm font-semibold text-text-primary">{title}</p>
        {subtitle && <p className="text-[11px] text-text-muted">{subtitle}</p>}
      </div>
    </div>
  );
}

const icons = {
  asset: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <rect x="3" y="4" width="18" height="14" rx="2" />
      <path d="M8 21h8" strokeLinecap="round" />
    </svg>
  ),
  location: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <path d="M12 22s7-7.58 7-12.5A7 7 0 0 0 5 9.5C5 14.42 12 22 12 22Z" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="12" cy="9.5" r="2.5" />
    </svg>
  ),
  event: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <path d="M6 3h9l3 3v15H6V3Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12h6M9 16h6" strokeLinecap="round" />
    </svg>
  ),
  people: (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
      <circle cx="9" cy="8" r="3" />
      <path d="M2 20c0-3.3 3-6 7-6s7 2.7 7 6" strokeLinecap="round" />
      <path d="M16 4.5a3 3 0 0 1 0 7M22 20c0-2.8-2-5.1-5-5.8" strokeLinecap="round" />
    </svg>
  ),
};

export function IncidentHeader({ vm }: { vm: OnwardViewModel }) {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    // Deferred (not a direct synchronous setState-in-effect call) so the
    // server-rendered null clock text never mismatches the client's first
    // paint, while still updating a tick after mount and every 30s after.
    const initial = setTimeout(() => setNow(new Date()), 0);
    const id = setInterval(() => setNow(new Date()), 30_000);
    return () => {
      clearTimeout(initial);
      clearInterval(id);
    };
  }, []);

  const op = vm.impact?.affected_operations?.[0];
  const shortId = vm.incident ? `INC-${vm.incident.id.slice(0, 4).toUpperCase()}` : null;

  return (
    <header className="flex h-[68px] shrink-0 items-center justify-between border-b border-panel-border bg-panel px-6">
      <div className="flex items-center gap-4">
        {vm.hasIncident ? (
          <>
            <div className="flex items-center gap-2 pr-4">
              <span className="h-2 w-2 rounded-full bg-status-red onward-pulse" />
              <div className="leading-tight">
                <p className="text-xs font-bold uppercase tracking-wide text-status-red">Live Incident</p>
                <p className="text-[11px] text-text-muted">
                  {shortId} · Reported {formatClockTime(vm.incident!.reported_at)}
                </p>
              </div>
            </div>
            <Chip icon={icons.asset} title={vm.asset?.code ?? "—"} subtitle={vm.asset?.name} />
            <Chip icon={icons.location} title={vm.asset?.location ?? "—"} />
            {op && <Chip icon={icons.event} title={op.name} subtitle={op.type} />}
            {op && <Chip icon={icons.people} title={String(op.people_affected)} subtitle="Students affected" />}
          </>
        ) : (
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-status-green" />
            <div className="leading-tight">
              <p className="text-xs font-bold uppercase tracking-wide text-status-green">System Ready</p>
              <p className="text-[11px] text-text-muted">Monitoring campus operations</p>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-5">
        {vm.hasIncident && vm.impactKnown && (
          <div className="text-right leading-none">
            <p className="font-mono text-2xl font-bold text-status-red">
              {formatCountdown(vm.impact?.minutes_until_impact ?? null)}
            </p>
            <p className="mt-1 text-[10px] font-semibold tracking-wide text-status-red/80">UNTIL IMPACT</p>
          </div>
        )}
        {now && (
          <div className="text-right leading-tight text-text-muted">
            <p className="text-xs">{now.toLocaleDateString([], { weekday: "short", day: "2-digit", month: "short" })}</p>
            <p className="text-xs">{now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</p>
          </div>
        )}
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-panel-elevated text-xs font-semibold text-text-secondary">
          TU
        </div>
      </div>
    </header>
  );
}
