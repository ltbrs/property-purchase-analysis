export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const USER_STORAGE_KEY = "property-analysis-user-id";
const CASE_STORAGE_KEY = "property-analysis-case-id";
export const WORKSPACE_CHANGE_EVENT = "property-analysis-workspace-change";
export const CASE_CREATION_REQUEST_EVENT = "property-analysis-case-creation-request";

export type Workspace = {
  userId: string;
  caseId: string;
};

export type AnalysisCase = {
  id: string;
  title: string;
  property_type: "unknown" | "apartment_coproperty" | "house";
  price_eur: string | null;
  surface_m2: string | null;
  lot_count: number | null;
  created_at: string;
  updated_at: string;
};

export async function readApiError(response: Response) {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? "Une erreur inattendue est survenue.";
  } catch {
    return "Le service est temporairement indisponible.";
  }
}

export function getOrCreateUserId() {
  let userId = localStorage.getItem(USER_STORAGE_KEY);
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(USER_STORAGE_KEY, userId);
  }
  return userId;
}

export function getWorkspace(): Workspace | null {
  const caseId = localStorage.getItem(CASE_STORAGE_KEY);
  if (!caseId) return null;
  return { userId: getOrCreateUserId(), caseId };
}

export async function fetchAnalysisCases() {
  const response = await fetch(`${API_URL}/analysis-cases`, {
    cache: "no-store",
    headers: { "X-User-Id": getOrCreateUserId() },
  });
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as AnalysisCase[];
}

export function saveWorkspace(caseId: string): Workspace {
  const workspace = { userId: getOrCreateUserId(), caseId };
  localStorage.setItem(CASE_STORAGE_KEY, caseId);
  window.dispatchEvent(new Event(WORKSPACE_CHANGE_EVENT));
  return workspace;
}

export function resetWorkspace(caseId: string) {
  if (localStorage.getItem(CASE_STORAGE_KEY) === caseId) {
    localStorage.removeItem(CASE_STORAGE_KEY);
    window.dispatchEvent(new Event(WORKSPACE_CHANGE_EVENT));
  }
}
