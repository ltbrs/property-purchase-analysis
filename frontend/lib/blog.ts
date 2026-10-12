export { SITE_URL } from "@/lib/seo";

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
    slug: "plan-pluriannuel-travaux-avant-achat",
    title: "Plan pluriannuel de travaux : que vérifier avant d’acheter ?",
    description:
      "Avant d’acheter en copropriété, lisez le PPT : travaux prévus, votes, quote-part et fonds travaux. Une checklist pour préparer votre budget.",
    excerpt:
      "Un plan sur dix ans, plusieurs décisions à recouper. Les points à vérifier pour distinguer coûts envisagés et appels de fonds votés.",
    category: "Copropriété",
    categoryHref: "/blog/copropriete",
    publishedAt: "2026-10-12",
    modifiedAt: "2026-10-12",
    readingTime: "7 min",
    cover: "/images/blog/plan-pluriannuel-travaux-avant-achat.png",
    coverAlt:
      "Plan de travaux et étapes d’un calendrier devant un immeuble de copropriété",
  },
  {
    slug: "travaux-votes-avant-compromis",
    title: "Travaux votés avant le compromis : qui paie ?",
    description:
      "Travaux de copropriété votés avant le compromis : qui paie selon les appels de fonds, et que doit préciser l’acte de vente ?",
    excerpt:
      "Le vote ne suffit pas à désigner le payeur. Dates d’exigibilité, clause du compromis et documents à contrôler avant d’acheter.",
    category: "Copropriété",
    categoryHref: "/blog/copropriete",
    publishedAt: "2026-04-26",
    modifiedAt: "2026-09-06",
    readingTime: "10 min",
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
    modifiedAt: "2026-09-06",
    readingTime: "12 min",
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
