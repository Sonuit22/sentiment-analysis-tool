# Next.js API Proxy Fix Report

## Problem

The deployed `/api/predict` route returned Next.js's default HTML 500 page. That response showed that an exception escaped from the Next.js route handler before a FastAPI response was returned.

## Root cause

The previous proxy performed several failure-prone operations before its diagnostic `try` block:

- resolving route parameters
- resolving and parsing `BACKEND_API_URL`
- constructing the target URL
- constructing forwarded headers

An exception in any of those steps bypassed proxy logging and produced Next.js's generic HTML 500 page. The previous catch also replaced caught failures with a generic service-unavailable message, hiding the underlying exception.

The response path also rebuilt an upstream stream with partial headers. During verification, returning the upstream response completely unchanged was found to preserve upstream transport headers after Node had decoded the response body, corrupting downstream JSON. The final implementation preserves the original backend status, status text, headers, and unconsumed body while removing only hop-by-hop/compression transport headers that must be regenerated for the client response.

## File modified

- `frontend/app/api/[...path]/route.ts`
- `API_PROXY_FIX_REPORT.md`

No UI, model, preprocessing, FastAPI schema, or prediction logic was changed.

## Fixes applied

### Server runtime and environment

- Explicitly configured `runtime = "nodejs"`.
- Reads `process.env.BACKEND_API_URL` at request time.
- Logs the environment value and whether it is available.
- Retains `https://sentiment-analysis-tool-a8nd.onrender.com` as the production-safe default.
- Rejects loopback backend URLs in production.
- Invalid URL parsing now reaches the outer traced exception handler rather than being silently hidden.

The production-server test set `BACKEND_API_URL` at process runtime. Proxy logs confirmed:

    backendApiUrlEnvironmentValue: https://sentiment-analysis-tool-a8nd.onrender.com
    backendApiUrlAvailable: true

Vercel must define this variable for the Production environment and redeploy after changing it.

### Request logging

Every proxied request now logs:

- configured and resolved backend URL
- complete target URL
- HTTP method
- request content type and byte length
- bounded JSON/text body
- multipart field names, string values, filenames, MIME types, and file sizes

Binary file contents are not printed, preventing audio and dataset logs from becoming unsafe or unusably large.

### Response logging

The proxy clones the backend response only for logging and records:

- target URL
- request method
- backend response status and status text
- bounded backend response body

The original response body remains unconsumed for the browser.

### Exception logging

All environment resolution, parameter handling, URL construction, body reading, request forwarding, and response handling now run inside one traced block. Every caught exception logs its name, message, stack trace, cause, method, target URL, and environment state.

Instead of an HTML 500 or generic hidden error, a proxy failure returns JSON with HTTP 502 and the actual exception message:

    { "detail": "API proxy failed: <exception message>" }

### Header forwarding

Only safe request headers are forwarded:

- `accept`
- `authorization`
- `content-type`
- `x-request-id`

The multipart `content-type` boundary is preserved. Host, content length, connection, compression, and other hop-by-hop transport headers are not forwarded.

### Body handling

The incoming request stream is read exactly once:

    const requestBody = await request.arrayBuffer()

That same buffer is forwarded to Render. Logging uses either the buffer directly for JSON or `body.slice(0)` for multipart inspection. The original `NextRequest` body is never read a second time.

GET and HEAD-style requests do not receive a body. JSON and multipart requests preserve their original bytes and content type.

### Backend response forwarding

The proxy returns the original backend status, status text, application headers, and unconsumed body. It strips only these transport headers before constructing the downstream response:

- `connection`
- `content-encoding`
- `content-length`
- `keep-alive`
- `transfer-encoding`

This avoids double compression, invalid lengths, and chunk-boundary corruption while preserving the FastAPI response instead of translating or throwing it.

## Verification

The Next.js 15 production build passed compilation, linting, TypeScript validation, page generation, and route generation.

The built production proxy was started with the Render URL supplied through `process.env.BACKEND_API_URL` and tested end-to-end:

### JSON prediction

Request through `POST /api/predict`:

    {
      "text": "This product is excellent and dependable.",
      "model": "Improved Logistic Regression"
    }

Result: HTTP 200 with valid parseable JSON, positive sentiment, confidence, probabilities, inference time, and the selected model.

### Multipart training upload

Request through `POST /api/training-analysis/upload` contained a real CSV plus model, test-size, and random-state form fields.

Result: HTTP 200 with 15 parsed rows and a completed model evaluation. Logs showed the multipart boundary, byte length, and parsed form field/file metadata.

### Multipart audio prediction

Request through `POST /api/predict/audio` contained a valid silent WAV.

Result: FastAPI's original HTTP 422 JSON response, `Speech could not be understood.` This is the expected result for silence and proves the multipart body reached Render intact.

### Logging verification

For all three requests, server logs contained:

- runtime `BACKEND_API_URL`
- resolved Render target URL
- HTTP method
- request body or multipart metadata
- backend response status
- backend response body

An invalid-runtime-configuration test set `BACKEND_API_URL` to `not-a-valid-url`. The route returned HTTP 502 with `{"detail":"API proxy failed: Invalid URL"}` and the server log contained the proxy failure marker, stack field, and `backendApiUrl` stack frame. It did not return an HTML 500 page.

## Deployment readiness

The proxy is ready for Vercel redeployment. Configure this Production environment variable before redeploying:

    BACKEND_API_URL=https://sentiment-analysis-tool-a8nd.onrender.com

After deployment, inspect the Vercel Function logs for `[api-proxy] Forwarding request`, `[api-proxy] Backend response`, or `[api-proxy] Proxy execution failed`. Any future proxy exception will include a full server-side stack trace and return JSON rather than the default Next.js HTML 500 page.
