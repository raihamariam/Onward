import type { NextConfig } from "next";

// Env vars come from apps/web/.env.local, generated from the repo-root .env
// by `npm run predev` / `npm run prebuild` (scripts/sync-env.mjs) — see that
// file for why a next.config.ts-level loadEnvConfig() on the root .env does
// not work here (it doesn't propagate to Turbopack's worker processes).
const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
