import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { BrandLink } from "@/components/design-system/brand-link";
import { ButtonLink } from "@/components/design-system/button-link";
import { marketingRoutes, productRoutes } from "@/lib/routes";

import "./marketing.css";

export const metadata: Metadata = {
  title: {
    default: "Acquora — Achetez en sachant",
    template: "%s — Acquora",
  },
};

const navigation = [
  { href: marketingRoutes.features, label: "Fonctionnalités" },
  { href: marketingRoutes.howItWorks, label: "Comment ça marche" },
  { href: marketingRoutes.pricing, label: "Tarifs" },
  { href: marketingRoutes.exampleAnalysis, label: "Exemple d’analyse" },
  { href: marketingRoutes.blog, label: "Blog" },
  { href: marketingRoutes.faq, label: "FAQ" },
] as const;

type MarketingLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function MarketingLayout({ children }: MarketingLayoutProps) {
  return (
    <div className="marketing-shell">
      <header className="marketing-header">
        <BrandLink
          className="marketing-brand"
          href={marketingRoutes.home}
          priority
        />
        <nav className="marketing-nav" aria-label="Navigation principale">
          {navigation.map((item) => (
            <Link key={item.href} href={item.href}>{item.label}</Link>
          ))}
        </nav>
        <ButtonLink href={productRoutes.home}>Mon espace personnel</ButtonLink>
      </header>

      <main className="marketing-main">{children}</main>

      <footer className="marketing-footer">
        <span>Acquora.fr</span>
        <nav aria-label="Rubriques du blog">
          <Link href={marketingRoutes.blogDpe}>DPE</Link>
          <Link href={marketingRoutes.blogCoproperty}>Copropriété</Link>
          <Link href={`${marketingRoutes.blog}/exemple-article`}>Article exemple</Link>
        </nav>
      </footer>
    </div>
  );
}
