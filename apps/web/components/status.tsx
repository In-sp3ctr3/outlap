import { Activity, AlertTriangle, CheckCircle2 } from "lucide-react";

import { freshnessTone, riskLabel } from "@/lib/format";

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const tone = freshnessTone(status);
  const Icon = tone === "good" ? CheckCircle2 : tone === "warn" ? AlertTriangle : Activity;
  return (
    <span className={`badge ${tone}`} aria-label={`${label ?? status}: ${status}`}>
      <Icon size={14} aria-hidden="true" />
      {label ?? status}
    </span>
  );
}

export function RiskMeter({ value }: { value: number }) {
  const label = riskLabel(value);
  const tone = value < 0.3 ? "good" : value < 0.55 ? "warn" : "bad";
  return (
    <div className="meter" aria-label={`Risk ${label}`}>
      <span className={`badge ${tone}`}>Risk {label}</span>
      <div className="meter-track">
        <div className={`meter-fill ${tone}`} style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
    </div>
  );
}

export function ConfidenceMeter({ value }: { value: number }) {
  return (
    <div className="meter" aria-label={`Confidence ${Math.round(value * 100)} percent`}>
      <span className="badge good">Confidence {Math.round(value * 100)}%</span>
      <div className="meter-track">
        <div className="meter-fill" style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
    </div>
  );
}
