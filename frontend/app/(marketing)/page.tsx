import Image from "next/image";
import Link from "next/link";

import { Icon, type IconName } from "@/components/icons";
import { HomeCta } from "@/components/marketing/home-cta";
import { ProductWorkflowPlayer } from "@/components/marketing/product-workflow-player";
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

const buyerQuestions = [
  {
    icon: "wrench",
    title: "Des travaux à payer après l’achat ?",
    text: "Un ravalement évoqué en AG, une toiture à reprendre, un appel de fonds : retrouvez ce qui est prévu, voté ou encore à chiffrer.",
    documents: "PV d’AG · Carnet d’entretien · Appels de fonds",
  },
  {
    icon: "wallet",
    title: "Un budget plus lourd que prévu ?",
    text: "Charges courantes, dépenses exceptionnelles, taxe foncière : distinguez les montants documentés de ce qu’il reste à confirmer.",
    documents: "Charges · Comptes de copropriété · Taxe foncière",
  },
  {
    icon: "home",
    title: "Un diagnostic qui mérite une explication ?",
    text: "Anomalie électrique, présence d’amiante, réserves de visite ou risque naturel : identifiez les conclusions à faire préciser.",
    documents: "DPE · Diagnostics techniques · État des risques",
  },
  {
    icon: "document",
    title: "Une information essentielle vous manque ?",
    text: "Une pièce ancienne, un lot différent, deux montants incompatibles : repérez les points qui empêchent de comprendre le dossier.",
    documents: "Dates · Lots · Surfaces · Pièces manquantes",
  },
] satisfies Array<{
  icon: IconName;
  title: string;
  text: string;
  documents: string;
}>;

const reportItems = [
  {
    icon: "wrench",
    tone: "warning",
    eyebrow: "Coût à clarifier",
    title: "Un ravalement évoqué, sans budget retrouvé",
    source: "PV d’AG · page 11",
    detail:
      "Le PV mentionne une demande de devis. Cette mention ne permet pas de conclure que les travaux ont été votés ni de calculer votre part.",
    question:
      "Au syndic : les devis et une résolution de vote sont-ils disponibles ?",
  },
  {
    icon: "refresh",
    tone: "warning",
    eyebrow: "Incohérence à vérifier",
    title: "Deux montants de charges à rapprocher",
    source: "Décompte de charges · page 4 et comptes · page 2",
    detail:
      "Les montants diffèrent. Il faut vérifier qu’ils couvrent le même lot, la même période et les mêmes postes avant de conclure à une erreur.",
    question:
      "Au vendeur : quel montant correspond aux charges annuelles de ce lot ?",
  },
  {
    icon: "document",
    tone: "missing",
    eyebrow: "Information manquante",
    title: "Le carnet d’entretien n’a pas été fourni",
    source: "Absent des pièces de cet exemple",
    detail:
      "L’historique de l’entretien de l’immeuble reste incomplet. L’absence de la pièce dans le dossier ne signifie pas que l’immeuble n’est pas entretenu.",
    question:
      "Au syndic : pouvez-vous transmettre le carnet d’entretien à jour ?",
  },
] satisfies Array<{
  icon: IconName;
  tone: string;
  eyebrow: string;
  title: string;
  source: string;
  detail: string;
  question: string;
}>;

const evidenceStats = [
  {
    value: "84,6 %",
    title:
      "des installations électriques de plus de 15 ans étudiées à la vente présentent une anomalie",
    note: "Baromètre ONSE 2025, sur 320 000 diagnostics de vente analysés par Diagamter. Des défauts d’installation, pas des rapports erronés.",
    href: "https://www.onse.fr/wp-content/uploads/2025/05/Barometre-ONSE-2025_020525.pdf#page=2",
    source: "ONSE 2025, page 2",
  },
  {
    value: "90 000",
    title:
      "copropriétés avec une date d’AG approuvant les comptes vieille de plus de deux ans",
    note: "Constat du Sénat en 2024 sur 438 000 copropriétés renseignées. Données déclaratives du registre, dont la qualité fait l’objet de réserves.",
    href: "https://www.senat.fr/rap/r23-736-1/r23-736-11.pdf#page=28",
    source: "Sénat 2024, page 28",
  },
  {
    value: "12,1 M",
    title:
      "de maisons en zone d’exposition moyenne ou forte au retrait-gonflement des argiles",
    note: "Cartographie Géorisques actualisée en 2026, France hexagonale. Une exposition géographique ne prouve pas la présence de fissures.",
    href: "https://www.georisques.gouv.fr/consulter-les-dossiers-thematiques/retrait-gonflement-des-argiles",
    source: "Géorisques, carte 2026",
  },
];

const documentGroups = [
  {
    title: "DPE",
    text: "Classe énergétique, caractéristiques du logement et recommandations de travaux.",
  },
  {
    title: "Diagnostics techniques",
    text: "Conclusions, anomalies et réserves : électricité, gaz, amiante, plomb et autres diagnostics présents.",
  },
  {
    title: "État des risques",
    text: "Expositions mentionnées, adresse du bien et date du document.",
  },
  {
    title: "Taxe foncière",
    text: "Montant annuel documenté, année de l’avis et biens concernés.",
  },
  {
    title: "PV d’assemblée générale",
    text: "Travaux évoqués ou votés, résolutions et sujets récurrents dans l’immeuble.",
  },
  {
    title: "Charges et comptes",
    text: "Charges courantes, appels de fonds, impayés et dépenses de copropriété.",
  },
  {
    title: "Règlement de copropriété",
    text: "Description du lot, règles d’usage et restrictions mentionnées.",
  },
  {
    title: "Carnet d’entretien",
    text: "Historique des travaux et entretien des équipements communs.",
  },
];

const steps = [
  {
    title: "Rassemblez les pièces reçues",
    text: "Créez un dossier pour le bien et ajoutez les documents du vendeur ou de l’agence. Vous pouvez compléter le dossier ensuite.",
  },
  {
    title: "Consultez les points de vigilance",
    text: "Retrouvez les risques, coûts documentés, contradictions et informations manquantes, avec leurs sources lorsqu’elles sont disponibles.",
  },
  {
    title: "Préparez vos questions",
    text: "Revenez aux pièces et faites préciser les points ouverts par le vendeur, le syndic, le notaire ou le professionnel concerné.",
  },
];

const questions = [
  {
    title: "Quels documents vérifier avant un achat immobilier ?",
    answer:
      "Commencez par le DPE, les diagnostics techniques et l’état des risques. Pour un appartement en copropriété, examinez aussi les PV d’AG, les charges et comptes, le règlement et le carnet d’entretien. L’avis de taxe foncière complète votre lecture du budget. Les pièces nécessaires dépendent du bien et de sa situation.",
  },
  {
    title: "Puis-je commencer sans avoir tous les documents ?",
    answer:
      "Oui. Vous pouvez créer votre dossier avec les pièces déjà reçues et le compléter ensuite. Les informations absentes restent des points à clarifier : un dossier incomplet ne permet pas de conclure à l’absence de risque.",
  },
  {
    title: "Acquora peut-il dire si un DPE est faux ?",
    answer:
      "Acquora aide à lire le DPE et à relever les incohérences visibles dans les pièces fournies. Une analyse documentaire ne peut pas vérifier les mesures prises sur place ni certifier l’exactitude du diagnostic. Un doute sur les données du logement doit être examiné avec un diagnostiqueur.",
  },
  {
    title: "Est-ce utile si j’ai déjà un notaire ?",
    answer:
      "Le rapport vous aide à préparer vos échanges : travaux à préciser, montants à rapprocher, documents à demander. Il complète votre lecture du dossier et ne remplace ni les vérifications du notaire, ni une expertise technique, ni un conseil juridique ou financier.",
  },
  {
    title: "Combien coûte l’analyse des documents ?",
    answer:
      "Les tarifs annoncés sont un aperçu d’un document à 0 €, une analyse complète à 39 € TTC par dossier et un pack de trois dossiers à 79 € TTC, sans abonnement. Les achats sont actuellement désactivés. L’exemple de rapport sur cette page est consultable sans compte.",
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
          <p className="home-kicker">
            <span /> Avant de signer le compromis
          </p>
          <h1 id="hero-title">
            Votre achat immobilier mérite plus qu’un coup de cœur.
          </h1>
          <p className="home-hero-lead">
            Travaux à venir, charges de copropriété, diagnostics :{" "}
            <strong>
              repérez ce qui peut changer votre budget ou votre décision.
            </strong>{" "}
            Acquora analyse les documents du bien et rassemble les points à
            clarifier dans un rapport sourcé.
          </p>
          <div className="home-hero-actions">
            <HomeCta
              href="#exemple-rapport"
              action="report_example"
              placement="hero"
              className="ds-button ds-button--primary home-primary-cta"
            >
              Voir un exemple de rapport <Icon name="arrow" />
            </HomeCta>
            <HomeCta
              href={productRoutes.home}
              action="create_case"
              placement="hero"
              className="home-secondary-cta"
            >
              Créer mon dossier <Icon name="arrow" />
            </HomeCta>
          </div>
          <p className="home-cta-note">
            Exemple accessible sans compte ni document à envoyer.
          </p>
          <div className="home-trust-list" aria-label="Engagements Acquora">
            {trustPoints.map((point) => (
              <span key={point.label}>
                <Icon name={point.icon} /> {point.label}
              </span>
            ))}
          </div>
        </div>
        <div className="home-hero-visual">
          <div className="home-hero-photo">
            <Image
              src="/images/acquora-apartment-hero.png"
              alt="Séjour lumineux d’un appartement avec parquet et grandes fenêtres"
              fill
              preload
              sizes="(max-width: 1088px) 100vw, 52vw"
            />
          </div>
          <div
            className="home-report-float"
            aria-label="Aperçu fictif de points à clarifier"
          >
            <div className="home-report-float-top">
              <span className="home-mini-icon">
                <Icon name="eye" />
              </span>
              <span>
                <small>Exemple fictif de rapport</small>
                <strong>Avant de vous engager</strong>
              </span>
            </div>
            <div className="home-report-line">
              <span className="home-risk-dot home-risk-dot--warning" />
              <span>
                <strong>Ravalement : quel budget prévoir ?</strong>
                <small>PV d’AG · page 11</small>
              </span>
            </div>
            <div className="home-report-line">
              <span className="home-risk-dot home-risk-dot--warning" />
              <span>
                <strong>Charges : quel montant retenir ?</strong>
                <small>Décompte de charges · page 4</small>
              </span>
            </div>
            <a className="home-float-link" href="#exemple-rapport">
              Lire ces points de vigilance <Icon name="arrow" />
            </a>
          </div>
        </div>
      </section>

      <section className="home-problem" aria-labelledby="problem-title">
        <div className="home-problem-heading">
          <p className="home-section-label">Ce que la visite ne vous dit pas</p>
          <h2 id="problem-title">
            Le prix est affiché.
            <br />
            Les dépenses à venir se cherchent dans les documents.
          </h2>
          <p>
            Vous avez reçu les pièces du bien. Voici les questions auxquelles
            elles devraient vous permettre de répondre.
          </p>
        </div>
        <div className="home-problem-grid">
          {buyerQuestions.map((question) => (
            <article key={question.title}>
              <span>
                <Icon name={question.icon} />
              </span>
              <h3>{question.title}</h3>
              <p>{question.text}</p>
              <p className="home-problem-documents">{question.documents}</p>
            </article>
          ))}
        </div>
      </section>

      <section
        id="exemple-rapport"
        className="home-evidence"
        aria-labelledby="evidence-title"
        tabIndex={-1}
      >
        <div className="home-evidence-copy">
          <p className="home-section-label">Un exemple concret</p>
          <h2 id="evidence-title">
            Du document difficile à lire à la question utile à poser.
          </h2>
          <p>
            Le rapport hiérarchise les points de vigilance, distingue les
            constats des incertitudes et renvoie aux documents et aux pages
            disponibles. Ouvrez un point de cet exemple pour voir comment le
            lire.
          </p>
          <ul>
            <li>
              <Icon name="check" /> Comprenez ce qui mérite votre attention
            </li>
            <li>
              <Icon name="check" /> Retrouvez la source du constat
            </li>
            <li>
              <Icon name="check" /> Identifiez ce qui reste à confirmer
            </li>
          </ul>
          <HomeCta
            href={productRoutes.home}
            action="create_case"
            placement="report"
            className="ds-button ds-button--primary home-primary-cta home-report-cta"
          >
            Créer mon dossier <Icon name="arrow" />
          </HomeCta>
          <p className="home-cta-note">
            Un compte est nécessaire pour ajouter vos documents.
          </p>
        </div>
        <div className="home-report-preview">
          <div className="home-report-preview-header">
            <div>
              <small>Exemple fictif, à titre illustratif</small>
              <strong>Achat d’un appartement en copropriété</strong>
            </div>
          </div>
          <div className="home-report-summary">
            <span>Avant de signer</span>
            <strong>3 points à clarifier</strong>
          </div>
          <div className="home-report-items">
            {reportItems.map((item, index) => (
              <details
                className={`home-example-item home-report-item--${item.tone}`}
                key={item.title}
                open={index === 0}
              >
                <summary>
                  <span className="home-report-item-icon">
                    <Icon name={item.icon} />
                  </span>
                  <span>
                    <small>{item.eyebrow}</small>
                    <strong>{item.title}</strong>
                    <em>
                      <Icon name="document" /> {item.source}
                    </em>
                  </span>
                  <Icon name="chevron" />
                </summary>
                <div className="home-example-detail">
                  <p>{item.detail}</p>
                  <p>
                    <strong>La question à poser</strong>
                    {item.question}
                  </p>
                </div>
              </details>
            ))}
          </div>
          <p className="home-example-note">
            Ces constats et références de pages sont fictifs. Ils illustrent la
            lecture du rapport et ne décrivent aucun bien réel.
          </p>
        </div>
      </section>

      <section className="home-reality" aria-labelledby="reality-title">
        <div className="home-reality-heading">
          <p className="home-section-label">
            Pourquoi prendre le temps de vérifier
          </p>
          <h2 id="reality-title">
            Des enjeux documentés, au-delà de la visite.
          </h2>
          <p>
            Ces données éclairent l’intérêt de lire votre dossier. Elles ne
            permettent pas de conclure sur l’état de votre futur logement.
          </p>
        </div>
        <div className="home-stat-grid">
          {evidenceStats.map((stat) => (
            <article key={stat.value}>
              <strong>{stat.value}</strong>
              <h3>{stat.title}</h3>
              <p>{stat.note}</p>
              <a href={stat.href} target="_blank" rel="noopener noreferrer">
                {stat.source} <Icon name="arrow" />
              </a>
            </article>
          ))}
        </div>
      </section>

      <section className="home-documents" aria-labelledby="documents-title">
        <div className="home-section-heading">
          <div>
            <p className="home-section-label">Les pièces de votre achat</p>
            <h2 id="documents-title">Quels documents Acquora analyse-t-il ?</h2>
          </div>
          <p>
            Maison ou appartement : commencez avec les pièces reçues. Les
            documents de copropriété concernent les biens qui en font partie.
          </p>
        </div>
        <div className="home-document-grid">
          {documentGroups.map((document) => (
            <article key={document.title}>
              <h3>{document.title}</h3>
              <p>{document.text}</p>
            </article>
          ))}
        </div>
        <Link
          href="/blog/documents-achat-appartement"
          className="home-inline-link"
        >
          Consulter la checklist des documents avant l’achat{" "}
          <Icon name="arrow" />
        </Link>
      </section>

      <section className="home-workflow" aria-labelledby="workflow-title">
        <div className="home-section-heading">
          <div>
            <p className="home-section-label">Du dossier à la décision</p>
            <h2 id="workflow-title">
              Avancez avec des points précis à vérifier.
            </h2>
          </div>
          <p>
            Un dossier par bien pour retrouver les documents, les constats et
            les questions encore ouvertes.
          </p>
        </div>
        <ol className="home-workflow-steps">
          {steps.map((step, index) => (
            <li key={step.title}>
              <span className="home-step-number">0{index + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </li>
          ))}
        </ol>
        <details className="home-video-disclosure">
          <summary>
            Voir le parcours Acquora en vidéo <Icon name="chevron" />
          </summary>
          <div className="home-workflow-video">
            <ProductWorkflowPlayer />
          </div>
        </details>
        <Link href={marketingRoutes.howItWorks} className="home-inline-link">
          Comprendre le fonctionnement de l’analyse <Icon name="arrow" />
        </Link>
      </section>

      <section className="home-faq" aria-labelledby="faq-title">
        <div>
          <p className="home-section-label">Avant de commencer</p>
          <h2 id="faq-title">Vos questions sur l’analyse avant achat.</h2>
          <p>
            Un point particulier dans votre dossier ?{" "}
            <Link href={marketingRoutes.contact}>Contactez-nous.</Link>
          </p>
        </div>
        <div className="home-faq-list">
          {questions.map((question) => (
            <details key={question.title}>
              <summary>
                {question.title}
                <Icon name="chevron" />
              </summary>
              <p>{question.answer}</p>
            </details>
          ))}
          <Link href={marketingRoutes.pricing} className="home-inline-link">
            Consulter les tarifs et la disponibilité <Icon name="arrow" />
          </Link>
        </div>
      </section>

      <section className="home-guides" aria-labelledby="guides-title">
        <p className="home-section-label">Préparer votre achat</p>
        <h2 id="guides-title">Deux guides pour aller plus loin.</h2>
        <div>
          <Link href="/blog/documents-achat-appartement">
            <span>Les pièces à demander</span>
            <strong>
              Quels documents vérifier avant d’acheter un appartement ?
            </strong>
            <Icon name="arrow" />
          </Link>
          <Link href="/blog/travaux-votes-avant-compromis">
            <span>Le budget travaux</span>
            <strong>Travaux votés avant le compromis : qui paie ?</strong>
            <Icon name="arrow" />
          </Link>
        </div>
      </section>

      <section className="home-final-cta" aria-labelledby="final-cta-title">
        <div>
          <p className="home-section-label">
            Le bien vous plaît. Faites le point.
          </p>
          <h2 id="final-cta-title">Avant de signer, sachez quoi demander.</h2>
        </div>
        <div>
          <p>
            Rassemblez les documents de votre futur achat pour préparer les
            échanges avec le vendeur, le syndic et le notaire.
          </p>
          <HomeCta
            href={productRoutes.home}
            action="create_case"
            placement="closing"
            className="ds-button ds-button--primary home-final-button"
          >
            Créer mon dossier <Icon name="arrow" />
          </HomeCta>
          <p className="home-launch-note">
            Service en préparation, achats d’analyses désactivés.{" "}
            <HomeCta
              href={marketingRoutes.contact}
              action="contact"
              placement="closing"
              className="home-contact-link"
            >
              Nous contacter
            </HomeCta>
          </p>
        </div>
      </section>
    </div>
  );
}
