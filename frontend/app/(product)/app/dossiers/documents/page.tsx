import { DocumentUpload } from "@/features/documents/document-upload";

export default async function DocumentsPage({ searchParams }: {
  searchParams: Promise<{ import?: string }>;
}) {
  const params = await searchParams;
  return (
    <section className="upload-page">
      <div className="upload-heading">
        <div>
          <p className="eyebrow">Dossier d’achat</p>
          <h1>Documents du bien</h1>
        </div>
        <p>Vérifiez ce qui est reçu, attendu ou encore manquant.</p>
      </div>
      <DocumentUpload pendingDocumentId={typeof params.import === "string" ? params.import : undefined} />
    </section>
  );
}
