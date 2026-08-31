"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/icons";
import { API_URL, getWorkspace, readApiError } from "@/lib/workspace";

export type PdfDocumentSelection = {
  documentId: string;
  filename: string;
  pageNumber?: number;
};

type DocumentViewUrl = {
  url: string;
  expires_at: string;
};

function pdfUrlAtPage(url: string, pageNumber?: number) {
  if (!pageNumber) return url;
  try {
    const pdfUrl = new URL(url);
    pdfUrl.hash = `page=${pageNumber}&view=FitH`;
    return pdfUrl.toString();
  } catch {
    return `${url}#page=${pageNumber}&view=FitH`;
  }
}

export function PdfViewer({
  document,
  onClose,
}: {
  document: PdfDocumentSelection;
  onClose: () => void;
}) {
  const [viewUrl, setViewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    const previousActiveElement = window.document.activeElement;
    const previousOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    async function loadViewUrl() {
      const workspace = getWorkspace();
      if (!workspace) {
        setError("Aucun dossier n’est actuellement sélectionné.");
        return;
      }

      try {
        const response = await fetch(
          `${API_URL}/analysis-cases/${workspace.caseId}/documents/${document.documentId}/view-url`,
          {
            cache: "no-store",
            signal: controller.signal,
          },
        );
        if (!response.ok) throw new Error(await readApiError(response));
        const signedLink = (await response.json()) as DocumentViewUrl;
        setViewUrl(pdfUrlAtPage(signedLink.url, document.pageNumber));
      } catch (loadError) {
        if (controller.signal.aborted) return;
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Le document ne peut pas être affiché pour le moment.",
        );
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    void loadViewUrl();
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      controller.abort();
      window.removeEventListener("keydown", closeOnEscape);
      window.document.body.style.overflow = previousOverflow;
      if (previousActiveElement instanceof HTMLElement) previousActiveElement.focus();
    };
  }, [document.documentId, document.pageNumber, onClose]);

  return (
    <div className="pdf-viewer-layer">
      <button
        type="button"
        className="pdf-viewer-backdrop"
        aria-label="Fermer le document"
        onClick={onClose}
      />
      <section
        className="pdf-viewer-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pdf-viewer-title"
      >
        <header className="pdf-viewer-header">
          <div>
            <p className="section-kicker">
              {document.pageNumber ? `Source · page ${document.pageNumber}` : "Document original"}
            </p>
            <h2 id="pdf-viewer-title">{document.filename}</h2>
          </div>
          <div className="pdf-viewer-actions">
            {viewUrl ? (
              <a href={viewUrl} target="_blank" rel="noreferrer">
                Ouvrir dans un onglet <Icon name="arrow" />
              </a>
            ) : null}
            <button
              ref={closeButtonRef}
              type="button"
              className="icon-button"
              aria-label="Fermer"
              onClick={onClose}
            >
              <Icon name="x" />
            </button>
          </div>
        </header>

        <div className="pdf-viewer-content">
          {error ? (
            <div className="pdf-viewer-state" role="alert">
              <span className="state-icon"><Icon name="alert" /></span>
              <strong>Aperçu indisponible</strong>
              <span>{error}</span>
            </div>
          ) : viewUrl ? (
            <iframe src={viewUrl} title={`Aperçu de ${document.filename}`} />
          ) : (
            <div className="pdf-viewer-state">
              <span className="state-icon is-loading"><Icon name="refresh" /></span>
              <strong>Ouverture du document…</strong>
              <span>Création d’un accès privé temporaire.</span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
