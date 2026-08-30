type BlogArticlePageProps = Readonly<{
  params: Promise<{ slug: string }>;
}>;

export default async function BlogArticlePage({ params }: BlogArticlePageProps) {
  const { slug } = await params;

  return <p className="marketing-placeholder">Article : {slug}.</p>;
}
