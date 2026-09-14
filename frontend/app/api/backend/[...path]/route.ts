import type { NextRequest } from "next/server";

import { createClient } from "@/lib/supabase/server";

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
  const supabase = await createClient();
  const { data: claimsData, error: claimsError } = await supabase.auth.getClaims();
  const { data: sessionData } = await supabase.auth.getSession();
  const accessToken = sessionData.session?.access_token;
  if (claimsError || !claimsData?.claims?.sub || !accessToken) {
    return Response.json({ detail: "Authentication required" }, { status: 401 });
  }

  const configuredBackendApiUrl = process.env.BACKEND_API_URL?.trim();
  const backendProxySecret = process.env.BACKEND_PROXY_SECRET?.trim();
  if (
    process.env.NODE_ENV === "production" &&
    (!configuredBackendApiUrl || !backendProxySecret)
  ) {
    return Response.json(
      { detail: "Le service d’analyse n’est pas configuré." },
      { status: 503 },
    );
  }
  const backendApiUrl =
    configuredBackendApiUrl ?? "http://localhost:8000/api/v1";
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
  if (backendProxySecret) {
    headers.set("X-Backend-Proxy-Secret", backendProxySecret);
  }
  headers.set("Authorization", `Bearer ${accessToken}`);

  const options: RequestInit & { duplex?: "half" } = {
    method: request.method,
    headers,
    cache: "no-store",
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    options.body = request.body;
    options.duplex = "half";
  }

  try {
    const backendResponse = await fetch(target, options);
    const backendContentType = backendResponse.headers
      .get("content-type")
      ?.toLowerCase();
    if (
      (backendResponse.status >= 300 && backendResponse.status < 400) ||
      backendContentType?.includes("text/html")
    ) {
      await backendResponse.body?.cancel();
      return Response.json(
        { detail: "Le service d’analyse est temporairement indisponible." },
        { status: 502 },
      );
    }

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
