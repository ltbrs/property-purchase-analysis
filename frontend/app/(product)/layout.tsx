import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: {
    index: false,
    follow: false,
    googleBot: {
      index: false,
      follow: false,
    },
  },
};

type ProductLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function ProductLayout({ children }: ProductLayoutProps) {
  return <div className="product-universe">{children}</div>;
}
