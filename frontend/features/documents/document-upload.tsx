"use client";

import { useEffect, useRef, useState } from "react";

import {
  API_URL,
  getOrCreateWorkspace,
  readApiError,
  resetWorkspace,
  type Workspace,
} from "@/lib/workspace";

const MAX_FILE_SIZE = 25 * 1024 * 1024;

type DocumentStatus =
  | "uploaded"
  | "extracting"
  | "extracted"
  | "analyzing"
  | "completed"
  | "failed";

type UploadedDocument = {
  id: string;
  analysis_case_id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
};

const statusLabels: Record<DocumentStatus, string> = {
  uploaded: "Importé",
  extracting: "Extraction en cours",
  extracted: "Extrait",
  analyzing: "Analyse en cours",
  completed: "Terminé",
  failed: "Échec",
};

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} Ko`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} Mo`;
}

async function fetchDocuments(workspace: Workspace) {
  return fetch(
    `${API_URL}/analysis-cases/${workspace.caseId}/documents`,
    { headers: { "X-User-Id": workspace.userId } },
  );
}

export function DocumentUpload() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        let currentWorkspace = await getOrCreateWorkspace();
        let response = await fetchDocuments(currentWorkspace);

        if (response.status === 404) {
          resetWorkspace(currentWorkspace.caseId);
          currentWorkspace = await getOrCreateWorkspace();
          response = await fetchDocuments(currentWorkspace);
        }
        if (!response.ok) {
          throw new Error(await readApiError(response));
        }

        const uploadedDocuments = (await response.json()) as UploadedDocument[];
        if (!cancelled) {
          setWorkspace(currentWorkspace);
          setDocuments(uploadedDocuments);
        }
      } catch (initializationError) {
        if (!cancelled) {
          setError(
            initializationError instanceof Error
              ? initializationError.message
              : "Impossible d’initialiser votre dossier.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsInitializing(false);
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  async function refreshDocuments() {
    if (!workspace) return;

    setIsRefreshing(true);
    setError(null);
    try {
      const response = await fetchDocuments(workspace);
      if (!response.ok) throw new Error(await readApiError(response));
      setDocuments((await response.json()) as UploadedDocument[]);
    } catch (refreshError) {
      setError(
        refreshError instanceof Error
          ? refreshError.message
          : "Impossible d’actualiser les documents.",
      );
    } finally {
      setIsRefreshing(false);
    }
  }

  async function uploadFiles(files: File[]) {
    if (!workspace || files.length === 0) return;

    setError(null);
    const invalidFile = files.find(
      (file) => file.type !== "application/pdf" || file.size > MAX_FILE_SIZE,
    );
    if (invalidFile) {
      setError(
        invalidFile.type !== "application/pdf"
          ? `« ${invalidFile.name} » n’est pas un fichier PDF.`
          : `« ${invalidFile.name} » dépasse la limite de 25 Mo.`,
      );
      return;
    }

    setIsUploading(true);
    const results = await Promise.allSettled(
      files.map(async (file) => {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch(
          `${API_URL}/analysis-cases/${workspace.caseId}/documents`,
          {
            method: "POST",
            headers: { "X-User-Id": workspace.userId },
            body: formData,
          },
        );
        if (!response.ok) {
          throw new Error(`${file.name} : ${await readApiError(response)}`);
        }
        return (await response.json()) as UploadedDocument;
      }),
    );

    const failures = results.flatMap((result) =>
      result.status === "rejected" ? [String(result.reason)] : [],
    );
    const successfulDocuments = results.flatMap((result) =>
      result.status === "fulfilled" ? [result.value] : [],
    );
    setDocuments((currentDocuments) => {
      const documentsById = new Map(
        currentDocuments.map((document) => [document.id, document]),
      );
      for (const document of successfulDocuments) {
        documentsById.set(document.id, document);
      }
      return Array.from(documentsById.values()).sort(
        (left, right) =>
          Date.parse(right.created_at) - Date.parse(left.created_at),
      );
    });
    setError(failures.length > 0 ? failures.join(" ") : null);
    setIsUploading(false);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="document-workspace">
      <div className="upload-card">
        <div className="upload-card-copy">
          <span className="upload-icon" aria-hidden="true">PDF</span>
          <div>
            <h2>Ajoutez vos fichiers PDF</h2>
            <p>Plusieurs fichiers possibles, 25 Mo maximum par document.</p>
          </div>
        </div>
        <label
          className={`file-button${isUploading || isInitializing ? " is-disabled" : ""}`}
        >
          {isUploading ? "Import en cours…" : "Choisir des documents"}
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            multiple
            disabled={!workspace || isUploading || isInitializing}
            onChange={(event) =>
              void uploadFiles(Array.from(event.currentTarget.files ?? []))
            }
          />
        </label>
        <p className="privacy-note">
          <span aria-hidden="true">●</span> Stockage privé — aucun document n’est public.
        </p>
      </div>

      {error ? (
        <div className="upload-error" role="alert">
          <strong>Import interrompu</strong>
          <span>{error}</span>
        </div>
      ) : null}

      <section className="document-list" aria-labelledby="document-list-title">
        <div className="document-list-heading">
          <div>
            <p className="section-kicker">Dossier en cours</p>
            <h2 id="document-list-title">Documents ajoutés</h2>
          </div>
          <button
            className="refresh-button"
            type="button"
            disabled={!workspace || isRefreshing}
            onClick={() => void refreshDocuments()}
          >
            {isRefreshing ? "Actualisation…" : "Actualiser"}
          </button>
        </div>

        {isInitializing ? (
          <div className="document-empty">Chargement de votre dossier…</div>
        ) : documents.length === 0 ? (
          <div className="document-empty">
            <strong>Votre dossier est encore vide.</strong>
            <span>Commencez par le DPE ou les derniers procès-verbaux d’AG.</span>
          </div>
        ) : (
          <ul className="document-items">
            {documents.map((document) => (
              <li key={document.id} className="document-item">
                <span className="document-type" aria-hidden="true">PDF</span>
                <div className="document-details">
                  <strong>{document.original_filename}</strong>
                  <span>
                    {formatFileSize(document.size_bytes)} · ajouté le{" "}
                    {dateFormatter.format(new Date(document.created_at))}
                  </span>
                  {document.failure_reason ? (
                    <span className="document-failure">{document.failure_reason}</span>
                  ) : null}
                </div>
                <span className={`status-badge status-${document.status}`}>
                  {statusLabels[document.status]}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
