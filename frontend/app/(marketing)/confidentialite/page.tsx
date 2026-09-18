import Link from "next/link";

import { marketingRoutes } from "@/lib/routes";
import { createMarketingMetadata } from "@/lib/seo";

export const metadata = createMarketingMetadata({
  title: "Politique de confidentialité",
  description:
    "Découvrez comment Acquora collecte, utilise, protège et supprime vos données personnelles, y compris lors d’une connexion avec Google.",
  path: "/confidentialite",
});

const sections = [
  { id: "responsable", label: "Responsable et contact" },
  { id: "donnees", label: "Données traitées" },
  { id: "google", label: "Connexion Google" },
  { id: "finalites", label: "Finalités et bases légales" },
  { id: "destinataires", label: "Destinataires" },
  { id: "conservation", label: "Durées de conservation" },
  { id: "traceurs", label: "Cookies et mesure d’audience" },
  { id: "droits", label: "Vos droits" },
  { id: "securite", label: "Sécurité" },
] as const;

export default function PrivacyPage() {
  return (
    <div className="legal-page">
      <header className="legal-hero">
        <p className="legal-kicker">Informations juridiques</p>
        <h1>Politique de confidentialité</h1>
        <p className="legal-lead">
          Cette politique explique de façon concrète quelles données Acquora traite,
          pourquoi elles sont nécessaires et comment exercer vos droits. Elle couvre le
          site public, votre compte, les documents immobiliers et la connexion Google.
        </p>
        <div className="legal-meta" aria-label="Informations essentielles">
          <div>
            <span>Mise à jour</span>
            <strong>18 septembre 2026</strong>
          </div>
          <div>
            <span>Contact unique</span>
            <a href="mailto:contact@acquora.fr">contact@acquora.fr</a>
          </div>
        </div>
      </header>

      <div className="legal-layout">
        <nav className="legal-toc" aria-label="Sommaire de la politique de confidentialité">
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
          <section id="responsable">
            <p className="legal-section-number">01</p>
            <h2>Responsable du traitement et contact</h2>
            <p>
              Le responsable du traitement est l’éditeur du service Acquora. Pour toute
              question relative à vos données personnelles ou pour exercer un droit,
              écrivez à <a href="mailto:contact@acquora.fr">contact@acquora.fr</a>.
            </p>
            <p>
              Cette adresse est également le point de contact pour les demandes de
              suppression d’un compte ou de données associées.
            </p>
          </section>

          <section id="donnees">
            <p className="legal-section-number">02</p>
            <h2>Données que nous traitons</h2>
            <ul>
              <li>
                <strong>Compte et authentification :</strong> nom, adresse e-mail,
                identifiant interne, fournisseur de connexion et état de vérification de
                l’adresse e-mail.
              </li>
              <li>
                <strong>Dossiers immobiliers :</strong> nom du dossier, type de bien,
                prix, surface et nombre de lots lorsque vous les renseignez.
              </li>
              <li>
                <strong>Documents et analyses :</strong> fichiers PDF téléversés,
                contenu extrait, métadonnées, classifications, faits normalisés, points
                de vigilance, rapports et références aux pages sources.
              </li>
              <li>
                <strong>Paiement :</strong> offre choisie, montant, statut, références
                de transaction et identifiants Stripe. Acquora ne reçoit ni ne conserve
                le numéro complet de votre carte bancaire.
              </li>
              <li>
                <strong>Contact :</strong> nom, adresse e-mail, sujet, message et une
                empreinte non réversible de l’adresse IP destinée à limiter les abus.
              </li>
              <li>
                <strong>Données techniques et d’usage :</strong> journaux de sécurité,
                pages consultées, provenance, appareil, navigateur et événements
                fonctionnels, par exemple la création d’un dossier ou le téléversement
                d’un type de document.
              </li>
            </ul>
            <aside className="legal-callout">
              Les documents immobiliers peuvent contenir des données concernant des
              tiers. Ne transmettez que les pièces utiles à votre projet et que vous êtes
              autorisé à utiliser.
            </aside>
          </section>

          <section id="google">
            <p className="legal-section-number">03</p>
            <h2>Données Google utilisées pour la connexion</h2>
            <p>
              Si vous choisissez « Continuer avec Google », Google transmet à Acquora
              un jeton d’identité sécurisé. Acquora et son service d’authentification
              Supabase utilisent les informations de profil strictement nécessaires à
              la création et à la sécurisation de votre session : identifiant Google,
              nom, adresse e-mail, état de vérification de l’adresse et, si Google la
              fournit, image de profil.
            </p>
            <p>
              Ces données sont enregistrées avec votre compte dans Supabase. Elles servent
              uniquement à vous identifier, à afficher les informations de votre compte et
              à assurer sa sécurité. Elles ne sont partagées avec aucun autre prestataire
              pour une finalité propre à celui-ci.
            </p>
            <div className="legal-facts">
              <div>
                <strong>Ce qui est demandé</strong>
                <p>Votre identité de base et votre adresse e-mail pour vous connecter.</p>
              </div>
              <div>
                <strong>Ce qui ne l’est pas</strong>
                <p>
                  Aucun accès à Google Drive, Gmail, Google Agenda, vos contacts, vos
                  fichiers ou votre mot de passe Google.
                </p>
              </div>
              <div>
                <strong>Ce que nous n’en faisons pas</strong>
                <p>
                  Les données Google ne sont ni vendues, ni utilisées pour la publicité,
                  ni transmises au modèle d’intelligence artificielle qui analyse vos
                  documents.
                </p>
              </div>
            </div>
            <p>
              Vous pouvez retirer l’accès d’Acquora depuis la page{" "}
              <a href="https://myaccount.google.com/connections" rel="noreferrer" target="_blank">
                Connexions à des applications tierces
              </a>{" "}
              de votre compte Google. Ce retrait empêche les connexions futures par ce moyen,
              mais ne supprime pas automatiquement votre compte Acquora. Pour supprimer les
              données déjà enregistrées, contactez-nous à l’adresse indiquée plus haut.
            </p>
          </section>

          <section id="finalites">
            <p className="legal-section-number">04</p>
            <h2>Pourquoi ces données sont utilisées</h2>
            <div className="legal-table-wrap">
              <table>
                <caption>Finalités des traitements et bases légales</caption>
                <thead>
                  <tr>
                    <th scope="col">Finalité</th>
                    <th scope="col">Base légale principale</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Créer le compte, authentifier l’utilisateur et sécuriser la session</td>
                    <td>Exécution du service demandé</td>
                  </tr>
                  <tr>
                    <td>Héberger, extraire et analyser les documents pour produire le rapport</td>
                    <td>Exécution du service demandé</td>
                  </tr>
                  <tr>
                    <td>Gérer les offres, paiements, crédits et justificatifs comptables</td>
                    <td>Exécution du contrat et obligations légales</td>
                  </tr>
                  <tr>
                    <td>Répondre aux messages et demandes relatives aux droits</td>
                    <td>Mesures précontractuelles, intérêt légitime ou obligation légale</td>
                  </tr>
                  <tr>
                    <td>Prévenir les abus, sécuriser et diagnostiquer le service</td>
                    <td>Intérêt légitime à protéger le service et ses utilisateurs</td>
                  </tr>
                  <tr>
                    <td>Mesurer l’audience et améliorer les parcours</td>
                    <td>Intérêt légitime ou consentement lorsque celui-ci est requis</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p>
              Les champs signalés comme obligatoires sont nécessaires pour fournir la
              fonctionnalité concernée. Sans eux, le compte, le paiement, l’analyse ou la
              réponse à votre demande peut ne pas être possible. Acquora ne prend pas de
              décision produisant un effet juridique à votre égard sur le seul fondement
              d’un traitement automatisé.
            </p>
          </section>

          <section id="destinataires">
            <p className="legal-section-number">05</p>
            <h2>Prestataires et destinataires</h2>
            <p>
              L’accès aux données est limité à l’éditeur d’Acquora et aux prestataires
              nécessaires au fonctionnement du service, dans la limite de leur mission.
            </p>
            <p>Ces destinataires peuvent comprendre :</p>
            <ul>
              <li>les prestataires d’hébergement, de stockage et de sécurité ;</li>
              <li>les services d’authentification et d’envoi d’e-mails transactionnels ;</li>
              <li>les prestataires de paiement et de prévention de la fraude ;</li>
              <li>les services nécessaires à l’extraction et à l’analyse automatisée des documents ;</li>
              <li>les outils de mesure d’audience et d’amélioration du service ;</li>
              <li>les organismes publics interrogés pour vérifier une donnée officielle.</li>
            </ul>
            <p>
              Seuls les contenus et identifiants nécessaires à chaque opération sont
              transmis. Les prestataires agissent dans le cadre de leur mission et ne
              reçoivent pas les documents pour les utiliser à des fins publicitaires.
            </p>
            <p>
              Certains prestataires sont établis ou peuvent traiter des données hors de
              l’Espace économique européen. Lorsque cela se produit, le transfert repose sur
              un mécanisme reconnu par le droit applicable, par exemple une décision
              d’adéquation ou des clauses contractuelles types.
            </p>
          </section>

          <section id="conservation">
            <p className="legal-section-number">06</p>
            <h2>Combien de temps les données sont conservées</h2>
            <ul>
              <li>
                <strong>Compte et données Google :</strong> pendant la durée d’utilisation
                du compte, puis jusqu’au traitement de la demande de suppression, sauf
                donnée devant être conservée pour une obligation légale ou un litige.
              </li>
              <li>
                <strong>Dossiers, documents et rapports :</strong> jusqu’à leur suppression
                par l’utilisateur ou à la suppression du compte. La suppression d’un document
                depuis l’application entraîne sa suppression du stockage actif et invalide
                les résultats qui en dépendaient.
              </li>
              <li>
                <strong>Demandes de contact :</strong> le temps nécessaire au traitement et,
                au maximum, trois ans après le dernier échange utile.
              </li>
              <li>
                <strong>Données de transaction et pièces comptables :</strong> pendant la
                durée imposée par les obligations comptables, fiscales et de preuve applicables.
              </li>
              <li>
                <strong>Journaux techniques et données d’usage :</strong> pour la durée
                strictement nécessaire à la sécurité, au diagnostic et à la production de
                statistiques, puis suppression ou anonymisation.
              </li>
            </ul>
            <p>
              Une suppression peut nécessiter un délai technique pour se répercuter dans les
              sauvegardes, qui restent protégées et ne sont utilisées qu’en cas de restauration.
            </p>
          </section>

          <section id="traceurs">
            <p className="legal-section-number">07</p>
            <h2>Cookies et mesure d’audience</h2>
            <p>
              Acquora utilise des cookies strictement nécessaires pour maintenir une session
              sécurisée. Google peut également utiliser ses propres mécanismes lorsque vous
              ouvrez volontairement la fenêtre de connexion Google.
            </p>
            <p>
              Des outils de mesure d’audience permettent de comprendre les parcours et
              événements utiles à l’amélioration du produit. Ils peuvent enregistrer un
              identifiant dans le navigateur et associer l’usage à l’identifiant interne
              d’un utilisateur connecté. Ils ne sont pas utilisés pour la publicité. Vous
              pouvez bloquer ou supprimer ces traceurs dans les réglages de votre navigateur,
              sans perdre l’accès aux fonctions essentielles d’Acquora.
            </p>
          </section>

          <section id="droits">
            <p className="legal-section-number">08</p>
            <h2>Vos droits</h2>
            <p>
              Selon votre situation, vous pouvez demander l’accès à vos données, leur
              rectification, leur effacement, la limitation de leur traitement, leur
              portabilité ou vous opposer à un traitement fondé sur l’intérêt légitime. Vous
              pouvez aussi retirer un consentement à tout moment, sans remettre en cause les
              traitements déjà effectués licitement.
            </p>
            <p>
              Écrivez à <a href="mailto:contact@acquora.fr">contact@acquora.fr</a> en
              précisant votre demande. Une preuve d’identité peut être demandée uniquement
              en cas de doute raisonnable. Vous pouvez également introduire une réclamation
              auprès de la <a href="https://www.cnil.fr/fr/plaintes" rel="noreferrer" target="_blank">CNIL</a>.
            </p>
          </section>

          <section id="securite">
            <p className="legal-section-number">09</p>
            <h2>Sécurité et évolution de la politique</h2>
            <p>
              Acquora met en œuvre des mesures adaptées à la sensibilité des données :
              contrôle d’accès côté serveur, stockage privé, communications chiffrées,
              liens signés de courte durée et séparation des secrets techniques. Aucun
              système n’offre toutefois une sécurité absolue.
            </p>
            <p>
              Cette politique peut évoluer pour refléter le service, les prestataires ou la
              réglementation. La date de mise à jour figure en tête de page. Une modification
              importante concernant l’usage des données Google ou une nouvelle finalité sera
              portée à la connaissance des utilisateurs avant son application lorsque cela
              est requis.
            </p>
            <p>
              Pour connaître les règles d’utilisation du service, consultez les{" "}
              <Link href={marketingRoutes.terms}>conditions générales</Link>. Pour une
              question non liée à vos droits, utilisez la page{" "}
              <Link href={marketingRoutes.contact}>Nous contacter</Link>.
            </p>
          </section>
        </article>
      </div>
    </div>
  );
}
