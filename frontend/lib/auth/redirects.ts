import { productRoutes } from "@/lib/routes";

export function safeRedirectPath(
  value: string | string[] | null | undefined,
  origin?: string,
) {
  const candidate = Array.isArray(value) ? value[0] : value;
  if (!candidate) return productRoutes.home;
  if (candidate.startsWith("/") && !candidate.startsWith("//")) {
    return candidate;
  }

  if (origin) {
    try {
      const parsed = new URL(candidate);
      if (parsed.origin === origin) {
        return `${parsed.pathname}${parsed.search}${parsed.hash}`;
      }
    } catch {
      // Invalid and external destinations fall back to the product home.
    }
  }

  return productRoutes.home;
}

export function getAuthOrigin() {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configured) return new URL(configured).origin;

  if (process.env.NODE_ENV === "production") {
    throw new Error("NEXT_PUBLIC_SITE_URL must be configured in production.");
  }
  return "http://localhost:3000";
}
