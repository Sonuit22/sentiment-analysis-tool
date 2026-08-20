# Production Deployment Audit

## Scope

This audit traced every application request across the Next.js 15 frontend, the Next.js catch-all API proxy, and the FastAPI service deployed on Render. It covered text prediction, audio, uploaded training experiments, analytics payloads, CORS, error propagation, model initialization, dependencies, local production builds, and the currently public deployments.

Production services:

- Frontend: `https://sentiment-analysis-tool-frontend.vercel.app`
- Backend: `https://sentiment-analysis-tool-a8nd.onrender.com`

## Issues found and fixes

### 1. Vercel API routes are serving HTTP 500 from the old deployment

The currently public Vercel revision returns the default static Next.js HTML 500 page for `/api/predict`, even though the same request succeeds directly on Render. All ten public page routes return HTTP 200, so the failure is isolated to the deployed server runtime.

The repository still had `outputFileTracingRoot` pointed above the configured `frontend` Root Directory. It is now scoped to `process.cwd()`, keeping traced server files inside the Vercel project boundary. The old experimental configuration and its build warning were removed. The clean Next.js production build emits the dynamic `/api/[...path]` route correctly.

### 2. Local production proxy incorrectly rejected the local backend

The proxy treated every `NODE_ENV=production` process as Vercel and replaced `http://127.0.0.1:8000` with Render. That broke legitimate `npm run start` integration testing. Loopback protection now applies only when `VERCEL=1`, so Vercel cannot call a nonexistent local backend while a local production server can.

### 3. Invalid backend environment values bypassed the documented fallback

An invalid `BACKEND_API_URL` previously threw during URL construction. The proxy now validates the URL and protocol, logs the configuration error, and uses the production Render fallback. A loopback URL on Vercel also uses that fallback.

### 4. Proxy response inspection delayed streaming

The proxy awaited a full clone of every backend response before returning it. Successful responses now stream immediately. Only non-success responses are cloned for bounded diagnostic logging, while the original status, headers, and unconsumed body are returned unchanged.

### 5. Proxy logs exposed prediction text

JSON request logging now records the model and character count while redacting the submitted text. Multipart logging records field names and file metadata, not file contents. Backend error bodies remain available for diagnostics.

### 6. Render cold starts caused intermittent frontend prediction failures

The browser client now retries one time only for transient proxy statuses 502, 503, and 504 or a transport-level network failure. HTTP 400/413/422 validation responses are never retried or replaced; their FastAPI `detail` messages are shown to the user.

### 7. Vercel request-size limits affected uploads

Audio already bypassed the proxy. Dataset uploads now also go directly from the browser to Render. Text prediction and read-only analytics continue through the same-origin Next.js proxy. The backend enforces explicit 10 MB dataset and 25 MB WAV limits and returns HTTP 413 with a useful message.

### 8. Uploaded training experiments mutated production inference state

`POST /training-analysis/upload` previously trained into the global singleton registry used by `/predict` and `/predict/audio`. Selecting only one model could remove the improved audio model and made results depend on a prior user's training request.

Every upload now runs in an isolated `ModelRegistry`. Its metrics, leaderboard, confusion matrix, classification report, samples, and word clouds are returned to that request, while the four production inference models and bundled analytics remain unchanged.

### 9. Model initialization depended on lazy process state

All four deterministic model pipelines now initialize during FastAPI lifespan startup. Startup fails loudly if Improved Logistic Regression is unavailable. Both text and audio use the same singleton registry and the same `ensure_model_ready()` acquisition path. Prediction never depends on opening Training Analysis first.

The repository contains model implementations rather than persisted trained classifier artifacts. Automatic deterministic startup initialization is therefore the faithful production behavior and requires no manual training.

### 10. Blocking work ran on the async event loop

Dataset parsing/training and Google transcription could block unrelated requests on a single Render worker. Both are now dispatched through FastAPI's worker threadpool. Google transcription also has a configurable 20-second operation timeout. ML preprocessing, feature extraction, classifiers, and audio post-processing were not changed.

### 11. Dataset parser failures could become generic HTTP 500 responses

Corrupt supported files are normalized to HTTP 422 with the real parsing message. Unsupported formats, empty files, insufficient class data, and invalid model selections also return precise HTTP 422 responses. Upload-size violations return 413, speech-service failures return 503, and unexpected server faults remain 500 with tracebacks in backend logs.

### 12. CORS was broader than required and the live service has stale settings

The source now allows only:

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `https://sentiment-analysis-tool-frontend.vercel.app`

The wildcard Vercel regex and wildcard request headers were removed. Swagger is served from Render's own origin and does not require a CORS entry. The currently deployed Render service still rejects the exact production frontend origin, proving the new revision and/or exact `ALLOWED_ORIGINS` value has not been activated there.

### 13. Uploaded-analysis tab state could display the wrong selection

When an upload evaluated a subset of models, the active evaluation tab could refer to a model absent from the new payload. The component now selects the first available evaluation automatically.

### 14. Linting and deployment documentation were stale

The deprecated interactive `next lint` command was replaced by the ESLint CLI with a committed flat configuration. The unused backend Vercel configuration was removed because the backend is hosted on Render. The README and Developer page now describe the actual Vercel + Render architecture, exact roots, commands, URLs, environment variables, upload flow, and automatic model initialization.

## Files modified

- `backend/app.py` — startup loading, exact CORS, isolated/threaded uploads, upload limits, threaded transcription, timeout, and error handling.
- `backend/service.py` — safe dataset parsing while preserving the existing model implementations.
- `backend/.env.example` — production runtime settings and limits.
- `backend/vercel.json` — removed because Render hosts the backend.
- `frontend/app/api/[...path]/route.ts` — validated fallback, Vercel-only loopback guard, one-read body forwarding, streaming responses, preserved errors, and redacted logs.
- `frontend/lib/api.ts` — exact model mapping, transient proxy retry, direct audio/dataset uploads, and backend error propagation.
- `frontend/next.config.ts` — Vercel-root-compatible output tracing and removal of experimental warnings.
- `frontend/eslint.config.mjs` and `frontend/package.json` — deterministic non-interactive linting.
- `frontend/components/TrainingDashboard.tsx` — valid active model after subset uploads.
- `frontend/components/PredictionWorkbench.tsx` — fixed audio-model copy and unused import cleanup.
- `frontend/app/developer/page.tsx` — accurate Render/Vercel architecture and API example.
- `package.json` and `package-lock.json` — Node runtime requirement and dependency lock refresh.
- `README.md` — corrected production deployment instructions.

## Dependency audit

Runtime imports match `backend/requirements.txt`:

- FastAPI, Uvicorn, and Pydantic
- python-multipart
- NumPy, pandas, and scikit-learn
- openpyxl for XLSX
- xlrd for legacy XLS
- SpeechRecognition

The tokenizer artifact is optional and is not used by the classical TF-IDF pipelines. The frontend dependency tree is valid, `npm audit` reports zero vulnerabilities, and the supported Node.js floor is 20.19.

## Local verification checklist

- [x] FastAPI startup loaded Naive Bayes, Logistic Regression, Improved Logistic Regression, and SVM.
- [x] `GET /health` returned models ready.
- [x] `POST /predict` returned HTTP 200 for all four exact model literals.
- [x] Invalid internal model ID returned FastAPI HTTP 422 details.
- [x] `POST /predict/audio` returned a complete prediction using a mocked successful Google transcript.
- [x] Non-WAV audio returned the exact HTTP 422 message.
- [x] CSV upload returned dataset metrics, charts data, leaderboard, evaluation, confusion matrix, classification report, samples, and word clouds.
- [x] JSON upload passed.
- [x] XLSX upload passed.
- [x] Genuine legacy XLS upload passed using xlrd.
- [x] Corrupt spreadsheet returned HTTP 422.
- [x] Oversized dataset returned HTTP 413.
- [x] Upload experiments did not change bundled inference models or analytics.
- [x] Model comparison and business insights returned complete payloads.
- [x] Exact production and localhost CORS preflights passed; an untrusted Vercel origin failed.
- [x] Next.js proxy forwarded JSON and multipart bodies once.
- [x] Proxy preserved FastAPI HTTP 422 JSON unchanged.
- [x] All four models returned HTTP 200 through the local production Next.js proxy.
- [x] All ten frontend routes returned HTTP 200 from `npm run start`.
- [x] ESLint passed with zero warnings.
- [x] Python compilation passed.
- [x] Next.js 15 production build passed compilation, linting, type checking, static generation, and route tracing without the prior experimental/root warning.

## Public deployment verification

Verified on 21 August 2026 before the new host deployments were activated:

- [x] All ten public Vercel page routes return HTTP 200.
- [x] All four model literals return HTTP 200 directly from Render.
- [x] Render health, training analysis, model comparison, and business insights return HTTP 200.
- [x] A generated spoken WAV returned HTTP 200 from Render with positive sentiment, confidence, probabilities, transcript, inference time, and `model_used: Improved Logistic Regression`.
- [ ] The public Vercel `/api/predict` route currently returns its old default HTML HTTP 500 page for all four models.
- [ ] Render currently returns HTTP 400 to the exact production-origin audio preflight.
- [ ] Live CSV/JSON/XLS/XLSX uploads were not run against the old backend because that revision mutates the production inference registry. The isolated implementation passed all local format tests and should be tested only after Render deploys the audited revision.

## Remaining deployment actions

The audited source revision is on GitHub `main`, but no new Vercel deployment record appeared and Render continued serving its previous CORS policy during verification. Both dashboards require authentication and were signed out in the available browser sessions.

After signing in:

1. Vercel: deploy the latest `main` revision with Root Directory `frontend`, Framework `Next.js`, and both backend URL variables set to the Render base URL.
2. Render: deploy the latest `main` revision with Root Directory `backend`, the documented Uvicorn start command, and `ALLOWED_ORIGINS` set exactly as shown in `backend/.env.example`.
3. Repeat the unchecked public verification items above.

No remaining local code, model, schema, dependency, build, or request-format defect is known. The only current blockers are the two authenticated host deployments.
