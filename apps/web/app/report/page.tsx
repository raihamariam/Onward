"use client";

import { Suspense, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

type IntakeResult =
  | { kind: "success"; incidentId: string; status: string; duplicate: boolean }
  | { kind: "error"; status: number; message: string };

function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

export default function ReportPage() {
  return (
    <Suspense fallback={null}>
      <ReportForm />
    </Suspense>
  );
}

function ReportForm() {
  const searchParams = useSearchParams();
  // A later QR code just needs to link here as /report?asset=<code> — this
  // page never has to change shape to support that.
  const initialAssetCode = searchParams.get("asset") ?? "";

  const [assetCode, setAssetCode] = useState(initialAssetCode);
  const [description, setDescription] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<IntakeResult | null>(null);

  const webhookUrl = useMemo(
    () => process.env.NEXT_PUBLIC_N8N_INCIDENT_WEBHOOK_URL ?? "",
    []
  );

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!webhookUrl) {
      setResult({
        kind: "error",
        status: 0,
        message: "NEXT_PUBLIC_N8N_INCIDENT_WEBHOOK_URL is not configured.",
      });
      return;
    }
    setSubmitting(true);
    setResult(null);
    try {
      const res = await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_code: assetCode,
          description,
          idempotency_key: idempotencyKey,
          source: "web",
        }),
      });
      const body = await res.json();
      if (res.ok) {
        setResult({
          kind: "success",
          incidentId: body.incident_id,
          status: body.status ?? "received",
          duplicate: Boolean(body.duplicate),
        });
        // A genuinely new report should not reuse this attempt's key —
        // retries of *this* submission (e.g. a network blip) should reuse
        // it, but a fresh report after success is a new incident.
        setIdempotencyKey(newIdempotencyKey());
      } else {
        setResult({
          kind: "error",
          status: res.status,
          message: body.message ?? "Request failed",
        });
      }
    } catch {
      setResult({
        kind: "error",
        status: 0,
        message: "Could not reach the intake service. You can retry — this submission's idempotency key is unchanged.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main style={{ maxWidth: 480, margin: "0 auto", padding: 24 }}>
      <h1>Report an incident</h1>
      <form onSubmit={submit}>
        <label htmlFor="asset_code">Asset code</label>
        <input
          id="asset_code"
          value={assetCode}
          onChange={(e) => setAssetCode(e.target.value)}
          placeholder="e.g. AV-204"
          required
        />
        <label htmlFor="description">What&apos;s wrong?</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. Projector won't turn on"
          required
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Submitting…" : "Submit"}
        </button>
      </form>

      {result?.kind === "success" && (
        <p>
          {result.duplicate ? "Already recorded — " : "Recorded — "}
          incident <code>{result.incidentId}</code> ({result.status}).
        </p>
      )}
      {result?.kind === "error" && (
        <p role="alert">
          {result.status ? `Error ${result.status}: ` : ""}
          {result.message}
        </p>
      )}
    </main>
  );
}
