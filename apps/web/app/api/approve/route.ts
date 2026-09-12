import { NextRequest, NextResponse } from "next/server";

// Proxies to WF-05a's approval webhook server-side, same reason and same
// shape as /api/report — keeps the n8n URL out of client network calls and
// sidesteps the NEXT_PUBLIC_ inlining quirk (see .env.example). This route
// owns nothing: WF-05a re-validates the plan exists, belongs to the
// incident, is feasible, and hasn't already been decided. The client can
// never make "approved" true by itself — this proxy just forwards the
// judge's choice and returns whatever n8n's authoritative decision was.
export async function POST(req: NextRequest) {
  const webhookUrl = process.env.APPROVAL_WEBHOOK_URL;

  if (!webhookUrl) {
    return NextResponse.json(
      { error: "not_configured", message: "APPROVAL_WEBHOOK_URL is not set" },
      { status: 500 }
    );
  }

  const payload = await req.json();
  const { incident_id, plan_id, decision } = payload ?? {};

  if (
    typeof incident_id !== "string" ||
    !incident_id ||
    typeof plan_id !== "string" ||
    !plan_id ||
    (decision !== "approved" && decision !== "rejected")
  ) {
    return NextResponse.json(
      {
        error: "invalid_request",
        message: "incident_id, plan_id, and decision ('approved' or 'rejected') are required",
      },
      { status: 400 }
    );
  }

  const upstream = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      incident_id,
      plan_id,
      decision,
      decided_by: "duty-manager-demo",
    }),
  });
  const body = await upstream.json();
  return NextResponse.json(body, { status: upstream.status });
}
