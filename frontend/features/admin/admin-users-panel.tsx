"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { productRoutes } from "@/lib/routes";
import { API_URL, readApiError } from "@/lib/workspace";

type AdminUser = {
  id: string;
  email: string | null;
  name: string | null;
  created_at: string;
  email_verified: boolean;
  plan: "single_analysis" | "search_pack" | null;
  available_credits: number;
  paid_credits: number;
  granted_credits: number;
};

export type AdminUsersPage = {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
};

type AdminUsersPanelProps = {
  initialPage: AdminUsersPage;
  search: string;
};

const planLabels: Record<NonNullable<AdminUser["plan"]>, string> = {
  single_analysis: "Analyse complète",
  search_pack: "Pack Recherche",
};

function pageUrl(page: number, search: string) {
  const query = new URLSearchParams({ page: String(page) });
  if (search) query.set("search", search);
  return `${productRoutes.admin}?${query}`;
}

export function AdminUsersPanel({ initialPage, search }: AdminUsersPanelProps) {
  const router = useRouter();
  const [selected, setSelected] = useState<AdminUser | null>(null);
  const [count, setCount] = useState(1);
  const [reason, setReason] = useState("Test de la fonctionnalité avec un proche");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function grantCredits(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || busy) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const response = await fetch(`${API_URL}/admin/users/${selected.id}/credits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count, reason: reason.trim() }),
      });
      if (!response.ok) throw new Error(await readApiError(response));
      setNotice(`${count} crédit${count > 1 ? "s" : ""} offert${count > 1 ? "s" : ""} à ${selected.email ?? selected.id}.`);
      setSelected(null);
      router.refresh();
    } catch (grantError) {
      setError(
        grantError instanceof Error
          ? grantError.message
          : "Impossible d’offrir les crédits.",
      );
    } finally {
      setBusy(false);
    }
  }

  const first = initialPage.total === 0 ? 0 : (initialPage.page - 1) * initialPage.page_size + 1;
  const last = Math.min(initialPage.page * initialPage.page_size, initialPage.total);
  const pageCount = Math.ceil(initialPage.total / initialPage.page_size);

  return (
    <section className="admin-page" aria-labelledby="admin-title">
      <div className="admin-heading">
        <p className="eyebrow">Administration</p>
        <h1 id="admin-title">Utilisateurs et crédits</h1>
        <p>Consultez les offres achetées et offrez des analyses aux personnes qui testent Acquora.</p>
      </div>

      <form className="admin-search" action={productRoutes.admin} method="get" role="search">
        <label htmlFor="admin-user-search">Rechercher par e-mail</label>
        <div>
          <input id="admin-user-search" name="search" type="search" defaultValue={search} maxLength={254} placeholder="nom@exemple.fr" />
          <button type="submit">Rechercher</button>
        </div>
      </form>

      {notice ? <p className="admin-notice" role="status">{notice}</p> : null}
      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th scope="col">Utilisateur</th>
              <th scope="col">Offre achetée</th>
              <th scope="col">Disponibles</th>
              <th scope="col">Achetés / offerts</th>
              <th scope="col">Inscription</th>
              <th scope="col"><span className="sr-only">Action</span></th>
            </tr>
          </thead>
          <tbody>
            {initialPage.users.map((user) => (
              <tr key={user.id}>
                <td>
                  <strong>{user.email ?? "Sans e-mail"}</strong>
                  <small>{user.name ?? (user.email_verified ? "Compte confirmé" : "E-mail non confirmé")}</small>
                </td>
                <td>{user.plan ? planLabels[user.plan] : "Aucune"}</td>
                <td><strong>{user.available_credits}</strong></td>
                <td>{user.paid_credits} / {user.granted_credits}</td>
                <td>{new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(new Date(user.created_at))}</td>
                <td>
                  <button type="button" onClick={() => { setSelected(user); setError(null); setNotice(null); setCount(1); }}>
                    Offrir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {initialPage.users.length === 0 ? <p className="admin-empty">Aucun utilisateur trouvé.</p> : null}
      </div>

      <nav className="admin-pagination" aria-label="Pages des utilisateurs">
        <span>{first} à {last} sur {initialPage.total} utilisateurs</span>
        <div>
          {initialPage.page > 1 ? <Link href={pageUrl(initialPage.page - 1, search)}>Précédent</Link> : null}
          {initialPage.page < pageCount ? <Link href={pageUrl(initialPage.page + 1, search)}>Suivant</Link> : null}
        </div>
      </nav>

      {selected ? (
        <div className="admin-dialog-backdrop" role="presentation">
          <section className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="grant-title">
            <h2 id="grant-title">Offrir des crédits</h2>
            <p>À {selected.email ?? selected.id}. Les crédits n’expirent pas et donnent chacun accès à une analyse.</p>
            <form onSubmit={grantCredits}>
              <label htmlFor="grant-count">Nombre de crédits</label>
              <input id="grant-count" type="number" min={1} max={10} required value={count} onChange={(event) => setCount(Number(event.target.value))} />
              <label htmlFor="grant-reason">Motif interne</label>
              <textarea id="grant-reason" minLength={5} maxLength={200} required value={reason} onChange={(event) => setReason(event.target.value)} />
              {error ? <p className="admin-error" role="alert">{error}</p> : null}
              <div className="admin-dialog-actions">
                <button type="button" className="admin-secondary" onClick={() => setSelected(null)} disabled={busy}>Annuler</button>
                <button type="submit" disabled={busy || count < 1 || count > 10}>{busy ? "Envoi…" : "Confirmer le don"}</button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </section>
  );
}
