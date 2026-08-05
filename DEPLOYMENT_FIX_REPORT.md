# Vercel Deployment Fix Report

## Root cause

Vercel uses `frontend` as its Root Directory, but `frontend/next.config.ts` moved output tracing outside that boundary with `outputFileTracingRoot: path.join(process.cwd(), "..")`.

This monorepo-style override conflicted with the configured deployment root. The source compiled, so Vercel marked the build Ready, but the deployed output did not contain routes where the project expected them. Requests therefore received Vercel's platform-level `404 NOT_FOUND` response before reaching Next.js.

## Files modified

- `frontend/next.config.ts`
- `DEPLOYMENT_FIX_REPORT.md`

No UI or application logic was changed.

## Fix

- Changed `outputFileTracingRoot` to `process.cwd()` and removed the unused `node:path` import.
- Explicitly scoped Next.js/Vercel output tracing to the configured `frontend` Root Directory.
- Confirmed there is no `output: "export"`, `basePath`, or `assetPrefix`.
- Confirmed there is no middleware, redirect, rewrite, custom header, or catch-all route interfering with `/`.

## App Router and package audit

- `frontend/app/layout.tsx` has a valid default root-layout export.
- `frontend/app/page.tsx` has a valid default page export for `/`.
- All routes follow the Next.js 15 App Router `app/**/page.tsx` convention.
- `frontend/package.json` uses the standard `next dev`, `next build`, and `next start` scripts.

## Vercel settings

Use these project settings:

- Root Directory: `frontend`
- Framework Preset: Next.js
- Build Command: `npm run build` or the detected default
- Output Directory: blank/default
- Install Command: default

Do not set Output Directory to `frontend/.next` or `.next`; Vercel's Next.js adapter manages the build output.

## Deployment readiness

The source configuration is now aligned with `frontend` as the Vercel project root. Commit and push the change, then redeploy without the previous build cache so Vercel packages the corrected route output.
