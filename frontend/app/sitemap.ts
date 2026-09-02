import type { MetadataRoute } from "next";

import { blogArticles, SITE_URL } from "@/lib/blog";
import { marketingRoutes } from "@/lib/routes";

export default function sitemap(): MetadataRoute.Sitemap {
  const marketingPages = Object.values(marketingRoutes).map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: path === "/blog" ? "weekly" as const : "monthly" as const,
    priority: path === "/" ? 1 : path === "/blog" ? 0.8 : 0.7,
  }));

  const articles = blogArticles.map((article) => ({
    url: `${SITE_URL}/blog/${article.slug}`,
    lastModified: article.modifiedAt,
    changeFrequency: "monthly" as const,
    priority: 0.8,
    images: [`${SITE_URL}${article.cover}`],
  }));

  return [...marketingPages, ...articles];
}
