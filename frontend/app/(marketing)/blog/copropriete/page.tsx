import Image from "next/image";
import Link from "next/link";

import { blogArticles, formatBlogDate } from "@/lib/blog";
import { createMarketingMetadata } from "@/lib/seo";

export const metadata = createMarketingMetadata({
  title: "Guides sur la copropriété",
  description:
    "Comprendre les documents, les charges, les travaux et le fonctionnement d’une copropriété avant un achat immobilier.",
  path: "/blog/copropriete",
});

export default function CopropertyBlogPage() {
  const articles = blogArticles.filter(
    (article) => article.category === "Copropriété",
  );

  return (
    <div className="blog-index">
      <header className="blog-index-header blog-index-header--compact">
        <p className="blog-kicker">Copropriété</p>
        <h1>Comprendre l’immeuble avant d’acheter.</h1>
        <p>
          Charges, décisions d’assemblée générale et travaux : les documents
          qui permettent de regarder au-delà de l’appartement.
        </p>
      </header>
      <section className="blog-grid" aria-label="Articles sur la copropriété">
        {articles.map((article) => (
          <article className="blog-card" key={article.slug}>
            <Link className="blog-card-image" href={`/blog/${article.slug}`}>
              <Image
                src={article.cover}
                alt={article.coverAlt}
                fill
                sizes="(max-width: 48rem) 100vw, 50vw"
              />
            </Link>
            <div className="blog-card-copy">
              <div className="blog-card-meta">
                <span>{article.category}</span>
                <time dateTime={article.modifiedAt}>
                  Mis à jour le {formatBlogDate(article.modifiedAt)}
                </time>
                <span>{article.readingTime} de lecture</span>
              </div>
              <h2><Link href={`/blog/${article.slug}`}>{article.title}</Link></h2>
              <p>{article.excerpt}</p>
              <Link className="blog-card-link" href={`/blog/${article.slug}`}>
                Lire le guide <span aria-hidden="true">→</span>
              </Link>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
