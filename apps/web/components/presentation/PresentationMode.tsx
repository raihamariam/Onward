"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";

// Presentation Mode is a URL flag (?present=1), not a separate app --
// every real control and every real data panel stays exactly the same;
// only chrome (sidebar, secondary text density) is reduced and key text
// is enlarged for projector readability. Toggling it never loses the
// currently-locked/overridden incident, since it only ever adds or removes
// the one query param.
export function PresentationModeToggle({ active }: { active: boolean }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function toggle() {
    const params = new URLSearchParams(searchParams.toString());
    if (active) {
      params.delete("present");
    } else {
      params.set("present", "1");
    }
    const qs = params.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname);
  }

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1.5 rounded-md border border-panel-border-strong px-3 py-1.5 text-xs font-medium text-text-secondary transition hover:text-text-primary"
    >
      <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5" stroke="currentColor" strokeWidth={1.75}>
        <rect x="2" y="4" width="20" height="13" rx="2" />
        <path d="M8 21h8M12 17v4" strokeLinecap="round" />
      </svg>
      {active ? "Exit Presentation" : "Presentation Mode"}
    </button>
  );
}
