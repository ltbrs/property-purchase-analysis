"use client";

import Link from "next/link";
import posthog from "posthog-js";
import { useEffect, useState } from "react";

import { Icon, type IconName } from "@/components/icons";
import {
  PdfViewer,
  type PdfDocumentSelection,
} from "@/features/documents/pdf-viewer";
import { isPostHogConfigured } from "@/instrumentation-client";
import { productRoutes } from "@/lib/routes";
import {
  API_URL,
  getWorkspace,
  readApiError,
  resetWorkspace,
  type Workspace,
} from "@/lib/workspace";

type Severity = "info" | "low" | "medium" | "high" | "critical";
type FindingStatus = "confirmed" | "likely" | "possible" | "missing_information";
type AnalysisType = "risk" | "verification" | "reassuring" | "missing_information";
type ReviewStatus = "open" | "not_problematic";
type Expectation = "definitely_expected" | "usually_useful" | "context_dependent";

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
  analysis_type: AnalysisType;
  review_status: ReviewStatus;
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
    analyzed_count: number;
    risk_count: number;
    verification_count: number;
    high_or_critical_count: number;
    missing_information_count: number;
    reassuring_count: number;
    risk_severity_counts: Record<Severity, number>;
  };
  sections: ReportSection[];
  disclaimer: string;
};

type BuyerReportProps = {
  variant?: "overview" | "details";
};

const severityLabels: Record<Severity, string> = {
  info: "Information",
  low: "Faible",
  medium: "À vérifier",
  high: "Important",
  critical: "Critique",
};

const statusLabels: Record<FindingStatus, string> = {
  confirmed: "Confirmé",
  likely: "Probable",
  possible: "Possible",
  missing_information: "Information manquante",
};

const analysisTypeLabels: Record<AnalysisType, string> = {
  risk: "Risque",
  verification: "Point à vérifier",
  reassuring: "Point rassurant",
  missing_information: "Élément manquant",
};

const expectationLabels: Record<Expectation, string> = {
  definitely_expected: "Attendu dans le dossier",
  usually_useful: "Habituellement utile",
  context_dependent: "Selon le contexte",
};

const severityRank: Record<Severity, number> = {
  critical: 5,
  high: 4,
  medium: 3,
  low: 2,
  info: 1,
};

const currencyFormatter = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

async function requestReport(workspace: Workspace) {
  return fetch(`${API_URL}/analysis-cases/${workspace.caseId}/report/refresh`, {
    method: "POST",
  });
}

async function fetchReport(workspace: Workspace): Promise<BuyerReportData | null> {
  const response = await requestReport(workspace);
  if (response.status === 404) {
    resetWorkspace(workspace.caseId);
    return null;
  }
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as BuyerReportData;
}

async function updateFindingReview(
  workspace: Workspace,
  findingKey: string,
  reviewStatus: ReviewStatus,
) {
  const response = await fetch(
    `${API_URL}/analysis-cases/${workspace.caseId}/findings/${encodeURIComponent(findingKey)}/review`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ review_status: reviewStatus }),
    },
  );
  if (!response.ok) throw new Error(await readApiError(response));
}

const pendingReportLoads = new Map<string, Promise<BuyerReportData | null>>();

function loadReport(): Promise<BuyerReportData | null> {
  const workspace = getWorkspace();
  if (!workspace) return Promise.resolve(null);

  const requestKey = workspace.caseId;
  const pendingLoad = pendingReportLoads.get(requestKey);
  if (pendingLoad) return pendingLoad;

  const load = fetchReport(workspace).finally(() => {
    if (pendingReportLoads.get(requestKey) === load) {
      pendingReportLoads.delete(requestKey);
    }
  });
  pendingReportLoads.set(requestKey, load);
  return load;
}

function FindingRow({
  finding,
  onSelect,
  onReview,
  isUpdating,
}: {
  finding: ReportFinding;
  onSelect: (finding: ReportFinding) => void;
  onReview: (finding: ReportFinding, checked: boolean) => void;
  isUpdating: boolean;
}) {
  const isUserReviewed = finding.review_status === "not_problematic";
  const isReviewable = finding.analysis_type !== "missing_information"
    && (finding.analysis_type !== "reassuring" || isUserReviewed);
  const icon = finding.analysis_type === "reassuring"
    ? "check"
    : finding.analysis_type === "missing_information"
      ? "document"
      : finding.analysis_type === "verification"
        ? "info"
        : "alert";

  return (
    <div className={`finding-row analysis-${finding.analysis_type}`}>
      <button type="button" className="finding-row-main" onClick={() => onSelect(finding)}>
        <span className={`finding-icon severity-${finding.severity}`}>
          <Icon name={icon} />
        </span>
        <span className="finding-row-copy">
          <strong>{finding.title}</strong>
          <small>
            {finding.sources[0]
              ? `${finding.sources[0].document_name} · p. ${finding.sources[0].page_number}`
              : statusLabels[finding.status]}
          </small>
        </span>
        {finding.amount_eur !== null ? (
          <span className="finding-row-amount">
            {currencyFormatter.format(Number(finding.amount_eur))}
          </span>
        ) : null}
        <span className={`severity-pill severity-${finding.severity}`}>
          {finding.analysis_type === "reassuring"
            ? "Rassurant"
            : severityLabels[finding.severity]}
        </span>
        <Icon className="row-chevron" name="chevron" />
      </button>
      {isReviewable ? (
        <label className="finding-review-control">
          <input
            type="checkbox"
            checked={isUserReviewed}
            disabled={isUpdating}
            onChange={(event) => onReview(finding, event.target.checked)}
          />
          <span>Non problématique</span>
        </label>
      ) : null}
    </div>
  );
}

function Metric({ value, label }: { value: number; label: string }) {
  return (
    <div className="report-metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

const distributionLabels: Record<Severity, string> = {
  info: "Informations",
  low: "Risques faibles",
  medium: "Risques à vérifier",
  high: "Risques importants",
  critical: "Risques critiques",
};

function SummaryDistribution({ summary }: { summary: BuyerReportData["summary"] }) {
  const segments = [
    {
      key: "reassuring",
      count: summary.reassuring_count,
      label: "Points rassurants",
      className: "is-reassuring",
    },
    ...(["info", "low", "medium", "high", "critical"] as const).map(
      (severity) => ({
        key: severity,
        count: summary.risk_severity_counts[severity],
        label: distributionLabels[severity],
        className: `severity-${severity}`,
      }),
    ),
    {
      key: "verification",
      count: summary.verification_count,
      label: "Points à vérifier",
      className: "is-verification",
    },
    {
      key: "missing",
      count: summary.missing_information_count,
      label: "Informations à compléter",
      className: "is-missing",
    },
  ].filter((segment) => segment.count > 0);
  const total = segments.reduce((sum, segment) => sum + segment.count, 0);

  if (total === 0) {
    return <p className="dossier-distribution-empty">Ajoutez des documents pour commencer l’analyse.</p>;
  }

  return (
    <div className="dossier-distribution">
      <div
        className="dossier-distribution-bar"
        role="img"
        aria-label={
          `Répartition de ${total} points : ${summary.risk_count} risques, `
          + `${summary.verification_count} points à vérifier, `
          + `${summary.missing_information_count} éléments manquants et `
          + `${summary.reassuring_count} points rassurants.`
        }
      >
        {segments.map((segment) => {
          const percentage = (segment.count / total) * 100;
          return (
            <span
              key={segment.key}
              className={`dossier-distribution-segment ${segment.className}`}
              style={{ width: `${percentage}%` }}
              title={`${segment.label} : ${segment.count} (${Math.round(percentage)} %)`}
            />
          );
        })}
      </div>
      <div className="dossier-distribution-legend" aria-hidden="true">
        {segments.map((segment) => (
          <span key={segment.key} className={segment.className}>
            <i /> {segment.label} · {segment.count}
          </span>
        ))}
      </div>
    </div>
  );
}

function DetailDrawer({
  finding,
  onClose,
  onViewSource,
  onReview,
  isUpdating,
}: {
  finding: ReportFinding;
  onClose: () => void;
  onViewSource: (source: ReportSource) => void;
  onReview: (finding: ReportFinding, checked: boolean) => void;
  isUpdating: boolean;
}) {
  const isUserReviewed = finding.review_status === "not_problematic";
  const isReviewable = finding.analysis_type !== "missing_information"
    && (finding.analysis_type !== "reassuring" || isUserReviewed);

  return (
    <div className="detail-layer">
      <button type="button" className="detail-backdrop" aria-label="Fermer le détail" onClick={onClose} />
      <aside className="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="finding-detail-title">
        <div className="detail-header">
          <div className="detail-labels">
            <span className={`severity-pill severity-${finding.severity}`}>
              {severityLabels[finding.severity]}
            </span>
            <span>{statusLabels[finding.status]}</span>
            <span>{analysisTypeLabels[finding.analysis_type]}</span>
          </div>
          <button type="button" className="icon-button" aria-label="Fermer" onClick={onClose}>
            <Icon name="x" />
          </button>
          <h2 id="finding-detail-title">{finding.title}</h2>
          {finding.amount_eur !== null ? (
            <strong className="detail-amount">{currencyFormatter.format(Number(finding.amount_eur))}</strong>
          ) : null}
        </div>

        <div className="detail-content">
          {isReviewable ? (
            <label className="detail-review-control">
              <input
                type="checkbox"
                checked={isUserReviewed}
                disabled={isUpdating}
                onChange={(event) => onReview(finding, event.target.checked)}
              />
              <span>
                <strong>Cette alerte n’est pas problématique</strong>
                <small>Elle sera reclassée comme point rassurant dans la synthèse.</small>
              </span>
            </label>
          ) : null}
          <section className="explanation-block">
            <div><Icon name="info" /><strong>Pourquoi c’est important</strong></div>
            <p>{finding.explanation}</p>
          </section>

          {finding.expectation_level ? (
            <div className="detail-fact">
              <span>Niveau d’attente</span>
              <strong>{expectationLabels[finding.expectation_level]}</strong>
            </div>
          ) : null}

          <section className="source-section">
            <p className="section-kicker">Sources</p>
            {finding.sources.length > 0 ? (
              <div className="source-list">
                {finding.sources.map((source) => (
                  <article key={`${source.document_id}-${source.page_number}`} className="source-card">
                    <div className="source-heading">
                      <span className="document-glyph"><Icon name="document" /></span>
                      <div>
                        <strong>{source.document_name}</strong>
                        <small>Page {source.page_number}</small>
                      </div>
                      <button
                        type="button"
                        className="source-view-button"
                        onClick={() => onViewSource(source)}
                      >
                        Voir la page <Icon name="arrow" />
                      </button>
                    </div>
                    {source.quote ? <blockquote>« {source.quote} »</blockquote> : null}
                  </article>
                ))}
              </div>
            ) : (
              <p className="no-source-note">Constat fondé sur une pièce absente ou une information insuffisante.</p>
            )}
          </section>
        </div>
      </aside>
    </div>
  );
}

export function BuyerReport({ variant = "details" }: BuyerReportProps) {
  const [report, setReport] = useState<BuyerReportData | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<ReportFinding | null>(null);
  const [viewingSource, setViewingSource] = useState<PdfDocumentSelection | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [needsWorkspace, setNeedsWorkspace] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatingFindingKey, setUpdatingFindingKey] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const loadedReport = await loadReport();
      setNeedsWorkspace(loadedReport === null);
      setReport(loadedReport);
      if (loadedReport !== null && isPostHogConfigured) {
        posthog.capture("analysis_report_refreshed", { report_variant: variant });
      }
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Le rapport n’a pas pu être généré.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    void loadReport()
      .then((loadedReport) => {
        if (!cancelled) {
          setNeedsWorkspace(loadedReport === null);
          setReport(loadedReport);
        }
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Le rapport n’a pas pu être généré.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (selectedFinding === null || viewingSource !== null) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setSelectedFinding(null);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selectedFinding, viewingSource]);

  async function reviewFinding(finding: ReportFinding, checked: boolean) {
    const workspace = getWorkspace();
    if (!workspace) {
      setNeedsWorkspace(true);
      return;
    }
    setUpdatingFindingKey(finding.finding_key);
    setError(null);
    try {
      await updateFindingReview(
        workspace,
        finding.finding_key,
        checked ? "not_problematic" : "open",
      );
      const updatedReport = await fetchReport(workspace);
      setReport(updatedReport);
      if (isPostHogConfigured) {
        posthog.capture("report_finding_review_updated", {
          analysis_type: finding.analysis_type,
          review_status: checked ? "not_problematic" : "open",
          severity: finding.severity,
        });
      }
      setSelectedFinding(
        updatedReport?.sections
          .flatMap((section) => section.findings)
          .find((item) => item.finding_key === finding.finding_key) ?? null,
      );
    } catch (reviewError) {
      setError(
        reviewError instanceof Error
          ? reviewError.message
          : "Le reclassement n’a pas pu être enregistré.",
      );
    } finally {
      setUpdatingFindingKey(null);
    }
  }

  if (isLoading && report === null) {
    return (
      <div className="report-state">
        <span className="state-icon is-loading"><Icon name="refresh" /></span>
        <strong>Analyse du dossier…</strong>
        <span>Les constats et leurs sources sont en cours de préparation.</span>
      </div>
    );
  }

  if (needsWorkspace) {
    return (
      <div className="report-state">
        <span className="state-icon"><Icon name="folder" /></span>
        <strong>Créez d’abord votre dossier</strong>
        <span>Renseignez le bien avant d’ajouter des documents ou de lancer l’analyse.</span>
        <Link href={productRoutes.cases}>Créer mon dossier</Link>
      </div>
    );
  }

  if (error && report === null) {
    return (
      <div className="report-state report-error" role="alert">
        <span className="state-icon"><Icon name="alert" /></span>
        <strong>Rapport indisponible</strong>
        <span>{error}</span>
        <button type="button" onClick={() => void refresh()}>Réessayer</button>
      </div>
    );
  }

  if (report === null) return null;

  const allFindings = report.sections.flatMap((section) => section.findings);
  const analysisSections = [
    {
      code: "risk" as const,
      title: "Risques",
      kicker: "À prendre en compte",
      icon: "alert" as IconName,
    },
    {
      code: "verification" as const,
      title: "Points à vérifier",
      kicker: "À confirmer",
      icon: "info" as IconName,
    },
    {
      code: "reassuring" as const,
      title: "Points rassurants",
      kicker: "Vérifiés ou reclassés",
      icon: "check" as IconName,
    },
    {
      code: "missing_information" as const,
      title: "Éléments manquants",
      kicker: "À compléter",
      icon: "document" as IconName,
    },
  ].map((section) => ({
    ...section,
    findings: allFindings
      .filter((finding) => finding.analysis_type === section.code)
      .toSorted((left, right) => severityRank[right.severity] - severityRank[left.severity]),
  }));
  const populatedSections = analysisSections.filter((section) => section.findings.length > 0);
  const priorityFindings = allFindings
    .filter((finding) => finding.analysis_type === "risk" || finding.analysis_type === "verification")
    .toSorted((left, right) => severityRank[right.severity] - severityRank[left.severity]);
  const firstPriorityFindings = priorityFindings.slice(0, 4);

  return (
    <div className={`buyer-report report-${variant}`}>
      <header className="report-page-heading">
        <div>
          <p className="report-updated">Analyse mise à jour le {dateFormatter.format(new Date(report.generated_at))}</p>
          <h1>{variant === "overview" ? "Votre dossier, en clair" : "Analyse du dossier"}</h1>
        </div>
        <div className="report-heading-actions">
          <span className="attention-count">
            <i /> {report.summary.high_or_critical_count} risque{report.summary.high_or_critical_count === 1 ? "" : "s"} important{report.summary.high_or_critical_count === 1 ? "" : "s"}
          </span>
          <button className="refresh-icon-button" type="button" disabled={isLoading} aria-label="Actualiser l’analyse" title="Actualiser l’analyse" onClick={() => void refresh()}>
            <Icon name="refresh" />
          </button>
        </div>
      </header>

      {error ? <p className="report-inline-error">{error}</p> : null}

      {variant === "overview" ? (
        <>
          <div className="overview-grid">
            <section className="panel priority-panel">
              <div className="panel-heading">
                <div><p className="section-kicker">À traiter en premier</p><h2>Points prioritaires</h2></div>
                <Link className="text-link" href={productRoutes.analysis}>Tout voir <Icon name="arrow" /></Link>
              </div>
              {firstPriorityFindings.length > 0 ? (
                <div className="finding-rows">
                  {firstPriorityFindings.map((finding) => (
                    <FindingRow
                      key={finding.finding_key}
                      finding={finding}
                      onSelect={setSelectedFinding}
                      onReview={(item, checked) => void reviewFinding(item, checked)}
                      isUpdating={updatingFindingKey === finding.finding_key}
                    />
                  ))}
                </div>
              ) : (
                <p className="panel-empty">Aucun risque ni point à vérifier dans les pièces analysées.</p>
              )}
            </section>

            <section className="dossier-card">
              <div className="dossier-card-heading">
                <div><p className="section-kicker">Synthèse</p><strong>{report.summary.analyzed_count}</strong><span>points analysés</span></div>
                <Icon name="document" />
              </div>
              <SummaryDistribution summary={report.summary} />
              <div className="dossier-metrics">
                <Metric value={report.summary.risk_count} label="risques" />
                <Metric value={report.summary.verification_count} label="à vérifier" />
                <Metric value={report.summary.reassuring_count} label="rassurants" />
                <Metric value={report.summary.missing_information_count} label="manquants" />
              </div>
              <Link className="dossier-card-link" href={productRoutes.documents}>Voir les documents <Icon name="arrow" /></Link>
            </section>
          </div>
        </>
      ) : populatedSections.length > 0 ? (
        <div className="report-sections">
          {populatedSections.map((section) => (
            <section key={section.code} id={section.code} className="report-section panel">
              <div className="panel-heading">
                <div className="section-title-with-icon">
                  <span><Icon name={section.icon} /></span>
                  <div><p className="section-kicker">{section.kicker}</p><h2>{section.title}</h2></div>
                </div>
                <span className="count-badge">{section.findings.length}</span>
              </div>
              <div className="finding-rows">
                {section.findings.map((finding) => (
                  <FindingRow
                    key={finding.finding_key}
                    finding={finding}
                    onSelect={setSelectedFinding}
                    onReview={(item, checked) => void reviewFinding(item, checked)}
                    isUpdating={updatingFindingKey === finding.finding_key}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="report-state">
          <span className="state-icon"><Icon name="document" /></span>
          <strong>Aucun point d’analyse disponible</strong>
          <span>Consultez la page Documents pour vérifier les pièces encore attendues.</span>
          <Link href={productRoutes.documents}>Voir les documents</Link>
        </div>
      )}

      <p className="report-disclaimer">{report.disclaimer}</p>
      {selectedFinding ? (
        <DetailDrawer
          finding={selectedFinding}
          onClose={() => setSelectedFinding(null)}
          onViewSource={(source) => setViewingSource({
            documentId: source.document_id,
            filename: source.document_name,
            pageNumber: source.page_number,
          })}
          onReview={(finding, checked) => void reviewFinding(finding, checked)}
          isUpdating={updatingFindingKey === selectedFinding.finding_key}
        />
      ) : null}
      {viewingSource ? (
        <PdfViewer
          document={viewingSource}
          onClose={() => setViewingSource(null)}
        />
      ) : null}
    </div>
  );
}
