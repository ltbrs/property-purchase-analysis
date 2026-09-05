"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type MouseEvent, type ReactNode } from "react";
import posthog from "posthog-js";

import { isPostHogConfigured } from "@/instrumentation-client";
import { BrandLink } from "@/components/design-system/brand-link";
import { Icon, type IconName } from "@/components/icons";
import { marketingRoutes, productRoutes } from "@/lib/routes";
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
  user: {
    id: string;
    email?: string | null;
    name?: string | null;
  };
}>;

export function ApplicationShell({ children, user }: ApplicationShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [analysisCases, setAnalysisCases] = useState<AnalysisCase[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);

  const caseNavItems: { href: string; label: string; icon: IconName }[] = [
    { href: productRoutes.caseOverview, label: "Vue d’ensemble", icon: "gauge" },
    { href: productRoutes.documents, label: "Documents", icon: "folder" },
    { href: productRoutes.analysis, label: "Analyse", icon: "shield" },
  ];
  const activeCase = analysisCases.find(({ id }) => id === activeCaseId) ?? null;
  const isGlobalView = pathname === productRoutes.home || pathname === productRoutes.cases;

  useEffect(() => {
    if (!isPostHogConfigured) return;

    posthog.identify(user.id, {
      ...(user.email ? { email: user.email } : {}),
      ...(user.name ? { name: user.name } : {}),
    });
  }, [user.email, user.id, user.name]);

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
    router.push(productRoutes.caseOverview);
  }

  function requestCaseCreation() {
    window.dispatchEvent(new Event(CASE_CREATION_REQUEST_EVENT));
  }

  function resetPostHogOnSignOut(event: MouseEvent<HTMLDivElement>) {
    const target = event.target;
    if (isPostHogConfigured && target instanceof HTMLElement && target.closest("[data-posthog-reset]")) {
      posthog.reset();
    }
  }

  return (
    <div className="app-frame" onClickCapture={resetPostHogOnSignOut}>
      <aside className={`sidebar${isMenuOpen ? " is-open" : ""}`}>
        <BrandLink
          className="brand"
          href={productRoutes.home}
          appearance="on-dark"
          priority
          onClick={() => setIsMenuOpen(false)}
        />

        <nav className="sidebar-nav sidebar-global-nav" aria-label="Navigation globale">
          <Link
            href={productRoutes.cases}
            className={isGlobalView ? "is-active" : undefined}
            aria-current={isGlobalView ? "page" : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            <Icon name="folder" />
            <span>Tous les dossiers</span>
          </Link>
          <Link
            href={productRoutes.account}
            className={pathname === productRoutes.account ? "is-active" : undefined}
            aria-current={pathname === productRoutes.account ? "page" : undefined}
            onClick={() => setIsMenuOpen(false)}
          >
            <Icon name="home" />
            <span>Mon compte</span>
          </Link>
        </nav>

        <section className="sidebar-cases" aria-labelledby="sidebar-cases-title">
          <div className="sidebar-section-heading">
            <span id="sidebar-cases-title">Dossiers</span>
            <Link href={`${productRoutes.cases}#nouveau-dossier`} aria-label="Créer un nouveau dossier" onClick={() => setIsMenuOpen(false)}>+</Link>
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
        <Link
          className="sidebar-exit"
          href={marketingRoutes.home}
          onClick={() => setIsMenuOpen(false)}
        >
          <Icon name="arrow" />
          <span>Retour sur Acquora.fr</span>
        </Link>
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
            <Link className="primary-action" href={productRoutes.documents}>
              <Icon name="upload" />
              <span>Ajouter</span>
            </Link>
          ) : (
            <Link className="primary-action" href={productRoutes.cases}>
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
