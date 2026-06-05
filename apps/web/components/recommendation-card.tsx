import { Copy, GitCompareArrows } from "lucide-react";

import type { RecommendationOption } from "@/lib/api";
import { formatBudget, formatPoints } from "@/lib/format";

import { ConfidenceMeter, RiskMeter, StatusBadge } from "./status";

export function RecommendationCard({
  option,
  onCompare,
}: {
  option: RecommendationOption;
  onCompare?: (option: RecommendationOption) => void;
}) {
  return (
    <article className="panel recommendation" data-testid="recommendation-card">
      <div className="page-head">
        <div>
          <h3>#{option.rank} Recommended move</h3>
          <p>{option.summary}</p>
        </div>
        <StatusBadge status={option.chipAction ? "degraded" : "healthy"} label={`Chip ${option.chipAction ?? "none"}`} />
      </div>
      <div className="grid three">
        <Metric label="Net" value={formatPoints(option.expectedNetPoints)} />
        <Metric label="Penalty" value={formatPoints(option.transferPenaltyPoints)} />
        <Metric label="Budget left" value={formatBudget(option.budgetRemainingMillions)} />
      </div>
      <div className="transfer-list" aria-label="Transfers">
        {option.transfers.map((transfer, index) => (
          <span className="transfer-pill" key={`${option.optionId}-${index}`}>
            {transfer.assetOutId && transfer.assetInId
              ? `${transfer.assetOutId} -> ${transfer.assetInId}`
              : transfer.reason ?? "Hold lineup"}
          </span>
        ))}
      </div>
      <div className="grid two">
        <RiskMeter value={option.riskScore} />
        <ConfidenceMeter value={option.confidence} />
      </div>
      <div className="status-strip">
        <span className="badge">Projection {option.projectionRunId}</span>
        <span className="badge">Rules {option.rulesetVersion}</span>
        <span className="badge">Optimizer {option.optimizerVersion}</span>
      </div>
      {option.warnings.length > 0 ? (
        <div className="empty" role="status">
          {option.warnings.join(" ")}
        </div>
      ) : null}
      <div className="button-row">
        <button className="button secondary" type="button" onClick={() => onCompare?.(option)}>
          <GitCompareArrows size={16} aria-hidden="true" />
          Compare
        </button>
        <button
          className="button secondary"
          type="button"
          onClick={() => navigator.clipboard?.writeText(option.summary)}
        >
          <Copy size={16} aria-hidden="true" />
          Copy action list
        </button>
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
