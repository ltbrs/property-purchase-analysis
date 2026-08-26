import { BuyerReport } from "@/features/reports/buyer-report";

export default function AnalysisPage() {
  return (
    <div className="analysis-page">
      <section className="analysis-heading">
        <p className="eyebrow">Rapport acheteur</p>
        <h1>Ce que révèlent vos documents.</h1>
        <p>
          Les constats sont classés par impact et reliés aux pages qui les
          justifient. Les absences et incertitudes restent explicitement signalées.
        </p>
      </section>
      <BuyerReport />
    </div>
  );
}
