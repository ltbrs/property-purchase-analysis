import { BuyerReport } from "@/features/reports/buyer-report";

export default function PublicDemoOverviewPage() {
  return (
    <div className="overview-page">
      <BuyerReport variant="overview" publicDemo />
    </div>
  );
}
