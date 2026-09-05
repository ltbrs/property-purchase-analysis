import type { ReactNode } from "react";
import { redirect } from "next/navigation";

import { auth } from "@/auth";
import { ApplicationShell } from "@/components/application-shell";
import { productRoutes } from "@/lib/routes";

type AppLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default async function AppLayout({ children }: AppLayoutProps) {
  const session = await auth();
  if (!session?.user?.id) {
    redirect(`${productRoutes.signIn}?callbackUrl=${encodeURIComponent(productRoutes.home)}`);
  }

  return (
    <ApplicationShell
      user={{
        id: session.user.id,
        email: session.user.email,
        name: session.user.name,
      }}
    >
      {children}
    </ApplicationShell>
  );
}
