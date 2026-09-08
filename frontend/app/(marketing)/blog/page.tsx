import Image from "next/image";
import Link from "next/link";

import { blogArticles, formatBlogDate } from "@/lib/blog";
import { createMarketingMetadata } from "@/lib/seo";

export const metadata = createMarketingMetadata({
  title: "Blog immobilier",
  description:
    "Guides pratiques pour lire les documents d’un achat immobilier, comprendre les risques et préparer vos questions.",
  path: "/blog",
});

export default function BlogPage() {
  return (
    <div className="blog-index">
      <header className="blog-index-header">
        <p className="blog-kicker">Guides d’achat immobilier</p>
        <h1>Décider avec les bons documents.</h1>
        <p>
          Des guides sourcés pour comprendre un appartement, sa copropriété et
          les coûts qui peuvent accompagner votre achat.
        </p>
      </header>

      <section className="blog-grid" aria-label="Tous les articles">
        {blogArticles.map((article) => (
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
                <Link href={article.categoryHref}>{article.category}</Link>
                <time dateTime={article.modifiedAt}>
                  Mis à jour le {formatBlogDate(article.modifiedAt)}
                </time>
                <span>{article.readingTime} de lecture</span>
              </div>
              <h2>
                <Link href={`/blog/${article.slug}`}>{article.title}</Link>
              </h2>
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
