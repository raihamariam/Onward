import type { NextConfig } from "next";
import path from "node:path";
import { loadEnvConfig } from "@next/env";

// apps/web has no .env of its own — the single source of truth is the
// repo-root .env (see ../../.env.example). Next.js only auto-loads .env
// files from its own directory, so load the root one explicitly.
loadEnvConfig(path.join(__dirname, "..", ".."));

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
