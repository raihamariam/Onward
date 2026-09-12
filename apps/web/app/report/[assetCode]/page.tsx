// Reads go directly to Supabase's Data API with the publishable key,
// server-side, protected by the public-SELECT RLS policy on `assets`
// (database/migrations/0001_init.sql) — same pattern as
// incidents/[id]/page.tsx. Writes stay exclusively n8n's job via
// /api/report (see CLAUDE.md's reads-vs-writes split).

import { ReportForm } from "./ReportForm";

type Asset = {
  id: string;
  code: string;
  name: string;
  location: string;
  status: string;
};

async function fetchAsset(code: string): Promise<Asset | null> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    throw new Error("SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY are not configured");
  }
  const res = await fetch(
    `${url}/rest/v1/assets?code=eq.${encodeURIComponent(code)}&select=*`,
    {
      headers: { apikey: key, Authorization: `Bearer ${key}` },
      cache: "no-store",
    }
  );
  if (!res.ok) {
    throw new Error(`Supabase read failed: HTTP ${res.status}`);
  }
  const rows: Asset[] = await res.json();
  return rows[0] ?? null;
}

export default async function ReportPage({
  params,
}: {
  params: Promise<{ assetCode: string }>;
}) {
  const { assetCode } = await params;
  const asset = await fetchAsset(assetCode);

  if (!asset) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-3 bg-neutral-950 px-6 text-center text-neutral-100">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
          Onward
        </p>
        <h1 className="text-2xl font-semibold">Unknown asset</h1>
        <p className="max-w-xs text-neutral-400">
          No registered asset matches <span className="font-mono">{assetCode}</span>.
          Check the QR code or contact operations.
        </p>
      </main>
    );
  }

  if (asset.status !== "active") {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-3 bg-neutral-950 px-6 text-center text-neutral-100">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500">
          Onward
        </p>
        <h1 className="text-2xl font-semibold">{asset.code} is not in service</h1>
        <p className="max-w-xs text-neutral-400">
          This asset is currently marked {asset.status}. Contact operations directly.
        </p>
      </main>
    );
  }

  return <ReportForm asset={asset} />;
}
