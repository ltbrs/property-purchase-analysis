import type { Metadata } from "next";
import Link from "next/link";

import { BrandLink } from "@/components/design-system/brand-link";
import { PasswordResetForm } from "@/features/auth/password-reset-form";
import { marketingRoutes, productRoutes } from "@/lib/routes";

export const metadata: Metadata = {
  title: "Mot de passe oublié : Acquora",
};

export default function ForgotPasswordPage() {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <BrandLink className="auth-brand" href={marketingRoutes.home} priority />
        <div className="auth-heading">
          <p className="eyebrow">Sécurité du compte</p>
          <h1 id="auth-title">Réinitialiser votre mot de passe</h1>
          <p>Recevez un lien sécurisé à l’adresse associée à votre compte.</p>
        </div>
        <PasswordResetForm mode="request" />
        <Link className="auth-secondary-link" href={productRoutes.signIn}>
          Retour à la connexion
        </Link>
      </section>
    </main>
  );
}
