export const SITE_URL = "https://acquora.fr";

export type BlogArticle = Readonly<{
  slug: string;
  title: string;
  description: string;
  excerpt: string;
  category: "Copropriété" | "DPE";
  categoryHref: "/blog/copropriete" | "/blog/dpe";
  publishedAt: string;
  modifiedAt: string;
  readingTime: string;
  cover: string;
  coverAlt: string;
}>;

export const blogArticles = [
  {
    slug: "documents-achat-appartement",
    title: "Documents à vérifier avant l’achat d’un appartement",
    description:
      "La checklist des documents à vérifier avant d’acheter un appartement : copropriété, charges, travaux, diagnostics et points à recouper.",
    excerpt:
      "Copropriété, charges, travaux et diagnostics : les pièces à demander, ce qu’elles révèlent et les incohérences à repérer avant de signer.",
    category: "Copropriété",
    categoryHref: "/blog/copropriete",
    publishedAt: "2026-09-02",
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
