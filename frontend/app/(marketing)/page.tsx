import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { ButtonLink } from "@/components/design-system/button-link";
import { Icon, type IconName } from "@/components/icons";
import { ProductWorkflowPlayer } from "@/components/marketing/product-workflow-player";
import { marketingRoutes, productRoutes } from "@/lib/routes";

export const metadata: Metadata = {
  description:
    "Acquora analyse les documents de votre achat immobilier et met en évidence risques, coûts futurs, incohérences et pièces manquantes.",
};

const trustPoints = [
  { icon: "shield", label: "Documents privés" },
  { icon: "document", label: "Sources et pages citées" },
  { icon: "eye", label: "Constats faciles à vérifier" },
] satisfies Array<{ icon: IconName; label: string }>;

const workflowSteps = [
  {
    number: "01",
    icon: "upload" as const,
    title: "Rassemblez vos documents",
    text: "Ajoutez DPE, diagnostics, procès-verbaux d’AG, charges et documents financiers.",
  },
  {
    number: "02",
    icon: "refresh" as const,
    title: "Acquora les recoupe",
    text: "Les informations utiles sont structurées, comparées et vérifiées par des règles explicites.",
  },
  {
    number: "03",
    icon: "gauge" as const,
    title: "Vous voyez l’essentiel",
    text: "Risques, coûts à anticiper, incohérences et questions à poser sont réunis dans un rapport sourcé.",
  },
];

const reportItems = [
  {
    icon: "alert" as const,
    tone: "critical",
    eyebrow: "Risque confirmé",
    title: "DPE classé F",
    source: "DPE.pdf · page 2",
  },
  {
    icon: "wrench" as const,
    tone: "warning",
    eyebrow: "Coût à clarifier",
    title: "Ravalement évoqué, non chiffré",
    source: "PV d’AG 2025 · page 11",
  },
  {
    icon: "document" as const,
    tone: "missing",
    eyebrow: "Information manquante",
    title: "Plan pluriannuel de travaux absent",
    source: "À demander au syndic",
  },
];

export default function MarketingHomePage() {
  return (
    <div className="marketing-home">
      <section className="home-hero" aria-labelledby="hero-title">
        <div className="home-hero-copy">
          <p className="home-kicker"><span /> L’analyse documentaire avant d’acheter</p>
          <h1 id="hero-title">Le bien vous plaît.<br />Vérifiez ce qui compte.</h1>
          <p className="home-hero-lead">
            Acquora lit les documents de votre achat immobilier et transforme
            les informations dispersées en un rapport clair, sourcé et utile
            avant de vous engager.
          </p>
          <div className="home-hero-actions">
            <ButtonLink href={productRoutes.home} className="home-primary-cta">
              Analyser mon bien <Icon name="arrow" />
            </ButtonLink>
            <Link className="home-secondary-cta" href={marketingRoutes.exampleAnalysis}>
              Voir un exemple d’analyse <Icon name="chevron" />
            </Link>
          </div>
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
              alt="Appartement parisien lumineux avec parquet et grandes fenêtres"
              fill
              priority
              sizes="(max-width: 768px) 100vw, 52vw"
            />
          </div>
          <div className="home-report-float">
            <div className="home-report-float-top">
              <span className="home-mini-icon"><Icon name="shield" /></span>
              <span><small>Rapport Acquora</small><strong>Les points à vérifier</strong></span>
              <span className="home-report-status">Prêt</span>
            </div>
            <div className="home-report-line">
              <span className="home-risk-dot home-risk-dot--critical" />
              <span><strong>DPE classé F</strong><small>Source : DPE · page 2</small></span>
            </div>
            <div className="home-report-line">
              <span className="home-risk-dot home-risk-dot--warning" />
              <span><strong>Travaux à chiffrer</strong><small>Source : PV d’AG · page 11</small></span>
            </div>
          </div>
          <span className="home-photo-caption">Un achat serein commence par les bons faits.</span>
        </div>
      </section>

      <section className="home-problem" aria-labelledby="problem-title">
        <p className="home-section-label">Avant le compromis</p>
        <h2 id="problem-title">Des centaines de pages.<br />Une décision qui, elle, ne peut pas attendre.</h2>
        <p>
          DPE, diagnostics, appels de fonds, travaux votés, procès-verbaux de copropriété…
          Acquora vous aide à relier les informations qui peuvent changer le vrai coût de votre achat.
        </p>
        <div className="home-topic-row" aria-label="Sujets analysés">
          <span><Icon name="wallet" /> Finances</span>
          <span><Icon name="building" /> Copropriété</span>
          <span><Icon name="leaf" /> Énergie</span>
          <span><Icon name="wrench" /> Travaux</span>
        </div>
      </section>

      <section className="home-workflow" aria-labelledby="workflow-title">
        <div className="home-section-heading">
          <div>
            <p className="home-section-label">Comment ça marche</p>
            <h2 id="workflow-title">De vos PDF à une vision claire.</h2>
          </div>
          <p>Un parcours simple, conçu pour vous aider à vérifier l’essentiel sans transformer votre achat en audit à plein temps.</p>
        </div>
        <div className="home-workflow-video">
          <ProductWorkflowPlayer />
        </div>
        <div className="home-workflow-steps">
          {workflowSteps.map((step) => (
            <article key={step.number}>
              <div className="home-step-top">
                <span className="home-step-icon"><Icon name={step.icon} /></span>
                <span className="home-step-number">{step.number}</span>
              </div>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="home-evidence" aria-labelledby="evidence-title">
        <div className="home-evidence-copy">
          <p className="home-section-label">Clair, mais jamais vague</p>
          <h2 id="evidence-title">Chaque constat revient à sa source.</h2>
          <p>
            Acquora distingue les faits confirmés, les risques à examiner,
            les incohérences et les informations absentes. Quand une page
            justifie un constat, elle reste accessible depuis le rapport.
          </p>
          <ul>
            <li><Icon name="check" /> Document et page associés</li>
            <li><Icon name="check" /> Niveau d’importance explicite</li>
            <li><Icon name="check" /> Incertitudes signalées, jamais masquées</li>
          </ul>
          <Link href={marketingRoutes.features} className="home-inline-link">
            Découvrir les fonctionnalités <Icon name="arrow" />
          </Link>
        </div>
        <div className="home-report-preview" aria-label="Exemple de constats dans un rapport">
          <div className="home-report-preview-header">
            <div>
              <small>Rapport d’analyse</small>
              <strong>Appartement · Paris 12e</strong>
            </div>
            <span><span /> Analyse terminée</span>
          </div>
          <div className="home-report-summary">
            <span>À regarder en priorité</span>
            <strong>3 points méritent votre attention</strong>
          </div>
          <div className="home-report-items">
            {reportItems.map((item) => (
              <div className={`home-report-item home-report-item--${item.tone}`} key={item.title}>
                <span className="home-report-item-icon"><Icon name={item.icon} /></span>
                <span>
                  <small>{item.eyebrow}</small>
                  <strong>{item.title}</strong>
                  <em><Icon name="document" /> {item.source}</em>
                </span>
                <Icon name="chevron" />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="home-final-cta" aria-labelledby="final-cta-title">
        <div>
          <p className="home-section-label">Votre décision mérite mieux qu’une impression.</p>
          <h2 id="final-cta-title">Achetez en sachant.</h2>
        </div>
        <div>
          <p>Créez votre dossier, ajoutez les documents disponibles et commencez à vérifier votre futur bien.</p>
          <ButtonLink href={productRoutes.home} className="home-final-button">
            Commencer mon analyse <Icon name="arrow" />
          </ButtonLink>
        </div>
      </section>
    </div>
  );
}
