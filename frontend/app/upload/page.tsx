import { DocumentUpload } from "../../features/documents/document-upload";

export default function UploadPage() {
  return (
    <section className="upload-page">
      <div className="upload-heading">
        <p className="eyebrow">Documents du bien</p>
        <h1>Constituez votre dossier d’analyse</h1>
        <p>
          Ajoutez les diagnostics, procès-verbaux et documents financiers dont
          vous disposez. Ils restent privés et chaque constat conservera sa source.
        </p>
      </div>
      <DocumentUpload />
    </section>
  );
}
