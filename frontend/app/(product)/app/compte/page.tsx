import { redirect } from "next/navigation";

import { signOutCurrentSession } from "@/features/auth/actions";
import { productRoutes } from "@/lib/routes";
import { createClient } from "@/lib/supabase/server";

function initials(name: string | null | undefined) {
  if (!name) return "A";
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toLocaleUpperCase("fr"))
    .join("");
}

export default async function AccountPage() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getUser();
  if (error || !data.user) redirect(productRoutes.signIn);

  const user = data.user;
  const metadata = user.user_metadata;
  const displayName =
    typeof metadata.full_name === "string"
      ? metadata.full_name
      : typeof metadata.name === "string"
        ? metadata.name
        : null;
  const providers = Array.from(
    new Set(user.identities?.map(({ provider }) => provider) ?? []),
  );
  const providerLabels: Record<string, string> = {
    email: "E-mail et mot de passe",
    google: "Google",
  };
  const providerDescription = providers.length
    ? providers.map((provider) => providerLabels[provider] ?? provider).join(", ")
    : "Compte Supabase";

  return (
    <section className="account-page" aria-labelledby="account-title">
      <div className="account-heading">
        <p className="eyebrow">Compte</p>
        <h1 id="account-title">Mon compte</h1>
        <p>Votre identité de connexion et l’accès à votre espace Acquora.</p>
      </div>

      <div className="account-card">
        <div className="account-avatar" aria-hidden="true">
          {initials(displayName)}
        </div>
        <div className="account-identity">
          <strong>{displayName ?? "Compte Acquora"}</strong>
          <span>{user.email}</span>
          <small>{providerDescription}</small>
        </div>
        <form action={signOutCurrentSession}>
          <button
            className="sign-out-button"
            data-product-analytics-reset
            type="submit"
          >
            Se déconnecter
          </button>
        </form>
      </div>
    </section>
  );
}
