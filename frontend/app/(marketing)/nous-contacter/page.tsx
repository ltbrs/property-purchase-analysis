import type { Metadata } from "next";

import { ContactForm } from "@/components/marketing/contact-form";

export const metadata: Metadata = {
  title: "Nous contacter",
  description:
    "Une question sur Acquora, votre analyse immobilière ou la confidentialité de vos documents ? Écrivez-nous.",
  alternates: { canonical: "https://acquora.fr/nous-contacter" },
};

export default function ContactPage() {
  return (
    <div className="contact-page">
      <section className="contact-intro" aria-labelledby="contact-title">
        <p className="contact-kicker">Nous contacter</p>
        <h1 id="contact-title">Parlons de votre projet.</h1>
        <p className="contact-lead">
          Une question sur Acquora, un retour sur une analyse ou une demande de
          partenariat ? Écrivez-nous. Votre message arrivera directement dans
          notre espace de suivi.
        </p>

        <div className="contact-expectations" aria-label="À quoi vous attendre">
          <article>
            <strong>Une réponse humaine</strong>
            <p>Chaque demande est lue par l’équipe Acquora.</p>
          </article>
          <article>
            <strong>Vos données restent sobres</strong>
            <p>Nous conservons uniquement les informations utiles à votre demande.</p>
          </article>
          <article>
            <strong>Aucun document sensible</strong>
            <p>
              N’ajoutez pas de document immobilier dans ce formulaire. Utilisez
              votre espace personnel pour vos analyses.
            </p>
          </article>
        </div>
      </section>

      <section className="contact-form-panel" aria-label="Formulaire de contact">
        <div className="contact-form-heading">
          <span>Votre message</span>
          <p>Tous les champs sont obligatoires.</p>
        </div>
        <ContactForm />
      </section>
    </div>
  );
}
