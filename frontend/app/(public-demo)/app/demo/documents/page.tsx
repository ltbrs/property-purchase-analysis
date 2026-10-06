import { DocumentUpload } from "@/features/documents/document-upload";

export default function PublicDemoDocumentsPage() {
  return (
    <section className="upload-page">
      <div className="upload-heading">
        <div>
          <p className="eyebrow">Dossier de démonstration</p>
          <h1>Documents du bien</h1>
        </div>
        <p>Consultez les pièces fictives analysées et leurs sources.</p>
      </div>
      <DocumentUpload publicDemo />
    </section>
  );
}
