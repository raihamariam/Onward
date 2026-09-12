"use client";

import type { OnwardViewModel } from "@/lib/onward/view-model";

export function ImpactSummary({ vm }: { vm: OnwardViewModel }) {
  if (!vm.hasImpact || !vm.impactKnown) return null;

  const op = vm.impact!.affected_operations?.[0];
  const criticalOps = vm.impact!.affected_operations?.length ?? 0;

  const rows: { value: string | number; label: string }[] = [
    { value: 1, label: "Asset affected" },
    { value: 1, label: "Location affected" },
    { value: criticalOps, label: criticalOps === 1 ? "Critical operation" : "Critical operations" },
  ];
  if (op) rows.push({ value: op.people_affected, label: "People affected" });

  return (
    <div className="rounded-lg border border-panel-border-strong bg-panel-elevated p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Impact Summary</p>
      <div className="mt-3 space-y-2">
        {rows.map((r) => (
          <div key={r.label} className="flex items-baseline gap-2">
            <span className="text-lg font-bold text-text-primary">{r.value}</span>
            <span className="text-xs text-text-secondary">{r.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
