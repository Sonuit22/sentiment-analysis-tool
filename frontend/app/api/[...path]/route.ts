import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 60;

const DEFAULT_BACKEND_API_URL = "https://sentiment-analysis-tool-a8nd.onrender.com";
const BODY_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const LOG_BODY_LIMIT = 20_000;

function backendApiUrl(configured: string | undefined): string {
  if (!configured) return DEFAULT_BACKEND_API_URL;
  let url: URL;
  try {
    url = new URL(configured);
  } catch (error) {
    console.warn("[api-proxy] Ignoring invalid BACKEND_API_URL", {
      configured,
      fallback: DEFAULT_BACKEND_API_URL,
      error: errorDetails(error),
    });
    return DEFAULT_BACKEND_API_URL;
  }
  if (!new Set(["http:", "https:"]).has(url.protocol)) {
    console.warn("[api-proxy] Ignoring unsupported BACKEND_API_URL protocol", {
      configured,
      fallback: DEFAULT_BACKEND_API_URL,
    });
    return DEFAULT_BACKEND_API_URL;
  }
  const loopback = ["localhost", "127.0.0.1", "::1"].includes(url.hostname);
  if (process.env.VERCEL === "1" && loopback) {
    console.warn("[api-proxy] Ignoring loopback BACKEND_API_URL in production", {
      configured,
      fallback: DEFAULT_BACKEND_API_URL,
    });
    return DEFAULT_BACKEND_API_URL;
  }
  return url.toString();
}

function errorDetails(error: unknown) {
  return error instanceof Error
    ? {
        name: error.name,
        message: error.message,
        stack: error.stack ?? "No stack trace available",
        cause: error.cause,
      }
    : {
        name: "NonErrorException",
        message: String(error),
        stack: "No stack trace available",
      };
}

function bounded(value: string): string {
  return value.length > LOG_BODY_LIMIT
    ? value.slice(0, LOG_BODY_LIMIT) + `... [truncated ${value.length - LOG_BODY_LIMIT} characters]`
    : value;
}

async function requestBodyForLog(body: ArrayBuffer | undefined, contentType: string | null) {
  if (!body) return null;
  if (contentType?.includes("application/json")) {
    const decoded = new TextDecoder().decode(body);
    let loggedBody: unknown = bounded(decoded);
    try {
      const parsed = JSON.parse(decoded) as unknown;
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        loggedBody = Object.fromEntries(
          Object.entries(parsed).map(([name, value]) => [
            name,
            name === "text" && typeof value === "string"
              ? { redacted: true, characters: value.length }
              : value,
          ]),
        );
      }
    } catch {
      // Invalid JSON is bounded and logged so the backend validation can be diagnosed.
    }
    return {
      contentType,
      byteLength: body.byteLength,
      body: loggedBody,
    };
  }
  if (contentType?.includes("multipart/form-data")) {
    try {
      const copy = body.slice(0);
      const form = await new Request("http://proxy-body.local", {
        method: "POST",
        headers: { "content-type": contentType },
        body: copy,
      }).formData();
      return {
        contentType,
        byteLength: body.byteLength,
        fields: Array.from(form.entries()).map(([name, value]) =>
          typeof value === "string"
            ? { name, value: bounded(value) }
            : { name, fileName: value.name, size: value.size, type: value.type },
        ),
      };
    } catch (error) {
      console.error("[api-proxy] Failed to inspect multipart request body", errorDetails(error));
      return { contentType, byteLength: body.byteLength, body: "Multipart body could not be inspected" };
    }
  }
  return {
    contentType,
    byteLength: body.byteLength,
    body: bounded(new TextDecoder().decode(body)),
  };
}

function forwardedHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  for (const name of ["accept", "authorization", "content-type", "x-request-id"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  return headers;
}

function originalBackendResponse(response: Response): Response {
  const headers = new Headers(response.headers);
  for (const name of [
    "connection",
    "content-encoding",
    "content-length",
    "keep-alive",
    "transfer-encoding",
  ]) {
    headers.delete(name);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const configuredBackendUrl = process.env.BACKEND_API_URL?.trim();
  let targetUrl = "not-resolved";
  try {
    const { path } = await context.params;
    const baseUrl = backendApiUrl(configuredBackendUrl);
    const encodedPath = path.map((segment) => encodeURIComponent(segment)).join("/");
    const target = new URL(encodedPath, baseUrl.endsWith("/") ? baseUrl : baseUrl + "/");
    target.search = request.nextUrl.search;
    targetUrl = target.toString();

    // Read the incoming stream exactly once. The same buffer is logged and forwarded.
    const requestBody = BODY_METHODS.has(request.method)
      ? await request.arrayBuffer()
      : undefined;
    const contentType = request.headers.get("content-type");
    const bodyLog = await requestBodyForLog(requestBody, contentType);

    console.info("[api-proxy] Forwarding request", {
      backendApiUrlEnvironmentValue: configuredBackendUrl ?? null,
      backendApiUrlAvailable: Boolean(configuredBackendUrl),
      resolvedBackendApiUrl: baseUrl,
      targetUrl,
      method: request.method,
      requestBody: bodyLog,
    });

    const response = await fetch(target, {
      method: request.method,
      headers: forwardedHeaders(request),
      body: requestBody,
      cache: "no-store",
    });

    let responseBody: string | undefined;
    if (!response.ok) {
      try {
        responseBody = bounded(await response.clone().text());
      } catch (error) {
        console.error("[api-proxy] Failed to inspect backend error response", {
          targetUrl,
          method: request.method,
          status: response.status,
          error: errorDetails(error),
        });
      }
    }
    console.info("[api-proxy] Backend response", {
      targetUrl,
      method: request.method,
      status: response.status,
      statusText: response.statusText,
      ...(responseBody === undefined ? {} : { responseBody }),
    });

    // Preserve the backend status and unconsumed body. Transport headers are removed
    // because Node fetch has already decoded the upstream response stream.
    return originalBackendResponse(response);
  } catch (error) {
    const details = errorDetails(error);
    console.error("[api-proxy] Proxy execution failed", {
      backendApiUrlEnvironmentValue: configuredBackendUrl ?? null,
      backendApiUrlAvailable: Boolean(configuredBackendUrl),
      targetUrl,
      method: request.method,
      error: details,
    });
    return Response.json(
      { detail: `API proxy failed: ${details.message}` },
      { status: 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
