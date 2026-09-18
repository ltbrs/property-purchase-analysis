import Link from "next/link";

import { marketingRoutes } from "@/lib/routes";
import { createMarketingMetadata } from "@/lib/seo";

export const metadata = createMarketingMetadata({
  title: "Conditions générales d’utilisation",
  description:
    "Consultez les conditions d’accès et d’utilisation du service Acquora, ses limites, les règles relatives aux comptes, aux analyses et aux paiements.",
  path: "/conditions-generales",
});

const sections = [
  { id: "objet", label: "Objet et éditeur" },
  { id: "service", label: "Fonctionnement du service" },
  { id: "compte", label: "Compte utilisateur" },
  { id: "documents", label: "Documents transmis" },
  { id: "paiement", label: "Offres et paiement" },
  { id: "retractation", label: "Rétractation" },
  { id: "limites", label: "Limites du service" },
  { id: "disponibilite", label: "Disponibilité" },
  { id: "propriete", label: "Propriété intellectuelle" },
  { id: "fin", label: "Fin d’accès et litiges" },
] as const;

export default function TermsPage() {
  return (
    <div className="legal-page">
      <header className="legal-hero">
        <p className="legal-kicker">Informations juridiques</p>
        <h1>Conditions générales d’utilisation</h1>
        <p className="legal-lead">
          Ces conditions encadrent l’accès à Acquora et son utilisation. Elles précisent
          ce que le service fournit, les responsabilités de chacun et les règles applicables
          aux analyses payantes.
        </p>
        <div className="legal-meta" aria-label="Informations essentielles">
          <div>
            <span>Entrée en vigueur</span>
            <strong>18 septembre 2026</strong>
          </div>
          <div>
            <span>Contact unique</span>
            <a href="mailto:contact@acquora.fr">contact@acquora.fr</a>
          </div>
        </div>
      </header>

      <div className="legal-layout">
        <nav className="legal-toc" aria-label="Sommaire des conditions générales">
          <strong>Sur cette page</strong>
          <ol>
            {sections.map((section) => (
              <li key={section.id}>
                <a href={`#${section.id}`}>{section.label}</a>
              </li>
            ))}
          </ol>
        </nav>

        <article className="legal-content">
          <section id="objet">
            <p className="legal-section-number">01</p>
            <h2>Objet, acceptation et éditeur</h2>
            <p>
              Acquora est un service en ligne d’aide à la décision pour les particuliers
              qui examinent les documents d’un achat immobilier en France. Le service est
              édité sous le nom Acquora et peut être contacté à{" "}
              <a href="mailto:contact@acquora.fr">contact@acquora.fr</a>.
            </p>
            <p>
              En créant un compte ou en utilisant Acquora, vous acceptez les présentes
              conditions. Si vous n’y consentez pas, vous ne devez pas utiliser le service.
              Vous devez avoir la capacité juridique nécessaire pour conclure ce contrat.
            </p>
          </section>

          <section id="service">
            <p className="legal-section-number">02</p>
            <h2>Ce que fournit Acquora</h2>
            <p>
              Acquora permet de créer des dossiers de biens, de téléverser des documents
              immobiliers au format accepté, d’en extraire les informations et de produire
              un rapport qui distingue notamment les faits documentés, points de vigilance,
              coûts, incohérences et informations manquantes. Les constats importants sont
              reliés à leur document et à leur page source lorsque cette information est
              disponible.
            </p>
            <p>
              Certaines fonctions sont gratuites. Les analyses complètes nécessitent un
              crédit d’analyse acquis selon les tarifs présentés avant le paiement. Les
              fonctions disponibles peuvent évoluer pour améliorer la fiabilité ou la
              sécurité du service.
            </p>
          </section>

          <section id="compte">
            <p className="legal-section-number">03</p>
            <h2>Compte et accès</h2>
            <ul>
              <li>Vous devez fournir des informations exactes et maintenir votre adresse e-mail accessible.</li>
              <li>Vous êtes responsable de la confidentialité de vos moyens de connexion et des actions effectuées depuis votre session.</li>
              <li>Vous devez prévenir Acquora rapidement si vous suspectez un accès non autorisé.</li>
              <li>La connexion Google est facultative. Une connexion par e-mail et mot de passe peut également être proposée.</li>
            </ul>
            <p>
              Acquora peut suspendre un accès en cas de risque de sécurité, de fraude,
              d’atteinte au service ou de violation grave des présentes conditions. Lorsque
              la situation le permet, l’utilisateur est informé et peut présenter ses observations.
            </p>
          </section>

          <section id="documents">
            <p className="legal-section-number">04</p>
            <h2>Documents, contenus et usages interdits</h2>
            <p>
              Vous conservez vos droits sur les documents et données que vous transmettez.
              Vous accordez à Acquora le droit technique limité de les héberger, copier,
              extraire et traiter uniquement pour fournir, sécuriser et améliorer les
              fonctions demandées, conformément à la{" "}
              <Link href={marketingRoutes.privacy}>politique de confidentialité</Link>.
            </p>
            <p>Vous vous engagez à ne pas :</p>
            <ul>
              <li>téléverser un document que vous n’êtes pas autorisé à utiliser ;</li>
              <li>transmettre un contenu illicite, malveillant ou sans lien avec l’objet du service ;</li>
              <li>chercher à contourner les contrôles d’accès, quotas, limites de taille ou mesures de sécurité ;</li>
              <li>utiliser Acquora pour porter atteinte aux droits ou à la vie privée d’un tiers ;</li>
              <li>revendre, reproduire massivement ou détourner le service de sa finalité.</li>
            </ul>
            <p>
              Vous devez relire les résultats et les confronter aux documents originaux.
              Si un fichier est illisible, incomplet, ancien ou contradictoire, le rapport
              peut lui aussi rester incomplet ou incertain.
            </p>
          </section>

          <section id="paiement">
            <p className="legal-section-number">05</p>
            <h2>Offres, prix et paiement</h2>
            <p>
              Les prix et le contenu de chaque offre sont indiqués en euros toutes taxes
              comprises avant la commande. Le paiement est unique et ne crée pas
              d’abonnement. Il est traité par Stripe sur une page sécurisée. La commande est
              confirmée après validation du paiement par Stripe.
            </p>
            <p>
              Un crédit permet d’activer une analyse pour un dossier. Sa durée de validité,
              lorsqu’elle est limitée, est indiquée avec l’offre. Un crédit consommé est lié
              au dossier activé. Les tarifs peuvent être modifiés pour l’avenir, sans effet
              sur un achat déjà confirmé.
            </p>
            <p>
              En cas d’erreur apparente, de paiement refusé ou de crédit non attribué après
              confirmation, contactez <a href="mailto:contact@acquora.fr">contact@acquora.fr</a>
              {" "}en indiquant la date et l’adresse e-mail du compte. Ne transmettez jamais
              vos données complètes de carte bancaire.
            </p>
          </section>

          <section id="retractation">
            <p className="legal-section-number">06</p>
            <h2>Droit de rétractation</h2>
            <p>
              Lorsqu’il agit en qualité de consommateur, l’utilisateur bénéficie du droit de
              rétractation prévu par la loi pour les contrats conclus à distance, en principe
              pendant quatorze jours à compter de la conclusion du contrat.
            </p>
            <p>
              Si l’utilisateur demande que le service numérique commence avant la fin de ce
              délai, les conséquences sur son droit de rétractation dépendent de l’état
              d’exécution du service et des accords exprès requis par la loi. Acquora ne
              limite pas les droits impératifs du consommateur. Toute demande peut être
              envoyée sans ambiguïté à <a href="mailto:contact@acquora.fr">contact@acquora.fr</a>
              {" "}avec les informations permettant d’identifier la commande.
            </p>
          </section>

          <section id="limites">
            <p className="legal-section-number">07</p>
            <h2>Nature et limites du service</h2>
            <aside className="legal-callout">
              Acquora est un outil d’aide à la décision documentaire. Il ne fournit pas de
              conseil juridique, notarial, financier, technique ou énergétique et ne remplace
              ni une visite du bien, ni un diagnostic, ni une expertise professionnelle.
            </aside>
            <p>
              Les résultats reposent sur les documents transmis et sur des traitements
              automatisés qui peuvent comporter des erreurs. L’absence d’un point de vigilance
              dans le rapport ne prouve pas l’absence de défaut, de coût ou de risque. Une
              estimation ou une incohérence signalée doit être vérifiée auprès du vendeur,
              du syndic, du notaire, du diagnostiqueur ou du professionnel compétent.
            </p>
            <p>
              L’utilisateur reste seul responsable de ses décisions d’achat, de financement,
              de négociation et de signature. Acquora ne garantit ni la réalisation d’une
              transaction, ni la valeur d’un bien, ni l’exhaustivité d’un dossier fourni par
              un tiers.
            </p>
          </section>

          <section id="disponibilite">
            <p className="legal-section-number">08</p>
            <h2>Disponibilité et responsabilité</h2>
            <p>
              Acquora cherche à fournir un service disponible, sécurisé et fidèle aux sources,
              sans garantir une disponibilité continue. Des interruptions peuvent être
              nécessaires pour la maintenance, la sécurité ou en raison d’un prestataire.
            </p>
            <p>
              Dans les limites permises par la loi, Acquora répond uniquement des dommages
              directs et prévisibles résultant d’un manquement qui lui est imputable. Aucune
              clause des présentes conditions n’exclut une responsabilité qui ne peut pas
              légalement être limitée, ni les garanties légales dont bénéficie un consommateur.
            </p>
          </section>

          <section id="propriete">
            <p className="legal-section-number">09</p>
            <h2>Propriété intellectuelle</h2>
            <p>
              La marque, l’interface, les textes, la structure du service, les modèles de
              rapport, le code et les éléments graphiques propres à Acquora sont protégés par
              les droits applicables. Les présentes conditions n’accordent aucun droit autre
              que l’accès personnel au service selon sa destination.
            </p>
            <p>
              Vous pouvez utiliser et partager votre rapport pour les besoins de votre projet
              immobilier. Les documents sources restent soumis aux droits de leurs auteurs et
              émetteurs respectifs.
            </p>
          </section>

          <section id="fin">
            <p className="legal-section-number">10</p>
            <h2>Suppression, évolution et règlement des différends</h2>
            <p>
              Vous pouvez cesser d’utiliser le service à tout moment et demander la suppression
              de votre compte à <a href="mailto:contact@acquora.fr">contact@acquora.fr</a>.
              Certaines données peuvent être conservées lorsque la loi l’impose ou pour la
              constatation, l’exercice ou la défense de droits.
            </p>
            <p>
              Acquora peut modifier ces conditions pour tenir compte d’une évolution du
              service ou du droit applicable. La version en vigueur est celle publiée sur cette
              page. Une modification importante est portée à la connaissance des utilisateurs
              lorsqu’une information préalable est nécessaire.
            </p>
            <p>
              Les présentes conditions sont régies par le droit français, sans priver un
              consommateur des protections impératives de son pays de résidence. En cas de
              difficulté, contactez d’abord Acquora afin de rechercher une solution amiable.
              À défaut, les règles légales de compétence juridictionnelle s’appliquent.
            </p>
            <p>
              Pour comprendre le traitement de vos données, consultez la{" "}
              <Link href={marketingRoutes.privacy}>politique de confidentialité</Link>. Vous
              pouvez aussi utiliser la page <Link href={marketingRoutes.contact}>Nous contacter</Link>.
            </p>
          </section>
        </article>
      </div>
    </div>
  );
}
