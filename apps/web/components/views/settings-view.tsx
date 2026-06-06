"use client";

import { useState } from "react";

import { PageHead } from "@/components/page-head";
import { StateNotice } from "@/components/state-notice";
import { StatusBadge } from "@/components/status";
import { importTeam, testProvider, type DashboardData } from "@/lib/api";

export function SettingsView({ data }: { data: DashboardData }) {
  const [providerMessage, setProviderMessage] = useState<string | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [teamImportJson, setTeamImportJson] = useState("");
  const [importError, setImportError] = useState<string | null>(null);

  function clearLocalData() {
    window.localStorage.removeItem("raceweek-setup-complete");
    window.location.assign("/");
  }

  async function handleProviderTest(providerName: string) {
    setTestingProvider(providerName);
    setProviderMessage(null);
    try {
      const result = await testProvider(providerName);
      setProviderMessage(result.message);
    } catch (caught) {
      setProviderMessage(caught instanceof Error ? caught.message : "Provider test failed");
    } finally {
      setTestingProvider(null);
    }
  }

  async function handleTeamImport() {
    setImportError(null);
    try {
      await importTeam(JSON.parse(teamImportJson));
      window.location.assign("/");
    } catch (caught) {
      setImportError(caught instanceof Error ? caught.message : "Team import failed");
    }
  }

  return (
    <>
      <PageHead title="Settings" detail="Providers, data sources, ruleset, projection weights, privacy, import/export, and legal." />
      <div className="grid two">
        <section className="panel">
          <h2>AI providers</h2>
          {data.providers.map((provider) => (
            <div className="provider-row" key={provider.providerName}>
              <p>
                <strong>{provider.displayName}</strong> · {provider.enabled ? "enabled" : "not configured"}
                {provider.apiKeyEnvVar ? ` · ${provider.apiKeyEnvVar}` : ""}
              </p>
              <button
                className="button secondary"
                type="button"
                disabled={testingProvider === provider.providerName}
                onClick={() => handleProviderTest(provider.providerName)}
              >
                Test
              </button>
            </div>
          ))}
          {testingProvider ? <StateNotice tone="loading" title="Testing provider" /> : null}
          {providerMessage ? (
            <StateNotice tone="info" title="Provider test result">{providerMessage}</StateNotice>
          ) : null}
        </section>
        <section className="panel">
          <h2>Data sources</h2>
          <div className="status-strip" style={{ marginTop: 12 }}>
            {data.dataSources.map((source) => (
              <StatusBadge
                key={source.source}
                status={source.status}
                label={`${source.source}: ${source.freshness}`}
              />
            ))}
          </div>
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
          <h2>Import/export</h2>
          <p>Manual JSON and CSV imports are local-first. Exported state contains fixture/demo data only and never includes provider keys.</p>
          <label className="field">
            Team import JSON
            <textarea
              className="textarea"
              value={teamImportJson}
              onChange={(event) => setTeamImportJson(event.target.value)}
              placeholder='{"teamSnapshotId":"team_manual_01", ...}'
            />
          </label>
          <div className="button-row">
            <button
              className="button"
              type="button"
              disabled={!teamImportJson.trim()}
              onClick={handleTeamImport}
            >
              Import team JSON
            </button>
            <button
              className="button secondary"
              type="button"
              onClick={() => navigator.clipboard?.writeText(JSON.stringify(data.teams[0] ?? {}, null, 2))}
            >
              Copy team JSON
            </button>
            <button
              className="button secondary"
              type="button"
              onClick={() => navigator.clipboard?.writeText(JSON.stringify(data.dataSources, null, 2))}
            >
              Copy data-source status
            </button>
          </div>
          {importError ? <StateNotice tone="error" title="Team import failed">{importError}</StateNotice> : null}
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
