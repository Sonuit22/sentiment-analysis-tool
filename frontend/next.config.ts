import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  // Vercel builds this directory as the project root. Dependencies are installed
  // locally here, so tracing must not escape into parent workspace lockfiles.
  outputFileTracingRoot: process.cwd(),
};

export default nextConfig;
