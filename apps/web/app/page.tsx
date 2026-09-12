"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

type Asset = { id: string; code: string; name: string; location: string };
type Incident = { id: string; asset_id: string; description: string; reported_at: string };
type Intelligence = {
  incident_type: string;
  severity: string;
  required_capability: string;
  confidence: number;
  requires_human_review: boolean;
};
type Impact = {
  minutes_until_impact: number | null;
  service_at_risk: string | null;
  affected_operations: { name: string; people_affected: number }[] | null;
  dependency_path: string[] | null;
};
type Plan = {
  id: string;
  plan_type: string;
  feasible: boolean;
  is_recommended: boolean;
  estimated_recovery_minutes: number;
  resource_ref: Record<string, string> | null;
  constraints: { name: string; passed: boolean; detail: string }[] | null;
  reason: string | null;
};
type Approval = { id: string; decision: "approved" | "rejected" };
type ExecutionRun = { status: "executing" | "completed" | "partially_completed" | "failed" };
type ExecutionAction = { action_type: string; status: "completed" | "failed" };
type WorkOrder = { status: string; description: string };

type StateResponse = {
  incident: Incident | null;
  asset: Asset | null;
  intelligence: Intelligence | null;
  impact: Impact | null;
  plans: Plan[];
  approval: Approval | null;
  executionRun: ExecutionRun | null;
  executionActions: ExecutionAction[];
  workOrders: WorkOrder[];
  reservations: unknown[];
};

const POLL_MS = 1500;

const PLAN_LABEL: Record<string, string> = {
  repair_via_technician: "Repair in place",
  replace_asset: "Replace asset",
  relocate_operation: "Relocate operation",
};

const ACTION_LABEL: Record<string, string> = {
  resource_reservation: "Reserve new location",
  calendar_update: "Update Calendar",
  work_order: "Open maintenance work order",
  slack_notify: "Notify operations",
  gmail_notify: "Notify lecturer / student",
  inventory_decrement: "Allocate replacement unit",
};

const EXPECTED_ACTIONS_BY_PLAN: Record<string, string[]> = {
  repair_via_technician: ["work_order", "slack_notify"],
  replace_asset: ["work_order", "slack_notify", "inventory_decrement"],
  relocate_operation: ["work_order", "slack_notify", "resource_reservation", "calendar_update", "gmail_notify"],
};

function Rail({ step }: { step: number }) {
  const labels = ["REPORT", "UNDERSTAND", "IMPACT", "RECOVER", "APPROVE", "EXECUTE"];
  return (
    <div className="flex items-center gap-3 text-[11px] font-medium tracking-[0.15em] text-neutral-600">
      {labels.map((label, i) => (
        <div key={label} className="flex items-center gap-3">
          <span className={i <= step ? "text-neutral-200" : "text-neutral-700"}>{label}</span>
          <span
            className={`h-1.5 w-1.5 rounded-full ${i <= step ? "bg-emerald-400" : "bg-neutral-800"}`}
          />
        </div>
      ))}
    </div>
  );
}

function Shell({ step, children }: { step: number; children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen flex-col bg-neutral-950 px-10 py-8 text-neutral-100 lg:px-16 lg:py-10">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-neutral-500">Onward</p>
        <Rail step={step} />
      </div>
      <div className="flex flex-1 flex-col items-center justify-center">{children}</div>
    </main>
  );
}

function CommandViewInner() {
  const searchParams = useSearchParams();
  const incidentOverride = searchParams.get("incident");
  const [data, setData] = useState<StateResponse | null>(null);
  const [deciding, setDeciding] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const url = incidentOverride
          ? `/api/incident-state?incident=${encodeURIComponent(incidentOverride)}`
          : "/api/incident-state";
        const res = await fetch(url, { cache: "no-store" });
        const body: StateResponse = await res.json();
        if (!cancelled) setData(body);
      } catch {
        // transient network hiccup — next poll tries again
      }
    }
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [incidentOverride]);

  async function decide(decision: "approved" | "rejected", planId: string, incidentId: string) {
    setDeciding(true);
    setDecisionError(null);
    try {
      const res = await fetch("/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ incident_id: incidentId, plan_id: planId, decision }),
      });
      const body = await res.json();
      if (!res.ok) {
        setDecisionError(body.message ?? "The decision could not be recorded.");
      }
    } catch {
      setDecisionError("Could not reach Onward.");
    } finally {
      setDeciding(false);
    }
  }

  // STATE 1 — ready
  if (!data || !data.incident) {
    return (
      <Shell step={0}>
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-neutral-600">System ready</p>
        <p className="mt-4 text-3xl text-neutral-400">Waiting for incident…</p>
      </Shell>
    );
  }

  const { incident, asset, intelligence, impact, plans, approval, executionRun, executionActions, workOrders } = data;

  // STATE 2 — incident received
  if (!intelligence) {
    return (
      <Shell step={1}>
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-emerald-400">Incident received</p>
        <h1 className="mt-4 text-5xl font-semibold">{asset?.code}</h1>
        <p className="mt-1 text-2xl text-neutral-400">{asset?.name}</p>
        <p className="text-lg text-neutral-500">{asset?.location}</p>
        <p className="mt-8 max-w-xl text-center text-2xl italic text-neutral-300">“{incident.description}”</p>
      </Shell>
    );
  }

  // STATE 3 — AI understanding
  if (!impact) {
    return (
      <Shell step={2}>
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-emerald-400">Incident analysed</p>
        <h1 className="mt-4 text-4xl font-semibold capitalize">
          {intelligence.incident_type.replace(/_/g, " ").toLowerCase()}
        </h1>
        <div className="mt-10 grid grid-cols-3 gap-10 text-center">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-neutral-500">Severity</p>
            <p className="mt-2 text-2xl font-semibold text-orange-400">{intelligence.severity}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-neutral-500">Required capability</p>
            <p className="mt-2 text-2xl font-semibold">{intelligence.required_capability}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-neutral-500">Confidence</p>
            <p className="mt-2 text-2xl font-semibold">{Math.round(intelligence.confidence * 100)}%</p>
          </div>
        </div>
        {intelligence.requires_human_review && (
          <p className="mt-8 rounded-full border border-amber-500/40 bg-amber-500/10 px-4 py-1.5 text-sm text-amber-300">
            Flagged for human review
          </p>
        )}
      </Shell>
    );
  }

  const op = impact.affected_operations?.[0];

  // STATE 4 — impact
  if (plans.length === 0) {
    return (
      <Shell step={3}>
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-emerald-400">
          What this failure threatens
        </p>
        <div className="mt-8 flex flex-col items-center gap-2 text-2xl">
          <span className="font-mono text-3xl font-semibold">{asset?.code}</span>
          <span className="text-neutral-600">↓</span>
          <span className="text-neutral-300">{asset?.location}</span>
          <span className="text-neutral-600">↓</span>
          <span className="text-neutral-300">{op?.name ?? impact.service_at_risk}</span>
          {op && (
            <>
              <span className="text-neutral-600">↓</span>
              <span className="text-4xl font-semibold text-white">{op.people_affected} people</span>
            </>
          )}
        </div>
        {impact.minutes_until_impact !== null && (
          <p className="mt-10 text-lg font-semibold uppercase tracking-[0.2em] text-red-400">
            {impact.minutes_until_impact} minutes until impact
          </p>
        )}
      </Shell>
    );
  }

  const recommended = plans.find((p) => p.is_recommended) ?? null;

  // STATE 5/6 — recovery options + approval, or rejected
  if (!approval) {
    return (
      <Shell step={4}>
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-emerald-400">Recovery options</p>
        <div className="mt-8 grid w-full max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
          {plans.map((p) => (
            <div
              key={p.id}
              className={`rounded-2xl border p-5 text-center ${
                p.is_recommended
                  ? "border-emerald-500/60 bg-emerald-500/10"
                  : "border-neutral-800 bg-neutral-900/50"
              }`}
            >
              <p className="text-sm font-semibold uppercase tracking-wide text-neutral-300">
                {PLAN_LABEL[p.plan_type] ?? p.plan_type}
              </p>
              {p.resource_ref?.name && (
                <p className="mt-1 text-neutral-400">{p.resource_ref.name}</p>
              )}
              <p className="mt-3 text-3xl font-bold">{p.estimated_recovery_minutes} min</p>
              <p
                className={`mt-2 text-xs font-semibold uppercase tracking-wide ${
                  p.is_recommended ? "text-emerald-400" : p.feasible ? "text-neutral-400" : "text-red-400"
                }`}
              >
                {p.is_recommended ? "Recommended" : p.feasible ? "Feasible" : "Too slow"}
              </p>
            </div>
          ))}
        </div>

        {recommended && (
          <div className="mt-10 flex flex-col items-center gap-5">
            <p className="text-lg text-neutral-300">
              Approve moving <span className="font-semibold text-white">{op?.name ?? "the operation"}</span> to{" "}
              <span className="font-semibold text-white">{recommended.resource_ref?.name}</span>?
            </p>
            <div className="flex gap-4">
              <button
                disabled={deciding}
                onClick={() => decide("approved", recommended.id, incident.id)}
                className="rounded-2xl bg-emerald-500 px-8 py-4 text-lg font-semibold text-neutral-950 transition disabled:opacity-40"
              >
                Approve Recovery
              </button>
              <button
                disabled={deciding}
                onClick={() => decide("rejected", recommended.id, incident.id)}
                className="rounded-2xl border border-neutral-700 px-8 py-4 text-lg font-semibold text-neutral-300 transition disabled:opacity-40"
              >
                Reject
              </button>
            </div>
            {decisionError && <p className="text-sm text-red-400">{decisionError}</p>}
          </div>
        )}
      </Shell>
    );
  }

  // Rejected
  if (approval.decision === "rejected") {
    return (
      <Shell step={4}>
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-red-400">Recovery rejected</p>
        <p className="mt-6 max-w-md text-center text-xl text-neutral-300">
          No consequential recovery actions executed.
        </p>
        <div className="mt-8 space-y-2 text-center text-neutral-500">
          <p>Calendar unchanged</p>
          <p>Room not reserved</p>
          <p>Notifications not sent</p>
          <p>Decision recorded</p>
        </div>
      </Shell>
    );
  }

  const expected = recommended ? EXPECTED_ACTIONS_BY_PLAN[recommended.plan_type] ?? [] : [];
  const doneTypes = new Set(executionActions.filter((a) => a.status === "completed").map((a) => a.action_type));
  const failedTypes = new Set(executionActions.filter((a) => a.status === "failed").map((a) => a.action_type));

  // STATE 7 — executing
  if (!executionRun || executionRun.status === "executing") {
    return (
      <Shell step={5}>
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-emerald-400">Coordinating recovery</p>
        <div className="mt-8 w-full max-w-md space-y-4">
          {expected.map((type) => (
            <div key={type} className="flex items-center justify-between text-lg">
              <span className="text-neutral-300">{ACTION_LABEL[type] ?? type}</span>
              <span>
                {doneTypes.has(type) ? (
                  <span className="text-emerald-400">✓</span>
                ) : failedTypes.has(type) ? (
                  <span className="text-red-400">✕</span>
                ) : (
                  <span className="text-neutral-600">…</span>
                )}
              </span>
            </div>
          ))}
        </div>
      </Shell>
    );
  }

  const workOrder = workOrders[0];

  // STATE 8 — final
  return (
    <Shell step={5}>
      {executionRun.status === "partially_completed" && (
        <p className="mb-4 rounded-full border border-amber-500/40 bg-amber-500/10 px-4 py-1.5 text-sm text-amber-300">
          Recovery partially completed
        </p>
      )}
      {executionRun.status === "failed" ? (
        <p className="text-2xl font-semibold text-red-400">Recovery could not be completed</p>
      ) : (
        <>
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-emerald-400">Operation recovered</p>
          <h1 className="mt-4 text-4xl font-bold">{op?.name ?? "Operation"}</h1>
          <p className="mt-1 text-2xl text-neutral-300">{recommended?.resource_ref?.name}</p>
          {op && (
            <p className="mt-2 text-lg text-neutral-500">{op.people_affected} students protected</p>
          )}
          <p className="mt-1 text-lg text-neutral-500">
            Recovery: {recommended?.estimated_recovery_minutes} minutes
          </p>
        </>
      )}

      {workOrder && (
        <div className="mt-10 rounded-2xl border border-neutral-800 bg-neutral-900/50 px-6 py-4 text-center">
          <p className="font-mono text-lg font-semibold">{asset?.code}</p>
          <p className="text-sm uppercase tracking-wide text-amber-400">Still offline</p>
          <p className="mt-1 text-sm text-neutral-500">Maintenance work order: {workOrder.status.toUpperCase()}</p>
        </div>
      )}
    </Shell>
  );
}

export default function CommandView() {
  return (
    <Suspense fallback={null}>
      <CommandViewInner />
    </Suspense>
  );
}
