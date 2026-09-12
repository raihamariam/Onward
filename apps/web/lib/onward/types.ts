// Shared types for the Onward Command View. These mirror exactly what
// app/api/incident-state/route.ts persists and returns -- nothing here is
// invented; every field traces back to a real Supabase column written by
// WF-01 through WF-05.

export type Asset = {
  id: string;
  code: string;
  name: string;
  location: string;
  status: string;
};

export type LocationRow = {
  id: string;
  code: string;
  name: string;
  capacity: number | null;
  status: string;
};

export type Incident = {
  id: string;
  asset_id: string;
  description: string;
  media_url: string | null;
  source: string;
  status: string;
  reported_at: string;
};

export type Intelligence = {
  incident_type: string;
  severity: string;
  required_capability: string;
  confidence: number;
  requires_human_review: boolean;
  review_reason: string | null;
  model: string;
  provider: string;
  interpreted_at: string;
};

export type AffectedOperation = {
  id: string;
  code: string;
  name: string;
  type: string;
  starts_at: string | null;
  criticality: string;
  dependency_path: string[];
  people_affected: number;
  required_capability: string | null;
};

export type Impact = {
  impact_known: boolean;
  impact_level: string;
  minutes_until_impact: number | null;
  service_at_risk: string | null;
  affected_operations: AffectedOperation[] | null;
  dependency_path: string[] | null;
  reason: string | null;
  calculated_at: string;
};

export type Constraint = { name: string; passed: boolean; detail: string };

export type Plan = {
  id: string;
  plan_type: "repair_via_technician" | "replace_asset" | "relocate_operation";
  feasible: boolean;
  is_recommended: boolean;
  estimated_recovery_minutes: number;
  resource_ref: Record<string, string> | null;
  constraints: Constraint[] | null;
  reason: string | null;
  rank: number | null;
};

export type Approval = {
  id: string;
  decision: "approved" | "rejected";
  decided_by: string;
  decided_at: string;
};

export type ExecutionRun = {
  status: "executing" | "completed" | "partially_completed" | "failed";
  started_at: string;
  completed_at: string | null;
};

export type ActionType =
  | "work_order"
  | "slack_notify"
  | "resource_reservation"
  | "calendar_update"
  | "gmail_notify"
  | "inventory_decrement";

export type ExecutionAction = {
  action_type: ActionType;
  status: "completed" | "failed";
  external_reference: string | null;
  attempts: number;
  error: string | null;
  executed_at: string;
};

export type WorkOrder = {
  status: string;
  description: string;
  assigned_technician_id: string | null;
};

export type Reservation = {
  location_id: string;
  reserved_at: string;
};

export type StateResponse = {
  incident: Incident | null;
  sessionStartedAt: string | null;
  asset: Asset | null;
  originLocation: LocationRow | null;
  candidateLocations: LocationRow[];
  intelligence: Intelligence | null;
  impact: Impact | null;
  plans: Plan[];
  approval: Approval | null;
  executionRun: ExecutionRun | null;
  executionActions: ExecutionAction[];
  workOrders: WorkOrder[];
  reservations: Reservation[];
};
