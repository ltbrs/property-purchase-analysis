import { createClient } from "@/lib/supabase/server";

export async function fetchAdminBackend(path: string): Promise<Response | null> {
  const supabase = await createClient();
  const { data: userData } = await supabase.auth.getUser();
  const { data: sessionData } = await supabase.auth.getSession();
  const accessToken = sessionData.session?.access_token;
  if (!userData.user || !accessToken) return null;

  const backendApiUrl = process.env.BACKEND_API_URL?.trim();
  const backendProxySecret = process.env.BACKEND_PROXY_SECRET?.trim();
  if (process.env.NODE_ENV === "production" && (!backendApiUrl || !backendProxySecret)) {
    throw new Error("Le service d’administration n’est pas configuré.");
  }
  const baseUrl = backendApiUrl ?? "http://localhost:8000/api/v1";
  const headers = new Headers({ Authorization: `Bearer ${accessToken}` });
  if (backendProxySecret) headers.set("X-Backend-Proxy-Secret", backendProxySecret);
  return fetch(`${baseUrl.replace(/\/$/, "")}/admin/${path}`, {
    headers,
    cache: "no-store",
  });
}

export async function isCurrentUserAdmin(): Promise<boolean> {
  try {
    const response = await fetchAdminBackend("me");
    return response?.ok ?? false;
  } catch {
    return false;
  }
}
