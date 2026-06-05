"use client";

import { Ban, BrainCircuit, Lock } from "lucide-react";
import { useState } from "react";

import { PageHead } from "@/components/page-head";
import { RecommendationCard } from "@/components/recommendation-card";
import { StateNotice } from "@/components/state-notice";
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
  onRecommend: (
    strategyMode?: string,
    allowedChips?: string[],
    lockedAssetIds?: string[],
    bannedAssetIds?: string[],
  ) => Promise<void>;
  onCompare: (option: RecommendationOption) => void;
}) {
  const [strategy, setStrategy] = useState("balanced");
  const [chip, setChip] = useState("");
  const [lockCore, setLockCore] = useState(false);
  const [banRisky, setBanRisky] = useState(false);
  const team = data.teams[0];
  if (!team) {
    return (
      <>
        <PageHead title="Optimizer" detail="Ranked legal lineups, transfer penalties, chip scenarios, assumptions, and provenance." />
        <StateNotice tone="empty" title="No team snapshot is loaded" />
      </>
    );
  }
  const lockedAssetIds = lockCore ? team.assets.map((asset) => asset.assetId) : [];
  const bannedAssetIds = banRisky
    ? data.assets
        .filter((asset) => (asset.riskScore ?? 0) >= 0.55 && !lockedAssetIds.includes(asset.assetId))
        .map((asset) => asset.assetId)
    : [];

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
              <option value="no_negative">no negative</option>
              <option value="autopilot">autopilot</option>
              <option value="3x_boost">3x boost</option>
              <option value="final_fix">final fix</option>
            </select>
          </label>
          <div className="field">
            Team
            <div className="input">{team.teamName}</div>
          </div>
        </div>
        <div className="button-row" style={{ marginTop: 14 }}>
          <button
            className="button"
            type="button"
            disabled={loadingRecommendation}
            onClick={() => onRecommend(strategy, chip ? [chip] : [], lockedAssetIds, bannedAssetIds)}
          >
            <BrainCircuit size={16} aria-hidden="true" />
            Run optimizer
          </button>
          <button
            aria-pressed={lockCore}
            className="button secondary"
            type="button"
            onClick={() => setLockCore((current) => !current)}
          >
            <Lock size={16} aria-hidden="true" />Lock current core
          </button>
          <button
            aria-pressed={banRisky}
            className="button secondary"
            type="button"
            onClick={() => setBanRisky((current) => !current)}
          >
            <Ban size={16} aria-hidden="true" />Ban risky assets
          </button>
        </div>
        {lockCore || banRisky ? (
          <p>
            Active constraints: {lockedAssetIds.length} locked, {bannedAssetIds.length} banned.
          </p>
        ) : null}
      </section>
      {loadingRecommendation ? (
        <StateNotice tone="loading" title="Calculating deterministic options" />
      ) : null}
      {recommendation ? (
        <div className="grid" style={{ marginTop: 16 }}>
          {recommendation.warnings.map((warning) => <div className="empty" role="status" key={warning}>{warning}</div>)}
          {recommendation.options.map((option) => <RecommendationCard option={option} key={option.optionId} onCompare={onCompare} />)}
        </div>
      ) : (
        <StateNotice tone="empty" title="Optimizer has not run for this session" />
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
