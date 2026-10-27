import { Check, Plus } from "lucide-react";

export function SkillChip({ label, kind }: { label: string; kind: "matched" | "missing" }) {
  const matched = kind === "matched";
  const Icon = matched ? Check : Plus;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${
        matched ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
      }`}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  );
}

export function StatBadge({ score }: { score: number }) {
  const band =
    score >= 80
      ? "bg-success/10 text-success"
      : score >= 60
        ? "bg-accent/10 text-accent"
        : score >= 40
          ? "bg-warning/10 text-warning"
          : "bg-danger/10 text-danger";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 font-mono text-sm font-semibold ${band}`}>
      {Math.round(score)}
    </span>
  );
}
