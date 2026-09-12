"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import type { StateResponse } from "@/lib/onward/types";
import { buildViewModel } from "@/lib/onward/view-model";

import { AppSidebar } from "@/components/app-shell/AppSidebar";
import { IncidentHeader } from "@/components/app-shell/IncidentHeader";
import { StageTracker } from "@/components/app-shell/StageTracker";
import { IncidentReportPanel } from "@/components/incident/IncidentReportPanel";
import { IntelligencePanel } from "@/components/incident/IntelligencePanel";
import { OperationalImpactGraph } from "@/components/impact/OperationalImpactGraph";
import { ImpactSummary } from "@/components/impact/ImpactSummary";
import { ImpactCountdown } from "@/components/impact/ImpactCountdown";
import { RecoveryOptions } from "@/components/recovery/RecoveryOptions";
import { RecoveryExplanation } from "@/components/recovery/RecoveryExplanation";
import { ExecutionPlan } from "@/components/execution/ExecutionPlan";
import { ExecutionLog } from "@/components/execution/ExecutionLog";
import { SystemTruthPanel } from "@/components/system/SystemTruthPanel";
import { PresentationModeToggle } from "@/components/presentation/PresentationMode";

const POLL_MS = 1500;

// Once the Command View finds a real incident for the current demo
// session (no ?incident= override in play), it "locks on" to that exact
// incident_id in sessionStorage so it keeps following that same incident
// even if a later, unrelated one gets created -- e.g. a second rehearsal
// submission -- rather than jumping to whatever's newest. The lock is
// scoped to the session it was found under: tests/prepare_demo.py starting
// a NEW session invalidates any old lock automatically (see the
// sessionStartedAt comparison below), so "prepare demo again" always goes
// back to a clean SYSTEM READY, never stuck on a previous rehearsal.
const LOCK_KEY = "onward_locked_incident_id";
const LOCK_SESSION_KEY = "onward_locked_session_started_at";

function CommandViewInner() {
  const searchParams = useSearchParams();
  const incidentOverride = searchParams.get("incident");
  const presentationMode = searchParams.get("present") === "1";
  const [data, setData] = useState<StateResponse | null>(null);
  const lockedIdRef = useRef<string | null>(null);
  const lockedSessionRef = useRef<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      lockedIdRef.current = window.sessionStorage.getItem(LOCK_KEY);
      lockedSessionRef.current = window.sessionStorage.getItem(LOCK_SESSION_KEY);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        let url: string;
        if (incidentOverride) {
          // Explicit override always wins — rehearsal/backup path.
          url = `/api/incident-state?incident=${encodeURIComponent(incidentOverride)}`;
        } else if (lockedIdRef.current) {
          // Already locked onto an incident this session — keep following it.
          url = `/api/incident-state?incident=${encodeURIComponent(lockedIdRef.current)}`;
        } else {
          // No lock yet — watch for the first incident in the current demo session.
          url = "/api/incident-state";
        }

        const res = await fetch(url, { cache: "no-store" });
        const body: StateResponse = await res.json();
        if (cancelled) return;

        if (!incidentOverride) {
          // A newer demo session started (tests/prepare_demo.py ran again)
          // — drop any stale lock and go back to watching for a fresh incident.
          if (body.sessionStartedAt && body.sessionStartedAt !== lockedSessionRef.current && !lockedIdRef.current) {
            lockedSessionRef.current = body.sessionStartedAt;
          } else if (body.sessionStartedAt && lockedSessionRef.current && body.sessionStartedAt !== lockedSessionRef.current) {
            lockedIdRef.current = null;
            lockedSessionRef.current = body.sessionStartedAt;
            window.sessionStorage.removeItem(LOCK_KEY);
            window.sessionStorage.setItem(LOCK_SESSION_KEY, body.sessionStartedAt);
            // Re-poll immediately under the new session instead of showing
            // a stale incident for one more tick.
            poll();
            return;
          }

          if (!lockedIdRef.current && body.incident) {
            lockedIdRef.current = body.incident.id;
            window.sessionStorage.setItem(LOCK_KEY, body.incident.id);
            if (body.sessionStartedAt) {
              window.sessionStorage.setItem(LOCK_SESSION_KEY, body.sessionStartedAt);
            }
          }
        }

        setData(body);
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

  if (!data) {
    return <div className="flex h-screen items-center justify-center bg-background text-text-muted">Loading Onward…</div>;
  }

  const vm = buildViewModel(data);
  const op = vm.impact?.affected_operations?.[0];

  return (
    <div className="flex h-screen overflow-hidden bg-background text-text-primary">
      {!presentationMode && <AppSidebar />}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-[68px] shrink-0 items-center border-b border-panel-border bg-panel">
          <div className="flex-1">
            <IncidentHeader vm={vm} />
          </div>
          <div className="pr-6">
            <PresentationModeToggle active={presentationMode} />
          </div>
        </header>

        <div className="flex h-14 shrink-0 items-center border-b border-panel-border bg-panel px-6">
          <StageTracker vm={vm} compact={presentationMode} />
        </div>

        <main className="flex-1 overflow-y-auto p-6">
          {vm.isCompleted && (
            <div className="mb-6 rounded-xl border border-status-green-border bg-status-green-bg p-5">
              <p className="text-xs font-bold uppercase tracking-wide text-status-green">Continuity Restored</p>
              <p className="mt-1 text-xl font-semibold text-text-primary">
                {op?.name ?? "The operation"} is continuing{vm.recommendedPlan?.resource_ref?.name ? ` at ${vm.recommendedPlan.resource_ref.name}` : ""}.
              </p>
              {op && <p className="mt-1 text-sm text-text-secondary">{op.people_affected} students protected.</p>}
            </div>
          )}
          {vm.isPartial && (
            <div className="mb-6 rounded-xl border border-status-amber-border bg-status-amber-bg p-5">
              <p className="text-xs font-bold uppercase tracking-wide text-status-amber">Recovery partially completed</p>
              <p className="mt-1 text-sm text-text-secondary">Some coordinated actions did not complete — see the execution log below.</p>
            </div>
          )}
          {vm.isFailed && (
            <div className="mb-6 rounded-xl border border-status-red-border bg-status-red-bg p-5">
              <p className="text-xs font-bold uppercase tracking-wide text-status-red">Recovery could not be completed</p>
              <p className="mt-1 text-sm text-text-secondary">See the execution log below for what failed.</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
            <div className="flex flex-col gap-5">
              <IncidentReportPanel vm={vm} />
              <div className="rounded-xl border border-panel-border bg-panel p-5">
                <IntelligencePanel vm={vm} />
              </div>
            </div>

            <div className="flex flex-col gap-5">
              <div className="rounded-xl border border-panel-border bg-panel p-5">
                <h2 className="mb-3 text-sm font-semibold text-text-primary">Operational Impact</h2>
                <OperationalImpactGraph vm={vm} />
              </div>
              <ImpactSummary vm={vm} />
              <ImpactCountdown vm={vm} />
            </div>

            <SystemTruthPanel vm={vm} />
          </div>

          <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[2fr_1fr]">
            <RecoveryOptions vm={vm} />
            <RecoveryExplanation vm={vm} />
          </div>

          {vm.recommendedPlan && vm.isDecided && !vm.isRejected && (
            <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2">
              <ExecutionPlan vm={vm} />
              <ExecutionLog vm={vm} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function CommandView() {
  return (
    <Suspense fallback={null}>
      <CommandViewInner />
    </Suspense>
  );
}
