import { Icon } from "@/components/icons";

type LoadingStateProps = {
  title: string;
  description?: string;
  compact?: boolean;
};

export function LoadingState({ title, description, compact = false }: LoadingStateProps) {
  return (
    <div
      className={`report-state loading-state${compact ? " is-compact" : ""}`}
      role="status"
      aria-live="polite"
    >
      <span className="state-icon is-loading"><Icon name="refresh" /></span>
      <strong>{title}</strong>
      {description ? <span>{description}</span> : null}
    </div>
  );
}
