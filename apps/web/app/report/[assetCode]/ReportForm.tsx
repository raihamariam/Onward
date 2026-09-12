"use client";

import { useState } from "react";

type Asset = {
  id: string;
  code: string;
  name: string;
  location: string;
  status: string;
};

type IntakeResult =
  | { kind: "success"; incidentId: string; duplicate: boolean }
  | { kind: "error"; status: number; message: string };

function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

export function ReportForm({ asset }: { asset: Asset }) {
  const [description, setDescription] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<IntakeResult | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;
    setSubmitting(true);
    setResult(null);
    try {
      const res = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_code: asset.code,
          description: description.trim(),
          idempotency_key: idempotencyKey,
          source: "qr",
        }),
      });
      const body = await res.json();
      if (res.ok) {
        setResult({
          kind: "success",
          incidentId: body.incident_id,
          duplicate: Boolean(body.duplicate),
        });
        // A genuinely new report after success should get a fresh key;
        // a retry of *this* attempt (network blip) should reuse it.
        setIdempotencyKey(newIdempotencyKey());
      } else {
        setResult({ kind: "error", status: res.status, message: body.message ?? "Request failed" });
      }
    } catch {
      setResult({
        kind: "error",
        status: 0,
        message: "Could not reach Onward. Check your connection and try again — this submission will not be duplicated.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (result?.kind === "success") {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-neutral-950 px-6 text-center text-neutral-100">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400">
          <svg viewBox="0 0 24 24" fill="none" className="h-8 w-8" stroke="currentColor" strokeWidth={2}>
            <path d="M20 6 9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-semibold">
            {result.duplicate ? "Already reported" : "Incident reported"}
          </h1>
          <p className="mt-2 max-w-xs text-neutral-400">
            Onward is on it. Operations has been notified and a recovery is being
            calculated now.
          </p>
        </div>
        <p className="font-mono text-xs text-neutral-600">{result.incidentId}</p>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col bg-neutral-950 px-6 pb-10 pt-12 text-neutral-100">
      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-neutral-500">
        Onward
      </p>

      <div className="mt-8 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <p className="font-mono text-lg font-semibold text-white">{asset.code}</p>
        <p className="text-base text-neutral-300">{asset.name}</p>
        <div className="mt-3 flex items-center gap-2 text-sm text-neutral-400">
          <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 shrink-0" stroke="currentColor" strokeWidth={2}>
            <path d="M12 22s7-7.58 7-12.5A7 7 0 0 0 5 9.5C5 14.42 12 22 12 22Z" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="12" cy="9.5" r="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          {asset.location}
        </div>
      </div>

      <form onSubmit={submit} className="mt-8 flex flex-1 flex-col">
        <label htmlFor="description" className="text-sm font-medium text-neutral-300">
          What happened?
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Projector won't turn on"
          rows={3}
          autoFocus
          required
          className="mt-3 w-full resize-none rounded-2xl border border-neutral-800 bg-neutral-900 px-4 py-4 text-lg text-white placeholder-neutral-600 outline-none focus:border-neutral-500"
        />

        {result?.kind === "error" && (
          <p role="alert" className="mt-3 text-sm text-red-400">
            {result.message}
          </p>
        )}

        <div className="flex-1" />

        <button
          type="submit"
          disabled={submitting || !description.trim()}
          className="mt-8 w-full rounded-2xl bg-white py-4 text-lg font-semibold text-neutral-950 transition disabled:cursor-not-allowed disabled:opacity-40"
        >
          {submitting ? "Reporting…" : "Report Incident"}
        </button>
      </form>
    </main>
  );
}
