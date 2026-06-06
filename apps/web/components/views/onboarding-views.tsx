"use client";

import { DatabaseZap, UsersRound } from "lucide-react";

import { CurrentTeamSelector } from "@/components/current-team-selector";
import { FantasySyncPanel } from "@/components/fantasy-sync-panel";
import { ImportWizard } from "@/components/import-wizard";
import { PageHead } from "@/components/page-head";
import { RealDataOnboarding } from "@/components/real-data-onboarding";
import { StateNotice } from "@/components/state-notice";
import type { DashboardData } from "@/lib/api";

export function OnboardingView({
  data,
  onRefresh,
}: {
  data: DashboardData;
  onRefresh: () => Promise<void>;
}) {
  return (
    <>
      <PageHead
        title="Real Data Setup"
        detail="Season, race context, market prices, teams, chips, budget, league, and review."
      />
      <section className="setup-progress panel" aria-label="Real data setup progress">
        {["Season", "Race Context", "Market Prices", "Teams", "Chips/Budget", "League", "Review"].map(
          (step, index) => (
            <div className={index < 2 ? "complete" : index === 2 ? "active" : ""} key={step}>
              <span>{index + 1}</span>
              {step}
            </div>
          ),
        )}
      </section>
      <RealDataOnboarding data={data} onRefresh={onRefresh} />
    </>
  );
}

export function OnboardingMarketView({
  data,
  onRefresh,
}: {
  data: DashboardData;
  onRefresh: () => Promise<void>;
}) {
  return (
    <>
      <PageHead
        title="Market Import"
        detail="Load current fantasy prices before recommendations can unlock."
      />
      <div className="grid two">
        <FantasySyncPanel onSynced={onRefresh} />
        <section className="panel setup-surface">
          <div className="section-title">
            <DatabaseZap size={18} aria-hidden="true" />
            <h2>Market readiness</h2>
          </div>
          {data.assets.length ? (
            <StateNotice tone="info" title={`${data.assets.length} market rows loaded`}>
              Prices are stored locally and tagged with their source snapshot.
            </StateNotice>
          ) : (
            <StateNotice tone="empty" title="Current fantasy prices are missing">
              Import the market table or run read-only Fantasy sync. Public race APIs cannot
              supply current fantasy prices.
            </StateNotice>
          )}
        </section>
      </div>
      <div style={{ marginTop: 16 }}>
        <ImportWizard onImported={onRefresh} />
      </div>
    </>
  );
}

export function OnboardingTeamView({
  data,
  onRefresh,
}: {
  data: DashboardData;
  onRefresh: () => Promise<void>;
}) {
  return (
    <>
      <PageHead
        title="Team Setup"
        detail="Select or import Teams 1-3, budget, free transfers, and chips."
      />
      <section className="panel setup-surface">
        <div className="section-title">
          <UsersRound size={18} aria-hidden="true" />
          <h2>Team requirements</h2>
        </div>
        <p>
          A ready team has five drivers, two constructors, known prices, a cost cap,
          bank, free transfers, and chip status.
        </p>
      </section>
      <div style={{ marginTop: 16 }}>
        <CurrentTeamSelector data={data} onImported={onRefresh} />
      </div>
    </>
  );
}
