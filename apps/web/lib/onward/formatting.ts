import type { ActionType, Constraint, Plan } from "./types";

export const PLAN_LABEL: Record<string, string> = {
  repair_via_technician: "Repair",
  replace_asset: "Replace projector",
  relocate_operation: "Relocate",
};

export const ACTION_LABEL: Record<ActionType, string> = {
  resource_reservation: "Reserve room",
  calendar_update: "Update Calendar",
  work_order: "Create Work Order",
  slack_notify: "Notify Operations",
  gmail_notify: "Notify Lecturer & Students",
  inventory_decrement: "Allocate replacement unit",
};

export const FAILURE_LABEL: Record<string, string> = {
  capacity: "Capacity too small",
  time_window: "Exceeds recovery window",
  location_status: "Location unavailable",
  technician_status: "Technician unavailable",
  inventory_status: "Out of stock",
  inventory_quantity: "Out of stock",
  capability: "Capability mismatch",
};

export function primaryFailedConstraint(p: Plan): Constraint | null {
  return (p.constraints ?? []).find((c) => !c.passed) ?? null;
}

export function findConstraint(p: Plan, name: string): Constraint | null {
  return (p.constraints ?? []).find((c) => c.name === name) ?? null;
}

export function planLabelWithResource(p: Plan): string {
  const base = PLAN_LABEL[p.plan_type] ?? p.plan_type;
  const resourceName = p.resource_ref?.name;
  if (!resourceName) return base;
  if (p.plan_type === "relocate_operation") return resourceName; // "Room 2.08"
  return `${base} (${resourceName})`; // "Repair (Alex Rivera)"
}

export function statusLabelForPlan(p: Plan): { label: string; tone: "recommended" | "feasible" | "rejected" } {
  if (p.is_recommended) return { label: "Recommended", tone: "recommended" };
  if (p.feasible) return { label: "Feasible", tone: "feasible" };
  return { label: "Rejected", tone: "rejected" };
}

export function reasonForPlan(p: Plan): string {
  const failed = primaryFailedConstraint(p);
  if (failed) return failed.detail;
  if (p.is_recommended) return "All constraints pass";
  return p.reason ?? "";
}

export function formatClockTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function formatCountdown(minutes: number | null): string {
  if (minutes === null || minutes === undefined) return "—:—";
  const clamped = Math.max(0, Math.round(minutes));
  const mm = Math.floor(clamped / 60);
  const ss = clamped % 60;
  if (mm > 0) return `${mm}:${String(ss).padStart(2, "0")}`;
  return `${clamped}:00`;
}

export function truncateReference(ref: string | null): string {
  if (!ref) return "—";
  if (ref.length <= 12) return ref;
  return `${ref.slice(0, 10)}…`;
}

export function relativeTimeFromNow(iso: string): string {
  const d = new Date(iso);
  const diffMs = Date.now() - d.getTime();
  const diffSec = Math.round(diffMs / 1000);
  if (diffSec < 5) return "just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.round(diffSec / 60);
  return `${diffMin}m ago`;
}
