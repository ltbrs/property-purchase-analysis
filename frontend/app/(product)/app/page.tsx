import { CaseDashboard } from "@/features/cases/case-dashboard";

export default async function AppHomePage({ searchParams }: {
  searchParams: Promise<{ import?: string }>;
}) {
  const params = await searchParams;
  return <CaseDashboard pendingDocumentId={typeof params.import === "string" ? params.import : undefined} />;
}
