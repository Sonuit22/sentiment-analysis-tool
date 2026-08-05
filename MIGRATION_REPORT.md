# Migration report

## Outcome

The Streamlit research interface was migrated into a production-oriented monorepo with a Next.js 15 TypeScript frontend and FastAPI backend. Every existing user-facing capability was retained and reorganized into ten dedicated product pages.

## Feature mapping

| Streamlit capability | Production destination |
| --- | --- |
| Home overview and workflow | `frontend/app/page.tsx` |
| Sentiment fundamentals | `frontend/app/about/page.tsx` |
| Custom text prediction | `frontend/app/prediction/page.tsx` |
| WAV transcription and audio sentiment | Prediction workbench + `POST /predict/audio` |
| Model descriptions | `frontend/app/model-details/page.tsx` |
| Bundled dataset experiment | Training Analysis + `GET /training-analysis` |
| CSV, JSON, XLSX, and XLS upload | Training Analysis + `POST /training-analysis/upload` |
| Model selection, split, and seed controls | Training Analysis experiment controls |
| Dataset overview and class distribution | Training Analysis metrics and Recharts pie chart |
| Accuracy/F1 comparison | Training Analysis and Model Comparison Recharts |
| Training time comparison | Training Analysis Recharts |
| Leaderboard | Training Analysis and Model Comparison tables |
| Confusion matrices | Training Analysis evaluation details |
| Classification reports | Training Analysis evaluation details |
| Sample classifications | Training Analysis evaluation details |
| Positive/negative/neutral word clouds | Training Analysis word-cloud cards |
| Keyword and sentiment business analysis | Business Insights dashboard |
| Use-case content | `frontend/app/use-cases/page.tsx` |
| Research explanation | Research Methodology page |
| Technical/deployment reference | Developer page |

## Backend changes

- Created a typed FastAPI application in `backend/app.py`.
- Added the required `POST /predict` and `GET /health` routes.
- Added training analysis, dataset upload, model comparison, business insight, and audio routes to preserve the full Streamlit workflow.
- Added Pydantic request and response models.
- Added configurable CORS through `ALLOWED_ORIGINS`.
- Added a process-safe, lazy model registry that caches the deterministic experiment during a warm backend instance.
- Returned sentiment, confidence, probability, per-class probabilities when available, inference time, and model name.
- Added structured evaluation payloads for Recharts and React tables.
- Kept audio post-processing in the original Improved Logistic Regression module.

## Model integrity

The files originally under `models/` and `utils/` were moved into `backend/models/` and `backend/utils/`. The algorithm source, hyperparameters, feature extraction, preprocessing, anchor examples, training functions, prediction functions, and audio post-processing were not changed. Only import statements were made safe for both monorepo imports and a backend-root Vercel deployment.

The root `tokenizer.pkl` was moved to `backend/models/tokenizer.pkl` locally. It remains ignored because it is an unused Keras tokenizer and is not referenced by any classical model. Repository history contains no persisted fitted classifier. Consequently, the service must initialize the same deterministic bundled-data training workflow on each cold serverless instance; it does not alter or tune the models.

## Frontend changes

- Built ten Next.js App Router pages in TypeScript.
- Added responsive fixed/sidebar navigation with a mobile drawer.
- Added local dark/light theme switching.
- Added an animated hero with reduced-motion support.
- Added reusable cards, metrics, loading states, errors, empty states, tables, and mobile layouts.
- Added Recharts for sentiment distribution, accuracy, weighted F1, training time, and keyword analysis.
- Added live text and WAV prediction workflows.
- Added upload-driven training controls for model subset, test split, and random seed.
- Added complete evaluation detail views and word clouds.
- Added Next.js metadata, 404 handling, route error handling, and a same-origin API proxy.
- Used server components by default and client components only for interactive or charting surfaces.

## Deployment changes

- Added root npm workspace scripts and a reproducible `package-lock.json`.
- Added a root `vercel.json` for the frontend project.
- Added `backend/vercel.json` and a Vercel-detectable FastAPI `app.py`.
- Added `.python-version` with Python 3.12 for a supported production runtime.
- Split direct Python runtime dependencies into `backend/requirements.txt`; the root `requirements.txt` delegates to it.
- Added `frontend/.env.example` and documented `BACKEND_API_URL` and `ALLOWED_ORIGINS`.
- Updated `.gitignore` for Next.js, Vercel, Python, secrets, IDEs, logs, caches, datasets, and model artifacts.
- Added an MIT license and replaced the README with production setup, API, and deployment guidance.

## Files archived and cleaned

- Legacy Streamlit entry point: `app.py` -> `legacy_streamlit/app.py`
- Legacy Streamlit page wrappers: `pages/` -> `legacy_streamlit/pages/`
- Local verification environment: `.cloud-verify/`
- Local Python virtual environment: `.venv/`
- Python bytecode caches, Next.js build output, and `node_modules/`
- Generated Next.js build output and local dependency directories are ignored rather than versioned

The local `.agents/` directory could not be removed because the host denied access. It is not tracked or included in the public release.

## Files moved

- `models/` -> `backend/models/`
- `utils/` -> `backend/utils/`
- Local ignored `tokenizer.pkl` -> `backend/models/tokenizer.pkl`
- `app.py` and `pages/` -> `legacy_streamlit/` as a recoverable research reference

## Verification

- Python bytecode compilation completed for the backend.
- Health response returned the expected service metadata and four available models.
- Improved Logistic Regression returned a positive prediction with confidence, probabilities, inference time, and model provenance for a positive smoke-test sentence.
- The bundled experiment returned four leaderboard entries over 544 rows.
- Business insight generation returned sentiment themes and keyword summaries.
- Next.js 15 production compilation, linting, type checking, static generation, and route tracing completed successfully.
- `npm audit` reported zero known vulnerabilities after dependency resolution.

## Deployment issues found

1. No persisted fitted classifier exists in the repository. The Streamlit app trained dynamically, despite language in the project implying trained models. The API preserves this behavior with lazy per-instance caching.
2. Serverless cold starts will include scikit-learn model initialization and may be noticeable.
3. Vercel deploys the frontend and FastAPI backend as separate related projects. `BACKEND_API_URL` must be set on the frontend.
4. Google Speech Recognition is an external service and can fail in offline or restricted environments.
5. Uploaded experiments live only in the current backend process. A serverless instance is not durable session storage.
6. The local Node.js 20.18 runtime is slightly below one optional ESLint package's preferred 20.19 engine, although the production build and type checks pass. Use Node.js 20.19+ in development.

## Remaining recommendations

- Persist approved fitted pipelines in durable object storage if cold-start latency is unacceptable. This requires an explicit model-artifact release process because no current artifacts exist.
- Move long-running upload experiments to a durable job platform if datasets will exceed small research samples; Vercel functions have execution limits.
- Add a managed datastore or signed object storage if experiment history must survive deployments.
- Add unit tests with frozen prediction fixtures before future model changes.
- Add browser end-to-end tests for navigation, uploads, text prediction, theme switching, and API failure states.
- Configure production monitoring, rate limiting, request-size limits, and analytics.
- Replace placeholder repository ownership details in public metadata if a named maintainer or organization should be shown.
