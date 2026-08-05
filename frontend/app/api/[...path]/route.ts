import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

const DEFAULT_BACKEND_API_URL = "https://sentiment-analysis-tool-a8nd.onrender.com";

function backendApiUrl(): string {
  const configured = process.env.BACKEND_API_URL?.trim();
  if (!configured) return DEFAULT_BACKEND_API_URL;
  try {
    const url = new URL(configured);
    const loopback = ["localhost", "127.0.0.1", "::1"].includes(url.hostname);
    if (process.env.NODE_ENV === "production" && loopback) {
      console.warn("[api-proxy] Ignoring loopback BACKEND_API_URL in production", {
        configured,
        fallback: DEFAULT_BACKEND_API_URL,
      });
      return DEFAULT_BACKEND_API_URL;
    }
    return url.toString();
  } catch {
    console.error("[api-proxy] Invalid BACKEND_API_URL; using the Render backend", {
      configured,
      fallback: DEFAULT_BACKEND_API_URL,
    });
    return DEFAULT_BACKEND_API_URL;
  }
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const baseUrl = backendApiUrl();
  const target = new URL(path.join("/"), baseUrl.endsWith("/") ? baseUrl : baseUrl + "/");
  target.search = request.nextUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");

  try {
    const response = await fetch(target, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
      cache: "no-store",
    });
    if (!response.ok) {
      console.error("[api-proxy] Backend returned an error", {
        method: request.method,
        target: target.toString(),
        status: response.status,
        detail: (await response.clone().text()).slice(0, 2_000),
      });
    }
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch (error) {
    console.error("[api-proxy] Backend request failed", {
      method: request.method,
      target: target.toString(),
      backendApiUrlConfigured: Boolean(process.env.BACKEND_API_URL),
      error: error instanceof Error
        ? { name: error.name, message: error.message, stack: error.stack, cause: error.cause }
        : error,
    });
    return NextResponse.json(
      { detail: "The analysis service is temporarily unavailable." },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
