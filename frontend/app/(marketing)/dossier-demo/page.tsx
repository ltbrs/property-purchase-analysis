import { permanentRedirect } from "next/navigation";

import { productRoutes } from "@/lib/routes";

export default function FormerDemoPage() {
  permanentRedirect(productRoutes.demo);
}
