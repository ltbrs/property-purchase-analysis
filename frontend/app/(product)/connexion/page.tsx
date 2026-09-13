import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { BrandLink } from "@/components/design-system/brand-link";
import { AuthForm } from "@/features/auth/auth-form";
import { safeRedirectPath } from "@/lib/auth/redirects";
import { marketingRoutes } from "@/lib/routes";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Connexion : Acquora",
};

type SignInPageProps = {
  searchParams: Promise<{
    callbackUrl?: string | string[];
    error?: string | string[];
  }>;
};

export default async function SignInPage({ searchParams }: SignInPageProps) {
  const params = await searchParams;
  const callbackUrl = safeRedirectPath(params.callbackUrl);
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  if (data?.claims?.sub) redirect(callbackUrl);
  const routeError = Array.isArray(params.error) ? params.error[0] : params.error;

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <BrandLink
          className="auth-brand"
          href={marketingRoutes.home}
          priority
        />
        <div className="auth-heading">
          <p className="eyebrow">Espace personnel</p>
          <h1 id="auth-title">Retrouvez vos dossiers d’achat</h1>
          <p>
            Connectez-vous avec Google ou avec votre adresse e-mail pour accéder à
            vos documents et à vos analyses.
          </p>
        </div>

        <AuthForm callbackUrl={callbackUrl} routeError={routeError} />

        <p className="auth-privacy">
          Google et notre service d’e-mail servent uniquement à sécuriser votre
          connexion. Vos documents immobiliers ne leur sont jamais transmis.
        </p>
      </section>
    </main>
  );
}
