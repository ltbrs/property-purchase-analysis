import type { Metadata } from "next";

import { Icon } from "@/components/icons";

export const metadata: Metadata = {
  title: "Tarifs",
  description:
    "Découvrez les tarifs Acquora pour analyser les documents d’un achat immobilier : aperçu gratuit, analyse complète ou pack de trois analyses.",
};

const offers = [
  {
    name: "Aperçu gratuit",
    description: "Pour vérifier qu’Acquora comprend bien les premières pièces du bien.",
    price: "0 €",
    priceDetail: "sans carte bancaire",
    features: [
      "1 document analysé",
      "Informations principales extraites",
      "Nombre de points de vigilance détectés",
      "Détails du rapport partiellement masqués",
    ],
  },
  {
    name: "Analyse complète",
    description: "Pour examiner un bien avant de faire une offre ou de vous engager.",
    price: "39 €",
    priceDetail: "TTC par dossier",
    features: [
      "Analyse complète des documents du dossier",
      "Risques et coûts à anticiper",
      "Incohérences et informations manquantes",
      "Sources et pages associées aux constats",
      "Questions utiles à transmettre aux professionnels",
    ],
  },
  {
    name: "Pack Recherche",
    description: "Pour comparer plusieurs biens au fil de votre recherche immobilière.",
    price: "79 €",
    priceDetail: "TTC pour 3 dossiers",
    features: [
      "3 analyses complètes",
      "Les mêmes contrôles pour chaque bien",
      "Analyses utilisables sans date limite",
      "Économie de 38 € par rapport à trois analyses séparées",
    ],
  },
] as const;

const comparisons = [
  {
    label: "Documents analysés",
    values: ["1 document", "Dossier complet", "3 dossiers complets"],
  },
  {
    label: "Constats détaillés et sourcés",
    values: ["Aperçu partiel", "Inclus", "Inclus"],
  },
  {
    label: "Informations manquantes et incohérences",
    values: ["Nombre détecté", "Détail inclus", "Détail inclus"],
  },
  {
    label: "Questions à poser",
    values: ["Non incluses", "Incluses", "Incluses"],
  },
  {
    label: "Durée de validité",
    values: ["Sans objet", "Sans objet", "Sans date limite"],
  },
] as const;

const questions = [
  {
    title: "Quand pourrai-je acheter une analyse ?",
    answer:
      "Acquora n’est pas encore ouvert au public. Les offres et les paiements sont donc désactivés pour le moment.",
  },
  {
    title: "Le pack de trois analyses expire-t-il ?",
    answer:
      "Non. Les trois analyses du Pack Recherche pourront être utilisées quand vous le souhaitez, sans date limite.",
  },
  {
    title: "Une analyse remplace-t-elle l’avis d’un professionnel ?",
    answer:
      "Non. Acquora est un outil d’aide à la compréhension et à la décision. Il ne remplace pas les conseils d’un notaire, d’un diagnostiqueur ou d’un professionnel du bâtiment.",
  },
] as const;

export default function PricingPage() {
  return (
    <div className="pricing-page">
      <section className="pricing-hero" aria-labelledby="pricing-title">
        {/* <p className="pricing-kicker"><span /> Tarifs</p>
        <h1 id="pricing-title">Un prix simple pour une décision importante.</h1>
        <p>
          Commencez par un aperçu, analysez un bien en profondeur ou gardez
          trois analyses pour votre recherche. Aucun abonnement.
        </p> */}
        <span className="pricing-launch-note">
          <Icon name="info" /> Acquora ouvre bientôt. Les achats sont désactivés pour le moment.
        </span>
      </section>

      <section className="pricing-offers" aria-label="Offres Acquora">
        {offers.map((offer) => (
          <article className="pricing-card" key={offer.name}>
            <div className="pricing-card-heading">
              <h2>{offer.name}</h2>
              <p>{offer.description}</p>
            </div>
            <div className="pricing-price">
              <strong>{offer.price}</strong>
              <span>{offer.priceDetail}</span>
            </div>
            <ul>
              {offer.features.map((feature) => (
                <li key={feature}><Icon name="check" /> {feature}</li>
              ))}
            </ul>
            <button type="button" disabled>Bientôt disponible</button>
          </article>
        ))}
      </section>

      <p className="pricing-payment-note">
        Paiement unique, sans abonnement. Les prix affichés sont toutes taxes comprises.
      </p>

      <section className="pricing-comparison" aria-labelledby="comparison-title">
        <div className="pricing-section-heading">
          <p className="pricing-section-label">Comparer les offres</p>
          <h2 id="comparison-title">Choisissez selon l’avancement de votre recherche.</h2>
        </div>
        <div className="pricing-table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Fonctionnalité</th>
                {offers.map((offer) => <th scope="col" key={offer.name}>{offer.name}</th>)}
              </tr>
            </thead>
            <tbody>
              {comparisons.map((row) => (
                <tr key={row.label}>
                  <th scope="row">{row.label}</th>
                  {row.values.map((value, index) => (
                    <td key={`${row.label}-${offers[index].name}`}>{value}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="pricing-reassurance" aria-labelledby="reassurance-title">
        <div>
          <p className="pricing-section-label">Ce que vous payez</p>
          <h2 id="reassurance-title">Un rapport fait pour vérifier, pas pour impressionner.</h2>
          <p>
            L’analyse complète rassemble les faits importants, les points de
            vigilance, les incohérences et les pièces absentes. Chaque constat
            important revient au document et à la page qui le justifient quand
            cette information est disponible.
          </p>
        </div>
        <div className="pricing-reassurance-list">
          <span><Icon name="shield" /><strong>Documents privés</strong><small>Vos pièces ne sont pas rendues publiques.</small></span>
          <span><Icon name="document" /><strong>Sources vérifiables</strong><small>Les constats renvoient aux pièces d’origine.</small></span>
          <span><Icon name="eye" /><strong>Incertitudes visibles</strong><small>Ce qui manque ou reste ambigu est signalé.</small></span>
        </div>
      </section>

      <section className="pricing-faq" aria-labelledby="pricing-faq-title">
        <div className="pricing-section-heading">
          <p className="pricing-section-label">Questions fréquentes</p>
          <h2 id="pricing-faq-title">Avant de choisir.</h2>
        </div>
        <div className="pricing-faq-list">
          {questions.map((question) => (
            <article key={question.title}>
              <h3>{question.title}</h3>
              <p>{question.answer}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
