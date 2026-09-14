import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { BrandLink } from "@/components/design-system/brand-link";
import { PasswordResetForm } from "@/features/auth/password-reset-form";
import { marketingRoutes, productRoutes } from "@/lib/routes";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Nouveau mot de passe : Acquora",
};

export default async function UpdatePasswordPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  if (!data?.claims?.sub) redirect(productRoutes.forgotPassword);

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <BrandLink className="auth-brand" href={marketingRoutes.home} priority />
        <div className="auth-heading">
          <p className="eyebrow">Sécurité du compte</p>
          <h1 id="auth-title">Choisissez un nouveau mot de passe</h1>
          <p>Utilisez au moins 12 caractères et évitez un mot de passe réutilisé.</p>
        </div>
        <PasswordResetForm mode="update" />
      </section>
    </main>
  );
}
