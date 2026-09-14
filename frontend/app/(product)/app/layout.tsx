import type { ReactNode } from "react";
import { redirect } from "next/navigation";

import { ApplicationShell } from "@/components/application-shell";
import { productRoutes } from "@/lib/routes";
import { createClient } from "@/lib/supabase/server";

type AppLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default async function AppLayout({ children }: AppLayoutProps) {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  const claims = data?.claims;
  if (!claims?.sub) {
    redirect(`${productRoutes.signIn}?callbackUrl=${encodeURIComponent(productRoutes.home)}`);
  }

  const appMetadata =
    claims.app_metadata && typeof claims.app_metadata === "object"
      ? claims.app_metadata
      : undefined;
  const authProvider =
    appMetadata &&
    "provider" in appMetadata &&
    typeof appMetadata.provider === "string"
      ? appMetadata.provider
      : undefined;

  return (
    <ApplicationShell
      user={{
        id: claims.sub,
        authProvider,
      }}
    >
      {children}
    </ApplicationShell>
  );
}
