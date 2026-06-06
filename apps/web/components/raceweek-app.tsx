"use client";

import { useEffect, useState } from "react";

import type { DashboardData, OptimizerReadiness, RecommendationOption, RecommendationRun } from "@/lib/api";
import { loadDashboard, loadOptimizerReadiness, runRecommendation } from "@/lib/api";

import { Sidebar, type View } from "./sidebar";
import { StateNotice } from "./state-notice";
import { TopBar } from "./top-bar";
import { AiStrategistView } from "./views/ai-strategist-view";
import { DashboardView } from "./views/dashboard-view";
import { DataHealthView } from "./views/data-health-view";
import { LeagueView } from "./views/league-view";
import { MarketView } from "./views/market-view";
import { MyTeamsView } from "./views/my-teams-view";
import { OnboardingMarketView, OnboardingTeamView, OnboardingView } from "./views/onboarding-views";
import { OptimizerView } from "./views/optimizer-view";
import { RaceWeekView } from "./views/race-week-view";
import { SettingsView } from "./views/settings-view";

export function RaceweekApp({ initialView }: { initialView: View }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationRun | null>(null);
  const [comparison, setComparison] = useState<RecommendationOption | null>(null);
  const [readiness, setReadiness] = useState<OptimizerReadiness | null>(null);
  const [loadingRecommendation, setLoadingRecommendation] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    void refresh();
  }, []);

  async function refresh() {
    try {
      setError(null);
      const [nextData, nextReadiness] = await Promise.all([
        loadDashboard(),
        loadOptimizerReadiness().catch(() => null),
      ]);
      setData(nextData);
      setReadiness(nextReadiness);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load dashboard");
    }
  }

  async function generateRecommendation(
    strategyMode = "balanced",
    allowedChips: string[] = [],
    lockedAssetIds: string[] = [],
    bannedAssetIds: string[] = [],
  ) {
    const team = data?.teams[0];
    const eventId = team?.eventId ?? data?.appStatus.currentEventId;
    if (!readiness?.ready) {
      const blockers = readiness?.blockingReasons.map((item) => item.message).join(" ") ?? "";
      setActionError(blockers || "Load market data and select Teams 1-3 before running the optimizer.");
      return;
    }
    if (!team || !eventId) {
      setActionError("Select a current team and event before running the optimizer.");
      return;
    }
    setLoadingRecommendation(true);
    try {
      setActionError(null);
      const result = await runRecommendation({
        eventId,
        teamSnapshotId: team.teamSnapshotId,
        strategyMode,
        allowedChips,
        lockedAssetIds,
        bannedAssetIds,
        maxOptions: 5,
      });
      setRecommendation(result);
      setComparison(null);
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : "Unable to run optimizer");
    } finally {
      setLoadingRecommendation(false);
    }
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <Sidebar active={initialView} />
      <main className="content" id="main-content" aria-busy={!data}>
        {error ? <StateNotice tone="error" title="API unavailable">{error}</StateNotice> : null}
        {actionError ? <StateNotice tone="error" title="Action failed">{actionError}</StateNotice> : null}
        {!data ? <DashboardSkeleton /> : null}
        {data ? (
          <>
            <TopBar data={data} />
            <ViewRouter
              view={initialView}
              data={data}
              readiness={readiness}
              recommendation={recommendation}
              comparison={comparison}
              loadingRecommendation={loadingRecommendation}
              onRefresh={refresh}
              onRecommend={generateRecommendation}
              onCompare={setComparison}
            />
          </>
        ) : null}
      </main>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <section className="panel skeleton-panel" aria-label="Loading real race-week data">
      <StateNotice tone="loading" title="Loading real race-week data">
        Fetching app status, data freshness, current team, and fantasy market catalog.
      </StateNotice>
      <div className="skeleton-grid" aria-hidden="true">
        <span className="skeleton-block" />
        <span className="skeleton-block" />
        <span className="skeleton-block" />
      </div>
    </section>
  );
}

function ViewRouter(props: {
  view: View;
  data: DashboardData;
  readiness: OptimizerReadiness | null;
  recommendation: RecommendationRun | null;
  comparison: RecommendationOption | null;
  loadingRecommendation: boolean;
  onRefresh: () => Promise<void>;
  onRecommend: (
    strategyMode?: string,
    allowedChips?: string[],
    lockedAssetIds?: string[],
    bannedAssetIds?: string[],
  ) => Promise<void>;
  onCompare: (option: RecommendationOption) => void;
}) {
  switch (props.view) {
    case "onboarding":
      return <OnboardingView data={props.data} onRefresh={props.onRefresh} />;
    case "onboarding-market":
      return <OnboardingMarketView data={props.data} onRefresh={props.onRefresh} />;
    case "onboarding-team":
      return <OnboardingTeamView data={props.data} onRefresh={props.onRefresh} />;
    case "race-week":
      return <RaceWeekView data={props.data} onRefresh={props.onRefresh} />;
    case "optimizer":
      return <OptimizerView {...props} />;
    case "market":
      return <MarketView data={props.data} onRefresh={props.onRefresh} />;
    case "my-teams":
      return <MyTeamsView data={props.data} onRefresh={props.onRefresh} />;
    case "league":
      return <LeagueView onRefresh={props.onRefresh} />;
    case "ai-strategist":
      return <AiStrategistView providers={props.data.providers} recommendation={props.recommendation} />;
    case "data-health":
      return <DataHealthView data={props.data} onRefresh={props.onRefresh} />;
    case "settings":
      return <SettingsView data={props.data} />;
    default:
      return <DashboardView {...props} />;
  }
}
