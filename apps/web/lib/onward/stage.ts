import type { OnwardViewModel } from "./view-model";

export type StageStatus =
  | "pending" // not reached yet, muted
  | "active" // currently processing, pulses
  | "completed" // done, solid green
  | "awaiting" // stage 5 only: waiting on a human, amber attention state
  | "rejected" // stage 5 only: human rejected, terminal
  | "partial" // stage 6 only: execution partially completed
  | "failed"; // stage 6 only: execution failed

export type StageState = {
  /** 0 = SYSTEM READY (no incident yet), otherwise 1-7 */
  current: number;
  statuses: [StageStatus, StageStatus, StageStatus, StageStatus, StageStatus, StageStatus, StageStatus];
};

/**
 * The one place that maps real persisted state to the 7-stage tracker.
 * Every component that needs to know "what stage are we in" imports this
 * instead of re-deriving its own notion of progress.
 */
export function computeStage(vm: OnwardViewModel): StageState {
  const s: StageStatus[] = ["pending", "pending", "pending", "pending", "pending", "pending", "pending"];

  if (!vm.hasIncident) {
    return { current: 0, statuses: s as StageState["statuses"] };
  }

  // Stage 1 — Incident: complete the instant the incident row exists.
  s[0] = "completed";

  // Stage 2 — Understand: active until intelligence lands.
  if (!vm.hasIntelligence) {
    s[1] = "active";
    return { current: 2, statuses: s as StageState["statuses"] };
  }
  s[1] = "completed";

  // Stage 3 — Impact
  if (!vm.hasImpact) {
    s[2] = "active";
    return { current: 3, statuses: s as StageState["statuses"] };
  }
  s[2] = "completed";

  // Stage 4 — Recover: only meaningful if there's an operation actually at
  // risk. If the deterministic engine found no impact, there is nothing to
  // recover from -- that is an honest terminal state, not "still loading".
  if (!vm.impactKnown) {
    return { current: 3, statuses: s as StageState["statuses"] };
  }
  if (!vm.hasPlans) {
    s[3] = "active";
    return { current: 4, statuses: s as StageState["statuses"] };
  }
  s[3] = "completed";

  // No feasible plan at all -- terminal, honest, not an approval state.
  if (vm.noFeasiblePlan) {
    return { current: 4, statuses: s as StageState["statuses"] };
  }

  // Stage 5 — Approve
  if (!vm.isDecided) {
    s[4] = "awaiting";
    return { current: 5, statuses: s as StageState["statuses"] };
  }
  if (vm.isRejected) {
    s[4] = "rejected";
    return { current: 5, statuses: s as StageState["statuses"] };
  }
  s[4] = "completed";

  // Stage 6 — Execute
  if (vm.isCompleted) {
    s[5] = "completed";
  } else if (vm.isPartial) {
    s[5] = "partial";
    return { current: 6, statuses: s as StageState["statuses"] };
  } else if (vm.isFailed) {
    s[5] = "failed";
    return { current: 6, statuses: s as StageState["statuses"] };
  } else {
    s[5] = "active";
    return { current: 6, statuses: s as StageState["statuses"] };
  }

  // Stage 7 — Completed: only ever reached on a genuine full success.
  s[6] = "completed";
  return { current: 7, statuses: s as StageState["statuses"] };
}
