import type { EmailOtpType } from "@supabase/supabase-js";
import { type NextRequest, NextResponse } from "next/server";

import { safeRedirectPath } from "@/lib/auth/redirects";
import { productRoutes } from "@/lib/routes";
import { createClient } from "@/lib/supabase/server";

const EMAIL_OTP_TYPES = new Set<EmailOtpType>([
  "email",
  "email_change",
  "invite",
  "magiclink",
  "recovery",
  "signup",
]);

export async function GET(request: NextRequest) {
  const tokenHash = request.nextUrl.searchParams.get("token_hash");
  const rawType = request.nextUrl.searchParams.get("type");
  const next = safeRedirectPath(
    request.nextUrl.searchParams.get("next"),
    request.nextUrl.origin,
  );

  if (tokenHash && rawType && EMAIL_OTP_TYPES.has(rawType as EmailOtpType)) {
    const supabase = await createClient();
    const { error } = await supabase.auth.verifyOtp({
      token_hash: tokenHash,
      type: rawType as EmailOtpType,
    });
    if (!error) return NextResponse.redirect(new URL(next, request.url));
  }

  const errorUrl = new URL(productRoutes.signIn, request.url);
  errorUrl.searchParams.set("error", "confirmation");
  return NextResponse.redirect(errorUrl);
}
