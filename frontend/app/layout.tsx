import type { Metadata } from "next";
import type { ReactNode } from "react";

import { ApplicationShell } from "@/components/application-shell";

import "./globals.css";

export const metadata: Metadata = {
  title: "Clairimmo — Analyse immobilière",
  description: "Analyse documentée des risques d'un achat immobilier en France.",
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="fr">
      <body>
        <ApplicationShell>{children}</ApplicationShell>
      </body>
    </html>
  );
}
