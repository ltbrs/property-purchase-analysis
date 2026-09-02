export const SITE_URL = "https://acquora.fr";

const blogDateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "Europe/Paris",
});

export type BlogArticle = Readonly<{
  slug: string;
  title: string;
  description: string;
  excerpt: string;
  category: "Copropriété";
  categoryHref: "/blog/copropriete";
  publishedAt: string;
  modifiedAt: string;
  readingTime: string;
  cover: string;
  coverAlt: string;
}>;

export const blogArticles = [
  {
    slug: "travaux-votes-avant-compromis",
    title: "Travaux votés avant le compromis : qui paie ?",
    description:
      "Travaux de copropriété votés avant le compromis : qui paie selon les appels de fonds, et que doit préciser l’acte de vente ?",
    excerpt:
      "Le vote ne suffit pas à désigner le payeur. Dates d’exigibilité, clause du compromis et documents à contrôler avant d’acheter.",
    category: "Copropriété",
    categoryHref: "/blog/copropriete",
    publishedAt: "2026-09-02",
    modifiedAt: "2026-09-02",
    readingTime: "8 min",
    cover: "/images/blog/travaux-votes-avant-compromis.svg",
    coverAlt:
      "Calendrier d’appels de fonds, clé et immeuble de copropriété",
  },
  {
    slug: "documents-achat-appartement",
    title: "Documents à vérifier avant l’achat d’un appartement",
    description:
      "La checklist des documents à vérifier avant d’acheter un appartement : copropriété, charges, travaux, diagnostics et points à recouper.",
    excerpt:
      "Copropriété, charges, travaux et diagnostics : les pièces à demander, ce qu’elles révèlent et les incohérences à repérer avant de signer.",
    category: "Copropriété",
    categoryHref: "/blog/copropriete",
    publishedAt: "2026-02-02",
    modifiedAt: "2026-09-02",
    readingTime: "10 min",
    cover: "/images/blog/documents-achat-appartement.svg",
    coverAlt:
      "Dossier de documents immobiliers devant un immeuble d’habitation",
  },
] as const satisfies readonly BlogArticle[];

export function getBlogArticle(slug: string): BlogArticle | undefined {
  return blogArticles.find((article) => article.slug === slug);
}

export function formatBlogDate(date: string): string {
  return blogDateFormatter.format(new Date(date + "T12:00:00Z"));
}
