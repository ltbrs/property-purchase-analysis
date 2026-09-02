import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ButtonLink } from "@/components/design-system/button-link";
import { Icon } from "@/components/icons";
import { blogArticles, getBlogArticle, SITE_URL, type BlogArticle } from "@/lib/blog";
import { marketingRoutes, productRoutes } from "@/lib/routes";

type BlogArticlePageProps = Readonly<{ params: Promise<{ slug: string }> }>;

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "Europe/Paris",
});

export function generateStaticParams() {
  return blogArticles.map(({ slug }) => ({ slug }));
}

export async function generateMetadata({ params }: BlogArticlePageProps): Promise<Metadata> {
  const article = getBlogArticle((await params).slug);
  if (!article) return {};

  const url = `${SITE_URL}/blog/${article.slug}`;
  const image = `${SITE_URL}${article.cover}`;
  return {
    title: article.title,
    description: article.description,
    alternates: { canonical: url },
    openGraph: {
      type: "article",
      locale: "fr_FR",
      url,
      siteName: "Acquora",
      title: article.title,
      description: article.description,
      publishedTime: article.publishedAt,
      modifiedTime: article.modifiedAt,
      images: [{ url: image, width: 1200, height: 675, alt: article.coverAlt }],
    },
    twitter: {
      card: "summary_large_image",
      title: article.title,
      description: article.description,
      images: [image],
    },
  };
}

function JsonLd({ article }: Readonly<{ article: BlogArticle }>) {
  const articleUrl = `${SITE_URL}/blog/${article.slug}`;
  const graph = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "BlogPosting",
        headline: article.title,
        description: article.description,
        image: `${SITE_URL}${article.cover}`,
        datePublished: article.publishedAt,
        dateModified: article.modifiedAt,
        inLanguage: "fr-FR",
        mainEntityOfPage: articleUrl,
        publisher: {
          "@type": "Organization",
          name: "Acquora",
          url: SITE_URL,
          logo: `${SITE_URL}/brand/acquora-logo-dark.svg`,
        },
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Accueil", item: SITE_URL },
          { "@type": "ListItem", position: 2, name: "Blog", item: `${SITE_URL}/blog` },
          { "@type": "ListItem", position: 3, name: article.title, item: articleUrl },
        ],
      },
    ],
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(graph).replace(/</g, "\\u003c") }}
    />
  );
}

function DocumentsArticle({ article }: Readonly<{ article: BlogArticle }>) {
  return (
    <>
      <JsonLd article={article} />
      <article className="blog-article">
        <nav className="blog-breadcrumb" aria-label="Fil d’Ariane">
          <Link href={marketingRoutes.home}>Accueil</Link>
          <span aria-hidden="true">/</span>
          <Link href={marketingRoutes.blog}>Blog</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Documents avant achat</span>
        </nav>

        <header className="article-header">
          <Link className="article-category" href={article.categoryHref}>{article.category}</Link>
          <h1>{article.title}</h1>
          <p className="article-standfirst">
            Une annonce et une visite ne suffisent pas à mesurer le coût réel d’un
            appartement. Voici les pièces à demander, ce qu’elles révèlent et les
            recoupements à faire avant de vous engager.
          </p>
          <div className="article-byline">
            <time dateTime={article.publishedAt}>
              Publié le {dateFormatter.format(new Date(`${article.publishedAt}T12:00:00+02:00`))}
            </time>
            <span>{article.readingTime} de lecture</span>
          </div>
        </header>

        <figure className="article-cover">
          <Image
            src={article.cover}
            alt={article.coverAlt}
            fill
            priority
            sizes="(max-width: 64rem) 100vw, 1024px"
          />
        </figure>

        <div className="article-layout">
          <aside className="article-toc" aria-label="Sommaire">
            <strong>Dans ce guide</strong>
            <ol>
              <li><a href="#checklist">La checklist</a></li>
              <li><a href="#copropriete">La copropriété</a></li>
              <li><a href="#diagnostics">Les diagnostics</a></li>
              <li><a href="#documents-utiles">Les pièces utiles</a></li>
              <li><a href="#recouper">Les recoupements</a></li>
              <li><a href="#signature">Avant la signature</a></li>
            </ol>
          </aside>

          <div className="article-body">
            <div className="article-callout article-callout--key">
              <strong>À retenir</strong>
              <p>
                Pour un appartement en copropriété, demandez en priorité le
                règlement et l’état descriptif de division, les trois derniers
                procès-verbaux d’assemblée générale, les informations de charges,
                le plan pluriannuel de travaux et le dossier de diagnostics. Ces
                pièces doivent être remises au plus tard lors de la promesse de
                vente. Les consulter avant une offre ferme vous permet toutefois
                de décider avec davantage d’informations.
              </p>
            </div>

            <p>
              La liste exacte dépend de l’âge du bâtiment, de sa localisation,
              de ses équipements et des travaux réalisés. Il faut donc distinguer
              les documents obligatoires, qui encadrent la vente, des justificatifs
              pratiques que vous pouvez demander pour comprendre le logement.
              La démarche officielle est détaillée dans la fiche de{" "}
              <a href="https://www.service-public.fr/particuliers/vosdroits/F37190">Service Public consacrée à l’achat d’un logement en copropriété</a>.
            </p>

            <h2 id="checklist">La checklist des documents à demander</h2>
            <p>
              Cette vue d’ensemble classe les pièces par décision. Elle évite de
              traiter de la même manière un document légal et une simple facture.
            </p>
            <div className="article-table-wrap">
              <table>
                <thead>
                  <tr><th>Document</th><th>Ce qu’il faut vérifier</th><th>Moment utile</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Règlement de copropriété et état descriptif de division</td>
                    <td>Usage du lot, annexes, parties privatives et communes, règles applicables à votre projet</td>
                    <td>Avant l’offre si votre projet comporte des travaux ou un usage particulier</td>
                  </tr>
                  <tr>
                    <td>Trois derniers procès-verbaux d’assemblée générale</td>
                    <td>Travaux votés, devis, incidents récurrents, procédures et décisions reportées</td>
                    <td>Avant l’offre</td>
                  </tr>
                  <tr>
                    <td>Charges et situation financière</td>
                    <td>Deux exercices, dépenses exceptionnelles, impayés, dettes fournisseurs et fonds travaux</td>
                    <td>Avant de finaliser votre budget</td>
                  </tr>
                  <tr>
                    <td>Plan pluriannuel de travaux, projet de plan et DTG s’il existe</td>
                    <td>Travaux envisagés, horizon, estimation et état général de l’immeuble</td>
                    <td>Avant le compromis</td>
                  </tr>
                  <tr>
                    <td>Dossier de diagnostic technique</td>
                    <td>Validité, périmètre, anomalies et recommandations propres au logement</td>
                    <td>Dès la première visite pour l’état des risques, au plus tard au compromis pour l’ensemble</td>
                  </tr>
                  <tr>
                    <td>Factures, autorisations et justificatifs de travaux</td>
                    <td>Nature des travaux, entreprise, date, garanties et accord de la copropriété ou de l’urbanisme si nécessaire</td>
                    <td>Avant de valoriser une rénovation dans votre offre</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h2 id="copropriete">1. Les documents de copropriété</h2>
            <p>
              Vous n’achetez pas seulement des pièces privatives. Vous entrez dans
              un immeuble organisé, avec des dépenses communes et des décisions
              collectives. L’<a href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000028779431">article L. 721-2 du Code de la construction et de l’habitation</a>{" "}
              énumère les informations à remettre à l’acquéreur.
            </p>

            <h3>Le règlement et l’état descriptif de division</h3>
            <p>
              Le règlement fixe la destination de l’immeuble et les règles d’usage.
              L’état descriptif identifie les lots et leurs tantièmes. Vérifiez que
              le numéro du lot, sa désignation et ses annexes correspondent à ce qui
              vous est vendu. Si vous prévoyez de louer, d’exercer une activité ou
              de modifier une partie commune, cherchez les clauses qui encadrent ce projet.
            </p>

            <h3>Les trois derniers procès-verbaux d’assemblée générale</h3>
            <p>
              Ne vous limitez pas aux résolutions adoptées. Repérez aussi les devis
              demandés, les études lancées, les travaux refusés ou reportés, les
              sinistres répétés et les procédures. Une toiture évoquée trois années
              de suite sans vote peut représenter un coût futur, même si aucun appel
              de fonds n’apparaît encore.
            </p>

            <h3>Les chiffres de la copropriété</h3>
            <p>
              Les informations transmises couvrent notamment les charges courantes
              et hors budget payées par le vendeur sur les deux exercices précédents,
              les sommes que l’acquéreur pourrait devoir, les impayés globaux, la
              dette fournisseurs et, lorsqu’il existe, le fonds de travaux. La{" "}
              <a href="https://www.anil.org/aj-copropriete-fiche-synthetique/">fiche synthétique présentée par l’ANIL</a>{" "}
              donne une vue d’ensemble, mais elle ne remplace pas la lecture des
              comptes et des procès-verbaux.
            </p>

            <div className="article-callout">
              <strong>À vérifier dans les chiffres</strong>
              <ul>
                <li>ce qui est inclus dans les charges, notamment chauffage, eau, ascenseur et gardiennage ;</li>
                <li>l’écart entre le budget voté et les dépenses réelles ;</li>
                <li>la progression des impayés et des dettes fournisseurs ;</li>
                <li>les appels de fonds déjà votés, leur calendrier et la répartition prévue dans l’acte.</li>
              </ul>
            </div>

            <h3>Le carnet d’entretien, le DTG et le plan de travaux</h3>
            <p>
              Le carnet d’entretien retrace des informations sur l’immeuble et ses
              contrats. Les conclusions du diagnostic technique global (DTG) sont
              communiquées s’il existe. Le plan pluriannuel de travaux adopté, ou
              son projet lorsqu’il a été élaboré, complète la vision à moyen terme.
              Comparez ces documents aux procès-verbaux : un poste coûteux peut être
              décrit dans une étude sans être encore voté.
            </p>

            <h2 id="diagnostics">2. Le dossier de diagnostic technique</h2>
            <p>
              Le DDT rassemble les diagnostics applicables au bien. Il ne contient
              pas toujours toutes les pièces ci-dessous. Leur présence dépend de la
              date de construction, de l’ancienneté des installations, de la
              localisation et des équipements.
            </p>
            <ul className="article-check-list">
              <li><strong>DPE :</strong> classe énergie et climat, estimation conventionnelle des dépenses, caractéristiques prises en compte et recommandations.</li>
              <li><strong>Plomb et amiante :</strong> présence repérée, zones non visitées et préconisations du rapport selon l’âge du bâtiment.</li>
              <li><strong>Électricité et gaz :</strong> anomalies des installations privatives lorsqu’elles ont plus de quinze ans.</li>
              <li><strong>Termites et mérule :</strong> documents selon les zones concernées.</li>
              <li><strong>État des risques :</strong> risques naturels, miniers, technologiques, sismiques, radon et autres informations applicables à l’adresse.</li>
              <li><strong>Bruit :</strong> état des nuisances sonores aériennes lorsque le logement se trouve dans une zone couverte.</li>
              <li><strong>Assainissement :</strong> contrôle applicable selon le raccordement et, pour l’assainissement collectif, selon certains territoires.</li>
              <li><strong>Surface privative :</strong> superficie du lot selon la loi Carrez.</li>
            </ul>
            <p>
              La liste officielle complète et ses conditions figurent sur{" "}
              <a href="https://www.service-public.fr/particuliers/vosdroits/F37190">Service Public</a>.
              Pour le DPE, vérifiez aussi sa date et son numéro d’identification.
              Les DPE réalisés entre le 1er janvier 2018 et le 30 juin 2021 ne sont
              plus valables depuis le 1er janvier 2025, comme le précise la{" "}
              <a href="https://www.service-public.fr/particuliers/vosdroits/F16096">fiche officielle sur le DPE</a>.
            </p>

            <div className="article-callout article-callout--warning">
              <strong>Un diagnostic n’est pas un devis</strong>
              <p>
                Une anomalie signale un point à examiner, mais ne chiffre pas
                nécessairement la remise en état. Pour une fissure, une humidité
                persistante ou une installation préoccupante, demandez l’avis et le
                chiffrage d’un professionnel compétent avant de vous engager.
              </p>
            </div>

            <h2 id="documents-utiles">3. Les documents utiles, même lorsqu’ils ne sont pas systématiquement annexés</h2>
            <p>
              Certaines pièces ne font pas partie de la liste générale remise dans
              toutes les ventes. Elles peuvent pourtant confirmer une dépense, un
              équipement ou une transformation annoncée :
            </p>
            <ul>
              <li>le dernier avis de taxe foncière pour connaître le montant récent, sans supposer qu’il restera identique ;</li>
              <li>des factures d’énergie récentes, à interpréter selon l’occupation et les usages du vendeur ;</li>
              <li>les factures, attestations d’assurance et garanties liées aux travaux ;</li>
              <li>les autorisations d’assemblée générale et d’urbanisme lorsque les travaux en nécessitaient ;</li>
              <li>les plans disponibles, utiles pour comparer la distribution réelle avec la désignation des lots ;</li>
              <li>le carnet d’information du logement (CIL), lorsqu’il doit avoir été établi après une construction ou certains travaux engagés depuis le 1er janvier 2023.</li>
            </ul>
            <p>
              Lorsqu’il existe, le CIL doit être remis à l’acquéreur au plus tard
              lors de l’acte authentique. Il centralise notamment des informations
              sur les matériaux, équipements et travaux énergétiques. Les cas
              concernés sont détaillés par{" "}
              <a href="https://www.service-public.fr/particuliers/vosdroits/F36759">Service Public</a>.
            </p>

            <h2 id="recouper">4. Les recoupements qui comptent vraiment</h2>
            <p>
              Lire chaque PDF séparément donne une vision incomplète. Les écarts
              entre documents sont souvent plus instructifs que leur contenu pris isolément.
            </p>
            <div className="article-comparisons">
              <section><span>01</span><div><h3>Lots vendus et réalité</h3><p>Comparez l’annonce, le projet de vente et l’état descriptif. Cave, parking, grenier et réunion de pièces doivent correspondre aux lots identifiés.</p></div></section>
              <section><span>02</span><div><h3>Travaux annoncés et décisions</h3><p>Rapprochez les factures du vendeur, les autorisations d’assemblée générale et les mentions des procès-verbaux.</p></div></section>
              <section><span>03</span><div><h3>Budget passé et coûts futurs</h3><p>Confrontez les deux exercices de charges, les appels déjà votés, le fonds travaux et le plan pluriannuel.</p></div></section>
              <section><span>04</span><div><h3>DPE et caractéristiques réelles</h3><p>Vérifiez que chauffage, eau chaude, surface, isolation et fenêtres décrits correspondent au logement visité.</p></div></section>
            </div>

            <h2 id="signature">5. Que vérifier avant le compromis puis avant l’acte ?</h2>
            <h3>Avant le compromis</h3>
            <p>
              Faites inscrire les conditions réellement nécessaires à votre achat,
              par exemple l’obtention d’un prêt ou d’une autorisation précise.
              Vérifiez aussi que toutes les pièces reçues sont lisibles, complètes
              et rattachées au bon lot. Le délai légal de rétractation est de dix
              jours. Pour une vente en copropriété, il ne commence qu’après remise
              de plusieurs documents déterminants, notamment ceux relatifs à
              l’organisation et à la situation financière de la copropriété.
            </p>

            <h3>Avant l’acte authentique</h3>
            <p>
              L’état daté est transmis par le syndic au notaire. Il précise la
              situation comptable du lot et aide à identifier les appels de fonds
              qui suivront l’achat. L’<a href="https://www.anil.org/parole-expert-copropriete-frais-etat-date/">ANIL rappelle le rôle de l’état daté et du fonds travaux</a>.
              Relisez le projet d’acte, la répartition convenue pour les appels de
              fonds et les engagements particuliers du vendeur. Une dernière visite
              permet enfin de vérifier l’état du logement et les éléments qui doivent y rester.
            </p>

            <div className="article-callout article-callout--key">
              <strong>Votre méthode en cinq étapes</strong>
              <ol>
                <li>Inventoriez les pièces reçues et les documents manquants.</li>
                <li>Vérifiez les dates, le lot, la surface et le périmètre de chaque document.</li>
                <li>Listez les travaux votés, étudiés et simplement évoqués.</li>
                <li>Chiffrez séparément charges récurrentes, appels certains et coûts encore incertains.</li>
                <li>Adressez les incohérences au vendeur, au syndic ou à votre notaire avant de signer.</li>
              </ol>
            </div>

            <h2>Questions fréquentes</h2>
            <h3>Peut-on demander ces documents avant de faire une offre ?</h3>
            <p>
              Oui, vous pouvez les demander. La remise de l’ensemble est imposée au
              plus tard lors de la promesse, mais rien ne vous oblige à attendre cette
              étape pour solliciter les documents disponibles. Le vendeur peut toutefois
              ne pas encore disposer de toutes les pièces.
            </p>
            <h3>Trois procès-verbaux suffisent-ils pour prévoir les travaux ?</h3>
            <p>
              Non. Ils constituent une base utile, mais le carnet d’entretien, le DTG
              lorsqu’il existe, le plan pluriannuel ou son projet et les devis apportent
              une vue plus complète. Une visite des parties communes reste nécessaire.
            </p>
            <h3>Le DPE indique-t-il les futures factures d’énergie ?</h3>
            <p>
              Il fournit une estimation conventionnelle, pas une promesse de facture.
              Le coût réel dépend notamment du climat, du nombre d’occupants, de leurs
              usages et des contrats d’énergie.
            </p>

            <section className="article-sources" aria-labelledby="sources-title">
              <h2 id="sources-title">Sources officielles</h2>
              <ul>
                <li><a href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000028779431">Code de la construction et de l’habitation, article L. 721-2</a></li>
                <li><a href="https://www.service-public.fr/particuliers/vosdroits/F37190">Service Public, achat d’un logement en copropriété</a></li>
                <li><a href="https://www.service-public.fr/particuliers/vosdroits/F16096">Service Public, diagnostic de performance énergétique</a></li>
                <li><a href="https://www.anil.org/aj-copropriete-fiche-synthetique/">ANIL, fiche synthétique de la copropriété</a></li>
                <li><a href="https://www.service-public.fr/particuliers/vosdroits/F36759">Service Public, carnet d’information du logement</a></li>
              </ul>
              <p>Sources consultées le 2 septembre 2026.</p>
            </section>

            <p className="article-disclaimer">
              Ce guide fournit une méthode de lecture générale. Il ne remplace pas
              les conseils personnalisés d’un notaire, d’un professionnel du bâtiment
              ou d’un autre spécialiste compétent pour votre situation.
            </p>

            <section className="article-cta" aria-labelledby="article-cta-title">
              <div>
                <p className="blog-kicker">Passez des documents à la décision</p>
                <h2 id="article-cta-title">Repérez ce qui mérite votre attention.</h2>
                <p>
                  Acquora analyse les documents disponibles, relie les informations
                  et conserve la source de chaque constat dans un rapport clair.
                </p>
              </div>
              <div>
                <ButtonLink href={productRoutes.home}>Analyser mon bien <Icon name="arrow" /></ButtonLink>
                <Link href={marketingRoutes.exampleAnalysis}>Voir un exemple d’analyse</Link>
              </div>
            </section>
          </div>
        </div>
      </article>
    </>
  );
}

export default async function BlogArticlePage({ params }: BlogArticlePageProps) {
  const article = getBlogArticle((await params).slug);
  if (!article) notFound();
  if (article.slug === "documents-achat-appartement") return <DocumentsArticle article={article} />;
  notFound();
}
