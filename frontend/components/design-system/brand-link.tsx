import Image from "next/image";
import Link from "next/link";
import type { ComponentProps } from "react";

type BrandLinkProps = Omit<ComponentProps<typeof Link>, "children"> & Readonly<{
  appearance?: "on-light" | "on-dark";
  className?: string;
  priority?: boolean;
}>;

export function BrandLink({
  appearance = "on-light",
  className,
  href,
  priority = false,
  ...linkProps
}: BrandLinkProps) {
  return (
    <Link
      className={className}
      href={href}
      aria-label="Acquora — accueil"
      {...linkProps}
    >
      <Image
        src={`/brand/acquora-wordmark-${appearance === "on-dark" ? "dark" : "light"}.svg`}
        alt="Acquora"
        width={520}
        height={150}
        priority={priority}
      />
    </Link>
  );
}
