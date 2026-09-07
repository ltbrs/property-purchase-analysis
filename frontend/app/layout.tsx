import type { Metadata } from "next";
import type { ReactNode } from "react";

import { VercelWebAnalytics } from "@/components/analytics/vercel-web-analytics";
import { SITE_DESCRIPTION, SITE_NAME, SITE_URL } from "@/lib/seo";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  applicationName: SITE_NAME,
  title: "Analyse des documents d’un achat immobilier | Acquora",
  description: SITE_DESCRIPTION,
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="fr">
      <body>
        {children}
        <VercelWebAnalytics />
      </body>
    </html>
  );
}
