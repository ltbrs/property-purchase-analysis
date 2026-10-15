"use client";

import { useEffect, useEffectEvent, useRef, useState } from "react";

import { Icon } from "@/components/icons";
import { discardPendingDocument, getPendingDocument } from "@/lib/pending-document";

export function PendingDocumentImport({ id, ready, onImport }: {
  id: string;
  ready: boolean;
  onImport: (file: File, onUploaded: () => Promise<void>) => Promise<boolean>;
}) {
  const started = useRef(false);
  const [attempt, setAttempt] = useState(0);
  const [status, setStatus] = useState("Votre PDF est prêt à être importé.");
  const [hasError, setHasError] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const importDocument = useEffectEvent(async () => {
    setHasError(false);
    setStatus("Import du PDF sélectionné sur la page d’accueil…");
    try {
      const file = await getPendingDocument(id);
      if (!file) {
        setStatus("Le PDF sélectionné n’est plus disponible sur cet appareil. Choisissez-le à nouveau ci-dessous.");
        return;
      }
      const imported = await onImport(file, async () => {
        // Once the server has registered the PDF, don't upload it again on reload.
        await discardPendingDocument(id);
      });
      if (!imported) throw new Error("Le transfert n’a pas abouti. Votre PDF reste disponible pour réessayer.");
      setIsDone(true);
    } catch (error) {
      setHasError(true);
      setStatus(error instanceof Error ? error.message : "Impossible d’importer le PDF. Réessayez.");
    }
  });

  useEffect(() => {
    if (!ready || started.current) return;
    started.current = true;
    void importDocument();
  }, [ready, attempt]);

  if (isDone) return null;
  return (
    <div className="pending-document-import" role={hasError ? "alert" : "status"}>
      <Icon name="document" />
      <p>{status}</p>
      {hasError ? <button type="button" onClick={() => { started.current = false; setAttempt((current) => current + 1); }}>Réessayer</button> : null}
    </div>
  );
}
