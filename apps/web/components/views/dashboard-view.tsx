"use client";

import { BrainCircuit } from "lucide-react";

import { MetricCard } from "@/components/metric-card";
import { PageHead } from "@/components/page-head";
import { RecommendationCard } from "@/components/recommendation-card";
import { StatusBadge } from "@/components/status";
import type { DashboardData, RecommendationOption, RecommendationRun } from "@/lib/api";
import { formatBudget, riskLabel } from "@/lib/format";

export function DashboardView({
  data,
  recommendation,
  loadingRecommendation,
  onRecommend,
  onCompare,
}: {
  data: DashboardData;
  recommendation: RecommendationRun | null;
  loadingRecommendation: boolean;
  onRecommend: (strategyMode?: string, allowedChips?: string[]) => Promise<void>;
  onCompare: (option: RecommendationOption) => void;
}) {
  const team = data.teams[0];
  const biggestRisk = data.assets.reduce((max, asset) => Math.max(max, asset.riskScore ?? 0), 0);
  const topOption = recommendation?.options[0];

  return (
    <>
      <PageHead
        title="Dashboard"
        detail="Next event, data freshness, team state, and the current recommendation."
        action={
          <button className="button" type="button" disabled={loadingRecommendation} onClick={() => onRecommend("balanced")}>
            <BrainCircuit size={16} aria-hidden="true" />
            Generate baseline
          </button>
        }
      />
      <div className="grid three">
        <MetricCard label="Next event" value={data.race.meetingName} detail={`${data.race.circuitName} · locks ${new Date(data.race.locksAt).toLocaleString()}`} />
        <MetricCard label="Budget / transfers" value={`${formatBudget(team.budgetRemainingMillions)} · ${team.freeTransfers} FT`} detail={team.teamName} />
        <MetricCard label="Biggest risk" value={riskLabel(biggestRisk)} detail="Highest fixture risk in market" />
      </div>
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Data health</h2>
        <div className="status-strip" style={{ marginTop: 12 }}>
          {data.dataSources.map((source) => (
            <StatusBadge key={source.source} status={source.status} label={`${source.source}: ${source.freshness}`} />
          ))}
        </div>
      </section>
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Recommendation highlight</h2>
        {topOption ? (
          <div style={{ marginTop: 14 }}>
            <RecommendationCard option={topOption} onCompare={onCompare} />
          </div>
        ) : (
          <div className="empty" style={{ marginTop: 14 }}>
            No recommendation generated yet.
          </div>
        )}
      </section>
    </>
  );
}
