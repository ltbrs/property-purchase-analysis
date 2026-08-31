import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { auth, signIn } from "@/auth";
import { BrandLink } from "@/components/design-system/brand-link";
import { marketingRoutes, productRoutes } from "@/lib/routes";

export const metadata: Metadata = {
  title: "Connexion — Acquora",
};

type SignInPageProps = {
  searchParams: Promise<{
    callbackUrl?: string | string[];
    error?: string | string[];
  }>;
};

function safeCallbackUrl(value: string | string[] | undefined) {
  const callbackUrl = Array.isArray(value) ? value[0] : value;
  return callbackUrl?.startsWith("/") && !callbackUrl.startsWith("//")
    ? callbackUrl
    : productRoutes.home;
}

function GoogleLogo() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M21.6 12.2c0-.7-.1-1.5-.2-2.2H12v4h5.4a4.7 4.7 0 0 1-2 3v2.7h3.4c2-1.9 2.8-4.5 2.8-7.5Z" />
      <path fill="#34A853" d="M12 22c2.7 0 5-.9 6.8-2.3L15.4 17c-.9.6-2.1 1-3.4 1-2.6 0-4.8-1.8-5.6-4.1H3v2.7A10.3 10.3 0 0 0 12 22Z" />
      <path fill="#FBBC05" d="M6.4 13.9A6 6 0 0 1 6.1 12c0-.7.1-1.3.3-1.9V7.4H3A10 10 0 0 0 2 12c0 1.7.4 3.2 1 4.6l3.4-2.7Z" />
      <path fill="#EA4335" d="M12 6c1.5 0 2.8.5 3.8 1.5l3-2.9A10 10 0 0 0 3 7.4l3.4 2.7A6 6 0 0 1 12 6Z" />
    </svg>
  );
}

export default async function SignInPage({ searchParams }: SignInPageProps) {
  const params = await searchParams;
  const callbackUrl = safeCallbackUrl(params.callbackUrl);
  const session = await auth();
  if (session?.user) redirect(callbackUrl);

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
            Connectez-vous avec Google pour accéder à vos documents et à vos analyses.
          </p>
        </div>

        {params.error ? (
          <p className="auth-error" role="alert">
            La connexion Google n’a pas abouti. Vous pouvez réessayer.
          </p>
        ) : null}

        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: callbackUrl });
          }}
        >
          <button className="google-sign-in" type="submit">
            <GoogleLogo />
            <span>Continuer avec Google</span>
          </button>
        </form>

        <p className="auth-privacy">
          Vos documents immobiliers restent privés et ne sont jamais partagés avec
          Google.
        </p>
      </section>
    </main>
  );
}
