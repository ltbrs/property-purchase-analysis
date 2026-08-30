"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { Icon, type IconName } from "@/components/icons";
import {
  type AnalysisCase,
  CASE_CREATION_REQUEST_EVENT,
  fetchAnalysisCases,
  getWorkspace,
  saveWorkspace,
  WORKSPACE_CHANGE_EVENT,
} from "@/lib/workspace";

type ApplicationShellProps = Readonly<{
  children: ReactNode;
}>;

export function ApplicationShell({ children }: ApplicationShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [analysisCases, setAnalysisCases] = useState<AnalysisCase[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);

  const caseNavItems: { href: string; label: string; icon: IconName }[] = [
    { href: "/overview", label: "Vue d’ensemble", icon: "gauge" },
    { href: "/upload", label: "Documents", icon: "folder" },
    { href: "/analysis", label: "Alertes", icon: "shield" },
  ];
  const activeCase = analysisCases.find(({ id }) => id === activeCaseId) ?? null;
  const isGlobalView = pathname === "/";

  useEffect(() => {
    let cancelled = false;

    async function refreshCases() {
      try {
        const cases = await fetchAnalysisCases();
        if (!cancelled) {
          setAnalysisCases(cases);
          setActiveCaseId(getWorkspace()?.caseId ?? null);
        }
      } catch {
        // Page content owns service errors; navigation keeps its last stable state.
      }
    }

    void refreshCases();
    window.addEventListener(WORKSPACE_CHANGE_EVENT, refreshCases);
    window.addEventListener("storage", refreshCases);
    return () => {
      cancelled = true;
      window.removeEventListener(WORKSPACE_CHANGE_EVENT, refreshCases);
      window.removeEventListener("storage", refreshCases);
    };
  }, [pathname]);

  function selectCase(analysisCase: AnalysisCase) {
    saveWorkspace(analysisCase.id);
    setActiveCaseId(analysisCase.id);
    setIsMenuOpen(false);
    router.push("/overview");
  }

  function requestCaseCreation() {
    window.dispatchEvent(new Event(CASE_CREATION_REQUEST_EVENT));
  }

  return (
    <div className="app-frame">
      <aside className={`sidebar${isMenuOpen ? " is-open" : ""}`}>
        <Link
          className="brand"
          href="/"
          aria-label="Acquora — accueil"
          onClick={() => setIsMenuOpen(false)}
        >
          <Image
            src="/brand/acquora-wordmark-dark.svg"
            alt="Acquora"
            width={520}
            height={150}
            priority
          />
        </Link>

        <nav className="sidebar-nav sidebar-global-nav" aria-label="Navigation globale">
          <Link
            href="/"
            className={isGlobalView ? "is-active" : undefined}
            aria-current={isGlobalView ? "page" : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            <Icon name="folder" />
            <span>Tous les dossiers</span>
          </Link>
        </nav>

        <section className="sidebar-cases" aria-labelledby="sidebar-cases-title">
          <div className="sidebar-section-heading">
            <span id="sidebar-cases-title">Dossiers</span>
            <Link href="/#nouveau-dossier" aria-label="Créer un nouveau dossier" onClick={() => setIsMenuOpen(false)}>+</Link>
          </div>
          {analysisCases.length > 0 ? (
            <div className="sidebar-case-list">
              {analysisCases.map((analysisCase) => (
                <button
                  key={analysisCase.id}
                  type="button"
                  className={analysisCase.id === activeCaseId ? "is-selected" : undefined}
                  aria-pressed={analysisCase.id === activeCaseId}
                  onClick={() => selectCase(analysisCase)}
                >
                  <span><Icon name={analysisCase.property_type === "house" ? "home" : "building"} /></span>
                  <strong>{analysisCase.title}</strong>
                  <Icon name="chevron" />
                </button>
              ))}
            </div>
          ) : (
            <p className="sidebar-cases-empty">Aucun dossier créé</p>
          )}
        </section>

        {activeCase ? (
          <nav className="sidebar-nav sidebar-case-nav" aria-label={`Navigation de ${activeCase.title}`}>
            <p>{activeCase.title}</p>
            {caseNavItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
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
        ) : null}

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
            <span>{isGlobalView ? "Espace immobilier" : "Dossier d’achat"}</span>
            <strong>{isGlobalView ? "Tous les dossiers" : activeCase?.title ?? "Aucun dossier sélectionné"}</strong>
          </div>
          {isGlobalView ? (
            <button className="primary-action" type="button" onClick={requestCaseCreation}>
              <Icon name="folder" />
              <span>Créer</span>
            </button>
          ) : activeCase ? (
            <Link className="primary-action" href="/upload">
              <Icon name="upload" />
              <span>Ajouter</span>
            </Link>
          ) : (
            <Link className="primary-action" href="/">
              <Icon name="folder" />
              <span>Dossiers</span>
            </Link>
          )}
        </header>
        <main
          key={activeCaseId ?? "no-active-case"}
          className="workspace-main"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
