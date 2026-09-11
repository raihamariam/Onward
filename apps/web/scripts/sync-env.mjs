#!/usr/bin/env node
// Copies the subset of the repo-root .env that apps/web actually needs into
// apps/web/.env.local. Next.js only reliably loads env files from its own
// project directory (confirmed experimentally: a next.config.ts-level
// loadEnvConfig() call on the root .env populates process.env in the main
// process but is NOT visible to Turbopack's request-handling workers, for
// either Route Handlers or Server Components) — so this is the boring, well-
// supported mechanism, not the clever one. Runs automatically via the
// predev/prebuild npm scripts. apps/web/.env.local is gitignored.

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootEnvPath = join(__dirname, "..", "..", "..", ".env");
const targetPath = join(__dirname, "..", ".env.local");

// Only what apps/web's own code reads via process.env — not the whole file,
// so decision-engine/n8n-only secrets never land in this directory.
const NEEDED_KEYS = ["SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "INCIDENT_WEBHOOK_URL"];

if (!existsSync(rootEnvPath)) {
  console.log("sync-env: no root .env found, skipping");
  process.exit(0);
}

const lines = readFileSync(rootEnvPath, "utf-8").split("\n");
const values = {};
for (const rawLine of lines) {
  const line = rawLine.trim();
  if (!line || line.startsWith("#") || !line.includes("=")) continue;
  const idx = line.indexOf("=");
  const key = line.slice(0, idx).trim();
  const value = line.slice(idx + 1).trim();
  if (NEEDED_KEYS.includes(key)) values[key] = value;
}

const missing = NEEDED_KEYS.filter((k) => !values[k]);
if (missing.length > 0) {
  console.log(`sync-env: root .env is missing ${missing.join(", ")} (leaving unset)`);
}

const out = NEEDED_KEYS.map((k) => `${k}=${values[k] ?? ""}`).join("\n") + "\n";
writeFileSync(targetPath, out, "utf-8");
console.log(`sync-env: wrote ${targetPath} (${Object.keys(values).length}/${NEEDED_KEYS.length} values present)`);
