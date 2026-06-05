"use client";

import { Ban, BrainCircuit, Lock } from "lucide-react";
import { useState } from "react";

import { PageHead } from "@/components/page-head";
import { RecommendationCard } from "@/components/recommendation-card";
import type { DashboardData, RecommendationOption, RecommendationRun } from "@/lib/api";

export function OptimizerView({
  data,
  recommendation,
  comparison,
  loadingRecommendation,
  onRecommend,
  onCompare,
}: {
  data: DashboardData;
  recommendation: RecommendationRun | null;
  comparison: RecommendationOption | null;
  loadingRecommendation: boolean;
  onRecommend: (strategyMode?: string, allowedChips?: string[]) => Promise<void>;
  onCompare: (option: RecommendationOption) => void;
}) {
  const [strategy, setStrategy] = useState("balanced");
  const [chip, setChip] = useState("");

  return (
    <>
      <PageHead title="Optimizer" detail="Ranked legal lineups, transfer penalties, chip scenarios, assumptions, and provenance." />
      <section className="panel">
        <div className="grid three">
          <label className="field">
            Strategy mode
            <select className="select" value={strategy} onChange={(event) => setStrategy(event.target.value)}>
              {["safe", "balanced", "aggressive", "budget_builder", "differential", "chip_optimized"].map((mode) => (
                <option key={mode} value={mode}>{mode}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Chip scenario
            <select className="select" value={chip} onChange={(event) => setChip(event.target.value)}>
              <option value="">none</option>
              <option value="wildcard">wildcard</option>
              <option value="limitless">limitless</option>
            </select>
          </label>
          <div className="field">
            Team
            <div className="input">{data.teams[0].teamName}</div>
          </div>
        </div>
        <div className="button-row" style={{ marginTop: 14 }}>
          <button className="button" type="button" disabled={loadingRecommendation} onClick={() => onRecommend(strategy, chip ? [chip] : [])}>
            <BrainCircuit size={16} aria-hidden="true" />
            Run optimizer
          </button>
          <button className="button secondary" type="button"><Lock size={16} aria-hidden="true" />Lock current core</button>
          <button className="button secondary" type="button"><Ban size={16} aria-hidden="true" />Ban risky assets</button>
        </div>
      </section>
      {loadingRecommendation ? <div className="loading" style={{ marginTop: 16 }}>Calculating deterministic options...</div> : null}
      {recommendation ? (
        <div className="grid" style={{ marginTop: 16 }}>
          {recommendation.warnings.map((warning) => <div className="empty" role="status" key={warning}>{warning}</div>)}
          {recommendation.options.map((option) => <RecommendationCard option={option} key={option.optionId} onCompare={onCompare} />)}
        </div>
      ) : (
        <div className="empty" style={{ marginTop: 16 }}>Optimizer has not run for this session.</div>
      )}
      {comparison ? (
        <section className="panel" style={{ marginTop: 16 }} aria-label="Comparison drawer">
          <h2>Comparison drawer</h2>
          <p>{comparison.summary}</p>
          <p>Source snapshots: {comparison.sourceSnapshotIds.join(", ")}</p>
        </section>
      ) : null}
    </>
  );
}
