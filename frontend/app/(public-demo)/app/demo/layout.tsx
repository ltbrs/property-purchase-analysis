import type { Metadata } from "next";
import type { ReactNode } from "react";

import { ApplicationShell } from "@/components/application-shell";

export const metadata: Metadata = {
  title: "Dossier de démonstration | Acquora",
  description: "Explorez un dossier immobilier fictif dans l’application Acquora, avec sa synthèse, ses documents et son analyse sourcée.",
  robots: { index: false, follow: false },
};

export default function PublicDemoLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <div className="product-universe">
      <ApplicationShell demoMode>{children}</ApplicationShell>
    </div>
  );
}
