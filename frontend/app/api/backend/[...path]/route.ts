import type { NextRequest } from "next/server";

import { auth } from "@/auth";

type BackendRouteContext = {
  params: Promise<{ path: string[] }>;
};

const FORWARDED_RESPONSE_HEADERS = [
  "cache-control",
  "content-disposition",
  "content-length",
  "content-type",
  "etag",
  "last-modified",
] as const;

async function proxyToBackend(
  request: NextRequest,
  context: BackendRouteContext,
) {
  const session = await auth();
  const userId = session?.user?.id;
  if (!userId) {
    return Response.json({ detail: "Authentication required" }, { status: 401 });
  }

  const backendApiUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";
  const { path } = await context.params;
  const target = new URL(
    `${backendApiUrl.replace(/\/$/, "")}/${path.map(encodeURIComponent).join("/")}`,
  );
  target.search = request.nextUrl.search;

  const headers = new Headers();
  const accept = request.headers.get("accept");
  const contentType = request.headers.get("content-type");
  if (accept) headers.set("Accept", accept);
  if (contentType) headers.set("Content-Type", contentType);
  headers.set("X-User-Id", userId);

  const options: RequestInit & { duplex?: "half" } = {
    method: request.method,
    headers,
    cache: "no-store",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    options.body = request.body;
    options.duplex = "half";
  }

  try {
    const backendResponse = await fetch(target, options);
    const responseHeaders = new Headers();
    for (const name of FORWARDED_RESPONSE_HEADERS) {
      const value = backendResponse.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    return new Response(backendResponse.body, {
      status: backendResponse.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      { detail: "Le service d’analyse est temporairement indisponible." },
      { status: 502 },
    );
  }
}

export const GET = proxyToBackend;
export const POST = proxyToBackend;
export const PUT = proxyToBackend;
export const PATCH = proxyToBackend;
export const DELETE = proxyToBackend;
