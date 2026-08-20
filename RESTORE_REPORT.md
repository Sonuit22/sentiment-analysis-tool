# Stable Frontend Restoration Report

## Summary

The frontend API integration has been restored to the last known stable request flow. Naive Bayes and SVM requests again pass through the Next.js API proxy to the deployed FastAPI service, backend validation messages remain readable, and HTML error documents are rejected before they can be displayed in the prediction error box.

Deployment configuration was not changed.

## What was reverted

### `frontend/app/api/[...path]/route.ts`

- Restored the previous backend URL resolution behavior.
- Restored the previous request logging and upstream response inspection behavior.
- Preserved the single-read `arrayBuffer()` forwarding path and the original backend status, headers, and response body.
- Preserved the existing Render fallback when a production environment contains a loopback backend URL.

### `frontend/lib/api.ts`

- Removed the recently introduced automatic proxy retry wrapper.
- Restored direct, single-request parsing for prediction and read-only analysis endpoints.
- Restored training dataset uploads through the Next.js API proxy.
- Preserved the exact frontend-to-backend model mapping:
  - `nb` -> `Naive Bayes`
  - `svm` -> `SVM`
  - `logistic` -> `Logistic Regression`
  - `improved` -> `Improved Logistic Regression`
- Added a narrow response safety check: `text/html` and HTML document payloads are converted to a readable error message and are never returned to the prediction UI.
- Preserved FastAPI `detail` messages, including HTTP 422 validation responses, as readable UI errors.

## Why it was reverted

The latest request-flow changes moved away from the previously working single-request behavior and changed proxy response handling. When the Next.js runtime returned its HTML 500 page, the client treated the response body as ordinary text and displayed the entire document. Restoring the stable flow reduces the change surface, while the HTML guard fixes the unsafe rendering behavior at the response boundary.

## Verification

- `npm run build`: passed with Next.js 15.5.22. The dynamic `/api/[...path]` route was included in the production build.
- `npm run start`: passed.
- Naive Bayes through `http://127.0.0.1:3000/api/predict` to the deployed Render backend: HTTP 200, positive sentiment, `model_used: "Naive Bayes"`.
- SVM through `http://127.0.0.1:3000/api/predict` to the deployed Render backend: HTTP 200, positive sentiment, `model_used: "SVM"`.
- Simulated Next.js HTML 500 response: passed; the exposed message was `The application server returned HTTP 500. Please try again.` and contained no HTML.
- Simulated FastAPI HTTP 422 JSON response: passed; the backend `detail` message was preserved verbatim.
- `git diff --check`: passed.

## Deliberately excluded from this restoration

Logistic Regression, Improved Logistic Regression, and audio prediction fixes are not included in the restoration changes. Their follow-up work is isolated on the separate `codex/logistic-improved-audio-fixes` branch so it cannot be mixed into the stable restoration commit.
