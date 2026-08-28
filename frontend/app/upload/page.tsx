import { DocumentUpload } from "../../features/documents/document-upload";

export default function UploadPage() {
  return (
    <section className="upload-page">
      <div className="upload-heading">
        <div>
          <p className="eyebrow">Bibliothèque</p>
          <h1>Documents</h1>
        </div>
        <p>Ajoutez les pièces disponibles. PDF uniquement, 25 Mo maximum.</p>
      </div>
      <DocumentUpload />
    </section>
  );
}
