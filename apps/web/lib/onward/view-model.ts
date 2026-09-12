import type { Plan, StateResponse } from "./types";

// One place that turns the raw API response into every derived boolean the
// UI needs. Every component reads from this instead of re-deriving its own
// notion of "are we waiting for X" -- so stage logic is computed exactly
// once (per the Phase 12 requirement not to duplicate it across
// components).

export type OnwardViewModel = StateResponse & {
  hasIncident: boolean;
  hasIntelligence: boolean;
  hasImpact: boolean;
  impactKnown: boolean;
  hasPlans: boolean;
  recommendedPlan: Plan | null;
  hasRecommendedPlan: boolean;
  noFeasiblePlan: boolean; // plans exist, none feasible/recommended
  isDecided: boolean;
  isApproved: boolean;
  isRejected: boolean;
  isExecuting: boolean;
  isExecutionTerminal: boolean;
  isCompleted: boolean; // execution_runs.status === 'completed'
  isPartial: boolean;
  isFailed: boolean;
  expectedActionTypes: string[];
  completedActionCount: number;
  totalExpectedActionCount: number;
};

const EXPECTED_ACTIONS_BY_PLAN: Record<string, string[]> = {
  repair_via_technician: ["work_order", "slack_notify"],
  replace_asset: ["work_order", "slack_notify", "inventory_decrement"],
  relocate_operation: [
    "work_order",
    "slack_notify",
    "resource_reservation",
    "calendar_update",
    "gmail_notify",
  ],
};

export function buildViewModel(data: StateResponse): OnwardViewModel {
  const hasIncident = Boolean(data.incident);
  const hasIntelligence = Boolean(data.intelligence);
  const hasImpact = Boolean(data.impact);
  const impactKnown = Boolean(data.impact?.impact_known);
  const hasPlans = data.plans.length > 0;
  const recommendedPlan = data.plans.find((p) => p.is_recommended) ?? null;
  const hasRecommendedPlan = Boolean(recommendedPlan);
  const noFeasiblePlan = hasPlans && !hasRecommendedPlan;

  const isDecided = Boolean(data.approval);
  const isApproved = data.approval?.decision === "approved";
  const isRejected = data.approval?.decision === "rejected";

  const executionStatus = data.executionRun?.status ?? null;
  const isExecuting = isApproved && (!data.executionRun || executionStatus === "executing");
  const isExecutionTerminal =
    executionStatus === "completed" || executionStatus === "partially_completed" || executionStatus === "failed";
  const isCompleted = executionStatus === "completed";
  const isPartial = executionStatus === "partially_completed";
  const isFailed = executionStatus === "failed";

  const expectedActionTypes = recommendedPlan
    ? EXPECTED_ACTIONS_BY_PLAN[recommendedPlan.plan_type] ?? []
    : [];
  const completedActionCount = data.executionActions.filter((a) => a.status === "completed").length;

  return {
    ...data,
    hasIncident,
    hasIntelligence,
    hasImpact,
    impactKnown,
    hasPlans,
    recommendedPlan,
    hasRecommendedPlan,
    noFeasiblePlan,
    isDecided,
    isApproved,
    isRejected,
    isExecuting,
    isExecutionTerminal,
    isCompleted,
    isPartial,
    isFailed,
    expectedActionTypes,
    completedActionCount,
    totalExpectedActionCount: expectedActionTypes.length,
  };
}
