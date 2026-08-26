export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const USER_STORAGE_KEY = "property-analysis-user-id";
const CASE_STORAGE_KEY = "property-analysis-case-id";

export type Workspace = {
  userId: string;
  caseId: string;
};

let workspaceInitialization: Promise<Workspace> | null = null;

export async function readApiError(response: Response) {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? "Une erreur inattendue est survenue.";
  } catch {
    return "Le service est temporairement indisponible.";
  }
}

async function createWorkspace(userId: string): Promise<Workspace> {
  const response = await fetch(`${API_URL}/analysis-cases`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": userId,
    },
    body: JSON.stringify({ title: "Mon achat immobilier" }),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  const analysisCase = (await response.json()) as { id: string };
  localStorage.setItem(CASE_STORAGE_KEY, analysisCase.id);
  return { userId, caseId: analysisCase.id };
}

export function getOrCreateWorkspace() {
  if (workspaceInitialization) return workspaceInitialization;

  workspaceInitialization = (async () => {
    let userId = localStorage.getItem(USER_STORAGE_KEY);
    if (!userId) {
      userId = crypto.randomUUID();
      localStorage.setItem(USER_STORAGE_KEY, userId);
    }

    const savedCaseId = localStorage.getItem(CASE_STORAGE_KEY);
    return savedCaseId
      ? { userId, caseId: savedCaseId }
      : createWorkspace(userId);
  })().catch((initializationError: unknown) => {
    workspaceInitialization = null;
    throw initializationError;
  });
  return workspaceInitialization;
}

export function resetWorkspace(caseId: string) {
  if (localStorage.getItem(CASE_STORAGE_KEY) === caseId) {
    localStorage.removeItem(CASE_STORAGE_KEY);
  }
  workspaceInitialization = null;
}
