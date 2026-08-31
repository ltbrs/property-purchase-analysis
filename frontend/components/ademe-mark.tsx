import Image from "next/image";
import type { ComponentProps } from "react";

type AdemeMarkProps = Omit<
  ComponentProps<typeof Image>,
  "src" | "alt" | "width" | "height"
>;

export function AdemeMark(props: AdemeMarkProps) {
  return (
    <Image
      src="/ademe-logo.svg"
      alt="ADEME — Agence de la transition écologique"
      width={79}
      height={94}
      {...props}
    />
  );
}
