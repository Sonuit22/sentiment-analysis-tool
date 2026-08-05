# Frontend API Compatibility Report

## Root cause

The frontend used short internal model IDs such as `improved`, while the FastAPI `PredictRequest` schema accepts only these exact literals:

- `Naive Bayes`
- `Logistic Regression`
- `Improved Logistic Regression`
- `SVM`

Because `improved` is not a member of that Pydantic `Literal` union, FastAPI rejected the request during body validation and returned HTTP 422 before prediction logic ran.

## Request locations audited

Prediction request bodies are constructed in `frontend/lib/api.ts`:

- `predictSentiment` creates the JSON body for `POST /api/predict`.
- `predictAudio` creates multipart form data for `POST /api/predict/audio`.

No other frontend source file constructs a text-prediction JSON request. The audio endpoint accepts only a WAV file and chooses Improved Logistic Regression on the backend, so no model field should be added to its multipart request.

## Files modified

- `frontend/lib/types.ts`
- `frontend/lib/api.ts`
- `frontend/components/PredictionWorkbench.tsx`
- `FRONTEND_API_COMPATIBILITY_REPORT.md`

## Fix applied

Added a typed API-boundary mapping:

- `improved` -> `Improved Logistic Regression`
- `logistic` -> `Logistic Regression`
- `nb` -> `Naive Bayes`
- `svm` -> `SVM`

The dropdown keeps short internal IDs as option values but continues to display the same user-friendly model names. Immediately before JSON serialization, `predictSentiment` converts the selected ID to the exact backend literal.

The API helper also accepts an already-canonical backend model name, preserving compatibility with any existing callers that already supply exact literals.

## Request before

    {
      "text": "This product is excellent.",
      "model": "improved"
    }

Live deployed-backend result: HTTP 422 with a Pydantic literal-validation error for `model`.

## Request after

    {
      "text": "This product is excellent.",
      "model": "Improved Logistic Regression"
    }

Live deployed-backend result: HTTP 200 with `sentiment`, `confidence`, `probability`, per-class `probabilities`, `inference_time_ms`, and `model_used`.

## FastAPI schema compatibility

The corrected text request contains exactly the required fields:

- `text`: non-empty string
- `model`: one of the four accepted literals

The audio request remains multipart form data containing only `file`, which matches `POST /predict/audio`.

## Deployment readiness

The frontend request contract is compatible with the deployed Render backend. Redeploy the frontend so the corrected API-boundary mapping replaces the stale client bundle that sends internal IDs directly.

