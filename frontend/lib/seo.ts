import type { Metadata } from "next";

export const SITE_NAME = "Acquora";
export const SITE_URL = "https://acquora.fr";
export const SITE_DESCRIPTION =
  "Acquora analyse les documents de votre achat immobilier et met en évidence les risques, coûts futurs, incohérences et pièces manquantes.";

const DEFAULT_SOCIAL_IMAGE = {
  url: `${SITE_URL}/images/product-workflow-poster.png`,
  width: 1200,
  height: 675,
  alt: "Parcours Acquora, des documents immobiliers au rapport d’analyse",
};

type MarketingMetadataOptions = Readonly<{
  title: string;
  description: string;
  path: string;
}>;

export function createMarketingMetadata({
  title,
  description,
  path,
}: MarketingMetadataOptions): Metadata {
  const url = new URL(path, SITE_URL).toString();
  const socialTitle = `${title} | ${SITE_NAME}`;

  return {
    title: path === "/" ? { absolute: socialTitle } : title,
    description,
    alternates: { canonical: url },
    openGraph: {
      type: "website",
      locale: "fr_FR",
      url,
      siteName: SITE_NAME,
      title: socialTitle,
      description,
      images: [DEFAULT_SOCIAL_IMAGE],
    },
    twitter: {
      card: "summary_large_image",
      title: socialTitle,
      description,
      images: [DEFAULT_SOCIAL_IMAGE.url],
    },
  };
}
