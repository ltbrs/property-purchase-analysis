export const API_URL = "/api/backend";

const CASE_STORAGE_KEY = "property-analysis-case-id";
export const WORKSPACE_CHANGE_EVENT = "property-analysis-workspace-change";
export const CASE_CREATION_REQUEST_EVENT = "property-analysis-case-creation-request";

export type Workspace = {
  caseId: string;
};

export type AnalysisCase = {
  id: string;
  title: string;
  property_type: "unknown" | "apartment_coproperty" | "house";
  price_eur: string | null;
  surface_m2: string | null;
  lot_count: number | null;
  case_kind: "user" | "demo";
  read_only: boolean;
  analysis_access_status: "not_activated" | "preview" | "active" | "expired";
  analysis_access_activated_at: string | null;
  analysis_access_expires_at: string | null;
  created_at: string;
  updated_at: string;
};

export type UserPreferences = {
  show_demo_case: boolean;
};

export async function readApiError(response: Response) {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? "Une erreur inattendue est survenue.";
  } catch {
    return "Le service est temporairement indisponible.";
  }
}

export function getWorkspace(): Workspace | null {
  const caseId = localStorage.getItem(CASE_STORAGE_KEY);
  if (!caseId) return null;
  return { caseId };
}

export async function fetchAnalysisCases() {
  const response = await fetch(`${API_URL}/analysis-cases`, {
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as AnalysisCase[];
}

export async function fetchUserPreferences() {
  const response = await fetch(`${API_URL}/me/preferences`, { cache: "no-store" });
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as UserPreferences;
}

export async function updateUserPreferences(preferences: UserPreferences) {
  const response = await fetch(`${API_URL}/me/preferences`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(preferences),
  });
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as UserPreferences;
}

export function saveWorkspace(caseId: string): Workspace {
  const workspace = { caseId };
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
