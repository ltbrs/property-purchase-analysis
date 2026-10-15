"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState, type DragEvent } from "react";

import { Icon } from "@/components/icons";
import { savePendingDocument } from "@/lib/pending-document";
import { marketingRoutes, productRoutes } from "@/lib/routes";

export function HomeDocumentDrop() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const busyRef = useRef(false);
  const [isBusy, setIsBusy] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function selectFiles(files: File[]) {
    if (busyRef.current || files.length === 0) return;
    setError(null);
    if (files.length !== 1) {
      setError("Commencez avec un seul PDF. Vous pourrez compléter le dossier ensuite.");
      return;
    }
    busyRef.current = true;
    setIsBusy(true);
    try {
      const id = await savePendingDocument(files[0]);
      router.push(`${productRoutes.home}?import=${encodeURIComponent(id)}`);
    } catch (selectionError) {
      setError(selectionError instanceof Error ? selectionError.message : "Impossible de préparer le PDF. Réessayez.");
      busyRef.current = false;
      setIsBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function drop(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    setIsDragging(false);
    void selectFiles(Array.from(event.dataTransfer.files));
  }

  return (
    <section
      id="deposer-document"
      className={`home-document-drop${isDragging ? " is-dragging" : ""}`}
      aria-labelledby="home-upload-title"
      aria-busy={isBusy}
      onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
      onDragLeave={(event) => {
        if (!(event.relatedTarget instanceof Node) || !event.currentTarget.contains(event.relatedTarget)) setIsDragging(false);
      }}
      onDrop={drop}
    >
      <span className="home-upload-icon"><Icon name="upload" /></span>
      <h2 id="home-upload-title">Commencez avec un PDF.</h2>
      <p>DPE, diagnostic ou PV d’assemblée générale.</p>
      <button
        type="button"
        className="ds-button ds-button--primary home-upload-button"
        disabled={isBusy}
        onClick={() => inputRef.current?.click()}
      >
        {isBusy ? "Préparation du PDF…" : "Choisir mon PDF"}
        <Icon name={isBusy ? "document" : "arrow"} />
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        aria-label="Choisir le premier document PDF du bien"
        onChange={(event) => void selectFiles(Array.from(event.target.files ?? []))}
      />
      <span className="home-upload-format">ou glissez-le ici · PDF jusqu’à 25 Mo</span>
      {error ? <p className="home-upload-error" role="alert">{error}</p> : null}
      <div className="home-upload-offer">
        <strong>Premier dossier : aperçu gratuit</strong>
        <span>Un premier constat et sa source, s’ils sont disponibles. Rapport complet : 19 € TTC, sans abonnement.</span>
      </div>
      <details className="home-upload-privacy">
        <summary><Icon name="shield" /> Documents privés <Icon name="chevron" /></summary>
        <p>
          Votre PDF reste sur cet appareil pendant la connexion, puis est importé dans votre dossier privé.{" "}
          <Link href={marketingRoutes.privacy}>Confidentialité</Link>
        </p>
      </details>
      <Link href={productRoutes.demo} className="home-upload-demo">Voir le dossier démo <Icon name="arrow" /></Link>
    </section>
  );
}
