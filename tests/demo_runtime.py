"""Phase 12 hardening -- the one controlled startup procedure before a
recording/rehearsal/demo, to bring the local decision-engine + its public
dev tunnel back to a known-good state.

Why this exists: the decision-engine runs locally (see CLAUDE.md Sec.9 --
the real production path is deploying it somewhere with a stable URL; the
Cloudflare Quick Tunnel is explicitly a dev/gate-testing bridge, not
production connectivity). A Quick Tunnel's URL is ephemeral and cannot be
renewed -- every restart needs a fresh URL, and every n8n node that calls
the decision-engine (WF-02, WF-03, WF-04, WF-05's freshness/fingerprint
recheck) has that URL hardcoded and must be updated to match.

Split into two commands because updating and republishing the four n8n
workflows requires n8n's own access/tooling (Claude Code's MCP connection),
not a portable credential this script could carry -- see DEMO_RUNBOOK.md
for why a single fully-standalone script isn't the safe design here.

  python tests/demo_runtime.py start
      Ensures exactly one decision-engine process is running (starts one,
      without --reload, if not), ensures exactly one Cloudflare Quick
      Tunnel is running against it (replacing any stale one -- a dead
      tunnel's URL can never be reused), validates the new URL is
      genuinely publicly reachable, and writes it into .env's
      DECISION_ENGINE_PUBLIC_URL. Prints the URL and stops there.

  <between the two commands: give the printed URL to Claude Code and ask
   it to update WF-02 / WF-03 / WF-04 / WF-05's decision-engine HTTP node
   with it and republish those four workflows -- or edit the four nodes
   by hand in the n8n editor if Claude Code isn't available>

  python tests/demo_runtime.py finish
      Re-verifies local + public health, runs tests/demo_preflight.py,
      runs tests/prepare_demo.py (leaves the Command View at SYSTEM
      READY), and prints a short summary.

Safety rule for the tunnel step (deliberate, do not loosen): the ONLY
processes this script will ever inspect for possible termination are
those whose command line contains the literal string
"--url http://localhost:8000" -- i.e. a Cloudflare Quick Tunnel pointed at
this project's own decision-engine port. Every match is printed (pid,
parent pid, command line, start time) before being terminated. A
cloudflared process for any other target, or any other tool entirely, is
never touched and is never even a candidate.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
DECISION_ENGINE_DIR = ROOT / "services" / "decision-engine"
STATE_PATH = ROOT / "tests" / ".demo_runtime_state.json"
LOG_DIR = ROOT / "tests" / ".demo_runtime_logs"
UVICORN_LOG = LOG_DIR / "decision-engine.log"
TUNNEL_LOG = LOG_DIR / "tunnel.log"

FRONTEND_URL = "https://onward-smoky.vercel.app"
TUNNEL_TARGET = "--url http://localhost:8000"  # the ONLY string this script matches processes against for kill eligibility

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def set_env_var(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    found = False
    for i, raw in enumerate(lines):
        if raw.strip().startswith(f"{key}=") or raw.strip() == key:
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ps_query(command_line_contains: str) -> list[dict]:
    """List Windows processes whose CommandLine contains the given substring, via WMI/CIM."""
    escaped = command_line_contains.replace('"', '`"')
    # Excludes powershell.exe unconditionally: this query itself always runs as a
    # powershell.exe process whose own -Command string contains the search text
    # (it's quoted right there in the filter below), which would otherwise match
    # itself every time. No real target of this script (uvicorn, cloudflared,
    # nohup) is ever a powershell.exe process, so this exclusion is always safe.
    ps_cmd = (
        f'Get-CimInstance Win32_Process | Where-Object {{ $_.CommandLine -like "*{escaped}*" -and $_.Name -ne "powershell.exe" }} '
        "| Select-Object ProcessId,ParentProcessId,CommandLine,CreationDate | ConvertTo-Json -Depth 3"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=25,
        )
    except Exception as e:  # noqa: BLE001
        print(f"  WARN: process query failed: {e}")
        return []
    if not out.stdout.strip():
        return []
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    return data


def listening_pids(port: int) -> list[int]:
    ps_cmd = (
        f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty OwningProcess"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:  # noqa: BLE001
        return []
    pids = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return sorted(set(pids))


def kill_pid(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)


def curl_status(url: str, timeout: int = 6, resolve: str | None = None) -> int | None:
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(timeout)]
    if resolve:
        cmd += ["--resolve", resolve]
    cmd.append(url)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    except Exception:  # noqa: BLE001
        return None
    code = out.stdout.strip()
    return int(code) if code.isdigit() else None


def check_public_health(url: str, attempts: int = 20, interval: int = 3) -> bool:
    """Poll <url>/health, falling back to a public-DNS-resolved IP (via
    --resolve) if the local resolver hasn't picked up this freshly-created
    trycloudflare.com subdomain yet -- a real, reproducible lag observed on
    this network, not a tunnel problem."""
    for _ in range(attempts):
        if curl_status(f"{url}/health", timeout=6) == 200:
            return True
        time.sleep(interval)
    host = url.replace("https://", "").rstrip("/")
    ip = public_dns_ip(host)
    if ip and curl_status(f"{url}/health", timeout=8, resolve=f"{host}:443:{ip}") == 200:
        return True
    return False


def public_dns_ip(hostname: str) -> str | None:
    """Fallback resolution via 1.1.1.1 -- local resolvers sometimes lag on a
    brand-new trycloudflare.com subdomain for a few seconds after creation.
    Takes the LAST IPv4 literal in nslookup's output: the first is the
    resolver's own address (e.g. "Server: 1.1.1.1"), the rest are the
    answer -- and IPv6 lines in between never produce a false IPv4 match,
    since this scans for the full dotted-quad pattern only."""
    try:
        out = subprocess.run(
            ["nslookup", hostname, "1.1.1.1"], capture_output=True, text=True, timeout=10
        )
    except Exception:  # noqa: BLE001
        return None
    ipv4s = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", out.stdout)
    answer_ips = [ip for ip in ipv4s if ip != "1.1.1.1"]
    return answer_ips[-1] if answer_ips else None


def ensure_decision_engine() -> tuple[bool, str]:
    print("1. Decision engine (local)")
    pids = listening_pids(8000)
    status = curl_status("http://localhost:8000/health")

    if len(pids) == 1 and status == 200:
        print(f"   OK  exactly one process listening on :8000 (pid {pids[0]}), /health = 200")
        return True, f"already running, pid {pids[0]}"

    if len(pids) > 1:
        print(f"   FAIL  {len(pids)} processes listening on :8000 ({pids}) -- ambiguous, not auto-fixing")
        return False, f"{len(pids)} processes on :8000, needs manual resolution"

    if len(pids) == 0:
        print("   none running -- starting uvicorn (no --reload)")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(UVICORN_LOG, "a", encoding="utf-8") as log:
            subprocess.Popen(
                ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=DECISION_ENGINE_DIR, stdout=log, stderr=subprocess.STDOUT,
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
            )
        for _ in range(20):
            time.sleep(1)
            if curl_status("http://localhost:8000/health") == 200:
                pids = listening_pids(8000)
                print(f"   OK  started, pid {pids[0] if pids else '?'}, /health = 200")
                return True, "started fresh"
        print("   FAIL  started but /health never returned 200 within 20s")
        return False, "started but health check timed out"

    print(f"   FAIL  process listening (pid {pids[0]}) but /health = {status}")
    return False, f"process up, health={status}"


def ensure_tunnel() -> tuple[bool, str | None]:
    print("2. Cloudflare Quick Tunnel")
    existing = ps_query(TUNNEL_TARGET)
    if existing:
        print(f"   found {len(existing)} existing tunnel process(es) targeting this project's decision-engine:")
        for p in existing:
            print(f"     pid={p.get('ProcessId')} ppid={p.get('ParentProcessId')} started={p.get('CreationDate')}")
            print(f"     cmd: {p.get('CommandLine')}")
        print("   these match the exact --url http://localhost:8000 signature -- safe to replace (a Quick")
        print("   Tunnel URL can never be renewed/reused, so a stale one must be closed before starting fresh)")
        for p in existing:
            kill_pid(p["ProcessId"])
        time.sleep(1)
    else:
        print("   none currently running")

    print("   starting exactly one fresh tunnel")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    TUNNEL_LOG.write_text("", encoding="utf-8")
    with open(TUNNEL_LOG, "w", encoding="utf-8") as log:
        subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://localhost:8000"],
            stdout=log, stderr=subprocess.STDOUT,
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
        )

    url = None
    for _ in range(30):
        time.sleep(1)
        text = TUNNEL_LOG.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", text)
        if m:
            url = m.group(0)
            break
    if not url:
        print("   FAIL  no tunnel URL appeared in cloudflared's output within 30s")
        return False, None
    print(f"   OK  tunnel URL: {url}")

    print("3. Public reachability of the new tunnel URL")
    ok = check_public_health(url)
    print("   OK  public /health = 200" if ok else "   FAIL  tunnel URL did not become publicly reachable")
    return ok, url


def cmd_start() -> int:
    print("ONWARD DEMO RUNTIME -- start\n")
    de_ok, de_detail = ensure_decision_engine()
    if not de_ok:
        print(f"\nBLOCKED at step 1: {de_detail}")
        return 1

    tunnel_ok, url = ensure_tunnel()
    if not tunnel_ok or not url:
        print("\nBLOCKED at step 2/3: tunnel did not come up cleanly")
        return 1

    set_env_var(ENV_PATH, "DECISION_ENGINE_PUBLIC_URL", url)
    STATE_PATH.write_text(json.dumps({"url": url, "started_at": time.time()}), encoding="utf-8")

    print(f"\nLocal decision engine and tunnel are ready.")
    print(f".env DECISION_ENGINE_PUBLIC_URL updated to: {url}")
    print("\nNEXT STEP (not scriptable -- needs n8n's own access/tooling):")
    print(f"  Ask Claude Code to update WF-02 / WF-03 / WF-04 / WF-05's decision-engine")
    print(f"  HTTP node URL to {url} (same paths as before: /incident/interpret,")
    print(f"  /impact/calculate, /recovery/plan x2) and republish all four.")
    print(f"  Then run: python tests/demo_runtime.py finish")
    return 0


def cmd_finish() -> int:
    print("ONWARD DEMO RUNTIME -- finish\n")
    if not STATE_PATH.exists():
        print("BLOCKED: no state from `demo_runtime.py start` found -- run that first.")
        return 1
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    url = state.get("url")

    print("Re-checking local + public health before proceeding...")
    local_ok = curl_status("http://localhost:8000/health") == 200
    public_ok = check_public_health(url, attempts=5, interval=3) if url else False
    print(f"  local:  {'OK' if local_ok else 'FAIL'}")
    print(f"  public: {'OK' if public_ok else 'FAIL'} ({url})")
    if not (local_ok and public_ok):
        print("\nBLOCKED: runtime is not healthy -- re-run `demo_runtime.py start`.")
        return 1

    print("\nRunning tests/demo_preflight.py ...\n")
    subprocess.run([sys.executable, str(ROOT / "tests" / "demo_preflight.py")])

    print("\nRunning tests/prepare_demo.py ...\n")
    subprocess.run([sys.executable, str(ROOT / "tests" / "prepare_demo.py")])

    print("\nConfirming the public Command View is at SYSTEM READY ...")
    try:
        out = subprocess.run(
            ["curl", "-s", f"{FRONTEND_URL}/api/incident-state"],
            capture_output=True, text=True, timeout=15,
        )
        body = json.loads(out.stdout) if out.stdout.strip() else {}
        ready = body.get("incident") is None
        print(f"  Command View: {'SYSTEM READY' if ready else 'NOT READY -- incident present: ' + str(body.get('incident', {}).get('id'))}")
    except Exception as e:  # noqa: BLE001
        print(f"  could not check ({e})")

    print("\nRuntime bring-up complete. See the assembled status report for the full checklist.")
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "start":
        return cmd_start()
    if mode == "finish":
        return cmd_finish()
    print("usage: python tests/demo_runtime.py [start|finish]")
    return 2


if __name__ == "__main__":
    sys.exit(main())
