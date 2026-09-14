import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";

import { productRoutes } from "@/lib/routes";
import { getSupabaseConfig } from "@/lib/supabase/config";

function copySessionState(source: NextResponse, target: NextResponse) {
  for (const cookie of source.cookies.getAll()) {
    target.cookies.set(cookie);
  }
  for (const name of ["cache-control", "expires", "pragma"] as const) {
    const value = source.headers.get(name);
    if (value) target.headers.set(name, value);
  }
  return target;
}

export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({ request });
  const { url, publishableKey } = getSupabaseConfig();
  const supabase = createServerClient(url, publishableKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet, headers) {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }
        response = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
        for (const [name, value] of Object.entries(headers)) {
          response.headers.set(name, value);
        }
      },
    },
  });

  // Keep this call immediately after client creation. It validates and refreshes
  // the cookie-backed session before protected routes are rendered.
  const { data } = await supabase.auth.getClaims();
  if (!data?.claims?.sub) {
    const signInUrl = new URL(productRoutes.signIn, request.url);
    signInUrl.searchParams.set(
      "callbackUrl",
      `${request.nextUrl.pathname}${request.nextUrl.search}`,
    );
    return copySessionState(response, NextResponse.redirect(signInUrl));
  }

  return response;
}
