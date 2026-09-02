import type { Metadata } from "next";
import Link from "next/link";

import { ButtonLink } from "@/components/design-system/button-link";
import { Icon, type IconName } from "@/components/icons";
import { marketingRoutes, productRoutes } from "@/lib/routes";

export const metadata: Metadata = {
  title: "Comment ça marche",
  description:
    "Découvrez comment Acquora transforme les documents de votre achat immobilier en un rapport clair, recoupé et sourcé.",
};

const documentRows = [
  { name: "DPE", pages: "18 pages", icon: "leaf" as const },
  { name: "Procès-verbaux d’AG", pages: "42 pages", icon: "building" as const },
  { name: "Documents financiers", pages: "27 pages", icon: "wallet" as const },
];

const controlFamilies = [
  {
    icon: "wallet" as const,
    title: "Budget et charges",
    text: "Dépenses récurrentes, impayés, appels de fonds et coûts à venir.",
  },
  {
    icon: "building" as const,
    title: "Copropriété",
    text: "Décisions d’assemblée, travaux discutés, votes et santé de l’immeuble.",
  },
  {
    icon: "leaf" as const,
    title: "Énergie",
    text: "Performance du logement, dépenses estimées et améliorations possibles.",
  },
  {
    icon: "shield" as const,
    title: "Diagnostics et sécurité",
    text: "Validité, anomalies signalées et périmètres qui restent à vérifier.",
  },
  {
    icon: "wrench" as const,
    title: "Travaux",
    text: "Travaux votés, envisagés ou reportés, avec les montants disponibles.",
  },
  {
    icon: "document" as const,
    title: "Pièces et cohérence",
    text: "Documents absents, informations contradictoires et questions à poser.",
  },
] satisfies Array<{ icon: IconName; title: string; text: string }>;

const reportBenefits = [
  "Les sujets importants sont classés par niveau d’attention.",
  "Chaque constat renvoie au document et à la page concernés.",
  "Les informations absentes et les incertitudes restent visibles.",
  "Les prochaines questions à poser sont formulées simplement.",
];

const principles = [
  {
    number: "01",
    title: "Les faits avant les conclusions",
    text: "Acquora distingue ce qui est écrit dans vos documents, ce qui en découle et ce qui reste à confirmer.",
  },
  {
    number: "02",
    title: "Une preuve pour chaque point important",
    text: "Vous pouvez revenir à la pièce et à la page d’origine, sans avoir à nous croire sur parole.",
  },
  {
    number: "03",
    title: "Aucune fausse certitude",
    text: "Quand un document manque, qu’une donnée est ambiguë ou que l’avis d’un professionnel est nécessaire, nous le disons.",
  },
];

export default function HowItWorksPage() {
  return (
    <div className="how-page">
      <section className="how-hero" aria-labelledby="how-hero-title">
        <div className="how-hero-copy">
          <p className="how-kicker"><span /> Comment ça marche</p>
          <h1 id="how-hero-title">
            Vos documents parlent.<br />Acquora les fait parler <em>ensemble.</em>
          </h1>
          <p className="how-hero-lead">
            Déposez les pièces du bien. Acquora les lit, vérifie plus de 100
            points de contrôle et recoupe les informations pour faire ressortir
            ce qui mérite vraiment votre attention.
          </p>
          <div className="how-hero-actions">
            <ButtonLink href={productRoutes.home} className="how-primary-cta">
              Analyser mon bien <Icon name="arrow" />
            </ButtonLink>
            <Link className="how-text-link" href={marketingRoutes.exampleAnalysis}>
              Voir un rapport exemple <Icon name="chevron" />
            </Link>
          </div>
          <div className="how-hero-reassurance" aria-label="Engagements Acquora">
            <span><Icon name="shield" /> Documents privés</span>
            <span><Icon name="eye" /> Sources vérifiables</span>
            <span><Icon name="check" /> Incertitudes signalées</span>
          </div>
        </div>

        <div className="how-workspace" aria-label="Aperçu du parcours d’analyse">
          <div className="how-workspace-topbar">
            <span className="how-workspace-mark"><Icon name="home" /></span>
            <div>
              <strong>Appartement · Lyon 6e</strong>
              <small>Dossier d’achat</small>
            </div>
            <span className="how-secure-pill"><Icon name="shield" /> Privé</span>
          </div>

          <ol className="how-progress" aria-label="Étapes de l’analyse">
            <li className="is-complete"><span><Icon name="check" /></span><small>Documents</small></li>
            <li className="is-current"><span>2</span><small>Analyse</small></li>
            <li><span>3</span><small>Rapport</small></li>
          </ol>

          <div className="how-workspace-body">
            <div className="how-document-list">
              <div className="how-panel-heading">
                <div>
                  <small>Étape 1</small>
                  <strong>Documents reçus</strong>
                </div>
                <span>3 fichiers</span>
              </div>
              {documentRows.map((document) => (
                <div className="how-document-row" key={document.name}>
                  <span className="how-document-icon"><Icon name={document.icon} /></span>
                  <span><strong>{document.name}</strong><small>{document.pages}</small></span>
                  <span className="how-row-check"><Icon name="check" /></span>
                </div>
              ))}
              <div className="how-add-row"><Icon name="upload" /> Ajouter un document</div>
            </div>

            <div className="how-analysis-card">
              <div className="how-analysis-orbit" aria-hidden="true">
                <span><Icon name="document" /></span>
                <span><Icon name="refresh" /></span>
                <span><Icon name="gauge" /></span>
              </div>
              <span className="how-live-pill"><span /> Analyse en cours</span>
              <strong>Les informations sont vérifiées et recoupées</strong>
              <div className="how-analysis-progress"><span /></div>
              <div className="how-analysis-stats">
                <span><strong>100+</strong><small>points contrôlés</small></span>
                <span><strong>3</strong><small>documents croisés</small></span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="how-steps" aria-labelledby="how-steps-title">
        <div className="how-section-intro">
          <p className="how-section-label">Un parcours simple</p>
          <h2 id="how-steps-title">Vous ajoutez les pièces.<br />Nous remettons les faits dans l’ordre.</h2>
          <p>
            Vous n’avez pas besoin de savoir où chercher. Acquora suit le fil du
            dossier, puis vous montre ce qui est confirmé, préoccupant,
            incohérent ou encore manquant.
          </p>
        </div>

        <div className="how-step-list">
          <article>
            <div className="how-step-number"><span>1</span><Icon name="upload" /></div>
            <div>
              <p className="how-step-kicker">Rassembler</p>
              <h3>Déposez les documents disponibles</h3>
              <p>DPE, diagnostics, procès-verbaux, comptes de copropriété ou règlement. Vous pouvez compléter le dossier au fur et à mesure.</p>
            </div>
            <div className="how-mini-form" aria-label="Exemple de dépôt de documents">
              <div className="how-drop-zone"><Icon name="upload" /><strong>Déposez vos PDF ici</strong><small>ou choisissez-les depuis votre appareil</small></div>
              <span><Icon name="shield" /> Vos documents restent privés</span>
            </div>
          </article>

          <article>
            <div className="how-step-number"><span>2</span><Icon name="refresh" /></div>
            <div>
              <p className="how-step-kicker">Comprendre</p>
              <h3>Acquora relie les informations</h3>
              <p>Une mention isolée peut sembler anodine. Comparée aux autres pièces, elle peut révéler un coût, une incohérence ou une information à demander.</p>
            </div>
            <div className="how-cross-mini" aria-label="Exemple d’analyse croisée">
              <div><span><Icon name="document" /></span><small>DPE</small><strong>Fenêtres à remplacer</strong></div>
              <span className="how-cross-plus">+</span>
              <div><span><Icon name="building" /></span><small>Règlement</small><strong>Accord préalable requis</strong></div>
            </div>
          </article>

          <article>
            <div className="how-step-number"><span>3</span><Icon name="gauge" /></div>
            <div>
              <p className="how-step-kicker">Décider</p>
              <h3>Recevez une synthèse exploitable</h3>
              <p>Vous voyez les priorités, leurs sources et les questions à poser avant de faire une offre, de signer ou de chiffrer votre projet.</p>
            </div>
            <div className="how-result-mini" aria-label="Exemple de conclusion Acquora">
              <span className="how-result-icon"><Icon name="alert" /></span>
              <span><small>Point à clarifier</small><strong>Le remplacement des fenêtres demande une autorisation</strong><em><Icon name="document" /> 2 sources rapprochées</em></span>
            </div>
          </article>
        </div>
      </section>

      <section className="how-controls" aria-labelledby="how-controls-title">
        <div className="how-controls-heading">
          <div>
            <p className="how-section-label">Une lecture systématique</p>
            <h2 id="how-controls-title">Plus de 100 points de contrôle.<br />Une seule vue d’ensemble.</h2>
          </div>
          <p>
            Les vérifications utiles dépendent du bien, de votre projet et des
            documents présents. Acquora regarde chaque sujet dans son contexte,
            sans transformer un simple doute en certitude.
          </p>
        </div>

        <div className="how-control-grid">
          {controlFamilies.map((family) => (
            <article key={family.title}>
              <span><Icon name={family.icon} /></span>
              <h3>{family.title}</h3>
              <p>{family.text}</p>
            </article>
          ))}
        </div>

        <div className="how-cross-analysis">
          <div className="how-cross-copy">
            <p className="how-section-label">L’analyse croisée</p>
            <h3>Un document donne un fait.<br />Le dossier donne son contexte.</h3>
            <p>
              Acquora ne lit pas les pièces les unes après les autres. Il
              rapproche les dates, les montants, les décisions et les
              descriptions d’un même sujet pour repérer ce qui ne se voit pas
              à la première lecture.
            </p>
          </div>

          <div className="how-cross-board" aria-label="Exemple de recoupement entre plusieurs documents">
            <div className="how-cross-sources">
              <div><span><Icon name="building" /></span><p><small>PV d’AG · page 8</small><strong>Ravalement évoqué</strong></p><em>2024</em></div>
              <div><span><Icon name="building" /></span><p><small>PV d’AG · page 12</small><strong>Étude technique votée</strong></p><em>2025</em></div>
              <div><span><Icon name="wallet" /></span><p><small>Budget · page 4</small><strong>Aucun montant provisionné</strong></p><em>2026</em></div>
            </div>
            <div className="how-cross-connector"><span><Icon name="refresh" /></span></div>
            <div className="how-cross-finding">
              <div className="how-finding-top"><span><Icon name="wrench" /></span><small>À clarifier avant l’achat</small></div>
              <h4>Un ravalement se prépare, mais son coût n’apparaît pas encore dans le budget.</h4>
              <p>Demandez au syndic le calendrier, l’estimation et la part prévisible pour le lot.</p>
              <div><Icon name="document" /> 3 sources rapprochées</div>
            </div>
          </div>
        </div>
      </section>

      <section className="how-report" aria-labelledby="how-report-title">
        <div className="how-report-preview">
          <div className="how-report-header">
            <div><small>Rapport Acquora</small><strong>Appartement · Lyon 6e</strong></div>
            <span><span /> Analyse terminée</span>
          </div>
          <div className="how-report-score">
            <span className="how-score-ring"><strong>7</strong><small>points</small></span>
            <div><small>Votre priorité</small><strong>3 sujets à clarifier avant de vous engager</strong><p>Le reste du dossier est organisé par thème et niveau d’attention.</p></div>
          </div>
          <div className="how-report-finding">
            <span><Icon name="wrench" /></span>
            <div><small>Coût à clarifier</small><strong>Ravalement en préparation</strong><p>Une étude a été votée, mais aucun budget prévisionnel n’est fourni.</p><em><Icon name="document" /> PV d’AG 2025 · page 12</em></div>
            <Icon name="chevron" />
          </div>
          <div className="how-report-finding how-report-finding--calm">
            <span><Icon name="check" /></span>
            <div><small>Point rassurant</small><strong>Comptes approuvés</strong><p>Les comptes du dernier exercice ont été approuvés en assemblée.</p><em><Icon name="document" /> PV d’AG 2025 · page 5</em></div>
            <Icon name="chevron" />
          </div>
        </div>

        <div className="how-report-copy">
          <p className="how-section-label">Le résultat</p>
          <h2 id="how-report-title">Un rapport à lire.<br />Des décisions à prendre.</h2>
          <p>
            Pas une pile d’alertes. Votre rapport hiérarchise les sujets et vous
            aide à préparer la suite avec le vendeur, le syndic, le notaire ou
            le professionnel concerné.
          </p>
          <ul>
            {reportBenefits.map((benefit) => (
              <li key={benefit}><Icon name="check" /> {benefit}</li>
            ))}
          </ul>
          <Link className="how-inline-link" href={marketingRoutes.exampleAnalysis}>
            Explorer un exemple d’analyse <Icon name="arrow" />
          </Link>
        </div>
      </section>

      <section className="how-principles" aria-labelledby="how-principles-title">
        <div className="how-principles-heading">
          <p className="how-section-label">Notre méthode de confiance</p>
          <h2 id="how-principles-title">Clair ne veut pas dire simpliste.</h2>
        </div>
        <div className="how-principle-grid">
          {principles.map((principle) => (
            <article key={principle.number}>
              <span>{principle.number}</span>
              <h3>{principle.title}</h3>
              <p>{principle.text}</p>
            </article>
          ))}
        </div>
        <p className="how-boundary-note">
          <Icon name="info" /> Acquora est un outil d’aide à la décision. Il ne
          remplace pas l’avis d’un notaire, d’un diagnostiqueur ou d’un
          professionnel du bâtiment lorsque leur expertise est nécessaire.
        </p>
      </section>

      <section className="how-final-cta" aria-labelledby="how-final-title">
        <div>
          <p className="how-section-label">Prêt à y voir plus clair ?</p>
          <h2 id="how-final-title">Votre bien mérite une lecture complète.</h2>
        </div>
        <div>
          <p>Créez votre dossier et ajoutez les documents déjà en votre possession. Vous pourrez le compléter ensuite.</p>
          <ButtonLink href={productRoutes.home} className="how-final-button">
            Commencer mon analyse <Icon name="arrow" />
          </ButtonLink>
        </div>
      </section>
    </div>
  );
}
