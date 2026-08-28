"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon, type IconName } from "@/components/icons";
import {
  API_URL,
  getOrCreateWorkspace,
  readApiError,
  resetWorkspace,
  type Workspace,
} from "@/lib/workspace";

type Severity = "info" | "low" | "medium" | "high" | "critical";
type FindingStatus = "confirmed" | "likely" | "possible" | "missing_information";
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

const expectationLabels: Record<Expectation, string> = {
  definitely_expected: "Attendu dans le dossier",
  usually_useful: "Habituellement utile",
  context_dependent: "Selon le contexte",
};

const sectionIcons: Record<string, IconName> = {
  financial: "wallet",
  building_coproperty: "building",
  energy: "leaf",
  diagnostics_safety: "shield",
  inconsistencies: "alert",
  missing_information: "document",
  reassuring: "check",
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

function FindingRow({
  finding,
  onSelect,
}: {
  finding: ReportFinding;
  onSelect: (finding: ReportFinding) => void;
}) {
  return (
    <button type="button" className="finding-row" onClick={() => onSelect(finding)}>
      <span className={`finding-icon severity-${finding.severity}`}>
        <Icon name={finding.status === "missing_information" ? "document" : "alert"} />
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
        {severityLabels[finding.severity]}
      </span>
      <Icon className="row-chevron" name="chevron" />
    </button>
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

function DetailDrawer({ finding, onClose }: { finding: ReportFinding; onClose: () => void }) {
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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      setReport(await loadReport());
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
        if (!cancelled) setReport(loadedReport);
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
    if (selectedFinding === null) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setSelectedFinding(null);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selectedFinding]);

  if (isLoading && report === null) {
    return (
      <div className="report-state">
        <span className="state-icon is-loading"><Icon name="refresh" /></span>
        <strong>Analyse du dossier…</strong>
        <span>Les constats et leurs sources sont en cours de préparation.</span>
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

  const populatedSections = report.sections.filter((section) => section.findings.length > 0);
  const missingSection = report.sections.find((section) => section.code === "missing_information");
  const riskFindings = report.sections
    .filter((section) => !["missing_information", "reassuring"].includes(section.code))
    .flatMap((section) => section.findings)
    .toSorted((left, right) => severityRank[right.severity] - severityRank[left.severity]);
  const priorityFindings = riskFindings.slice(0, 3);
  const categorySections = report.sections.filter((section) =>
    ["building_coproperty", "energy", "financial", "diagnostics_safety"].includes(section.code),
  );

  return (
    <div className={`buyer-report report-${variant}`}>
      <header className="report-page-heading">
        <div>
          <p className="report-updated">Analyse mise à jour le {dateFormatter.format(new Date(report.generated_at))}</p>
          <h1>{variant === "overview" ? "Ce qui mérite votre attention." : "Toutes les alertes"}</h1>
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
                <div><p className="section-kicker">Prioritaire</p><h2>Alertes</h2></div>
                <Link className="text-link" href="/analysis">Tout voir <Icon name="arrow" /></Link>
              </div>
              {priorityFindings.length > 0 ? (
                <div className="finding-rows">
                  {priorityFindings.map((finding) => (
                    <FindingRow key={finding.finding_key} finding={finding} onSelect={setSelectedFinding} />
                  ))}
                </div>
              ) : (
                <p className="panel-empty">Aucune alerte détectée dans les pièces analysées.</p>
              )}
            </section>

            <section className="dossier-card">
              <div className="dossier-card-heading">
                <div><p className="section-kicker">Dossier</p><strong>{report.summary.finding_count}</strong><span>constats documentés</span></div>
                <Icon name="document" />
              </div>
              <div className="dossier-metrics">
                <Metric value={report.summary.high_or_critical_count} label="prioritaires" />
                <Metric value={report.summary.missing_information_count} label="manquants" />
                <Metric value={report.summary.reassuring_count} label="rassurants" />
              </div>
            </section>
          </div>

          <section className="category-grid" aria-label="Alertes par catégorie">
            {categorySections.map((section) => {
              const criticalCount = section.findings.filter((finding) => ["critical", "high"].includes(finding.severity)).length;
              return (
                <Link key={section.code} href={`/analysis#${section.code}`} className="category-card">
                  <span className={`category-icon${criticalCount > 0 ? " is-critical" : ""}`}><Icon name={sectionIcons[section.code] ?? "document"} /></span>
                  <span className="category-copy">
                    <strong>{section.title}</strong>
                    <small>{section.findings.length === 0 ? "Aucun constat" : `${section.findings.length} constat${section.findings.length === 1 ? "" : "s"}`}</small>
                  </span>
                  <Icon className="row-chevron" name="chevron" />
                </Link>
              );
            })}
          </section>

          <div className="lower-grid">
            <section className="panel missing-panel">
              <div className="panel-heading">
                <div><p className="section-kicker">Avant compromis</p><h2>Informations manquantes</h2></div>
                <span className="count-badge">{missingSection?.findings.length ?? 0}</span>
              </div>
              {missingSection && missingSection.findings.length > 0 ? (
                <div className="missing-list">
                  {missingSection.findings.slice(0, 3).map((finding) => (
                    <button key={finding.finding_key} type="button" onClick={() => setSelectedFinding(finding)}>
                      <span /><strong>{finding.title}</strong><Icon name="chevron" />
                    </button>
                  ))}
                </div>
              ) : (
                <p className="panel-empty">Aucune information manquante signalée.</p>
              )}
            </section>

            <section className="panel trust-panel">
              <div className="trust-icon"><Icon name="check" /></div>
              <div>
                <p className="section-kicker">Traçabilité</p>
                <h2>{report.summary.reassuring_count} élément{report.summary.reassuring_count === 1 ? "" : "s"} rassurant{report.summary.reassuring_count === 1 ? "" : "s"}</h2>
                <p>Les faits utiles restent liés au document et à la page qui les justifient.</p>
              </div>
            </section>
          </div>
        </>
      ) : populatedSections.length > 0 ? (
        <div className="report-sections">
          {populatedSections.map((section) => (
            <section key={section.code} id={section.code} className="report-section panel">
              <div className="panel-heading">
                <div className="section-title-with-icon">
                  <span><Icon name={sectionIcons[section.code] ?? "document"} /></span>
                  <div><p className="section-kicker">{section.code === "reassuring" ? "Vérifié" : "Catégorie"}</p><h2>{section.title}</h2></div>
                </div>
                <span className="count-badge">{section.findings.length}</span>
              </div>
              <div className="finding-rows">
                {section.findings.map((finding) => (
                  <FindingRow key={finding.finding_key} finding={finding} onSelect={setSelectedFinding} />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="report-state">
          <span className="state-icon"><Icon name="document" /></span>
          <strong>Aucun constat pour le moment</strong>
          <span>Ajoutez des documents pour commencer l’analyse.</span>
          <Link href="/upload">Ajouter des documents</Link>
        </div>
      )}

      <p className="report-disclaimer">{report.disclaimer}</p>
      {selectedFinding ? <DetailDrawer finding={selectedFinding} onClose={() => setSelectedFinding(null)} /> : null}
    </div>
  );
}
