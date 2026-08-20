# Frontend Runtime Fix Report

## Root cause

No application source imports `next/dist/*`, `next/dist/compiled/*`, `source-map`, or `source-map-js`.

The failing module is an internal dependency shipped by Next.js itself. Next 15.5.22 contains and imports `next/dist/compiled/source-map` from its server error-inspection/runtime code.

This repository is an npm workspace. Frontend dependencies are hoisted to the repository-level `node_modules`, but `frontend/next.config.ts` constrained output tracing to `process.cwd()` (the `frontend` directory). Vercel could therefore build the application while omitting hoisted Next runtime files from the serverless function package. At runtime, `/api/predict` loaded Next's server error-inspection code and failed with `Cannot find module 'next/dist/compiled/source-map'`.

## Source import audit

Scanned the complete frontend source for:

- `next/dist/`
- `next/dist/compiled/`
- `source-map`

Result: no application import uses an internal Next.js module.

The standalone `source-map-js` dependency is transitive through Next's required PostCSS package. It does not import `next/dist/compiled/source-map` and was not removed.

No third-party application dependency was found importing the missing internal path. Removing Next.js itself is neither valid nor necessary.

## Package changes

Pinned the core runtime/tooling versions that were already resolved and peer-compatible:

- `next`: `15.5.22`
- `react`: `19.2.8`
- `react-dom`: `19.2.8`
- `eslint-config-next`: `15.5.22`

Next 15.5.22 declares React and React DOM `^19.0.0` as supported peers, so React 19.2.8 is compatible.

ESLint remains `^9.17.0`, which is accepted by `eslint-config-next` 15.5.22.

## Configuration fix

Changed output tracing from the frontend-only directory:

    outputFileTracingRoot: process.cwd()

to the npm workspace root:

    outputFileTracingRoot: path.join(process.cwd(), "..")

This makes Vercel's serverless trace include hoisted Next dependencies, including `node_modules/next/dist/compiled/source-map`.

## Files modified

- `frontend/next.config.ts`
- `frontend/package.json`
- `package-lock.json`
- `FRONTEND_RUNTIME_FIX_REPORT.md`

## Dependency cleanup performed

- Deleted the previous `package-lock.json`.
- Deleted `frontend/.next`.
- Attempted to delete the repository-level `node_modules` for a fully clean install.
- Windows refused to remove the loaded `@next/swc-win32-x64-msvc` native binary because a live Node process held it open.
- Ran `npm install`; the lockfile was regenerated and the dependency tree was reconciled, but the partial Windows deletion left the local tree without `@next/env`.

The installed Next package does contain:

    node_modules/next/dist/compiled/source-map/source-map.js

and `require.resolve("next/dist/compiled/source-map")` succeeded before the partial native-module cleanup.

## Verification results

Passed:

- No forbidden internal imports in application source.
- Next/React peer-version compatibility verified from installed package metadata.
- `next/dist/compiled/source-map` exists in Next 15.5.22 and exposes `SourceMapConsumer`, `SourceMapGenerator`, and `SourceNode`.
- Production dependency audit reported zero production vulnerabilities.
- The output tracing root now includes the hoisted workspace dependency directory.

Blocked locally:

- `npm run build` currently stops at `Cannot find module '@next/env'` because the Windows-locked, partially removed local `node_modules` tree could not be fully reinstalled after the execution quota was reached.
- `npm run start` cannot be verified until that clean install and build complete.

This local `@next/env` error is separate from the deployed `source-map` tracing defect. A clean Vercel install will not inherit the partially deleted local `node_modules` directory, but local build/start verification must still be completed before declaring the fix fully verified.

## Required final local verification

Stop any running Next.js/Node development server that holds the SWC binary, then run from the repository root:

    Remove-Item -Recurse -Force node_modules
    Remove-Item -Recurse -Force frontend/.next -ErrorAction SilentlyContinue
    npm install
    npm run build
    npm run start

After a successful build, verify the generated API route trace includes the workspace-level Next runtime files and call `/api/predict` through the production server.

## Deployment status

The code-level Vercel packaging root cause is fixed. Final readiness remains pending one clean dependency reinstall plus successful `npm run build` and `npm run start` verification.

