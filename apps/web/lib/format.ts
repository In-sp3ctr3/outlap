export function formatPoints(value: number): string {
  return `${value.toFixed(1)} pts`;
}

export function formatBudget(value: number): string {
  return `${value.toFixed(1)}M`;
}

export function riskLabel(value: number): "Low" | "Medium" | "High" {
  if (value < 0.3) return "Low";
  if (value < 0.55) return "Medium";
  return "High";
}

export function freshnessTone(status: string): "good" | "warn" | "bad" {
  if (status === "healthy") return "good";
  if (status === "degraded" || status === "stale") return "warn";
  return "bad";
}
