import type { LucideIcon } from "lucide-react";

export function PageIntro({
  kicker,
  title,
  description,
}: {
  kicker: string;
  title: string;
  description: string;
}) {
  return (
    <div className="page-intro">
      <span className="eyebrow">{kicker}</span>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  );
}

export function FeatureCard({
  icon: Icon,
  title,
  children,
}: {
  icon: LucideIcon;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <article className="card feature-card">
      <div className="card-icon"><Icon size={20} /></div>
      <h3>{title}</h3>
      <div className="muted">{children}</div>
    </article>
  );
}

export function Metric({
  label,
  value,
  note,
  tone = "default",
}: {
  label: string;
  value: string;
  note?: string;
  tone?: "default" | "positive" | "negative";
}) {
  return (
    <div className={"metric metric-" + tone}>
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}

export function LoadingState({ label = "Analyzing data" }: { label?: string }) {
  return (
    <div className="loading-state" role="status">
      <div className="loading-bars"><i /><i /><i /><i /></div>
      <span>{label}?</span>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return <div className="error-state" role="alert">{message}</div>;
}
