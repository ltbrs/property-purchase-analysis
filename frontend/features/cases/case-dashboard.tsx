"use client";

import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/icons";
import { CaseCreation } from "@/features/cases/case-creation";
import { propertyTypeLabels } from "@/features/documents/document-catalog";
import { isPostHogConfigured } from "@/instrumentation-client";
import { productRoutes } from "@/lib/routes";
import {
  type AnalysisCase,
  CASE_CREATION_REQUEST_EVENT,
  fetchAnalysisCases,
  getWorkspace,
  saveWorkspace,
} from "@/lib/workspace";

const currencyFormatter = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("fr-FR", {
  maximumFractionDigits: 2,
});

export function CaseDashboard() {
  const router = useRouter();
  const creationRef = useRef<HTMLDivElement>(null);
  const [analysisCases, setAnalysisCases] = useState<AnalysisCase[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [showCreation, setShowCreation] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadCases() {
      try {
        const cases = await fetchAnalysisCases();
        if (!cancelled) {
          setAnalysisCases(cases);
          setActiveCaseId(getWorkspace()?.caseId ?? null);
          setShowCreation((current) => current || cases.length === 0);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Impossible de charger les dossiers.",
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    function requestCreation() {
      setShowCreation(true);
      window.requestAnimationFrame(() => {
        creationRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }

    function requestCreationFromHash() {
      if (window.location.hash === "#nouveau-dossier") {
        window.requestAnimationFrame(requestCreation);
      }
    }

    void loadCases();
    requestCreationFromHash();
    window.addEventListener(CASE_CREATION_REQUEST_EVENT, requestCreation);
    window.addEventListener("hashchange", requestCreationFromHash);
    return () => {
      cancelled = true;
      window.removeEventListener(CASE_CREATION_REQUEST_EVENT, requestCreation);
      window.removeEventListener("hashchange", requestCreationFromHash);
    };
  }, []);

  function selectCase(analysisCase: AnalysisCase) {
    if (isPostHogConfigured) {
      posthog.capture("analysis_case_selected", {
        property_type: analysisCase.property_type,
      });
    }
    saveWorkspace(analysisCase.id);
    setActiveCaseId(analysisCase.id);
    router.push(productRoutes.caseOverview);
  }

  function beginCreation() {
    setShowCreation(true);
    window.requestAnimationFrame(() => {
      creationRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  return (
    <div className="case-dashboard">
      <header className="case-dashboard-heading">
        <div>
          <p className="eyebrow">Vue globale</p>
          <h1>Vos dossiers immobiliers</h1>
          <p>Sélectionnez un bien pour retrouver sa synthèse, ses documents et son analyse.</p>
        </div>
        <button type="button" onClick={beginCreation}>
          <Icon name="folder" /> Nouveau dossier
        </button>
      </header>

      {error ? <p className="creation-error" role="alert">{error}</p> : null}

      <section className="case-library" aria-labelledby="case-library-title">
        <div className="case-library-heading">
          <div>
            <p className="section-kicker">Portefeuille</p>
            <h2 id="case-library-title">Tous les dossiers</h2>
          </div>
          <span>{analysisCases.length}</span>
        </div>

        {isLoading ? (
          <div className="document-empty">Chargement des dossiers…</div>
        ) : analysisCases.length > 0 ? (
          <div className="case-grid">
            {analysisCases.map((analysisCase) => {
              const isActive = analysisCase.id === activeCaseId;
              return (
                <button
                  key={analysisCase.id}
                  type="button"
                  className={`case-card${isActive ? " is-active" : ""}`}
                  onClick={() => selectCase(analysisCase)}
                >
                  <span className="case-card-icon"><Icon name={analysisCase.property_type === "house" ? "home" : "building"} /></span>
                  <span className="case-card-main">
                    <span className="case-card-status">{isActive ? "Dossier sélectionné" : propertyTypeLabels[analysisCase.property_type]}</span>
                    <strong>{analysisCase.title}</strong>
                    <span className="case-card-details">
                      {analysisCase.price_eur ? currencyFormatter.format(Number(analysisCase.price_eur)) : "Prix non renseigné"}
                      {analysisCase.surface_m2 ? ` · ${numberFormatter.format(Number(analysisCase.surface_m2))} m²` : ""}
                      {analysisCase.lot_count ? ` · ${analysisCase.lot_count} lot${analysisCase.lot_count > 1 ? "s" : ""}` : ""}
                    </span>
                  </span>
                  <span className="case-card-action">Ouvrir <Icon name="arrow" /></span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="case-library-empty">
            <span><Icon name="folder" /></span>
            <strong>Aucun dossier pour le moment</strong>
            <p>Créez votre premier dossier pour commencer l’analyse d’un bien.</p>
          </div>
        )}
      </section>

      {showCreation ? (
        <div ref={creationRef} id="nouveau-dossier" className="case-creation-container">
          {analysisCases.length > 0 ? (
            <div className="creation-container-heading">
              <div>
                <p className="section-kicker">Ajouter un bien</p>
                <h2>Créer un nouveau dossier</h2>
              </div>
              <button type="button" onClick={() => setShowCreation(false)}>
                Fermer
              </button>
            </div>
          ) : null}
          <CaseCreation
            onCreated={(analysisCase) => {
              setAnalysisCases((current) => [analysisCase, ...current]);
              setActiveCaseId(analysisCase.id);
            }}
          />
        </div>
      ) : null}
    </div>
  );
}
