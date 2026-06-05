"use client";

import { PageHead } from "@/components/page-head";
import type { DashboardData } from "@/lib/api";

export function SettingsView({ data }: { data: DashboardData }) {
  function clearLocalData() {
    window.localStorage.removeItem("raceweek-setup-complete");
    window.location.assign("/");
  }

  return (
    <>
      <PageHead title="Settings" detail="Providers, data sources, ruleset, projection weights, privacy, import/export, and legal." />
      <div className="grid two">
        <section className="panel">
          <h2>AI providers</h2>
          {data.providers.map((provider) => (
            <p key={provider.providerName}><strong>{provider.displayName}</strong> · {provider.keyConfigured ? "configured" : "bring your own key"}</p>
          ))}
        </section>
        <section className="panel">
          <h2>Privacy</h2>
          <p>No telemetry is enabled by default. Provider keys stay server-side and are never sent to the browser.</p>
          <button className="button secondary" type="button" onClick={clearLocalData}>Clear local setup state</button>
        </section>
        <section className="panel">
          <h2>Ruleset</h2>
          <p>fantasy_demo_2026_v1 · 5 drivers · 2 constructors · 100.0M cap · 10 point extra-transfer penalty.</p>
        </section>
        <section className="panel">
          <h2>About</h2>
          <p className="legal">
            RaceWeek Strategist is an unofficial fan-made fantasy analytics tool. It is not affiliated with, endorsed by, or sponsored by Formula 1,
            Formula One Management, or any team/constructor. Users are responsible for complying with the terms of the services they connect.
          </p>
        </section>
      </div>
    </>
  );
}
