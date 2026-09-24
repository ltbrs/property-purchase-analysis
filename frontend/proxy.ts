import { NextResponse, type NextRequest } from "next/server";

import { updateSession } from "@/lib/supabase/proxy";

export async function proxy(request: NextRequest) {
  if (
    request.nextUrl.pathname === "/app/demo" ||
    request.nextUrl.pathname.startsWith("/app/demo/")
  ) {
    return NextResponse.next();
  }
  return updateSession(request);
}

export const config = {
  matcher: ["/app/:path*"],
};
