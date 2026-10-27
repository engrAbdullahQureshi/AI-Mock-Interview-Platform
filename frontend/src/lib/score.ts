// Score → color band mapping (BLUEPRINT §2)
// >=80 success · 60–79 accent · 40–59 warning · <40 danger

export type ScoreBand = "success" | "accent" | "warning" | "danger";

export function scoreBand(score: number): ScoreBand {
  if (score >= 80) return "success";
  if (score >= 60) return "accent";
  if (score >= 40) return "warning";
  return "danger";
}

const HEX: Record<ScoreBand, string> = {
  success: "#22c55e",
  accent: "#6366f1",
  warning: "#f59e0b",
  danger: "#ef4444",
};

// Returns the raw hex for SVG / inline styles
export function scoreColor(score: number): string {
  return HEX[scoreBand(score)];
}

// Returns a Tailwind text color class
export function scoreTextClass(score: number): string {
  return {
    success: "text-success",
    accent: "text-accent",
    warning: "text-warning",
    danger: "text-danger",
  }[scoreBand(score)];
}

export function verdictFromScore(score: number): string {
  if (score >= 85) return "Excellent fit";
  if (score >= 75) return "Strong fit — a few gaps to strengthen";
  if (score >= 60) return "Promising — some gaps to close";
  if (score >= 40) return "Partial fit — notable gaps";
  return "Early-stage fit";
}
