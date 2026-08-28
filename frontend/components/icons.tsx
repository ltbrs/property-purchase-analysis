import type { SVGProps } from "react";

export type IconName =
  | "alert"
  | "arrow"
  | "building"
  | "check"
  | "chevron"
  | "document"
  | "folder"
  | "gauge"
  | "home"
  | "info"
  | "leaf"
  | "menu"
  | "refresh"
  | "shield"
  | "upload"
  | "wallet"
  | "wrench"
  | "x";

type IconProps = SVGProps<SVGSVGElement> & {
  name: IconName;
};

const paths: Record<IconName, React.ReactNode> = {
  alert: <><path d="M10.3 2.9 1.8 17.1A2 2 0 0 0 3.5 20h17a2 2 0 0 0 1.7-2.9L13.7 2.9a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></>,
  arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
  building: <><path d="M3 21h18" /><path d="M6 21V3h9v18" /><path d="M15 8h3v13" /><path d="M9 7h2M9 11h2M9 15h2" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  chevron: <path d="m9 18 6-6-6-6" />,
  document: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M8 13h8M8 17h6" /></>,
  folder: <path d="M3 5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />,
  gauge: <><path d="M4.9 19a10 10 0 1 1 14.2 0" /><path d="m12 12 4-4" /><path d="M12 19h.01" /></>,
  home: <><path d="m3 11 9-8 9 8" /><path d="M5 10v10h14V10M9 20v-6h6v6" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></>,
  leaf: <><path d="M11 20A7 7 0 0 1 9 6c4-4 10-3 12-3 0 2 1 8-3 12a7 7 0 0 1-7 2" /><path d="M3 21c0-5 3-9 9-12" /></>,
  menu: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
  refresh: <><path d="M20 11a8 8 0 1 0-2.3 5.7" /><path d="M20 4v7h-7" /></>,
  shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /><path d="M12 8v4M12 16h.01" /></>,
  upload: <><path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M20 15v5H4v-5" /></>,
  wallet: <><path d="M3 6h16a2 2 0 0 1 2 2v10H5a2 2 0 0 1-2-2Z" /><path d="M3 7V5a2 2 0 0 1 2-2h12v3M16 12h3" /></>,
  wrench: <path d="M14.7 6.3a4 4 0 0 0-5-5L12 3.6 9.6 6 7.3 3.7a4 4 0 0 0 5 5l-8.6 8.6a2 2 0 0 0 2.8 2.8Z" />,
  x: <><path d="m6 6 12 12M18 6 6 18" /></>,
};

export function Icon({ name, ...props }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {paths[name]}
    </svg>
  );
}
