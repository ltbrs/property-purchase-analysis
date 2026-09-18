"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Icon, type IconName } from "@/components/icons";
import {
  BillingPanel,
  type BillingSummary,
} from "@/features/billing/billing-panel";
import {
  PdfViewer,
  type PdfDocumentSelection,
} from "@/features/documents/pdf-viewer";
import { captureProductEvent } from "@/lib/analytics/product-analytics";
import { productRoutes } from "@/lib/routes";
import {
  API_URL,
  getWorkspace,
  readApiError,
  resetWorkspace,
  type AnalysisCase,
  type Workspace,
} from "@/lib/workspace";

type Severity = "info" | "low" | "medium" | "high" | "critical";
type FindingStatus = "confirmed" | "likely" | "possible" | "missing_information";
type AnalysisType = "risk" | "verification" | "reassuring" | "missing_information";
type ReviewStatus = "open" | "not_problematic";
type Expectation = "definitely_expected" | "usually_useful" | "context_dependent";
type AnalysisAccessStatus = AnalysisCase["analysis_access_status"];

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

type BuyerReportPreviewData = {
  analysis_case_id: string;
  generated_at: string;
  risk_count: number;
  verification_count: number;
  missing_information_count: number;
  reassuring_count: number;
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

async function generateReport(workspace: Workspace) {
  return fetch(`${API_URL}/analysis-cases/${workspace.caseId}/report/refresh`, {
    method: "POST",
  });
}

async function refreshReport(workspace: Workspace): Promise<BuyerReportData> {
  const response = await generateReport(workspace);
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as BuyerReportData;
}

async function refreshReportPreview(workspace: Workspace): Promise<BuyerReportPreviewData> {
  const response = await fetch(
    `${API_URL}/analysis-cases/${workspace.caseId}/report/preview`,
    { method: "POST" },
  );
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as BuyerReportPreviewData;
}

async function fetchExistingReport(workspace: Workspace): Promise<BuyerReportData | null> {
  const response = await fetch(
    `${API_URL}/analysis-cases/${workspace.caseId}/report`,
    { cache: "no-store" },
  );
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as BuyerReportData;
}

async function processCaseDocuments(workspace: Workspace) {
  const response = await fetch(
    `${API_URL}/analysis-cases/${workspace.caseId}/documents`,
    { cache: "no-store" },
  );
  if (!response.ok) throw new Error(await readApiError(response));
  const documents = (await response.json()) as Array<{ id: string; status: string }>;
  await Promise.all(
    documents
      .filter(({ status: documentStatus }) => documentStatus !== "completed")
      .map(async ({ id }) => {
        const processing = await fetch(
          `${API_URL}/analysis-cases/${workspace.caseId}/documents/${id}/process`,
          { method: "POST" },
        );
        if (!processing.ok) throw new Error(await readApiError(processing));
      }),
  );
  return documents.length;
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

type AnalysisLoad = {
  accessStatus: AnalysisAccessStatus;
  readOnly: boolean;
  report: BuyerReportData | null;
  preview: BuyerReportPreviewData | null;
};

const pendingReportLoads = new Map<string, Promise<AnalysisLoad | null>>();

function loadReport(): Promise<AnalysisLoad | null> {
  const workspace = getWorkspace();
  if (!workspace) return Promise.resolve(null);

  const requestKey = workspace.caseId;
  const pendingLoad = pendingReportLoads.get(requestKey);
  if (pendingLoad) return pendingLoad;

  const load = (async () => {
    const caseResponse = await fetch(`${API_URL}/analysis-cases/${workspace.caseId}`, {
      cache: "no-store",
    });
    if (caseResponse.status === 404) {
      resetWorkspace(workspace.caseId);
      return null;
    }
    if (!caseResponse.ok) throw new Error(await readApiError(caseResponse));
    const analysisCase = (await caseResponse.json()) as AnalysisCase;
    if (analysisCase.read_only) {
      return {
        accessStatus: analysisCase.analysis_access_status,
        readOnly: true,
        report: await fetchExistingReport(workspace),
        preview: null,
      };
    }
    if (analysisCase.analysis_access_status === "not_activated") {
      return {
        accessStatus: analysisCase.analysis_access_status,
        readOnly: false,
        report: null,
        preview: null,
      };
    }
    if (analysisCase.analysis_access_status === "preview") {
      const documentCount = await processCaseDocuments(workspace);
      return {
        accessStatus: analysisCase.analysis_access_status,
        readOnly: false,
        report: null,
        preview: documentCount > 0 ? await refreshReportPreview(workspace) : null,
      };
    }
    if (analysisCase.analysis_access_status === "expired") {
      return {
        accessStatus: analysisCase.analysis_access_status,
        readOnly: false,
        report: await fetchExistingReport(workspace),
        preview: null,
      };
    }
    await processCaseDocuments(workspace);
    return {
      accessStatus: analysisCase.analysis_access_status,
      readOnly: false,
      report: await refreshReport(workspace),
      preview: null,
    };
  })().finally(() => {
    if (pendingReportLoads.get(requestKey) === load) pendingReportLoads.delete(requestKey);
  });
  pendingReportLoads.set(requestKey, load);
  return load;
}

function FindingRow({
  finding,
  onSelect,
  onReview,
  isUpdating,
  readOnly,
}: {
  finding: ReportFinding;
  onSelect: (finding: ReportFinding) => void;
  onReview: (finding: ReportFinding, checked: boolean) => void;
  isUpdating: boolean;
  readOnly: boolean;
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
      {isReviewable && !readOnly ? (
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
  readOnly,
}: {
  finding: ReportFinding;
  onClose: () => void;
  onViewSource: (source: ReportSource) => void;
  onReview: (finding: ReportFinding, checked: boolean) => void;
  isUpdating: boolean;
  readOnly: boolean;
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
          {isReviewable && !readOnly ? (
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
  const [preview, setPreview] = useState<BuyerReportPreviewData | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<ReportFinding | null>(null);
  const [viewingSource, setViewingSource] = useState<PdfDocumentSelection | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [needsWorkspace, setNeedsWorkspace] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatingFindingKey, setUpdatingFindingKey] = useState<string | null>(null);
  const [accessStatus, setAccessStatus] = useState<AnalysisAccessStatus | null>(null);
  const [readOnly, setReadOnly] = useState(false);
  const [availableAnalyses, setAvailableAnalyses] = useState(0);
  const handleBillingSummary = useCallback((summary: BillingSummary) => {
    setAvailableAnalyses(summary.available_analyses);
  }, []);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const loaded = await loadReport();
      setNeedsWorkspace(loaded === null);
      setAccessStatus(loaded?.accessStatus ?? null);
      setReadOnly(loaded?.readOnly ?? false);
      setReport(loaded?.report ?? null);
      setPreview(loaded?.preview ?? null);
      if (loaded?.report) {
        captureProductEvent("analysis_report_refreshed", { report_variant: variant });
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
      .then((loaded) => {
        if (!cancelled) {
          setNeedsWorkspace(loaded === null);
          setAccessStatus(loaded?.accessStatus ?? null);
          setReadOnly(loaded?.readOnly ?? false);
          setReport(loaded?.report ?? null);
          setPreview(loaded?.preview ?? null);
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

  async function activateAnalysis() {
    if (readOnly) return;
    const workspace = getWorkspace();
    if (!workspace) {
      setNeedsWorkspace(true);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const activation = await fetch(
        `${API_URL}/billing/analysis-cases/${workspace.caseId}/activate`,
        { method: "POST" },
      );
      if (!activation.ok) throw new Error(await readApiError(activation));
      await processCaseDocuments(workspace);
      const loadedReport = await refreshReport(workspace);
      setAccessStatus("active");
      setReport(loadedReport);
      setPreview(null);
      setAvailableAnalyses((current) => Math.max(0, current - 1));
      captureProductEvent("analysis_case_activated", {});
    } catch (activationError) {
      setError(
        activationError instanceof Error
          ? activationError.message
          : "L’analyse complète n’a pas pu être lancée.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (selectedFinding === null || viewingSource !== null) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setSelectedFinding(null);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selectedFinding, viewingSource]);

  async function reviewFinding(finding: ReportFinding, checked: boolean) {
    if (readOnly) return;
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
      const updatedReport = await fetchExistingReport(workspace);
      setReport(updatedReport);
      captureProductEvent("report_finding_review_updated", {
        analysis_type: finding.analysis_type,
        review_status: checked ? "not_problematic" : "open",
        severity: finding.severity,
      });
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

  if (isLoading && report === null && preview === null) {
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

  if (error && report === null && accessStatus === null) {
    return (
      <div className="report-state report-error" role="alert">
        <span className="state-icon"><Icon name="alert" /></span>
        <strong>Rapport indisponible</strong>
        <span>{error}</span>
        <button type="button" onClick={() => void refresh()}>Réessayer</button>
      </div>
    );
  }

  if (accessStatus === "preview" && preview === null) {
    return (
      <div className="report-state">
        <span className="state-icon"><Icon name="upload" /></span>
        <strong>Ajoutez votre document d’essai</strong>
        <span>Votre premier PDF sera analysé gratuitement. Les catégories de constats seront comptées, puis les détails resteront masqués jusqu’au déblocage.</span>
        <Link href={productRoutes.documents}>Ajouter un document</Link>
      </div>
    );
  }

  if (accessStatus === "preview" && preview !== null) {
    const previewMetrics = [
      { value: preview.risk_count, label: "risques détectés" },
      { value: preview.verification_count, label: "points à vérifier" },
      { value: preview.reassuring_count, label: "points rassurants" },
      { value: preview.missing_information_count, label: "éléments manquants" },
    ];
    return (
      <div className="analysis-preview">
        <section className="analysis-preview-summary">
          <p className="eyebrow">Aperçu gratuit</p>
          <h1>Votre document a bien été analysé</h1>
          <p>Voici le nombre de constats trouvés. Leur contenu et leurs sources sont masqués jusqu’au déblocage du dossier.</p>
          <div className="analysis-preview-metrics">
            {previewMetrics.map((metric) => (
              <div key={metric.label}>
                <strong>{metric.value}</strong>
                <span>{metric.label}</span>
              </div>
            ))}
          </div>
        </section>
        <div className="analysis-preview-locked" aria-hidden="true">
          {[0, 1, 2].map((item) => (
            <div key={item} className="analysis-preview-finding">
              <span />
              <div><strong>Constat issu de votre document</strong><p>Le détail, l’explication et la source seront affichés ici.</p></div>
            </div>
          ))}
        </div>
        <div className="analysis-preview-paywall">
          <div>
            <h2>Consultez les constats et leurs sources</h2>
            <p>Débloquez ce dossier pour voir les risques, les éléments manquants et les pages justificatives, puis ajouter toutes les pièces utiles.</p>
            {availableAnalyses > 0 ? (
              <button type="button" disabled={isLoading} onClick={() => void activateAnalysis()}>
                {isLoading ? "Analyse en cours…" : "Utiliser une analyse disponible"}
              </button>
            ) : null}
          </div>
          <BillingPanel compact onSummaryChange={handleBillingSummary} />
        </div>
        {error ? <p className="billing-error" role="alert">{error}</p> : null}
      </div>
    );
  }

  if (report === null && accessStatus !== null) {
    return (
      <div className="analysis-paywall">
        <div className="analysis-paywall-copy">
          <span className="state-icon"><Icon name="shield" /></span>
          <p className="eyebrow">Analyse complète</p>
          <h1>
            {accessStatus === "expired"
              ? "La période de mise à jour est terminée"
              : "Débloquez l’analyse complète de ce bien"}
          </h1>
          <p>
            Risques, coûts futurs, incohérences et informations manquantes restent reliés
            aux documents et aux pages qui les justifient.
          </p>
          {availableAnalyses > 0 ? (
            <button type="button" disabled={isLoading} onClick={() => void activateAnalysis()}>
              {isLoading ? "Analyse en cours…" : "Utiliser une analyse disponible"}
            </button>
          ) : null}
          {error ? <p className="billing-error" role="alert">{error}</p> : null}
        </div>
        <BillingPanel
          compact
          onSummaryChange={handleBillingSummary}
        />
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
      {readOnly ? (
        <div className="demo-read-only-banner">
          <Icon name="shield" />
          <div>
            <strong>Données fictives, lecture seule</strong>
            <span>Explorez les constats et leurs sources comme dans un dossier réel. Les validations et recalculs sont désactivés.</span>
          </div>
        </div>
      ) : null}
      <header className="report-page-heading">
        <div>
          <p className="report-updated">Analyse mise à jour le {dateFormatter.format(new Date(report.generated_at))}</p>
          <h1>{variant === "overview" ? "Votre dossier, en clair" : "Analyse du dossier"}</h1>
        </div>
        <div className="report-heading-actions">
          <span className="attention-count">
            <i /> {report.summary.high_or_critical_count} risque{report.summary.high_or_critical_count === 1 ? "" : "s"} important{report.summary.high_or_critical_count === 1 ? "" : "s"}
          </span>
          {readOnly ? null : accessStatus === "active" ? (
            <button className="refresh-icon-button" type="button" disabled={isLoading} aria-label="Actualiser l’analyse" title="Actualiser l’analyse" onClick={() => void refresh()}>
              <Icon name="refresh" />
            </button>
          ) : (
            <button className="analysis-renew-button" type="button" onClick={() => setReport(null)}>
              Mettre à jour
            </button>
          )}
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
                      readOnly={readOnly}
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
                    readOnly={readOnly}
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
          readOnly={readOnly}
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
