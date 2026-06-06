"use client";

import { DatabaseZap, ListChecks } from "lucide-react";

import type { DashboardData } from "@/lib/api";

import { CurrentTeamSelector } from "./current-team-selector";
import { FantasySyncPanel } from "./fantasy-sync-panel";
import { FreshnessDomainRow } from "./freshness";
import { ImportWizard } from "./import-wizard";

export function RealDataOnboarding({
  data,
  onRefresh,
}: {
  data: DashboardData;
  onRefresh: () => Promise<void>;
}) {
  const marketReady = data.assets.length > 0;
  const setupRows = data.freshness.filter((item) =>
    ["fantasy.market", "fantasy.user_team", "fantasy.scores"].includes(item.key),
  );

  return (
    <div className="onboarding-flow">
      <section className="panel setup-surface">
        <div className="page-head">
          <div>
            <h2>Real data onboarding</h2>
            <p>Load the fantasy market first, then choose Teams 1, 2, and 3 from the catalog.</p>
          </div>
          <DatabaseZap size={24} aria-hidden="true" />
        </div>
        <div className="freshness-list">
          {setupRows.map((item) => (
            <FreshnessDomainRow item={item} compact key={item.key} />
          ))}
        </div>
      </section>
      {!marketReady ? (
        <>
          <FantasySyncPanel onSynced={onRefresh} />
          <section className="onboarding-import" aria-labelledby="onboarding-import-title">
            <div className="section-title">
              <ListChecks size={18} aria-hidden="true" />
              <h2 id="onboarding-import-title">Fallback source data import</h2>
            </div>
            <ImportWizard onImported={onRefresh} />
          </section>
        </>
      ) : null}
      <CurrentTeamSelector data={data} onImported={onRefresh} />
    </div>
  );
}
