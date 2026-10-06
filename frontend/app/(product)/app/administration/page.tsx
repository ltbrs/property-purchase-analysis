import { notFound } from "next/navigation";

import { AdminUsersPanel, type AdminUsersPage } from "@/features/admin/admin-users-panel";
import { fetchAdminBackend } from "@/lib/admin-server";

type AdminPageProps = {
  searchParams: Promise<{ page?: string; search?: string }>;
};

export const metadata = { title: "Administration | Acquora", robots: "noindex, nofollow" };

export default async function AdminPage({ searchParams }: AdminPageProps) {
  const params = await searchParams;
  const page = Math.max(1, Number.parseInt(params.page ?? "1", 10) || 1);
  const search = typeof params.search === "string" ? params.search.slice(0, 254).trim() : "";
  const query = new URLSearchParams({ page: String(page), search });
  const response = await fetchAdminBackend(`users?${query}`);
  if (!response || response.status === 404) notFound();
  if (!response.ok) throw new Error("Impossible de charger les utilisateurs.");
  const usersPage = (await response.json()) as AdminUsersPage;

  return <AdminUsersPanel initialPage={usersPage} search={search} />;
}
