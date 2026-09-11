import { NextRequest, NextResponse } from "next/server";

// Proxies to WF-01's webhook server-side. Not a business-logic layer — it
// exists only because Next.js's NEXT_PUBLIC_ build-time inlining scans
// .env files inside apps/web itself, and this repo's single .env lives at
// the root (see next.config.ts). Reading the webhook URL server-side here
// avoids needing a second, duplicated env file just to satisfy that scan.
export async function POST(req: NextRequest) {
  const webhookUrl =
    process.env.INCIDENT_WEBHOOK_URL ||
    process.env.NEXT_PUBLIC_N8N_INCIDENT_WEBHOOK_URL ||
    process.env.N8N_WEBHOOK_BASE_URL;

  if (!webhookUrl) {
    return NextResponse.json(
      { error: "not_configured", message: "INCIDENT_WEBHOOK_URL is not set" },
      { status: 500 }
    );
  }

  const payload = await req.json();
  const upstream = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await upstream.json();
  return NextResponse.json(body, { status: upstream.status });
}
