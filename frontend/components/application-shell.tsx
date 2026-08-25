import Link from "next/link";
import type { ReactNode } from "react";

type ApplicationShellProps = Readonly<{
  children: ReactNode;
}>;

export function ApplicationShell({ children }: ApplicationShellProps) {
  return (
    <div className="shell">
      <header className="shell-header">
        <nav className="shell-nav" aria-label="Navigation principale">
          <Link className="brand" href="/">
            Analyse immobilière
          </Link>
          <div className="nav-links">
            <Link href="/upload">Documents</Link>
            <Link href="/analysis">Analyse</Link>
          </div>
        </nav>
      </header>
      <main className="shell-main">{children}</main>
    </div>
  );
}

