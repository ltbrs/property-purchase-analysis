"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { AdemeMark } from "@/components/ademe-mark";
import { Icon } from "@/components/icons";
import {
  documentTypeLabels,
  expectedDocumentsFor,
  propertyTypeLabels,
  type DocumentType,
  type ExpectedDocument,
  type PropertyType,
} from "@/features/documents/document-catalog";
import {
  DpeExtractionViewer,
  type DpeExtractionSelection,
} from "@/features/documents/dpe-extraction-viewer";
import {
  PdfViewer,
  type PdfDocumentSelection,
} from "@/features/documents/pdf-viewer";
import {
  RawExtractionViewer,
  type RawExtractionSelection,
} from "@/features/documents/raw-extraction-viewer";
import { productRoutes } from "@/lib/routes";
import {
  API_URL,
  getWorkspace,
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

type AdemeVerificationStatus =
  | "not_attempted"
  | "verified"
  | "verified_with_inconsistencies"
  | "not_found"
  | "unavailable";

type UploadedDocument = {
  id: string;
  analysis_case_id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  failure_reason: string | null;
  document_type: DocumentType | null;
  ademe_verification_status: AdemeVerificationStatus | null;
  created_at: string;
  updated_at: string;
};

type AnalysisCase = {
  id: string;
  title: string;
  property_type: PropertyType;
};

const statusLabels: Record<DocumentStatus, string> = {
  uploaded: "Importé",
  extracting: "Extraction en cours",
  extracted: "Extrait",
  analyzing: "Analyse en cours",
  completed: "Analysé",
  failed: "Échec",
};

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "medium",
});

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} Ko`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} Mo`;
}

async function fetchDocuments(workspace: Workspace) {
  return fetch(`${API_URL}/analysis-cases/${workspace.caseId}/documents`);
}

async function fetchAnalysisCase(workspace: Workspace) {
  return fetch(`${API_URL}/analysis-cases/${workspace.caseId}`);
}

function PropertyTypeSelector({
  value,
  isSaving,
  onChange,
}: {
  value: PropertyType;
  isSaving: boolean;
  onChange: (value: Exclude<PropertyType, "unknown">) => void;
}) {
  const choices: {
    value: Exclude<PropertyType, "unknown">;
    label: string;
    description: string;
    icon: "building" | "home";
  }[] = [
    {
      value: "apartment_coproperty",
      label: "Appartement en copropriété",
      description: "Inclut les pièces de l’immeuble et de la copropriété.",
      icon: "building",
    },
    {
      value: "house",
      label: "Maison individuelle",
      description: "Exclut les PV d’AG et les comptes de copropriété.",
      icon: "home",
    },
  ];

  return (
    <fieldset className="property-type-fieldset" disabled={isSaving}>
      <legend>Type de logement</legend>
      <p>Cette information adapte automatiquement les documents à demander.</p>
      <div className="property-type-options">
        {choices.map((choice) => (
          <label
            key={choice.value}
            className={`property-type-option${value === choice.value ? " is-selected" : ""}`}
          >
            <input
              type="radio"
              name="property-type"
              value={choice.value}
              checked={value === choice.value}
              onChange={() => onChange(choice.value)}
            />
            <span className="property-type-icon"><Icon name={choice.icon} /></span>
            <span>
              <strong>{choice.label}</strong>
              <small>{choice.description}</small>
            </span>
            <span className="radio-indicator" aria-hidden="true" />
          </label>
        ))}
      </div>
      <span className="property-save-status" aria-live="polite">
        {isSaving ? "Mise à jour du dossier…" : ""}
      </span>
    </fieldset>
  );
}

function DocumentFile({
  document,
  deletingDocumentId,
  showType,
  onDelete,
  onViewDpe,
  onViewExtraction,
  onView,
}: {
  document: UploadedDocument;
  deletingDocumentId: string | null;
  showType?: boolean;
  onDelete: (document: UploadedDocument) => void;
  onViewDpe: (document: UploadedDocument) => void;
  onViewExtraction: (document: UploadedDocument) => void;
  onView: (document: UploadedDocument) => void;
}) {
  const canViewExtraction = ["extracted", "analyzing", "completed"].includes(
    document.status,
  );
  const isAdemeVerified = document.ademe_verification_status === "verified";
  const hasAdemeInconsistencies =
    document.ademe_verification_status === "verified_with_inconsistencies";
  const analysisStatusIcon = document.status === "failed"
    ? "alert"
    : ["extracted", "completed"].includes(document.status)
      ? "check"
      : "refresh";
  const documentStatusLabel = [
    "reçu",
    ...(document.status === "uploaded"
      ? []
      : [statusLabels[document.status].toLocaleLowerCase("fr-FR")]),
    ...(isAdemeVerified
      ? ["vérifié auprès de l’ADEME"]
      : hasAdemeInconsistencies
        ? ["écarts détectés avec l’ADEME"]
        : []),
  ].join(", ");

  return (
    <div className="document-file">
      <span className="document-type" aria-hidden="true"><Icon name="document" /></span>
      <div className="document-file-content">
        <div className="document-file-heading">
          <div className="document-details">
            <strong>{document.original_filename}</strong>
            <span>
              {showType
                ? `${documentTypeLabels[document.document_type ?? "unknown"]} · `
                : ""}
              {formatFileSize(document.size_bytes)} · {dateFormatter.format(new Date(document.created_at))}
            </span>
          </div>
          <div
            className="document-status"
            aria-label={`Statut : ${documentStatusLabel}`}
          >
            <span className="document-status-step is-complete">
              <Icon name="check" /> Reçu
            </span>
            {document.status !== "uploaded" ? (
              <span className={`document-status-step status-${document.status}`}>
                <Icon name={analysisStatusIcon} />
                {statusLabels[document.status]}
              </span>
            ) : null}
            {isAdemeVerified || hasAdemeInconsistencies ? (
              <span
                className={`ademe-verification${hasAdemeInconsistencies ? " has-inconsistencies" : ""}`}
                title={
                  isAdemeVerified
                    ? "Le numéro DPE a été retrouvé dans le registre public de l’ADEME et les données comparables sont cohérentes."
                    : "Le numéro DPE a été retrouvé dans le registre public de l’ADEME, avec des écarts sur certaines données."
                }
              >
                <AdemeMark />
                <span aria-hidden="true"><Icon name={isAdemeVerified ? "check" : "info"} /></span>
                {isAdemeVerified ? "Vérifié" : "Écarts détectés"}
              </span>
            ) : null}
          </div>
        </div>
        {document.failure_reason ? (
          <span className="document-failure">{document.failure_reason}</span>
        ) : null}
        <div className="document-actions">
          <button
            className="view-document-button"
            type="button"
            aria-label={`Visualiser ${document.original_filename}`}
            onClick={() => onView(document)}
          >
            <Icon name="eye" /> Visualiser
          </button>
          {document.document_type === "dpe" && document.status === "completed" ? (
            <button
              className="dpe-data-button"
              type="button"
              aria-label={`Voir les données DPE de ${document.original_filename}`}
              onClick={() => onViewDpe(document)}
            >
              <Icon name="gauge" /> Données DPE
            </button>
          ) : null}
          {canViewExtraction ? (
            <button
              className="raw-extraction-button"
              type="button"
              aria-label={`Voir l’extraction brute de ${document.original_filename}`}
              onClick={() => onViewExtraction(document)}
            >
              <Icon name="table" /> Extraction
            </button>
          ) : null}
          <button
            className="delete-document-button"
            type="button"
            disabled={deletingDocumentId !== null}
            aria-label={`Supprimer ${document.original_filename}`}
            title={`Supprimer ${document.original_filename}`}
            onClick={() => onDelete(document)}
          >
            {deletingDocumentId === document.id ? "Suppression…" : <Icon name="trash" />}
          </button>
        </div>
      </div>
    </div>
  );
}

function ExpectedDocumentRow({
  expectation,
  documents,
  propertyType,
  deletingDocumentId,
  onDelete,
  onViewDpe,
  onViewExtraction,
  onView,
}: {
  expectation: ExpectedDocument;
  documents: UploadedDocument[];
  propertyType: PropertyType;
  deletingDocumentId: string | null;
  onDelete: (document: UploadedDocument) => void;
  onViewDpe: (document: UploadedDocument) => void;
  onViewExtraction: (document: UploadedDocument) => void;
  onView: (document: UploadedDocument) => void;
}) {
  const isPresent = documents.length > 0;
  const state = isPresent ? "present" : propertyType === "unknown" ? "pending" : "missing";
  const stateLabel = isPresent ? "Reçu" : propertyType === "unknown" ? "À confirmer" : "Manquant";

  return (
    <li className={`coverage-item is-${state}`}>
      <div className="coverage-summary">
        <span className="coverage-state" aria-hidden="true">
          <Icon name={isPresent ? "check" : "document"} />
        </span>
        <div className="coverage-copy">
          <div>
            <strong>{expectation.label}</strong>
            {!isPresent ? (
              <span className={`coverage-badge is-${state}`}>{stateLabel}</span>
            ) : null}
          </div>
          {!isPresent ? <p>{expectation.description}</p> : null}
          {!isPresent && expectation.priority === "essential" ? (
            <small>Prioritaire pour l’analyse</small>
          ) : null}
        </div>
      </div>
      {documents.length > 0 ? (
        <div className="coverage-files">
          {documents.map((document) => (
            <DocumentFile
              key={document.id}
              document={document}
              deletingDocumentId={deletingDocumentId}
              onDelete={onDelete}
              onViewDpe={onViewDpe}
              onViewExtraction={onViewExtraction}
              onView={onView}
            />
          ))}
        </div>
      ) : null}
    </li>
  );
}

export function DocumentUpload() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [propertyType, setPropertyType] = useState<PropertyType>("unknown");
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isInitializing, setIsInitializing] = useState(true);
  const [needsWorkspace, setNeedsWorkspace] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSavingPropertyType, setIsSavingPropertyType] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [viewingDocument, setViewingDocument] = useState<PdfDocumentSelection | null>(null);
  const [viewingDpe, setViewingDpe] = useState<DpeExtractionSelection | null>(null);
  const [viewingExtraction, setViewingExtraction] =
    useState<RawExtractionSelection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const currentWorkspace = getWorkspace();
        if (!currentWorkspace) {
          setNeedsWorkspace(true);
          return;
        }
        const [documentsResponse, caseResponse] = await Promise.all([
          fetchDocuments(currentWorkspace),
          fetchAnalysisCase(currentWorkspace),
        ]);

        if (documentsResponse.status === 404 || caseResponse.status === 404) {
          resetWorkspace(currentWorkspace.caseId);
          setNeedsWorkspace(true);
          return;
        }
        if (!documentsResponse.ok) throw new Error(await readApiError(documentsResponse));
        if (!caseResponse.ok) throw new Error(await readApiError(caseResponse));

        const [uploadedDocuments, analysisCase] = await Promise.all([
          documentsResponse.json() as Promise<UploadedDocument[]>,
          caseResponse.json() as Promise<AnalysisCase>,
        ]);
        if (!cancelled) {
          setWorkspace(currentWorkspace);
          setDocuments(uploadedDocuments);
          setPropertyType(analysisCase.property_type);
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
        if (!cancelled) setIsInitializing(false);
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  if (needsWorkspace) {
    return (
      <div className="report-state">
        <span className="state-icon"><Icon name="folder" /></span>
        <strong>Créez d’abord votre dossier</strong>
        <span>Le type du bien permettra d’adapter la liste des pièces attendues.</span>
        <Link href={productRoutes.cases}>Créer mon dossier</Link>
      </div>
    );
  }

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

  async function updatePropertyType(nextPropertyType: Exclude<PropertyType, "unknown">) {
    if (!workspace || nextPropertyType === propertyType) return;

    setIsSavingPropertyType(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/analysis-cases/${workspace.caseId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ property_type: nextPropertyType }),
      });
      if (!response.ok) throw new Error(await readApiError(response));
      const analysisCase = (await response.json()) as AnalysisCase;
      setPropertyType(analysisCase.property_type);
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "Impossible de mettre à jour le type de logement.",
      );
    } finally {
      setIsSavingPropertyType(false);
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
            body: formData,
          },
        );
        if (!response.ok) {
          throw new Error(`${file.name} : ${await readApiError(response)}`);
        }
        return (await response.json()) as UploadedDocument;
      }),
    );

    const uploadFailures = results.flatMap((result) =>
      result.status === "rejected" ? [String(result.reason)] : [],
    );
    const successfulDocuments = results.flatMap((result) =>
      result.status === "fulfilled" ? [result.value] : [],
    );
    setDocuments((currentDocuments) => {
      const documentsById = new Map(
        currentDocuments.map((document) => [document.id, document]),
      );
      for (const document of successfulDocuments) documentsById.set(document.id, document);
      return Array.from(documentsById.values()).sort(
        (left, right) => Date.parse(right.created_at) - Date.parse(left.created_at),
      );
    });
    setIsUploading(false);

    setIsProcessing(successfulDocuments.length > 0);
    setDocuments((currentDocuments) =>
      currentDocuments.map((document) =>
        successfulDocuments.some(
          (uploadedDocument) =>
            uploadedDocument.id === document.id &&
            uploadedDocument.status !== "completed",
        )
          ? { ...document, status: "extracting" }
          : document,
      ),
    );
    const processingResults = await Promise.allSettled(
      successfulDocuments.map(async (document) => {
        const response = await fetch(
          `${API_URL}/analysis-cases/${workspace.caseId}/documents/${document.id}/process`,
          { method: "POST" },
        );
        if (!response.ok) {
          throw new Error(
            `${document.original_filename} : ${await readApiError(response)}`,
          );
        }
        return (await response.json()) as UploadedDocument;
      }),
    );
    const processingFailures = processingResults.flatMap((result) =>
      result.status === "rejected" ? [String(result.reason)] : [],
    );
    try {
      const refreshedDocuments = await fetchDocuments(workspace);
      if (!refreshedDocuments.ok) {
        throw new Error(await readApiError(refreshedDocuments));
      }
      setDocuments((await refreshedDocuments.json()) as UploadedDocument[]);
    } catch (refreshError) {
      const processedDocuments = processingResults.flatMap((result) =>
        result.status === "fulfilled" ? [result.value] : [],
      );
      setDocuments((currentDocuments) => {
        const documentsById = new Map(
          currentDocuments.map((document) => [document.id, document]),
        );
        for (const document of processedDocuments) {
          documentsById.set(document.id, document);
        }
        return Array.from(documentsById.values());
      });
      processingFailures.push(
        refreshError instanceof Error
          ? refreshError.message
          : "Impossible d’actualiser les documents.",
      );
    } finally {
      setIsProcessing(false);
    }
    const failures = [...uploadFailures, ...processingFailures];
    setError(failures.length > 0 ? failures.join(" ") : null);
    if (inputRef.current) inputRef.current.value = "";
  }

  async function deleteDocument(document: UploadedDocument) {
    if (!workspace || deletingDocumentId) return;

    const shouldDelete = window.confirm(
      `Supprimer définitivement « ${document.original_filename} » ?\n\nLe fichier sera supprimé et le rapport du dossier devra être recalculé.`,
    );
    if (!shouldDelete) return;

    setDeletingDocumentId(document.id);
    setError(null);
    try {
      const response = await fetch(
        `${API_URL}/analysis-cases/${workspace.caseId}/documents/${document.id}`,
        { method: "DELETE" },
      );
      if (!response.ok) throw new Error(await readApiError(response));
      setDocuments((currentDocuments) =>
        currentDocuments.filter(({ id }) => id !== document.id),
      );
    } catch (deletionError) {
      setError(
        deletionError instanceof Error
          ? deletionError.message
          : "Impossible de supprimer ce document.",
      );
    } finally {
      setDeletingDocumentId(null);
    }
  }

  const expectedDocuments = expectedDocumentsFor(propertyType);
  const matchedDocumentIds = new Set<string>();
  const coverage = expectedDocuments.map((expectation) => {
    const matchingDocuments = documents.filter(
      (document) =>
        document.status !== "failed" &&
        document.document_type !== null &&
        expectation.acceptedTypes.includes(document.document_type),
    );
    for (const document of matchingDocuments) matchedDocumentIds.add(document.id);
    return { expectation, documents: matchingDocuments };
  });
  const otherDocuments = documents.filter((document) => !matchedDocumentIds.has(document.id));
  const missingCount = propertyType === "unknown"
    ? 0
    : coverage.filter(({ documents: matchingDocuments }) => matchingDocuments.length === 0).length;

  return (
    <div className="document-workspace">
      <PropertyTypeSelector
        value={propertyType}
        isSaving={isSavingPropertyType}
        onChange={(value) => void updatePropertyType(value)}
      />

      <div className="upload-card">
        <div className="upload-card-copy">
          <span className="upload-icon" aria-hidden="true"><Icon name="upload" /></span>
          <div>
            <h2>Ajouter des documents</h2>
            <p>PDF uniquement, 25 Mo maximum par fichier.</p>
          </div>
        </div>
        <label className={`file-button${isUploading || isProcessing || isInitializing ? " is-disabled" : ""}`}>
          <Icon name="upload" />
          {isUploading
            ? "Import en cours…"
            : isProcessing
              ? "Analyse en cours…"
              : "Choisir des fichiers"}
          <input
            ref={inputRef}
            type="file"
            name="property-documents"
            aria-label="Choisir des documents PDF"
            accept="application/pdf,.pdf"
            multiple
            disabled={!workspace || isUploading || isProcessing || isInitializing}
            onChange={(event) =>
              void uploadFiles(Array.from(event.currentTarget.files ?? []))
            }
          />
        </label>
        <p className="privacy-note"><Icon name="shield" /> Stockage privé</p>
      </div>

      {error ? (
        <div className="upload-error" role="alert">
          <strong>Action interrompue</strong>
          <span>{error}</span>
        </div>
      ) : null}

      <section className="document-coverage" aria-labelledby="document-coverage-title">
        <div className="document-list-heading">
          <div>
            <p className="section-kicker">{propertyTypeLabels[propertyType]}</p>
            <h2 id="document-coverage-title">Documents à réunir</h2>
            <p>
              {propertyType === "unknown"
                ? "Choisissez le type de logement pour identifier précisément les pièces manquantes."
                : missingCount === 0
                  ? "Toutes les catégories attendues sont couvertes."
                  : `${missingCount} catégorie${missingCount === 1 ? "" : "s"} de documents à compléter.`}
            </p>
          </div>
          <button
            className="refresh-button"
            type="button"
            disabled={!workspace || isRefreshing}
            onClick={() => void refreshDocuments()}
          >
            <Icon name="refresh" />
            <span>{isRefreshing ? "Actualisation…" : "Actualiser"}</span>
          </button>
        </div>

        {isInitializing ? (
          <div className="document-empty">Chargement de votre dossier…</div>
        ) : (
          <ul className="coverage-list">
            {coverage.map(({ expectation, documents: matchingDocuments }) => (
              <ExpectedDocumentRow
                key={expectation.key}
                expectation={expectation}
                documents={matchingDocuments}
                propertyType={propertyType}
                deletingDocumentId={deletingDocumentId}
                onDelete={(document) => void deleteDocument(document)}
                onViewDpe={(document) => setViewingDpe({
                  documentId: document.id,
                  filename: document.original_filename,
                })}
                onViewExtraction={(document) => setViewingExtraction({
                  documentId: document.id,
                  filename: document.original_filename,
                })}
                onView={(document) => setViewingDocument({
                  documentId: document.id,
                  filename: document.original_filename,
                })}
              />
            ))}
          </ul>
        )}
      </section>

      {!isInitializing && otherDocuments.length > 0 ? (
        <section className="other-documents" aria-labelledby="other-documents-title">
          <div className="document-list-heading">
            <div>
              <p className="section-kicker">Autres fichiers</p>
              <h2 id="other-documents-title">À classer ou complémentaires <span>{otherDocuments.length}</span></h2>
            </div>
          </div>
          <div className="other-document-list">
            {otherDocuments.map((document) => (
              <DocumentFile
                key={document.id}
                document={document}
                deletingDocumentId={deletingDocumentId}
                showType
                onDelete={(item) => void deleteDocument(item)}
                onViewDpe={(document) => setViewingDpe({
                  documentId: document.id,
                  filename: document.original_filename,
                })}
                onViewExtraction={(document) => setViewingExtraction({
                  documentId: document.id,
                  filename: document.original_filename,
                })}
                onView={(document) => setViewingDocument({
                  documentId: document.id,
                  filename: document.original_filename,
                })}
              />
            ))}
          </div>
        </section>
      ) : null}
      {viewingDocument ? (
        <PdfViewer
          document={viewingDocument}
          onClose={() => setViewingDocument(null)}
        />
      ) : null}
      {viewingExtraction ? (
        <RawExtractionViewer
          document={viewingExtraction}
          onClose={() => setViewingExtraction(null)}
        />
      ) : null}
      {viewingDpe ? (
        <DpeExtractionViewer
          document={viewingDpe}
          onClose={() => setViewingDpe(null)}
        />
      ) : null}
    </div>
  );
}
