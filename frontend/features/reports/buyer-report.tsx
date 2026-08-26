"use client";

import { useEffect, useState } from "react";

import {
  API_URL,
  getOrCreateWorkspace,
  readApiError,
  resetWorkspace,
  type Workspace,
} from "@/lib/workspace";

type Severity = "info" | "low" | "medium" | "high" | "critical";
type FindingStatus =
  | "confirmed"
  | "likely"
  | "possible"
  | "missing_information";
type Expectation =
  | "definitely_expected"
  | "usually_useful"
  | "context_dependent";

type ReportSource = {
  document_id: string;
  document_name: string;
  page_number: number;
  quote: string | null;
};

type ReportFinding = {
  code: string;
  finding_key: string;
  severity: Severity;
  title: string;
  explanation: string;
  status: FindingStatus;
  confidence: number | null;
  amount_eur: number | string | null;
  expectation_level: Expectation | null;
  missing_reason: "absent" | "insufficient" | null;
  sources: ReportSource[];
};

type ReportSection = {
  code: string;
  title: string;
  findings: ReportFinding[];
};

type BuyerReportData = {
  analysis_case_id: string;
  title: string;
  generated_at: string;
  summary: {
    finding_count: number;
    high_or_critical_count: number;
    missing_information_count: number;
    reassuring_count: number;
  };
  sections: ReportSection[];
  disclaimer: string;
};

const severityLabels: Record<Severity, string> = {
  info: "Information",
  low: "Faible",
  medium: "À examiner",
  high: "Important",
  critical: "Critique",
};

const statusLabels: Record<FindingStatus, string> = {
  confirmed: "Confirmé",
  likely: "Probable",
  possible: "Possible",
  missing_information: "Information manquante",
};

const expectationLabels: Record<Expectation, string> = {
  definitely_expected: "Attendu dans le dossier",
  usually_useful: "Habituellement utile",
  context_dependent: "Selon le contexte",
};

const currencyFormatter = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "long",
  timeStyle: "short",
});

async function requestReport(workspace: Workspace) {
  return fetch(`${API_URL}/analysis-cases/${workspace.caseId}/report/refresh`, {
    method: "POST",
    headers: { "X-User-Id": workspace.userId },
  });
}

async function loadReport() {
  let workspace = await getOrCreateWorkspace();
  let response = await requestReport(workspace);
  if (response.status === 404) {
    resetWorkspace(workspace.caseId);
    workspace = await getOrCreateWorkspace();
    response = await requestReport(workspace);
  }
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as BuyerReportData;
}

function FindingCard({ finding }: { finding: ReportFinding }) {
  return (
    <article className={`finding-card severity-${finding.severity}`}>
      <div className="finding-heading">
        <div>
          <div className="finding-badges">
            <span className={`severity-badge severity-${finding.severity}`}>
              {severityLabels[finding.severity]}
            </span>
            <span className="certainty-badge">{statusLabels[finding.status]}</span>
            {finding.expectation_level ? (
              <span className="expectation-badge">
                {expectationLabels[finding.expectation_level]}
              </span>
            ) : null}
          </div>
          <h3>{finding.title}</h3>
        </div>
        {finding.amount_eur !== null ? (
          <strong className="finding-amount">
            {currencyFormatter.format(Number(finding.amount_eur))}
          </strong>
        ) : null}
      </div>
      <p>{finding.explanation}</p>
      {finding.sources.length > 0 ? (
        <ul className="finding-sources" aria-label="Sources documentaires">
          {finding.sources.map((source) => (
            <li key={`${source.document_id}-${source.page_number}`}>
              <span aria-hidden="true">PDF</span>
              <div>
                <strong>{source.document_name}</strong>
                <small>Page {source.page_number}</small>
                {source.quote ? <q>{source.quote}</q> : null}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="finding-no-source">
          Constat fondé sur l’absence de pièce dans le dossier transmis.
        </p>
      )}
    </article>
  );
}

export function BuyerReport() {
  const [report, setReport] = useState<BuyerReportData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      setReport(await loadReport());
    } catch (refreshError) {
      setError(
        refreshError instanceof Error
          ? refreshError.message
          : "Le rapport n’a pas pu être généré.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    void loadReport()
      .then((loadedReport) => {
        if (!cancelled) setReport(loadedReport);
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Le rapport n’a pas pu être généré.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (isLoading && report === null) {
    return <div className="report-state">Génération du rapport documenté…</div>;
  }

  if (error && report === null) {
    return (
      <div className="report-state report-error" role="alert">
        <strong>Rapport indisponible</strong>
        <span>{error}</span>
        <button type="button" onClick={() => void refresh()}>
          Réessayer
        </button>
      </div>
    );
  }

  if (report === null) return null;

  const populatedSections = report.sections.filter(
    (section) => section.findings.length > 0,
  );

  return (
    <div className="buyer-report">
      <section className="report-summary" aria-labelledby="report-summary-title">
        <div>
          <p className="section-kicker">Synthèse du dossier</p>
          <h2 id="report-summary-title">{report.title}</h2>
          <p>
            Mis à jour le {dateFormatter.format(new Date(report.generated_at))}
          </p>
        </div>
        <button
          className="refresh-button"
          type="button"
          disabled={isLoading}
          onClick={() => void refresh()}
        >
          {isLoading ? "Mise à jour…" : "Actualiser l’analyse"}
        </button>
        <dl className="summary-metrics">
          <div>
            <dt>Constats</dt>
            <dd>{report.summary.finding_count}</dd>
          </div>
          <div>
            <dt>Importants ou critiques</dt>
            <dd>{report.summary.high_or_critical_count}</dd>
          </div>
          <div>
            <dt>Informations manquantes</dt>
            <dd>{report.summary.missing_information_count}</dd>
          </div>
          <div>
            <dt>Éléments rassurants</dt>
            <dd>{report.summary.reassuring_count}</dd>
          </div>
        </dl>
      </section>

      {error ? <p className="report-inline-error">{error}</p> : null}

      {populatedSections.length > 0 ? (
        <div className="report-sections">
          {populatedSections.map((section) => (
            <section key={section.code} className="report-section">
              <div className="report-section-heading">
                <h2>{section.title}</h2>
                <span>{section.findings.length}</span>
              </div>
              <div className="finding-list">
                {section.findings.map((finding) => (
                  <FindingCard key={finding.finding_key} finding={finding} />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="report-state">
          Aucun constat n’a encore pu être établi à partir des documents.
        </div>
      )}

      <p className="report-disclaimer">{report.disclaimer}</p>
    </div>
  );
}
