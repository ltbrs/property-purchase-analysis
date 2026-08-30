import type { ReactNode } from "react";

type ProductLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function ProductLayout({ children }: ProductLayoutProps) {
  return <div className="product-universe">{children}</div>;
}
