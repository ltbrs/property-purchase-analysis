import Link from "next/link";

import { Icon } from "@/components/icons";
import { productRoutes } from "@/lib/routes";
import { createMarketingMetadata } from "@/lib/seo";

export const metadata = createMarketingMetadata({
  title: "Tarifs de l’analyse documentaire immobilière",
  description:
    "Découvrez les tarifs Acquora pour analyser les documents d’un achat immobilier : dossier gratuit, analyse complète ou pack de trois analyses.",
  path: "/tarifs",
});

const offers = [
  {
    name: "Dossier gratuit",
    description: "Pour préparer le bien et vérifier les pièces à réunir avant l’analyse.",
    price: "0 €",
    priceDetail: "sans carte bancaire",
    href: productRoutes.cases,
    cta: "Créer un dossier",
    features: [
      { label: "Biens concernés", value: "1 bien à préparer" },
      { label: "Documents", value: "liste des pièces attendues" },
      { label: "Risques et coûts", value: "non inclus" },
      { label: "Incohérences et informations manquantes", value: "non incluses" },
      { label: "Sources et pages", value: "non incluses" },
      { label: "Questions à poser", value: "non incluses" },
      { label: "Accès", value: "création sans carte bancaire" },
    ],
  },
  {
    name: "Analyse complète",
    description: "Pour examiner un bien avant de faire une offre ou de vous engager.",
    price: "19 €",
    priceDetail: "TTC par dossier",
    href: `${productRoutes.account}?offre=single_analysis`,
    cta: "Choisir cette analyse",
    features: [
      { label: "Biens concernés", value: "1 bien analysé" },
      { label: "Documents", value: "analyse complète" },
      { label: "Risques et coûts", value: "inclus" },
      { label: "Incohérences et informations manquantes", value: "incluses" },
      { label: "Sources et pages", value: "incluses" },
      { label: "Questions à poser", value: "incluses" },
      { label: "Accès", value: "ajout de documents pendant 30 jours" },
    ],
  },
  {
    name: "Pack Recherche",
    description: "Pour comparer plusieurs biens au fil de votre recherche immobilière.",
    price: "39 €",
    priceDetail: "TTC pour 3 dossiers",
    href: `${productRoutes.account}?offre=search_pack`,
    cta: "Choisir le pack",
    features: [
      { label: "Biens concernés", value: "3 biens analysés" },
      { label: "Documents", value: "analyse complète pour chaque bien" },
      { label: "Risques et coûts", value: "inclus pour chaque bien" },
      { label: "Incohérences et informations manquantes", value: "incluses pour chaque bien" },
      { label: "Sources et pages", value: "incluses pour chaque bien" },
      { label: "Questions à poser", value: "incluses pour chaque bien" },
      { label: "Accès", value: "3 crédits valables 12 mois" },
    ],
  },
] as const;

export default function PricingPage() {
  return (
    <div className="pricing-page">
      <section className="pricing-hero" aria-labelledby="pricing-title">
        <p className="pricing-kicker"><span /> Tarifs</p>
        <h1 id="pricing-title">Un prix simple pour une décision importante.</h1>
        <p>
          Préparez gratuitement votre dossier, analysez un bien en profondeur ou
          gardez trois analyses pour votre recherche. Aucun abonnement.
        </p>
        <span className="pricing-launch-note">
          <Icon name="info" /> Paiement unique, sans abonnement.
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
                <li key={feature.label}>
                  <Icon name="check" />
                  <span>{feature.label} : <strong>{feature.value}</strong></span>
                </li>
              ))}
            </ul>
            <Link className="pricing-cta" href={offer.href}>{offer.cta}</Link>
          </article>
        ))}
      </section>

      <p className="pricing-payment-note">
        Paiement unique, sans abonnement. Les prix affichés sont toutes taxes comprises.
      </p>

      {/*
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
      */}
    </div>
  );
}
