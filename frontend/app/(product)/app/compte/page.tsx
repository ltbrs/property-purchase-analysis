import { redirect } from "next/navigation";

import { auth, signOut } from "@/auth";
import { marketingRoutes, productRoutes } from "@/lib/routes";

function initials(name: string | null | undefined) {
  if (!name) return "A";
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toLocaleUpperCase("fr"))
    .join("");
}

export default async function AccountPage() {
  const session = await auth();
  if (!session?.user) redirect(productRoutes.signIn);

  return (
    <section className="account-page" aria-labelledby="account-title">
      <div className="account-heading">
        <p className="eyebrow">Compte</p>
        <h1 id="account-title">Mon compte</h1>
        <p>Votre identité de connexion et l’accès à votre espace Acquora.</p>
      </div>

      <div className="account-card">
        <div className="account-avatar" aria-hidden="true">
          {initials(session.user.name)}
        </div>
        <div className="account-identity">
          <strong>{session.user.name ?? "Compte Google"}</strong>
          <span>{session.user.email}</span>
          <small>Connecté avec Google</small>
        </div>
        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: marketingRoutes.home });
          }}
        >
          <button className="sign-out-button" data-posthog-reset type="submit">
            Se déconnecter
          </button>
        </form>
      </div>
    </section>
  );
}
