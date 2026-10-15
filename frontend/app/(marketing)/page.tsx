import Image from "next/image";
import Link from "next/link";

import { Icon, type IconName } from "@/components/icons";
import { HomeCta } from "@/components/marketing/home-cta";
import { HomeDocumentDrop } from "@/components/marketing/home-document-drop";
import { marketingRoutes, productRoutes } from "@/lib/routes";
import { createMarketingMetadata, SITE_NAME, SITE_URL } from "@/lib/seo";

const pageTitle = "Achat immobilier : vérifiez les documents avant de signer";
const pageDescription =
  "Travaux, charges, diagnostics : Acquora analyse les documents de votre achat immobilier et relève les points à clarifier. Découvrez un exemple de rapport sourcé.";

export const metadata = createMarketingMetadata({
  title: pageTitle,
  description: pageDescription,
  path: "/",
});

const brandEntity = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: `${SITE_URL}/`,
      name: SITE_NAME,
      alternateName: "acquora.fr",
      description: pageDescription,
      inLanguage: "fr-FR",
      publisher: { "@id": `${SITE_URL}/#organization` },
    },
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      url: `${SITE_URL}/`,
      name: SITE_NAME,
      description: pageDescription,
      logo: {
        "@type": "ImageObject",
        url: `${SITE_URL}/icon.svg`,
        width: 64,
        height: 64,
      },
      contactPoint: {
        "@type": "ContactPoint",
        contactType: "service client",
        url: `${SITE_URL}/nous-contacter`,
        availableLanguage: "fr",
      },
    },
    {
      "@type": "WebPage",
      "@id": `${SITE_URL}/#webpage`,
      url: `${SITE_URL}/`,
      name: pageTitle,
      description: pageDescription,
      inLanguage: "fr-FR",
      isPartOf: { "@id": `${SITE_URL}/#website` },
      about: { "@id": `${SITE_URL}/#organization` },
    },
  ],
};

const trustPoints = [
  { icon: "document", label: "Sources consultables" },
  { icon: "eye", label: "Incertitudes signalées" },
  { icon: "shield", label: "Documents privés" },
] satisfies Array<{ icon: IconName; label: string }>;

const documentLabels = [
  "DPE", "Diagnostics techniques", "PV d’AG", "Charges et comptes",
  "Taxe foncière", "État des risques", "Règlement de copropriété", "Carnet d’entretien",
];

const steps = [
  { title: "Ajoutez vos documents", text: "Un dossier par bien, à compléter avec les pièces reçues." },
  { title: "Consultez les constats", text: "Risques, coûts documentés et pièces manquantes, avec leurs sources." },
  { title: "Préparez vos questions", text: "Reprenez les points ouverts avec le vendeur, le syndic ou le notaire." },
];

const questions = [
  {
    title: "Puis-je commencer avec un seul document ?",
    answer: "Oui. Pour votre premier dossier, essayez gratuitement un PDF et découvrez un premier constat sourcé, s’il est disponible. Vous pourrez compléter le dossier après déblocage du rapport.",
  },
  {
    title: "Combien coûte le rapport complet ?",
    answer: "19 € TTC pour un bien, ou 39 € TTC pour trois biens. Paiement unique, sans abonnement. Le dossier démo est accessible sans compte.",
  },
  {
    title: "Le rapport remplace-t-il un professionnel ?",
    answer: "Il prépare vos échanges et signale les incertitudes. Il ne remplace ni les vérifications du notaire, ni une expertise technique, ni un conseil juridique ou financier.",
  },
];

export default function MarketingHomePage() {
  return (
    <div className="marketing-home">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(brandEntity).replace(/</g, "\\u003c"),
        }}
      />
      <section className="home-hero" aria-labelledby="hero-title">
        <div className="home-hero-copy">
          <p className="home-kicker"><span /> Avant de signer le compromis</p>
          <h1 id="hero-title">Votre achat immobilier mérite plus qu’un coup de cœur.</h1>
          <p className="home-hero-hook">
            Travaux, charges, diagnostics : faites le point avant de signer.
          </p>
          <div className="home-hero-actions">
            <a href="#deposer-document" className="ds-button ds-button--primary home-primary-cta">
              Vérifier mon premier document <Icon name="arrow" />
            </a>
            <HomeCta href={productRoutes.demo} action="report_example" placement="hero" className="home-secondary-cta">
              Voir le dossier démo <Icon name="arrow" />
            </HomeCta>
          </div>
          <div className="home-trust-list" aria-label="Engagements Acquora">
            {trustPoints.map((point) => (
              <span key={point.label}><Icon name={point.icon} /> {point.label}</span>
            ))}
          </div>
        </div>
        <HomeDocumentDrop />
      </section>

      <section id="exemple-rapport" className="home-evidence home-evidence--compact" aria-labelledby="evidence-title" tabIndex={-1}>
        <figure className="home-apartment">
          <Image
            src="/images/acquora-apartment-hero.png"
            alt="Séjour lumineux avec parquet et grandes fenêtres"
            fill
            sizes="(max-width: 1088px) 100vw, 50vw"
          />
          <figcaption>Le bien vous plaît.<br />Regardez aussi les documents.</figcaption>
        </figure>
        <div className="home-report-preview home-discovery">
          <p className="home-section-label">Dans le dossier démo</p>
          <h2 id="evidence-title">Des travaux déjà votés.</h2>
          <strong className="home-discovery-amount">6 960 €</strong>
          <p className="home-discovery-summary">
            Quote-part de toiture pour les lots du bien. Le montant restant à votre charge est à clarifier.
          </p>
          <Link href={productRoutes.demoDocuments} className="home-discovery-source">
            <Icon name="document" /> PV d’AG 2026, p. 2 · Appel de fonds toiture, p. 1
          </Link>
          <div className="home-discovery-question">
            <strong>À demander avant de signer</strong>
            <p>Quels appels ont déjà été réglés et quelle répartition est prévue pour la suite ?</p>
          </div>
          <HomeCta href={productRoutes.demo} action="report_example" placement="report" className="ds-button ds-button--primary home-primary-cta home-report-cta">
            Explorer le dossier démo <Icon name="arrow" />
          </HomeCta>
          <p className="home-example-note">Données synthétiques, sans lien avec votre bien.</p>
        </div>
      </section>

      <section className="home-workflow home-workflow--compact" aria-labelledby="workflow-title">
        <p className="home-section-label">Comment ça marche</p>
        <h2 id="workflow-title">Des documents aux questions utiles.</h2>
        <ol className="home-workflow-steps">
          {steps.map((step, index) => (
            <li key={step.title}>
              <span className="home-step-number">0{index + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </li>
          ))}
        </ol>
        <ul className="home-document-tags" aria-label="Documents analysés">
          {documentLabels.map((label) => <li key={label}>{label}</li>)}
        </ul>
        <Link href={marketingRoutes.howItWorks} className="home-inline-link">
          Comprendre l’analyse <Icon name="arrow" />
        </Link>
      </section>

      <section className="home-faq" aria-labelledby="faq-title">
        <div>
          <p className="home-section-label">Avant de commencer</p>
          <h2 id="faq-title">L’essentiel à savoir.</h2>
        </div>
        <div className="home-faq-list">
          {questions.map((question) => (
            <details key={question.title}>
              <summary>{question.title}<Icon name="chevron" /></summary>
              <p>{question.answer}</p>
            </details>
          ))}
          <Link href={marketingRoutes.pricing} className="home-inline-link">
            Voir les tarifs <Icon name="arrow" />
          </Link>
        </div>
      </section>

      <section className="home-guides home-guides--compact" aria-label="Guides pour préparer votre achat">
        <div>
          <Link href="/blog/documents-achat-appartement">
            <strong>Les documents à demander avant l’achat</strong><Icon name="arrow" />
          </Link>
          <Link href="/blog/travaux-votes-avant-compromis">
            <strong>Travaux votés : qui paie ?</strong><Icon name="arrow" />
          </Link>
        </div>
      </section>

      <section className="home-final-cta" aria-labelledby="final-cta-title">
        <div><h2 id="final-cta-title">Avant de signer, sachez quoi demander.</h2></div>
        <div>
          <HomeCta href="#deposer-document" action="create_case" placement="closing" className="ds-button ds-button--primary home-final-button">
            Commencer avec un PDF <Icon name="arrow" />
          </HomeCta>
          <p className="home-launch-note">Premier aperçu gratuit. Rapport complet : 19 € TTC, sans abonnement.</p>
        </div>
      </section>
    </div>
  );
}
