import type { NextRequest } from "next/server";

type RouteContext = { params: Promise<{ path: string[] }> };

export async function GET(_request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const isCase = path.length === 1 && path[0] === "case";
  const isReport = path.length === 1 && path[0] === "report";
  const isDocumentList = path.length === 1 && path[0] === "documents";
  const isDocument =
    path.length === 3 &&
    path[0] === "documents" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(path[1]) &&
    ["view-url", "extraction", "dpe-extraction"].includes(path[2]);
  if (!isCase && !isReport && !isDocumentList && !isDocument) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }

  const configuredBackendApiUrl = process.env.BACKEND_API_URL?.trim();
  const backendProxySecret = process.env.BACKEND_PROXY_SECRET?.trim();
  if (process.env.NODE_ENV === "production" && (!configuredBackendApiUrl || !backendProxySecret)) {
    return Response.json({ detail: "Le service d’analyse n’est pas configuré." }, { status: 503 });
  }
  const backendApiUrl = configuredBackendApiUrl ?? "http://localhost:8000/api/v1";
  const headers = new Headers();
  if (backendProxySecret) headers.set("X-Backend-Proxy-Secret", backendProxySecret);

  try {
    const backendResponse = await fetch(
      `${backendApiUrl.replace(/\/$/, "")}/demo/${path.join("/")}`,
      { headers, cache: "no-store", redirect: "manual" },
    );
    if (
      (backendResponse.status >= 300 && backendResponse.status < 400) ||
      !backendResponse.headers.get("content-type")?.toLowerCase().includes("application/json")
    ) {
      await backendResponse.body?.cancel();
      return Response.json({ detail: "Le service d’analyse est temporairement indisponible." }, { status: 502 });
    }
    const responseHeaders = new Headers({ "Cache-Control": "no-store" });
    const contentType = backendResponse.headers.get("content-type");
    if (contentType) responseHeaders.set("Content-Type", contentType);
    return new Response(backendResponse.body, {
      status: backendResponse.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json({ detail: "Le service d’analyse est temporairement indisponible." }, { status: 502 });
  }
}
