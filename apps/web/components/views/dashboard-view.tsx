"use client";

import { BrainCircuit } from "lucide-react";

import { FreshnessPanelCompact } from "@/components/freshness";
import { MetricCard } from "@/components/metric-card";
import { PageHead } from "@/components/page-head";
import { RecommendationCard } from "@/components/recommendation-card";
import { RealDataOnboarding } from "@/components/real-data-onboarding";
import { StateNotice } from "@/components/state-notice";
import type { DashboardData, RecommendationOption, RecommendationRun } from "@/lib/api";
import { formatBudget, riskLabel } from "@/lib/format";

export function DashboardView({
  data,
  recommendation,
  loadingRecommendation,
  onRecommend,
  onCompare,
  onRefresh,
}: {
  data: DashboardData;
  recommendation: RecommendationRun | null;
  loadingRecommendation: boolean;
  onRecommend: (
    strategyMode?: string,
    allowedChips?: string[],
    lockedAssetIds?: string[],
    bannedAssetIds?: string[],
  ) => Promise<void>;
  onCompare: (option: RecommendationOption) => void;
  onRefresh: () => Promise<void>;
}) {
  const team = data.teams[0];
  const biggestRisk = data.assets.reduce((max, asset) => Math.max(max, asset.riskScore ?? 0), 0);
  const topOption = recommendation?.options[0];
  const hasBlockingData = data.freshness.some((item) => item.isBlocking && item.status !== "real_current");

  return (
    <>
      <PageHead
        title="Dashboard"
        detail="Real race context, imported fantasy data, freshness, and recommendation readiness."
        action={
          <button
            className="button"
            type="button"
            disabled={loadingRecommendation || hasBlockingData}
            onClick={() => onRecommend("balanced")}
          >
            <BrainCircuit size={16} aria-hidden="true" />
            Generate baseline
          </button>
        }
      />
      <div className="grid three">
        <MetricCard
          label="Race context"
          value={data.race?.meetingName ?? "Missing"}
          detail={data.race?.circuitName ?? "Sync public race context"}
        />
        <MetricCard
          label="Budget / transfers"
          value={team ? `${formatBudget(team.budgetRemainingMillions)} · ${team.freeTransfers} FT` : "Missing"}
          detail={team?.teamName ?? "Select Teams 1-3 from the market catalog"}
        />
        <MetricCard
          label="Market risk"
          value={data.assets.length ? riskLabel(biggestRisk) : "Missing"}
          detail={`${data.assets.length} real market rows`}
        />
      </div>
      <div style={{ marginTop: 16 }}>
        <FreshnessPanelCompact items={data.freshness} />
      </div>
      {hasBlockingData ? (
        <div style={{ marginTop: 16 }}>
          <RealDataOnboarding data={data} onRefresh={onRefresh} />
        </div>
      ) : null}
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Recommendation highlight</h2>
        {topOption ? (
          <div style={{ marginTop: 14 }}>
            <RecommendationCard option={topOption} onCompare={onCompare} />
          </div>
        ) : (
          <StateNotice
            tone="empty"
            title={hasBlockingData ? "Optimizer waiting for real data" : "No recommendation generated yet"}
          />
        )}
      </section>
    </>
  );
}
