import Link from "next/link";

import { ButtonLink } from "@/components/design-system/button-link";
import { Icon } from "@/components/icons";
import { productRoutes } from "@/lib/routes";

const sources = {
  ppt: "https://www.service-public.gouv.fr/particuliers/vosdroits/F36760",
  purchase: "https://www.service-public.gouv.fr/particuliers/vosdroits/F37190",
  fund: "https://www.service-public.gouv.fr/particuliers/vosdroits/F34026",
  sale: "https://www.service-public.gouv.fr/particuliers/vosdroits/F32920",
  works: "https://www.anil.org/votre-besoin/gerer-un-bien/copropriete/travaux-de-la-prise-de-decision-a-la-realisation/",
} as const;

export function PptArticleContent() {
  return (
    <>
      <div className="article-callout article-callout--key">
        <strong>À retenir</strong>
        <p>
          Avant d’acheter, vérifiez la version du plan, les postes retenus en
          assemblée générale, leur coût estimé et les décisions de financement.
          Un travail inscrit au plan ne suffit pas à connaître votre prochain
          appel de fonds. <a href={sources.ppt}>Service Public distingue le plan adopté du vote des travaux</a>.
        </p>
      </div>
      <p>
        Votre objectif est concret : savoir quelles dépenses sont déjà décidées,
        quels travaux pourraient peser sur votre budget et quelles informations
        manquent encore. La méthode ci-dessous est une proposition de lecture
        Acquora, à appliquer aux documents de l’immeuble que vous envisagez d’acheter.
      </p>

      <h2 id="projet-plan-vote">PPPT, PPT et travaux votés : identifiez le stade de chaque poste</h2>
      <p>
        Le projet de plan pluriannuel de travaux (PPPT) présente des interventions
        proposées. Le plan pluriannuel de travaux (PPT) correspond à la partie
        adoptée par l’assemblée générale, en totalité ou en partie.
        Les travaux prévus restent à soumettre au vote selon l’échéancier.
        Ces étapes sont détaillées dans la <a href={sources.ppt}>fiche officielle sur le PPT</a>.
      </p>
      <div className="article-table-wrap" role="region" aria-label="Les trois stades des travaux" tabIndex={0}>
        <table>
          <caption>Comment classer les informations dans votre dossier d’achat</caption>
          <thead>
            <tr><th scope="col">Pièce ou décision</th><th scope="col">Ce que vous pouvez en tirer</th><th scope="col">Pièce à rechercher ensuite</th></tr>
          </thead>
          <tbody>
            <tr><td>Projet de plan</td><td>Des besoins identifiés et une première estimation</td><td>Le PV qui précise les suites données à l’étude</td></tr>
            <tr><td>Plan adopté</td><td>Une programmation retenue par la copropriété</td><td>Les résolutions sur la réalisation et le financement de chaque chantier</td></tr>
            <tr><td>Travaux votés et appels de fonds</td><td>Des montants et des échéances à rapprocher de la vente</td><td>La quote-part du lot, les appels et la clause du compromis</td></tr>
          </tbody>
        </table>
      </div>
      <p>
        L’<a href={sources.works}>ANIL décrit le parcours de décision des travaux</a> :
        l’assemblée se prononce sur leur réalisation et leurs modalités de
        règlement. Un vote commandant une étude ne doit donc pas être lu comme
        un vote de réalisation du chantier. Il peut en revanche entraîner le
        paiement de cette étude.
      </p>

      <h2 id="obligation">Quels immeubles doivent avoir un projet de plan ?</h2>
      <p>
        Depuis le 1er janvier 2025, l’élaboration d’un PPPT concerne en principe
        toutes les copropriétés à usage total ou partiel d’habitation dont la
        réception des travaux de construction remonte à plus de quinze ans.
        Une dispense est possible si le diagnostic technique global (DTG) ne
        révèle aucun besoin de travaux sur les dix années suivantes.
        Le projet est actualisé tous les dix ans.
        Voir les <a href={sources.ppt}>conditions d’application présentées par Service Public</a>.
      </p>
      <p>
        L’obligation d’élaborer et de présenter le projet ne signifie pas que
        les copropriétaires doivent l’adopter. Demandez le rapport et le
        procès-verbal (PV) de l’assemblée pour comprendre la décision prise.
        <a href={sources.ppt}> La fiche officielle précise cette distinction</a>.
      </p>

      <h2 id="lecture">Les cinq points à lire avant de regarder le total</h2>
      <p>
        Le projet comprend notamment une estimation sommaire des coûts, un ordre
        de priorité et un échéancier sur dix ans, comme le rappelle
        l’<a href={sources.works}>ANIL dans son guide des travaux en copropriété</a>.
        Pour votre achat, utilisez ces informations comme point de départ du recoupement.
      </p>
      <ol>
        <li><strong>Le périmètre :</strong> vérifiez l’adresse, les bâtiments et les équipements étudiés. Un ensemble immobilier peut comporter plusieurs bâtiments avec des besoins différents.</li>
        <li><strong>La date et la version :</strong> relevez la date du rapport, puis recherchez les travaux réalisés depuis et les décisions plus récentes.</li>
        <li><strong>Les priorités :</strong> repérez les postes liés à la sécurité, à la conservation de l’immeuble et à l’énergie. Demandez une explication sur les interventions reportées.</li>
        <li><strong>Les montants :</strong> cherchez ce que l’estimation inclut : taxes, études, maîtrise d’œuvre et frais associés. Notez explicitement les éléments non précisés.</li>
        <li><strong>Le calendrier :</strong> rapprochez l’horizon proposé de votre date d’achat. Une intervention annoncée dans deux ans appelle une question sur la prochaine décision et son financement.</li>
      </ol>
      <div className="article-callout article-callout--warning">
        <strong>Une estimation à faire préciser</strong>
        <p>
          Si le rapport annonce un montant sans détailler son périmètre, demandez
          les hypothèses et les devis disponibles. Conservez le chiffre comme
          estimation datée. Ne le présentez pas comme le prix définitif du chantier.
        </p>
      </div>

      <h2 id="budget">Passer du coût de l’immeuble au budget de votre lot</h2>
      <p>
        Ne divisez pas le total par le nombre d’appartements. Demandez la clé de
        répartition applicable au poste étudié et la quote-part de votre lot.
        La fiche de <a href={sources.fund}>Service Public sur le fonds de travaux</a>{" "}
        rappelle que l’affectation des fonds tient compte des parties communes
        spéciales et des clés de répartition des charges.
      </p>
      <h3>Vérifier le financement déjà décidé</h3>
      <p>
        Le fonds de travaux est une réserve collective. Son existence ne signifie
        pas qu’il sera entièrement utilisé pour le chantier qui vous intéresse :
        l’assemblée générale décide de l’affectation de tout ou partie des sommes.
        Les sommes versées sont attachées aux lots et ne sont pas remboursées au
        vendeur par le syndicat à la vente. Une convention entre les parties peut
        prévoir un remboursement. Ces règles figurent dans la <a href={sources.fund}>fiche officielle sur le fonds de travaux</a>.
      </p>
      <p>
        Demandez le solde disponible, la part rattachée au lot, les affectations
        déjà votées et les autres chantiers financés. Si une aide ou un emprunt
        est annoncé, sollicitez le justificatif, ses conditions et les montants
        effectivement retenus. Un financement encore espéré doit rester identifié
        comme incertain dans votre préparation du budget.
      </p>
      <div className="article-callout">
        <strong>Exemple fictif : une estimation de quote-part</strong>
        <p>
          Supposons un poste estimé à 120 000 € pour l’immeuble et une clé applicable
          de 35/1 000 pour le lot. L’ordre de grandeur brut serait de
          120 000 € × 35 / 1 000 = <strong>4 200 €</strong>.
          Ce calcul illustratif suppose que le montant et la clé soient confirmés.
          Il ne tient compte d’aucun financement, frais supplémentaire ou appel déjà réglé.
        </p>
        <p>
          Ce n’est pas une somme exigible. Pour savoir quand et combien payer,
          recherchez le vote du chantier, son financement et les appels propres au lot.
        </p>
      </div>
      <h3>Distinguer le coût envisagé des appels qui suivront la vente</h3>
      <p>
        Pour les dépenses hors budget prévisionnel, le syndic appelle les
        provisions auprès de la personne copropriétaire à leur date d’exigibilité.
        Le vendeur et l’acquéreur peuvent convenir d’une autre répartition entre
        eux, sans l’imposer au syndic. <a href={sources.sale}>Service Public explique les règles l’année de la vente</a>.
        Notre guide sur les <Link href="/blog/travaux-votes-avant-compromis">travaux votés avant le compromis et leur paiement</Link>{" "}
        détaille ce recoupement.
      </p>

      <h2 id="plan-manquant">Que faire si le PPT manque ou a été refusé ?</h2>
      <p>
        Pour l’achat d’un logement en copropriété avec promesse de vente,
        le plan adopté, ou à défaut le projet lorsqu’il a été élaboré, fait partie
        des pièces à remettre au plus tard à la promesse. Des exceptions existent,
        notamment si vous possédez déjà un lot dans la même copropriété.
        Consultez les <a href={sources.purchase}>documents à recevoir selon Service Public</a>{" "}
        et faites vérifier votre cas par le notaire.
      </p>
      <ul>
        <li><strong>Étude en cours :</strong> demandez la commande, le périmètre et la date de remise annoncée. Le coût futur reste non chiffré tant que le rapport manque.</li>
        <li><strong>Projet refusé :</strong> demandez le projet complet, la résolution et les raisons du refus. Les besoins décrits méritent toujours d’être examinés.</li>
        <li><strong>Dispense annoncée :</strong> demandez le DTG qui la justifie, sa date et ses conclusions. Une explication orale ne permet pas de vérifier le fondement de la dispense.</li>
        <li><strong>Aucune explication :</strong> transmettez au notaire la liste des pièces absentes et demandez au vendeur une clarification écrite auprès du syndic.</li>
      </ul>
      <p>
        L’absence de plan dans votre dossier ne prouve ni une irrégularité,
        ni l’absence de travaux à venir. Consignez ce qui reste inconnu et la
        réponse attendue. La <Link href="/blog/documents-achat-appartement">checklist des documents avant l’achat d’un appartement</Link>{" "}
        vous aide à compléter ce dossier.
      </p>

      <h2 id="checklist">Votre checklist avant le compromis</h2>
      <ul className="article-check-list">
        <li>Obtenir le projet complet et la version du plan adoptée, s’ils existent.</li>
        <li>Retrouver dans les PV les résolutions relatives au plan et à chaque chantier.</li>
        <li>Noter les estimations, leurs dates, leur périmètre et les postes non chiffrés.</li>
        <li>Faire confirmer la clé de répartition et la quote-part propres au lot.</li>
        <li>Vérifier les financements décidés et l’affectation du fonds travaux.</li>
        <li>Séparer les appels votés avec échéances des travaux encore envisagés.</li>
        <li>Faire relire au notaire la clause de répartition des coûts entre vendeur et acquéreur.</li>
      </ul>
      <div className="article-callout">
        <strong>La question à transmettre au vendeur et au syndic</strong>
        <p>
          « Pour chaque poste du plan concernant ce lot, quelle décision a été
          votée, quelle quote-part est retenue, quel financement est confirmé
          et quels appels de fonds restent à venir ? Merci de joindre les
          résolutions et les pièces correspondantes. »
        </p>
      </div>

      <section className="article-sources" aria-labelledby="sources-title">
        <h2 id="sources-title">Sources officielles</h2>
        <ul>
          <li><a href={sources.ppt}>Service Public, projet et plan pluriannuel de travaux en copropriété</a></li>
          <li><a href={sources.works}>ANIL, de la décision des travaux à leur réalisation</a></li>
          <li><a href={sources.fund}>Service Public, constitution et utilisation du fonds de travaux</a></li>
          <li><a href={sources.purchase}>Service Public, documents et étapes de l’achat en copropriété</a></li>
          <li><a href={sources.sale}>Service Public, répartition des charges l’année de la vente</a></li>
        </ul>
        <p>Sources consultées le 12 octobre 2026. Les cas particuliers doivent être vérifiés à partir des documents de votre copropriété.</p>
      </section>
      <p className="article-disclaimer">
        Ce guide propose une méthode de lecture des documents. Il ne constitue
        pas un conseil juridique, notarial, technique ou financier personnalisé.
        Faites confirmer les engagements de la vente par votre notaire et les
        besoins du bâtiment par un professionnel compétent.
      </p>
      <section aria-labelledby="related-title">
        <h2 id="related-title">Pour compléter votre dossier</h2>
        <ul>
          <li><Link href="/blog/documents-achat-appartement">Les documents à vérifier avant l’achat d’un appartement</Link></li>
          <li><Link href="/blog/travaux-votes-avant-compromis">Qui paie les travaux votés avant le compromis ?</Link></li>
        </ul>
      </section>
      <section className="article-cta" aria-labelledby="article-cta-title">
        <div>
          <p className="blog-kicker">Préparez vos questions</p>
          <h2 id="article-cta-title">Rapprochez le plan des autres pièces du dossier.</h2>
          <p>
            Acquora analyse les documents disponibles et présente les coûts,
            les incohérences et les informations manquantes avec leurs sources.
            Découvrez <Link href="/comment-ca-marche">comment se déroule l’analyse de vos documents</Link>.
          </p>
        </div>
        <div>
          <ButtonLink href={productRoutes.home}>Analyser mon bien <Icon name="arrow" /></ButtonLink>
        </div>
      </section>
    </>
  );
}
