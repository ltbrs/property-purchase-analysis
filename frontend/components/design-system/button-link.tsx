import Link from "next/link";
import type { ComponentProps } from "react";

type ButtonLinkProps = ComponentProps<typeof Link> & {
  tone?: "primary";
};

export function ButtonLink({ className, tone = "primary", ...props }: ButtonLinkProps) {
  const classes = ["ds-button", `ds-button--${tone}`, className]
    .filter(Boolean)
    .join(" ");

  return <Link className={classes} {...props} />;
}
