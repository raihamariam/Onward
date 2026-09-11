// Reads go directly to Supabase's Data API with the publishable key,
// server-side, protected by the public-SELECT RLS policy (database/migrations
// /0001_init.sql). Writes stay exclusively n8n's job — see CLAUDE.md's
// reads-vs-writes split. No Supabase client library needed for one read.

type Incident = {
  id: string;
  asset_id: string;
  description: string;
  idempotency_key: string;
  source: string;
  status: string;
  reported_at: string;
  created_at: string;
};

async function fetchIncident(id: string): Promise<Incident | null> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    throw new Error("SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY are not configured");
  }
  const res = await fetch(
    `${url}/rest/v1/incidents?id=eq.${encodeURIComponent(id)}&select=*`,
    {
      headers: { apikey: key, Authorization: `Bearer ${key}` },
      cache: "no-store",
    }
  );
  if (!res.ok) {
    throw new Error(`Supabase read failed: HTTP ${res.status}`);
  }
  const rows: Incident[] = await res.json();
  return rows[0] ?? null;
}

export default async function IncidentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const incident = await fetchIncident(id);

  if (!incident) {
    return (
      <main style={{ maxWidth: 480, margin: "0 auto", padding: 24 }}>
        <h1>Incident not found</h1>
        <p>No incident with id {id}.</p>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 480, margin: "0 auto", padding: 24 }}>
      <h1>Incident {incident.id}</h1>
      <dl>
        <dt>Status</dt>
        <dd>{incident.status}</dd>
        <dt>Asset</dt>
        <dd>{incident.asset_id}</dd>
        <dt>Description</dt>
        <dd>{incident.description}</dd>
        <dt>Source</dt>
        <dd>{incident.source}</dd>
        <dt>Reported at</dt>
        <dd>{incident.reported_at}</dd>
        <dt>Idempotency key</dt>
        <dd>{incident.idempotency_key}</dd>
      </dl>
    </main>
  );
}
