"use client";

import { useEffect, useState } from "react";

import type { DashboardData, RecommendationOption, RecommendationRun } from "@/lib/api";
import { loadDashboard, resetDemo, runRecommendation } from "@/lib/api";

import { SetupWizard } from "./setup-wizard";
import { Sidebar, type View } from "./sidebar";
import { AiStrategistView } from "./views/ai-strategist-view";
import { DashboardView } from "./views/dashboard-view";
import { DataHealthView } from "./views/data-health-view";
import { LeagueView } from "./views/league-view";
import { MarketView } from "./views/market-view";
import { MyTeamsView } from "./views/my-teams-view";
import { OptimizerView } from "./views/optimizer-view";
import { RaceWeekView } from "./views/race-week-view";
import { SettingsView } from "./views/settings-view";

export function RaceweekApp({ initialView }: { initialView: View }) {
  const [setupComplete, setSetupComplete] = useState(initialView !== "setup");
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationRun | null>(null);
  const [comparison, setComparison] = useState<RecommendationOption | null>(null);
  const [loadingRecommendation, setLoadingRecommendation] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("raceweek-setup-complete") === "true";
    setSetupComplete(initialView !== "setup" || stored);
  }, [initialView]);

  useEffect(() => {
    if (setupComplete) {
      void refresh();
    }
  }, [setupComplete]);

  async function refresh() {
    try {
      setError(null);
      setData(await loadDashboard());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load dashboard");
    }
  }

  async function completeSetup() {
    window.localStorage.setItem("raceweek-setup-complete", "true");
    setSetupComplete(true);
    await resetDemo();
    await refresh();
  }

  async function generateRecommendation(strategyMode = "balanced", allowedChips: string[] = []) {
    setLoadingRecommendation(true);
    try {
      const result = await runRecommendation({ strategyMode, allowedChips, maxOptions: 5 });
      setRecommendation(result);
      setComparison(null);
    } finally {
      setLoadingRecommendation(false);
    }
  }

  if (!setupComplete && initialView === "setup") {
    return <SetupWizard onComplete={completeSetup} />;
  }

  const view = initialView === "setup" ? "dashboard" : initialView;
  return (
    <div className="app-shell">
      <Sidebar active={view} />
      <main className="content">
        {error ? <div className="error">API unavailable: {error}</div> : null}
        {!data ? <div className="loading">Loading race-week control room...</div> : null}
        {data ? (
          <ViewRouter
            view={view}
            data={data}
            recommendation={recommendation}
            comparison={comparison}
            loadingRecommendation={loadingRecommendation}
            onRefresh={refresh}
            onRecommend={generateRecommendation}
            onCompare={setComparison}
          />
        ) : null}
      </main>
    </div>
  );
}

function ViewRouter(props: {
  view: View;
  data: DashboardData;
  recommendation: RecommendationRun | null;
  comparison: RecommendationOption | null;
  loadingRecommendation: boolean;
  onRefresh: () => Promise<void>;
  onRecommend: (strategyMode?: string, allowedChips?: string[]) => Promise<void>;
  onCompare: (option: RecommendationOption) => void;
}) {
  switch (props.view) {
    case "race-week":
      return <RaceWeekView data={props.data} />;
    case "optimizer":
      return <OptimizerView {...props} />;
    case "market":
      return <MarketView assets={props.data.assets} />;
    case "my-teams":
      return <MyTeamsView data={props.data} />;
    case "league":
      return <LeagueView />;
    case "ai-strategist":
      return <AiStrategistView recommendation={props.recommendation} />;
    case "data-health":
      return <DataHealthView data={props.data} onRefresh={props.onRefresh} />;
    case "settings":
      return <SettingsView data={props.data} />;
    default:
      return <DashboardView {...props} />;
  }
}
