"use client";

import { useEffect, useState } from "react";

import { Icon } from "@/components/icons";
import { useDocumentDialog } from "@/features/documents/use-document-dialog";
import { API_URL, PUBLIC_DEMO_API_URL, getWorkspace, readApiError } from "@/lib/workspace";

export type RawExtractionSelection = {
  documentId: string;
  filename: string;
};

type ExtractedTable = {
  cells: string[][];
  markdown: string;
  table_id: string | null;
  columns: string[] | null;
  bounding_box: Record<string, number> | null;
};

type ExtractionPage = {
  page_number: number;
  text: string;
  tables: ExtractedTable[];
  extraction_method: string;
  read_status: string;
  failure_reason: string | null;
};

type RawExtraction = {
  parser_name: string;
  parser_version: string | null;
  duration_ms: number;
  metadata: Record<string, unknown>;
  pages: ExtractionPage[];
  created_at: string;
  processing_stage: string | null;
  failure_reason: string | null;
};

const retryablePageStatuses = ["unreadable", "failed", "limit_exceeded"];

function pageReadingMessage(page: ExtractionPage) {
  switch (page.read_status) {
    case "unreadable": return "Le service de lecture n’a pas pu déchiffrer le texte de cette page.";
    case "failed": return page.failure_reason || "La lecture de cette page a échoué. Vous pouvez réessayer.";
    case "limit_exceeded": return "Cette page n’a pas été lue car la limite de pages scannées a été atteinte.";
    case "retry": return page.failure_reason || "Une nouvelle tentative de lecture est programmée.";
    case "pending": return "Lecture de cette page en attente.";
    default: return null;
  }
}

export function RawExtractionViewer({
  document,
  onClose,
  publicDemo = false,
  canRetry = false,
  processing = false,
  onRetryStarted,
}: {
  document: RawExtractionSelection;
  onClose: () => void;
  publicDemo?: boolean;
  canRetry?: boolean;
  processing?: boolean;
  onRetryStarted?: () => void;
}) {
  const [extraction, setExtraction] = useState<RawExtraction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryError, setRetryError] = useState<string | null>(null);
  const [retryingPage, setRetryingPage] = useState<number | null>(null);
  const closeButtonRef = useDocumentDialog(onClose);
  const isProcessing = processing || !!(extraction?.processing_stage
    && !["completed", "failed"].includes(extraction.processing_stage));
  const hasPendingPages = extraction?.processing_stage !== "failed"
    && (extraction?.pages.some((page) => ["pending", "retry"].includes(page.read_status)) ?? false);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function loadExtraction() {
      const workspace = publicDemo ? null : getWorkspace();
      if (!publicDemo && !workspace) {
        setError("Aucun dossier n’est actuellement sélectionné.");
        return;
      }

      try {
        const response = await fetch(
          publicDemo
            ? `${PUBLIC_DEMO_API_URL}/documents/${document.documentId}/extraction`
            : `${API_URL}/analysis-cases/${workspace!.caseId}/documents/${document.documentId}/extraction`,
          {
            cache: "no-store",
            signal: controller.signal,
          },
        );
        if (!response.ok) throw new Error(await readApiError(response));
        const loadedExtraction = (await response.json()) as RawExtraction;
        if (!controller.signal.aborted) {
          setExtraction(loadedExtraction);
          setError(null);
        }
      } catch (loadError) {
        if (controller.signal.aborted) return;
        setError(
          loadError instanceof Error
            ? loadError.message
            : "L’extraction brute ne peut pas être affichée pour le moment.",
        );
      } finally {
        if (!controller.signal.aborted && (isProcessing || hasPendingPages)) {
          timer = setTimeout(() => void loadExtraction(), 3000);
        }
      }
    }

    void loadExtraction();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [document.documentId, publicDemo, isProcessing, hasPendingPages]);

  async function retryPage(pageNumber: number) {
    const workspace = getWorkspace();
    if (!workspace || publicDemo || !canRetry || retryingPage !== null || isProcessing || hasPendingPages) return;
    setRetryingPage(pageNumber);
    setRetryError(null);
    try {
      const response = await fetch(
        `${API_URL}/analysis-cases/${workspace.caseId}/documents/${document.documentId}/extraction/pages/${pageNumber}/retry`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error(await readApiError(response));
      setExtraction((current) => current ? {
        ...current,
        processing_stage: "vision",
        failure_reason: null,
        pages: current.pages.map((page) => page.page_number === pageNumber
          ? { ...page, read_status: "pending", failure_reason: null } : page),
      } : current);
      onRetryStarted?.();
    } catch (retryFailure) {
      setRetryError(retryFailure instanceof Error ? retryFailure.message : "La nouvelle lecture n’a pas pu être lancée.");
    } finally {
      setRetryingPage(null);
    }
  }

  return (
    <div className="pdf-viewer-layer">
      <button
        type="button"
        className="pdf-viewer-backdrop"
        aria-label="Fermer l’extraction brute"
        onClick={onClose}
      />
      <section
        className="pdf-viewer-dialog raw-extraction-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="raw-extraction-title"
      >
        <header className="pdf-viewer-header">
          <div>
            <p className="section-kicker">Texte extrait du document</p>
            <h2 id="raw-extraction-title">{document.filename}</h2>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            className="icon-button"
            aria-label="Fermer"
            onClick={onClose}
          >
            <Icon name="x" />
          </button>
        </header>

        <div className="raw-extraction-content">
          {error && !extraction ? (
            <div className="pdf-viewer-state" role="alert">
              <span className="state-icon"><Icon name="alert" /></span>
              <strong>Extraction indisponible</strong>
              <span>{error}</span>
            </div>
          ) : extraction ? (
            <>
              <div className="raw-extraction-summary">
                <div>
                  <strong>{extraction.pages.length}</strong>
                  <span>pages extraites</span>
                </div>
                <div>
                  <strong>{extraction.parser_name}</strong>
                  <span>
                    {extraction.parser_version
                      ? `version ${extraction.parser_version}`
                      : "version inconnue"}
                  </span>
                </div>
                <div>
                  <strong>{extraction.duration_ms} ms</strong>
                  <span>durée du parsing</span>
                </div>
              </div>
              <p className="raw-extraction-note">
                Cette vue restitue le texte détecté dans le PDF, complété par une
                transcription OpenAI des pages scannées. Les passages illisibles
                restent signalés. Vous pouvez comparer chaque page au document original.
              </p>
              {error || retryError ? <p className="raw-extraction-error" role="alert">{retryError || error}</p> : null}
              {extraction.failure_reason ? <p className="raw-extraction-error" role="status">{extraction.failure_reason}</p> : null}
              <div className="raw-extraction-pages">
                {extraction.pages.map((page) => (
                  <article className="raw-extraction-page" key={page.page_number}>
                    <header>
                      <strong>Page {page.page_number}</strong>
                      <span>
                        {page.extraction_method === "vision" ? "Lecture visuelle · " : "Lecture PDF · "}
                        {page.text.trim().length.toLocaleString("fr-FR")} caractères
                        {page.tables.length > 0
                          ? ` · ${page.tables.length} tableau${page.tables.length === 1 ? "" : "x"}`
                          : ""}
                      </span>
                    </header>
                    {pageReadingMessage(page) ? (
                      <details className="raw-extraction-reading" open>
                        <summary>{["pending", "retry"].includes(page.read_status)
                            ? extraction.processing_stage === "failed" ? "Lecture interrompue" : "Lecture en cours"
                            : "Lecture à relancer"}</summary>
                        <div>
                          <p role="status">{extraction.processing_stage === "failed" && ["pending", "retry"].includes(page.read_status)
                            ? "La lecture de cette page a été interrompue." : pageReadingMessage(page)}</p>
                          {!publicDemo && canRetry && retryablePageStatuses.includes(page.read_status) ? (
                            <button
                              type="button"
                              className="raw-extraction-button"
                              disabled={retryingPage !== null || isProcessing || hasPendingPages}
                              onClick={() => void retryPage(page.page_number)}
                            >
                              <Icon name="refresh" />
                              {retryingPage === page.page_number ? "Relance en cours…" : `Réessayer la page ${page.page_number}`}
                            </button>
                          ) : null}
                        </div>
                      </details>
                    ) : null}
                    <pre>{page.text.trim() || "Aucun texte détecté sur cette page."}</pre>
                    {page.tables.map((table, index) => (
                      <details key={`${page.page_number}-${index}`}>
                        <summary>Tableau {index + 1}</summary>
                        <pre>{table.markdown.trim() || JSON.stringify(table.cells, null, 2)}</pre>
                      </details>
                    ))}
                  </article>
                ))}
              </div>
              <details className="raw-extraction-metadata">
                <summary>Métadonnées techniques</summary>
                <pre>{JSON.stringify(extraction.metadata, null, 2)}</pre>
              </details>
            </>
          ) : (
            <div className="pdf-viewer-state">
              <span className="state-icon is-loading"><Icon name="refresh" /></span>
              <strong>Chargement de l’extraction…</strong>
              <span>Lecture des pages et tableaux persistés.</span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
