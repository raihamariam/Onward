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

// The client's StateResponse type (lib/onward/types.ts) has no optional
// fields -- every array/object is always present, even when there's no
// incident yet (SYSTEM READY). Returning a partial shape here crashed
// buildViewModel() before it could ever render that state, since it reads
// data.plans.length etc. unconditionally. Both no-session and no-incident
// early returns go through this so the contract can't drift apart again.
function emptyState(sessionStartedAt: string | null) {
  return {
    incident: null,
    sessionStartedAt,
    asset: null,
    originLocation: null,
    candidateLocations: [],
    intelligence: null,
    impact: null,
    plans: [],
    approval: null,
    executionRun: null,
    executionActions: [],
    workOrders: [],
    reservations: [],
  };
}

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

    // Always resolve the current demo session, regardless of which incident
    // branch below is used -- the client needs this on EVERY poll (even
    // while pinned to a locked incident id) to notice when
    // tests/prepare_demo.py starts a new session and drop its old lock.
    // If database/migrations/0009_demo_sessions.sql hasn't been applied
    // yet, treat that exactly like "no session started" (SYSTEM READY)
    // rather than a 500 -- the safe default either way.
    let sessionRows: { started_at: string }[] = [];
    try {
      sessionRows = await sb(`demo_sessions?select=started_at&order=started_at.desc&limit=1`);
    } catch {
      sessionRows = [];
    }
    const sessionStartedAt: string | null = sessionRows[0]?.started_at ?? null;

    let incident;
    if (incidentIdParam) {
      // Explicit/pinned incident id always wins for WHICH incident to show
      // -- covers both the documented ?incident= backup/rehearsal override
      // and the Command View's own client-side lock-on once it has found
      // one for the current session.
      const rows = await sb(
        `incidents?id=eq.${encodeURIComponent(incidentIdParam)}&select=*`
      );
      incident = rows[0] ?? null;
    } else {
      // No pin yet: only ever follow an incident reported AFTER the most
      // recent demo session started. Historical incidents are never
      // deleted -- this is purely "where do we start looking", so a stale
      // rehearsal incident can never re-surface on the live screen. No
      // session yet -> SYSTEM READY, never "whatever's newest in the whole
      // table" (the Phase 11 bug).
      if (!sessionStartedAt) {
        return NextResponse.json(emptyState(null));
      }
      const rows = await sb(
        `incidents?reported_at=gt.${encodeURIComponent(sessionStartedAt)}&select=*&order=reported_at.asc&limit=1`
      );
      incident = rows[0] ?? null;
    }

    if (!incident) {
      return NextResponse.json(emptyState(sessionStartedAt));
    }

    const [asset, intelligenceRows, impactRows, plans, approvalRows] =
      await Promise.all([
        sb(`assets?id=eq.${incident.asset_id}&select=*`),
        sb(`incident_intelligence?incident_id=eq.${incident.id}&select=*`),
        sb(`operational_impact?incident_id=eq.${incident.id}&select=*`),
        sb(`recovery_plans?incident_id=eq.${incident.id}&select=*&order=rank.asc`),
        sb(`approvals?incident_id=eq.${incident.id}&select=*`),
      ]);

    // Real capacity/status for the room the incident's asset is already in
    // (asset.location is a plain text name, e.g. "Room 3.12" -- matched
    // against locations.name) and for every relocate_operation candidate's
    // target room. Both are used for display only, never recomputed --
    // this is so the UI can show a real capacity number instead of parsing
    // it back out of a constraint's own English sentence.
    const assetLocationName = asset[0]?.location as string | undefined;
    const relocateLocationIds = Array.from(
      new Set(
        (plans as { plan_type: string; resource_ref: Record<string, string> | null }[])
          .filter((p) => p.plan_type === "relocate_operation" && p.resource_ref?.location_id)
          .map((p) => p.resource_ref!.location_id)
      )
    );

    const [originLocationRows, candidateLocationRows] = await Promise.all([
      assetLocationName
        ? sb(`locations?name=eq.${encodeURIComponent(assetLocationName)}&select=id,code,name,capacity,status`)
        : Promise.resolve([]),
      relocateLocationIds.length > 0
        ? sb(`locations?id=in.(${relocateLocationIds.join(",")})&select=id,code,name,capacity,status`)
        : Promise.resolve([]),
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
      sessionStartedAt,
      asset: asset[0] ?? null,
      originLocation: originLocationRows[0] ?? null,
      candidateLocations: candidateLocationRows,
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
