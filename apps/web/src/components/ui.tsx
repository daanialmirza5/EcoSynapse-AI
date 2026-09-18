import type { ReactNode } from "react";

export function Card({ title, children, actions }: { title?: string; children: ReactNode; actions?: ReactNode }) {
  return (
    <div className="card p-4 md:p-5">
      {(title || actions) && (
        <div className="flex items-center justify-between mb-3">
          {title && <h3 className="font-semibold text-stone-800">{title}</h3>}
          {actions}
        </div>
      )}
      {children}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return <div className="text-sm text-stone-500 italic py-6 text-center">{message}</div>;
}

export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return <div className="text-sm text-stone-500 py-6 text-center animate-pulse">{message}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
      {message}
    </div>
  );
}

const CONFIDENCE_COLORS: Record<string, string> = {
  low: "bg-amber-100 text-amber-800",
  medium: "bg-sky-100 text-sky-800",
  high: "bg-eco-100 text-eco-800",
};

export function ConfidenceBadge({ level }: { level: string }) {
  return <span className={`badge ${CONFIDENCE_COLORS[level] || "bg-stone-100 text-stone-700"}`}>{level} confidence</span>;
}

const EVIDENCE_COLORS: Record<string, string> = {
  supported: "bg-eco-100 text-eco-800",
  partially_supported: "bg-amber-100 text-amber-800",
  insufficient_evidence: "bg-stone-200 text-stone-700",
  unverified: "bg-red-100 text-red-800",
};

export function EvidenceStatusBadge({ status }: { status: string }) {
  return (
    <span className={`badge ${EVIDENCE_COLORS[status] || "bg-stone-100 text-stone-700"}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

const HORIZON_COLORS: Record<string, string> = {
  short: "bg-sky-100 text-sky-800",
  medium: "bg-indigo-100 text-indigo-800",
  long: "bg-purple-100 text-purple-800",
};

export function TimeHorizonBadge({ horizon }: { horizon: string }) {
  return <span className={`badge ${HORIZON_COLORS[horizon] || "bg-stone-100 text-stone-700"}`}>{horizon} term</span>;
}

const STRENGTH_COLORS: Record<string, string> = {
  strong: "bg-eco-100 text-eco-800",
  moderate: "bg-sky-100 text-sky-800",
  weak: "bg-amber-100 text-amber-800",
  hypothesis: "bg-stone-200 text-stone-700",
};

export function EvidenceStrengthBadge({ strength }: { strength: string }) {
  return (
    <span className={`badge ${STRENGTH_COLORS[strength] || "bg-stone-100 text-stone-700"}`}>
      evidence: {strength}
    </span>
  );
}

export function ClaimTypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    source_supported: "bg-eco-100 text-eco-800",
    model_derived: "bg-sky-100 text-sky-800",
    hypothesis: "bg-amber-100 text-amber-800",
    user_observation: "bg-indigo-100 text-indigo-800",
    unknown: "bg-stone-200 text-stone-700",
  };
  return <span className={`badge ${colors[type] || "bg-stone-100"}`}>{type.replace(/_/g, " ")}</span>;
}
