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
  { href: marketingRoutes.howItWorks, label: "Comment ça marche" },
  { href: marketingRoutes.pricing, label: "Tarifs" },
  { href: marketingRoutes.blog, label: "Blog" },
  { href: marketingRoutes.contact, label: "Nous contacter" },
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
        <div className="marketing-footer-inner">
          <div className="marketing-footer-intro">
            <BrandLink
              appearance="on-dark"
              className="marketing-footer-brand"
              href={marketingRoutes.home}
            />
            <p>
              Les documents de votre achat immobilier, transformés en points de
              vigilance clairs et sourcés.
            </p>
          </div>

          <nav className="marketing-footer-links" aria-label="Pied de page">
            <div>
              <strong>Découvrir</strong>
              <Link href={marketingRoutes.howItWorks}>Comment ça marche</Link>
              <Link href={marketingRoutes.pricing}>Tarifs</Link>
            </div>
            <div>
              <strong>Ressources</strong>
              <Link href={marketingRoutes.blog}>Tous les guides</Link>
              <Link href={marketingRoutes.blogCoproperty}>Copropriété</Link>
              <Link href={`${marketingRoutes.blog}/documents-achat-appartement`}>
                Documents à vérifier
              </Link>
            </div>
            <div>
              <strong>Acquora</strong>
              <Link href={marketingRoutes.contact}>Nous contacter</Link>
              <Link href={productRoutes.home}>Mon espace personnel</Link>
            </div>
          </nav>

          <div className="marketing-footer-bottom">
            <span>© {new Date().getFullYear()} Acquora</span>
            <p>
              Outil d’aide à la décision. Ne remplace pas les conseils d’un
              notaire, d’un diagnostiqueur ou d’un professionnel du bâtiment.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
