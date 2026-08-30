import type { ReactNode } from "react";

import { ApplicationShell } from "@/components/application-shell";

type AppLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function AppLayout({ children }: AppLayoutProps) {
  return <ApplicationShell>{children}</ApplicationShell>;
}
