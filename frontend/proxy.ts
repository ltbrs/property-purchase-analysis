import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { productRoutes } from "@/lib/routes";

export const proxy = auth((request) => {
  if (request.auth?.user?.id) return NextResponse.next();

  const signInUrl = new URL(productRoutes.signIn, request.url);
  signInUrl.searchParams.set(
    "callbackUrl",
    `${request.nextUrl.pathname}${request.nextUrl.search}`,
  );
  return NextResponse.redirect(signInUrl);
});

export const config = {
  matcher: ["/app/:path*"],
};
