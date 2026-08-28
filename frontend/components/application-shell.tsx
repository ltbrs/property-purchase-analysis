"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";

import { Icon, type IconName } from "@/components/icons";

type ApplicationShellProps = Readonly<{
  children: ReactNode;
}>;

export function ApplicationShell({ children }: ApplicationShellProps) {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems: { href: string; label: string; icon: IconName }[] = [
    { href: "/", label: "Vue d’ensemble", icon: "gauge" },
    { href: "/upload", label: "Documents", icon: "folder" },
    { href: "/analysis", label: "Alertes", icon: "shield" },
  ];

  return (
    <div className="app-frame">
      <aside className={`sidebar${isMenuOpen ? " is-open" : ""}`}>
        <Link className="brand" href="/" onClick={() => setIsMenuOpen(false)}>
          <span className="brand-mark"><Icon name="home" /></span>
          <span>Clairimmo</span>
        </Link>

        <nav className="sidebar-nav" aria-label="Navigation principale">
          {navItems.map((item) => {
            const isActive =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={isActive ? "is-active" : undefined}
                aria-current={isActive ? "page" : undefined}
                onClick={() => setIsMenuOpen(false)}
              >
                <Icon name={item.icon} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-note">
          <Icon name="info" />
          <p>Chaque constat reste relié à sa page source.</p>
        </div>
      </aside>

      {isMenuOpen ? (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Fermer le menu"
          onClick={() => setIsMenuOpen(false)}
        />
      ) : null}

      <div className="workspace-shell">
        <header className="workspace-header">
          <button
            type="button"
            className="menu-button"
            aria-label="Ouvrir le menu"
            aria-expanded={isMenuOpen}
            onClick={() => setIsMenuOpen(true)}
          >
            <Icon name="menu" />
          </button>
          <div className="case-title">
            <span>Dossier d’achat</span>
            <strong>Mon achat immobilier</strong>
          </div>
          <Link className="primary-action" href="/upload">
            <Icon name="upload" />
            <span>Ajouter</span>
          </Link>
        </header>
        <main className="workspace-main">{children}</main>
      </div>
    </div>
  );
}
