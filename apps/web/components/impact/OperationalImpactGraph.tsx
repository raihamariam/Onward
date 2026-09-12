"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";

function GraphNode({
  icon,
  title,
  subtitle,
  status,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  status: string;
  tone: "red" | "amber" | "green";
}) {
  const toneClasses = {
    red: "border-status-red-border bg-status-red-bg text-status-red",
    amber: "border-status-amber-border bg-status-amber-bg text-status-amber",
    green: "border-status-green-border bg-status-green-bg text-status-green",
  }[tone];

  return (
    <div className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${toneClasses}`}>
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-black/20">{icon}</span>
      <div className="min-w-0 leading-tight">
        <p className="truncate text-sm font-semibold text-text-primary">{title}</p>
        {subtitle && <p className="truncate text-xs text-text-secondary">{subtitle}</p>}
        <p className="mt-0.5 text-[10px] font-bold uppercase tracking-wide">{status}</p>
      </div>
    </div>
  );
}

const iconAsset = (
  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
    <rect x="3" y="4" width="18" height="14" rx="2" />
    <path d="M8 21h8" strokeLinecap="round" />
  </svg>
);
const iconLocation = (
  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
    <path d="M12 22s7-7.58 7-12.5A7 7 0 0 0 5 9.5C5 14.42 12 22 12 22Z" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="12" cy="9.5" r="2.5" />
  </svg>
);
const iconEvent = (
  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
    <path d="M6 3h9l3 3v15H6V3Z" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M9 12h6M9 16h6" strokeLinecap="round" />
  </svg>
);
const iconPeople = (
  <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth={1.75}>
    <circle cx="9" cy="8" r="3" />
    <path d="M2 20c0-3.3 3-6 7-6s7 2.7 7 6" strokeLinecap="round" />
  </svg>
);

export function OperationalImpactGraph({ vm }: { vm: OnwardViewModel }) {
  if (!vm.hasIntelligence) return null;

  if (!vm.hasImpact) {
    return (
      <div className="flex items-center gap-2 text-sm text-text-secondary">
        <span className="h-2 w-2 rounded-full bg-status-green onward-pulse" />
        Tracing dependency graph…
      </div>
    );
  }

  if (!vm.impactKnown) {
    return <p className="text-sm text-text-secondary">No current operation at risk.</p>;
  }

  const op = vm.impact!.affected_operations?.[0];
  if (!op) return <p className="text-sm text-text-secondary">No current operation at risk.</p>;

  // Once the recommended plan's real relocation has genuinely completed,
  // the graph reflects the actual recovered relationship instead of the
  // original at-risk chain -- only ever using real, persisted state
  // (execution_runs.status + the plan's own resource_ref), never assumed.
  if (vm.isCompleted && vm.recommendedPlan?.resource_ref?.name) {
    const newLocation = vm.recommendedPlan.resource_ref.name;
    return (
      <div className="flex flex-col items-stretch gap-1">
        <GraphNode icon={iconAsset} title={vm.asset!.code} subtitle={vm.asset!.name} status="Offline" tone="red" />
        <Connector />
        <GraphNode icon={iconLocation} title={newLocation} status="Active" tone="green" />
        <Connector />
        <GraphNode icon={iconEvent} title={op.name} subtitle={op.type} status="Continuing" tone="green" />
        <Connector />
        <GraphNode icon={iconPeople} title={`${op.people_affected} Students`} status="Protected" tone="green" />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-stretch gap-1">
      <GraphNode icon={iconAsset} title={vm.asset!.code} subtitle={vm.asset!.name} status="Failed" tone="red" />
      <Connector />
      <GraphNode icon={iconLocation} title={vm.asset!.location} status="At risk" tone="amber" />
      <Connector />
      <GraphNode icon={iconEvent} title={op.name} subtitle={op.type} status="At risk" tone="amber" />
      <Connector />
      <GraphNode icon={iconPeople} title={`${op.people_affected} Students`} status="Affected" tone="green" />
    </div>
  );
}

function Connector() {
  return (
    <div className="flex justify-start pl-[18px]">
      <div className="h-3 w-px bg-panel-border-strong" />
    </div>
  );
}
