import { BuyerReport } from "@/features/reports/buyer-report";

export default function HomePage() {
  return (
    <div className="overview-page">
      <BuyerReport variant="overview" />
    </div>
  );
}
