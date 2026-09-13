"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { captureProductEvent } from "@/lib/analytics/product-analytics";

type HomeCtaProps = Readonly<{
  href: string;
  action: "report_example" | "create_case" | "contact";
  placement: "hero" | "report" | "closing";
  className: string;
  children: ReactNode;
}>;

export function HomeCta({
  action,
  placement,
  children,
  ...props
}: HomeCtaProps) {
  return (
    <Link
      {...props}
      onClick={() => {
        captureProductEvent("landing_cta_clicked", { action, placement });
      }}
    >
      {children}
    </Link>
  );
}
