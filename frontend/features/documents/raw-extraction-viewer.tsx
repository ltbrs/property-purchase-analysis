"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/icons";
import { API_URL, getWorkspace, readApiError } from "@/lib/workspace";

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
};

type RawExtraction = {
  parser_name: string;
  parser_version: string | null;
  duration_ms: number;
  metadata: Record<string, unknown>;
  pages: ExtractionPage[];
  created_at: string;
};

export function RawExtractionViewer({
  document,
  onClose,
}: {
  document: RawExtractionSelection;
  onClose: () => void;
}) {
  const [extraction, setExtraction] = useState<RawExtraction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    const previousActiveElement = window.document.activeElement;
    const previousOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    async function loadExtraction() {
      const workspace = getWorkspace();
      if (!workspace) {
        setError("Aucun dossier n’est actuellement sélectionné.");
        return;
      }

      try {
        const response = await fetch(
          `${API_URL}/analysis-cases/${workspace.caseId}/documents/${document.documentId}/extraction`,
          {
            cache: "no-store",
            signal: controller.signal,
          },
        );
        if (!response.ok) throw new Error(await readApiError(response));
        setExtraction((await response.json()) as RawExtraction);
      } catch (loadError) {
        if (controller.signal.aborted) return;
        setError(
          loadError instanceof Error
            ? loadError.message
            : "L’extraction brute ne peut pas être affichée pour le moment.",
        );
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    void loadExtraction();
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      controller.abort();
      window.removeEventListener("keydown", closeOnEscape);
      window.document.body.style.overflow = previousOverflow;
      if (previousActiveElement instanceof HTMLElement) previousActiveElement.focus();
    };
  }, [document.documentId, onClose]);

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
            <p className="section-kicker">Extraction brute Xberg</p>
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
          {error ? (
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
                Cette vue restitue le texte et les tableaux tels que Xberg les a
                détectés. Une information visible dans le PDF peut manquer ici,
                notamment lorsqu’elle est intégrée à un graphique ou une image.
              </p>
              <div className="raw-extraction-pages">
                {extraction.pages.map((page) => (
                  <article className="raw-extraction-page" key={page.page_number}>
                    <header>
                      <strong>Page {page.page_number}</strong>
                      <span>
                        {page.text.trim().length.toLocaleString("fr-FR")} caractères
                        {page.tables.length > 0
                          ? ` · ${page.tables.length} tableau${page.tables.length === 1 ? "" : "x"}`
                          : ""}
                      </span>
                    </header>
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
