"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/icons";
import { API_URL, getWorkspace, readApiError } from "@/lib/workspace";

export type DpeExtractionSelection = {
  documentId: string;
  filename: string;
};

type SourceReference = {
  page_number: number;
  quote: string | null;
};

type DpeFact<T> = {
  value: T | null;
  source: SourceReference | null;
};

type AdemeData = {
  dpe_rating: string | null;
  ges_rating: string | null;
  energy_consumption_kwh_m2_year: number | null;
  greenhouse_gas_emissions_kg_co2_m2_year: number | null;
  surface: number | null;
  dpe_date: string | null;
  dpe_valid_until: string | null;
};

type DpeExtraction = {
  normalized_facts: {
    dpe_number: DpeFact<string>;
    dpe_rating: DpeFact<string>;
    dpe_rating_method: "document" | "ademe" | "calculated" | "missing";
    ges_rating: DpeFact<string>;
    energy_consumption_kwh_m2_year: DpeFact<number>;
    greenhouse_gas_emissions_kg_co2_m2_year: DpeFact<number>;
    estimated_annual_energy_cost_min: DpeFact<number>;
    estimated_annual_energy_cost_max: DpeFact<number>;
    surface: DpeFact<number>;
    heating_type: DpeFact<string>;
    hot_water_type: DpeFact<string>;
    dpe_date: DpeFact<string>;
    dpe_valid_until: DpeFact<string>;
    recommendations: {
      description: string;
      source: SourceReference;
    }[];
    ademe_verification: {
      status:
        | "not_attempted"
        | "verified"
        | "verified_with_inconsistencies"
        | "not_found"
        | "unavailable";
      dpe_number: string | null;
      data: AdemeData | null;
      consistent_fields: string[];
      inconsistent_fields: string[];
    };
  };
};

const numberFormatter = new Intl.NumberFormat("fr-FR", {
  maximumFractionDigits: 2,
});
const currencyFormatter = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});
const dateFormatter = new Intl.DateTimeFormat("fr-FR", { dateStyle: "long" });

function formatDate(value: string | null) {
  if (!value) return "Non extrait";
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.valueOf()) ? value : dateFormatter.format(parsed);
}

function FactCard({
  label,
  value,
  source,
}: {
  label: string;
  value: string;
  source?: SourceReference | null;
}) {
  return (
    <div className="dpe-fact-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {source ? <small>Source : page {source.page_number}</small> : null}
    </div>
  );
}

export function DpeExtractionViewer({
  document,
  onClose,
}: {
  document: DpeExtractionSelection;
  onClose: () => void;
}) {
  const [extraction, setExtraction] = useState<DpeExtraction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    const previousActiveElement = window.document.activeElement;
    const previousOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    async function loadDpeExtraction() {
      const workspace = getWorkspace();
      if (!workspace) {
        setError("Aucun dossier n’est actuellement sélectionné.");
        return;
      }
      try {
        const response = await fetch(
          `${API_URL}/analysis-cases/${workspace.caseId}/documents/${document.documentId}/dpe-extraction`,
          {
            cache: "no-store",
            headers: { "X-User-Id": workspace.userId },
            signal: controller.signal,
          },
        );
        if (!response.ok) throw new Error(await readApiError(response));
        setExtraction((await response.json()) as DpeExtraction);
      } catch (loadError) {
        if (controller.signal.aborted) return;
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Les données DPE ne peuvent pas être affichées pour le moment.",
        );
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    void loadDpeExtraction();
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      controller.abort();
      window.removeEventListener("keydown", closeOnEscape);
      window.document.body.style.overflow = previousOverflow;
      if (previousActiveElement instanceof HTMLElement) previousActiveElement.focus();
    };
  }, [document.documentId, onClose]);

  const facts = extraction?.normalized_facts;
  const ademe = facts?.ademe_verification.data;
  const verificationStatus = facts?.ademe_verification.status;
  const verificationCopy = {
    verified: ["Vérifié auprès de l’ADEME", "Le numéro a été retrouvé et les données comparables sont cohérentes."],
    verified_with_inconsistencies: ["Écarts avec l’ADEME", "Le numéro existe, mais certaines données diffèrent du registre."],
    not_found: ["Non retrouvé dans le registre", "Le numéro extrait n’a pas été trouvé dans le jeu de données ADEME."],
    unavailable: ["Vérification indisponible", "L’API ADEME n’était pas disponible pendant l’analyse."],
    not_attempted: ["Vérification non effectuée", "Aucun numéro DPE exploitable n’a été détecté."],
  } as const;
  const verification = verificationStatus
    ? verificationCopy[verificationStatus]
    : null;

  return (
    <div className="pdf-viewer-layer">
      <button
        type="button"
        className="pdf-viewer-backdrop"
        aria-label="Fermer les données DPE"
        onClick={onClose}
      />
      <section
        className="pdf-viewer-dialog dpe-viewer-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dpe-viewer-title"
      >
        <header className="pdf-viewer-header">
          <div>
            <p className="section-kicker">Données DPE structurées</p>
            <h2 id="dpe-viewer-title">{document.filename}</h2>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            className="icon-button"
            aria-label="Fermer"
            onClick={onClose}
          >
            <Icon name="x" />
          </button>
        </header>

        <div className="dpe-viewer-content">
          {error ? (
            <div className="pdf-viewer-state" role="alert">
              <span className="state-icon"><Icon name="alert" /></span>
              <strong>Données DPE indisponibles</strong>
              <span>{error}</span>
            </div>
          ) : facts && verification ? (
            <>
              <section className={`dpe-verification-card is-${verificationStatus}`}>
                <span className="dpe-verification-icon"><Icon name={verificationStatus === "verified" ? "check" : "info"} /></span>
                <div>
                  <strong>{verification[0]}</strong>
                  <p>{verification[1]}</p>
                  {facts.dpe_number.value ? <small>N° {facts.dpe_number.value}</small> : null}
                </div>
              </section>

              <div className="dpe-rating-grid">
                <div className="dpe-rating-card">
                  <span>Classe énergie</span>
                  <strong>{facts.dpe_rating.value ?? ademe?.dpe_rating ?? "—"}</strong>
                  <small>
                    {facts.dpe_rating_method === "ademe"
                      ? "Valeur ADEME"
                      : facts.dpe_rating_method === "calculated"
                        ? "Calculée depuis les valeurs extraites"
                        : "Valeur du document"}
                  </small>
                </div>
                <div className="dpe-rating-card is-ges">
                  <span>Classe GES</span>
                  <strong>{facts.ges_rating.value ?? ademe?.ges_rating ?? "—"}</strong>
                  <small>Émissions de gaz à effet de serre</small>
                </div>
              </div>

              <section className="dpe-data-section">
                <h3>Valeurs clés</h3>
                <div className="dpe-facts-grid">
                  <FactCard
                    label="Consommation énergétique"
                    value={
                      (facts.energy_consumption_kwh_m2_year.value ?? ademe?.energy_consumption_kwh_m2_year) != null
                        ? `${numberFormatter.format(facts.energy_consumption_kwh_m2_year.value ?? ademe?.energy_consumption_kwh_m2_year ?? 0)} kWhEP/m²/an`
                        : "Non extraite"
                    }
                    source={facts.energy_consumption_kwh_m2_year.source ?? facts.dpe_number.source}
                  />
                  <FactCard
                    label="Émissions"
                    value={
                      (facts.greenhouse_gas_emissions_kg_co2_m2_year.value ?? ademe?.greenhouse_gas_emissions_kg_co2_m2_year) != null
                        ? `${numberFormatter.format(facts.greenhouse_gas_emissions_kg_co2_m2_year.value ?? ademe?.greenhouse_gas_emissions_kg_co2_m2_year ?? 0)} kgCO₂e/m²/an`
                        : "Non extraites"
                    }
                    source={facts.greenhouse_gas_emissions_kg_co2_m2_year.source ?? facts.dpe_number.source}
                  />
                  <FactCard
                    label="Surface de référence"
                    value={
                      (facts.surface.value ?? ademe?.surface) != null
                        ? `${numberFormatter.format(facts.surface.value ?? ademe?.surface ?? 0)} m²`
                        : "Non extraite"
                    }
                    source={facts.surface.source}
                  />
                  <FactCard label="Établi le" value={formatDate(facts.dpe_date.value ?? ademe?.dpe_date ?? null)} source={facts.dpe_date.source} />
                  <FactCard label="Valable jusqu’au" value={formatDate(facts.dpe_valid_until.value ?? ademe?.dpe_valid_until ?? null)} source={facts.dpe_valid_until.source} />
                  <FactCard
                    label="Coût annuel estimé"
                    value={
                      facts.estimated_annual_energy_cost_min.value != null && facts.estimated_annual_energy_cost_max.value != null
                        ? `${currencyFormatter.format(facts.estimated_annual_energy_cost_min.value)} à ${currencyFormatter.format(facts.estimated_annual_energy_cost_max.value)}`
                        : "Non extrait"
                    }
                    source={facts.estimated_annual_energy_cost_max.source}
                  />
                </div>
              </section>

              <section className="dpe-data-section">
                <h3>Équipements</h3>
                <div className="dpe-facts-grid">
                  <FactCard label="Chauffage" value={facts.heating_type.value ?? "Non extrait"} source={facts.heating_type.source} />
                  <FactCard label="Eau chaude" value={facts.hot_water_type.value ?? "Non extrait"} source={facts.hot_water_type.source} />
                </div>
              </section>

              {facts.recommendations.length > 0 ? (
                <section className="dpe-data-section">
                  <h3>Recommandations du DPE</h3>
                  <ul className="dpe-recommendations">
                    {facts.recommendations.map((recommendation, index) => (
                      <li key={`${recommendation.source.page_number}-${index}`}>
                        <span>{recommendation.description}</span>
                        <small>Page {recommendation.source.page_number}</small>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}
            </>
          ) : (
            <div className="pdf-viewer-state">
              <span className="state-icon is-loading"><Icon name="refresh" /></span>
              <strong>Chargement des données DPE…</strong>
              <span>Lecture de l’extraction structurée et de la vérification ADEME.</span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
