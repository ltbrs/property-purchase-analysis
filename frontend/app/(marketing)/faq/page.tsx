import { permanentRedirect } from "next/navigation";

import { marketingRoutes } from "@/lib/routes";

export default function FaqPage() {
  permanentRedirect(marketingRoutes.contact);
}
