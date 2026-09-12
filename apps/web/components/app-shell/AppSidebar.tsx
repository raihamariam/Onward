"use client";

// Visual navigation matching the reference dashboard. Per the brief, only
// "Operations" (this dashboard) is backed by real functionality this
// phase -- the rest are present for professional completeness and clearly
// inert rather than pretending to lead anywhere.

const NAV_ITEMS = [
  { label: "Operations", active: true },
  { label: "Incidents", badge: true },
  { label: "Assets" },
  { label: "Rooms" },
  { label: "Operations" },
  { label: "Reports" },
];

function NavIcon({ label }: { label: string }) {
  const common = "h-[18px] w-[18px]";
  switch (label) {
    case "Operations":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={common} stroke="currentColor" strokeWidth={1.75}>
          <path d="M3 12h4l2 5 4-14 2 9h6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "Incidents":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={common} stroke="currentColor" strokeWidth={1.75}>
          <path d="M4 5h16v11H8l-4 4V5Z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "Assets":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={common} stroke="currentColor" strokeWidth={1.75}>
          <rect x="3" y="4" width="18" height="14" rx="2" />
          <path d="M8 21h8" strokeLinecap="round" />
        </svg>
      );
    case "Rooms":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={common} stroke="currentColor" strokeWidth={1.75}>
          <path d="M4 21V6l8-3 8 3v15" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M9 21v-6h6v6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "Reports":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={common} stroke="currentColor" strokeWidth={1.75}>
          <path d="M6 3h9l3 3v15H6V3Z" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M9 12h6M9 16h6" strokeLinecap="round" />
        </svg>
      );
    default:
      return null;
  }
}

export function AppSidebar() {
  return (
    <aside className="flex h-full w-[220px] shrink-0 flex-col border-r border-panel-border bg-panel">
      <div className="flex items-center gap-2 px-5 pt-6 pb-8">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-status-green-bg text-status-green">
          <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={2}>
            <path d="M3 15a9 9 0 0 1 9-9M21 9a9 9 0 0 1-9 9" strokeLinecap="round" />
            <path d="M12 3v3M12 18v3" strokeLinecap="round" />
          </svg>
        </span>
        <div>
          <p className="text-sm font-bold tracking-wide text-text-primary">ONWARD</p>
          <p className="text-[10px] leading-tight text-text-muted">From disruption to continuity</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {NAV_ITEMS.map((item, i) => (
          <div
            key={`${item.label}-${i}`}
            className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm ${
              item.active
                ? "bg-panel-elevated text-text-primary"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            <span className="flex items-center gap-2.5">
              <NavIcon label={item.label} />
              {item.label}
            </span>
            {item.badge && (
              <span className="rounded-full bg-status-red-bg px-1.5 py-0.5 text-[10px] font-semibold text-status-red">
                1
              </span>
            )}
          </div>
        ))}

        <div className="my-3 h-px bg-panel-border" />

        <div className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-text-secondary hover:text-text-primary">
          <svg viewBox="0 0 24 24" fill="none" className="h-[18px] w-[18px]" stroke="currentColor" strokeWidth={1.75}>
            <circle cx="12" cy="12" r="3" />
            <path
              d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.55V21a2 2 0 1 1-4 0v-.09A1.7 1.7 0 0 0 9 19.4a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.55-1H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.55V3a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9a1.7 1.7 0 0 0 1.55 1H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.51 1Z"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Settings
        </div>
      </nav>

      <div className="border-t border-panel-border px-5 py-4">
        <p className="flex items-center gap-2 text-xs font-medium text-status-green">
          <span className="h-1.5 w-1.5 rounded-full bg-status-green" />
          System Online
        </p>
        <p className="mt-0.5 text-[11px] text-text-muted">Monitoring campus operations</p>
      </div>
    </aside>
  );
}
