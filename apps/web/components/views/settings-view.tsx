"use client";

import { useState } from "react";

import { FreshnessDomainRow } from "@/components/freshness";
import { ImportWizard } from "@/components/import-wizard";
import { PageHead } from "@/components/page-head";
import { StateNotice } from "@/components/state-notice";
import { resetRealData, testProvider, type DashboardData } from "@/lib/api";

export function SettingsView({ data }: { data: DashboardData }) {
  const [providerMessage, setProviderMessage] = useState<string | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);

  async function clearLocalData() {
    setResetting(true);
    await resetRealData();
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
          <h2>Data freshness</h2>
          <div className="freshness-list">
            {data.freshness.map((item) => (
              <FreshnessDomainRow item={item} compact key={item.key} />
            ))}
          </div>
        </section>
        <section className="panel">
          <h2>Privacy</h2>
          <p>No telemetry is enabled by default. Provider keys stay server-side and are never sent to the browser.</p>
          <button className="button secondary" type="button" disabled={resetting} onClick={clearLocalData}>Clear local real data</button>
        </section>
        <section className="panel">
          <h2>Ruleset</h2>
          <p>v1 fantasy rules · 5 drivers · 2 teams · 100.0M cap · 10 point extra-transfer penalty.</p>
        </section>
        <section className="panel">
          <h2>Import/export</h2>
          <p>Fallback CSV/TSV imports are local-first and write provenance records to DuckDB.</p>
          <ImportWizard onImported={async () => window.location.assign("/settings")} />
        </section>
        <section className="panel">
          <h2>About</h2>
          <p className="legal">
            Outlap is an unofficial fan-made fantasy analytics tool. It is not affiliated with, endorsed by, or sponsored by Formula 1,
            Formula One Management, or any team/constructor. Users are responsible for complying with the terms of the services they connect.
          </p>
        </section>
      </div>
    </>
  );
}
