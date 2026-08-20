# Frontend Runtime Fix Report

## Root cause

No application source, API proxy, custom logger, error handler, build plugin, or Next.js configuration directly imports an internal Next.js module.

The only runtime import of the missing module is shipped by Next.js 15.5.22 itself:

```js
// node_modules/next/dist/server/patch-error-inspect.js
const _sourcemap = require("next/dist/compiled/source-map");
```

The repository previously declared `frontend` as an npm workspace. npm therefore installed and hoisted Next.js into the repository-level `node_modules`, while Vercel treated `frontend` as the project root and `outputFileTracingRoot` was limited to `process.cwd()` (`frontend`). The build could find the hoisted framework package, but the serverless function trace did not package all files from that parent installation. When the API route initialized Next's server error-inspection runtime, Node could not resolve `next/dist/compiled/source-map`, so the function crashed before user code could return a response.

## Audit results

Searched all frontend source, configuration, package manifests, lockfiles, generated server output, and installed dependencies for:

- `next/dist/*`
- `next/server.edge`
- `next/dist/compiled/*`
- `source-map`
- `source-map-js`
- `@jridgewell/source-map`
- `next/dist/compiled/source-map`

Results:

- Application source: no forbidden imports.
- `frontend/app/api/[...path]/route.ts`: no forbidden imports.
- Custom logging/error handling: no forbidden imports.
- `frontend/next.config.ts`: no webpack or build plugin imports.
- `vercel.json`: no frontend Vercel configuration file exists; no rewrite or bundling rule caused the failure.
- `source-map` and `@jridgewell/source-map`: not installed.
- `source-map-js`: transitive dependency of Next's required PostCSS package. It does not import `next/dist/compiled/source-map` and is not the failing dependency.
- `next/dist/compiled/source-map`: bundled inside the official Next.js package and imported by `next/dist/server/patch-error-inspect.js`.

## Exact fix

The frontend is now a self-contained npm project instead of a hoisted workspace:

1. Removed the root `workspaces: ["frontend"]` declaration.
2. Updated root convenience scripts to use `npm --prefix frontend`.
3. Added `frontend/package-lock.json` generated from `frontend/package.json`.
4. Installed all frontend dependencies in `frontend/node_modules`.
5. Kept `outputFileTracingRoot: process.cwd()` so Vercel traces only the self-contained frontend project and cannot select a parent lockfile.
6. Pinned the Vercel project runtime to Node `>=20.19` through `frontend/package.json`.
7. Removed stale `.next`, root-hoisted dependencies, and the old partial frontend installation before the clean install.

After the fix, these files are in the same project boundary:

```text
frontend/node_modules/next/dist/server/patch-error-inspect.js
frontend/node_modules/next/dist/compiled/source-map/source-map.js
frontend/package-lock.json
```

No internal Next.js import was copied, replaced, aliased, or added to application code.

## Files modified

- `package.json`
- `package-lock.json`
- `frontend/package.json`
- `frontend/package-lock.json` (added)
- `frontend/next.config.ts` (documented and retained the correct frontend-local trace root)
- `FRONTEND_RUNTIME_FIX_REPORT.md`

No UI component, API proxy implementation, backend source, or deployment setting was changed.

## Verification

- Clean `npm install`: passed.
- Next.js version: `15.5.22`.
- React and React DOM versions: `19.2.8`.
- `require.resolve("next/dist/compiled/source-map")`: resolves from `frontend/node_modules`.
- Production `npm run build`: passed without workspace-root warnings.
- Dynamic `/api/[...path]` function: included in the production build.
- Production `npm run start`: passed.
- `POST http://127.0.0.1:3000/api/predict`: HTTP 200 through the proxy to Render.
- `POST http://127.0.0.1:3000/api/predict/audio`: HTTP 200 through the proxy to Render using the public SpeechRecognition `english.wav` fixture.
- Both proxy responses preserved the backend JSON response.
- No `Cannot find module 'next/dist/compiled/source-map'` error occurred.

## Why Vercel reported a successful build

The build environment could resolve the parent-hoisted Next.js installation, so compilation completed. Vercel's runtime function package is produced from output-file tracing with `frontend` as its root. The dependency existed during compilation but was outside the function's effective package boundary, producing a deployment that was marked Ready but failed only when the API function loaded at runtime.
