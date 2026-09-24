import { BuyerReport } from "@/features/reports/buyer-report";

export default function PublicDemoAnalysisPage() {
  return (
    <div className="analysis-page">
      <BuyerReport variant="details" publicDemo />
    </div>
  );
}
