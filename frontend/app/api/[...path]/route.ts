import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const baseUrl = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
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
