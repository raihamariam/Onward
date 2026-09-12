import { NextRequest, NextResponse } from "next/server";

// Server-side aggregation read for the Command View's polling loop. Uses
// the publishable key, same as incidents/[id]/page.tsx and report/[assetCode]
// — every table here is (or, for the Phase 6 execution tables, needs to
// become — see database/migrations/0008_command_view_rls.sql) protected by
// a public-SELECT RLS policy, not by this route holding any elevated
// access. The Command View polls this one route on a plain interval
// instead of talking to Supabase directly, so no Supabase key is ever sent
// to the browser (avoids the NEXT_PUBLIC_ inlining quirk noted in
// .env.example, same reasoning as /api/report and /api/approve).

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_PUBLISHABLE_KEY;

async function sb(path: string) {
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    throw new Error("SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY are not configured");
  }
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Supabase read failed (${path}): HTTP ${res.status}`);
  }
  return res.json();
}

export async function GET(req: NextRequest) {
  try {
    const incidentIdParam = req.nextUrl.searchParams.get("incident");

    let incident;
    if (incidentIdParam) {
      const rows = await sb(
        `incidents?id=eq.${encodeURIComponent(incidentIdParam)}&select=*`
      );
      incident = rows[0] ?? null;
    } else {
      const rows = await sb(
        `incidents?select=*&order=reported_at.desc&limit=1`
      );
      incident = rows[0] ?? null;
    }

    if (!incident) {
      return NextResponse.json({ incident: null });
    }

    const [asset, intelligenceRows, impactRows, plans, approvalRows] =
      await Promise.all([
        sb(`assets?id=eq.${incident.asset_id}&select=*`),
        sb(`incident_intelligence?incident_id=eq.${incident.id}&select=*`),
        sb(`operational_impact?incident_id=eq.${incident.id}&select=*`),
        sb(`recovery_plans?incident_id=eq.${incident.id}&select=*&order=rank.asc`),
        sb(`approvals?incident_id=eq.${incident.id}&select=*`),
      ]);

    const approval = approvalRows[0] ?? null;

    let executionRun = null;
    let executionActions: unknown[] = [];
    let workOrders: unknown[] = [];
    let reservations: unknown[] = [];

    if (approval) {
      const [runRows, actionRows, workOrderRows, reservationRows] =
        await Promise.all([
          sb(`execution_runs?approval_id=eq.${approval.id}&select=*`),
          sb(`execution_actions?incident_id=eq.${incident.id}&select=*`),
          sb(`work_orders?incident_id=eq.${incident.id}&select=*`),
          sb(`resource_reservations?incident_id=eq.${incident.id}&select=*`),
        ]);
      executionRun = runRows[0] ?? null;
      executionActions = actionRows;
      workOrders = workOrderRows;
      reservations = reservationRows;
    }

    return NextResponse.json({
      incident,
      asset: asset[0] ?? null,
      intelligence: intelligenceRows[0] ?? null,
      impact: impactRows[0] ?? null,
      plans,
      approval,
      executionRun,
      executionActions,
      workOrders,
      reservations,
    });
  } catch (err) {
    return NextResponse.json(
      { error: "state_read_failed", message: err instanceof Error ? err.message : String(err) },
      { status: 500 }
    );
  }
}
