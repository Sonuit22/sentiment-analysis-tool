# Audio Endpoint Fix Report

## Why the backend rejected the request

`POST /predict/audio` is intentionally tied to Improved Logistic Regression because its module owns the audio transcript normalization, sentiment hint scoring, and audio-specific post-processing.

The endpoint previously called `registry.ensure_ready()`, which considered the registry ready when any model was loaded. Upload-based training can replace the active registry with only the models selected for that analysis. If that selection omitted Improved Logistic Regression, the registry was non-empty but the required audio model was absent, producing HTTP 422:

    Improved Logistic Regression is not available.

## Supported models

- Text prediction: Naive Bayes, Logistic Regression, Improved Logistic Regression, and SVM.
- Audio prediction: Improved Logistic Regression only.

The audio-specific preprocessing and post-processing remain unchanged. Support was not added to the other models because doing so would change the established audio prediction behavior.

## Files changed

- `backend/service.py`
- `backend/app.py`
- `frontend/lib/api.ts`
- `frontend/components/PredictionWorkbench.tsx`
- `AUDIO_ENDPOINT_FIX_REPORT.md`

## Exact fix

The model registry now records the active dataset split settings and exposes `ensure_model_ready()`. When the audio model was excluded by a prior training-analysis selection, this method deterministically restores only Improved Logistic Regression using the same dataset, split, training function, preprocessing, and random state. Existing loaded models and training-analysis results are left intact.

The endpoint no longer reads the registry's private model dictionary or emits the misleading unavailable-model validation error. It obtains the supported audio model through the registry method and continues through the original transcription, preprocessing, prediction, confidence, and post-processing logic.

The frontend already has no audio model selector: its four-model selector is rendered only for text mode. The audio help text now explicitly states that Improved Logistic Regression is fixed. HTTP error bodies continue to be parsed once, and FastAPI `detail` messages from 422 responses are displayed unchanged. Only browser-level network failures receive a generic availability message; that message no longer incorrectly assumes CORS.

## Verification results

- Forced the registry into the reported state with only Naive Bayes loaded, then submitted a valid WAV multipart request.
- The backend restored Improved Logistic Regression through its unchanged training and preprocessing module.
- `POST /predict/audio` returned HTTP 200 with `positive` sentiment, confidence, probability, class probabilities, inference time, and `model_used: Improved Logistic Regression`.
- A non-WAV multipart request returned HTTP 422 with `{"detail":"Upload a WAV audio file."}`.
- Python compilation completed without errors.
- The Next.js 15 production build passed compilation, linting, TypeScript checking, static generation, and route tracing.
- `git diff --check` completed without whitespace errors.
