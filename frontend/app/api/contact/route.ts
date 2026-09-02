import type { NextRequest } from "next/server";

const MAX_BODY_BYTES = 16 * 1024;

function isSameOrigin(request: NextRequest) {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  if (!origin || !host) return true;

  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

function getClientIp(request: NextRequest) {
  const value =
    request.headers.get("cf-connecting-ip") ??
    request.headers.get("x-real-ip") ??
    request.headers.get("x-forwarded-for") ??
    "unknown";
  return value.split(",", 1)[0].trim().slice(0, 100) || "unknown";
}

async function readLimitedBody(request: NextRequest) {
  const declaredLength = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(declaredLength) && declaredLength > MAX_BODY_BYTES) {
    throw new Error("body_too_large");
  }

  if (!request.body) return "";
  const reader = request.body.getReader();
  const decoder = new TextDecoder();
  let size = 0;
  let body = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > MAX_BODY_BYTES) {
      await reader.cancel();
      throw new Error("body_too_large");
    }
    body += decoder.decode(value, { stream: true });
  }

  return body + decoder.decode();
}

export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return Response.json({ detail: "Forbidden" }, { status: 403 });
  }
  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
    return Response.json({ detail: "JSON body required" }, { status: 415 });
  }

  let body: string;
  try {
    body = await readLimitedBody(request);
    JSON.parse(body);
  } catch (error) {
    const status = error instanceof Error && error.message === "body_too_large" ? 413 : 400;
    return Response.json({ detail: "Invalid request" }, { status });
  }

  const backendApiUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";
  const headers = new Headers({
    "Content-Type": "application/json",
    "X-Contact-Client-IP": getClientIp(request),
  });
  const proxySecret = process.env.CONTACT_PROXY_SECRET;
  if (!proxySecret && process.env.NODE_ENV === "production") {
    return Response.json(
      { detail: "Le service de contact n’est pas configuré." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
  if (proxySecret) headers.set("X-Contact-Proxy-Secret", proxySecret);

  try {
    const backendResponse = await fetch(`${backendApiUrl.replace(/\/$/, "")}/contact`, {
      method: "POST",
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    const responseHeaders = new Headers({
      "Cache-Control": "no-store",
      "Content-Type": "application/json",
    });
    const retryAfter = backendResponse.headers.get("retry-after");
    if (retryAfter) responseHeaders.set("Retry-After", retryAfter);

    return new Response(await backendResponse.text(), {
      status: backendResponse.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      { detail: "Le service de contact est temporairement indisponible." },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
