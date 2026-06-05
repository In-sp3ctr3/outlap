"use client";

import { Upload } from "lucide-react";
import { useState } from "react";

import { StateNotice } from "@/components/state-notice";
import { StatusBadge } from "@/components/status";

const manualTeamPayload = {
  teamSnapshotId: "team_manual_setup_01",
  teamName: "Manual Import Team",
  eventId: "event_demo_01",
  slot: 1,
  costCapMillions: 100,
  budgetUsedMillions: 99,
  budgetRemainingMillions: 1,
  freeTransfers: 2,
  transferPenaltyPoints: 10,
  capturedAt: "2026-06-05T00:00:00Z",
  sourceSnapshotId: "snapshot_manual_setup_team_01",
  assets: [
    { assetId: "asset_driver_alpha", assetType: "driver", boostMultiplier: 2 },
    { assetId: "asset_driver_bravo", assetType: "driver", boostMultiplier: 1 },
    { assetId: "asset_driver_charlie", assetType: "driver", boostMultiplier: 1 },
    { assetId: "asset_driver_delta", assetType: "driver", boostMultiplier: 1 },
    { assetId: "asset_driver_echo", assetType: "driver", boostMultiplier: 1 },
    { assetId: "asset_constructor_two", assetType: "constructor", boostMultiplier: 1 },
    { assetId: "asset_constructor_three", assetType: "constructor", boostMultiplier: 1 },
  ],
  chips: [
    { chipName: "wildcard", status: "available" },
    { chipName: "limitless", status: "available" },
    { chipName: "no_negative", status: "available" },
    { chipName: "autopilot", status: "available" },
    { chipName: "3x_boost", status: "available" },
    { chipName: "final_fix", status: "available" },
  ],
};

export function SetupWizard({ onComplete }: { onComplete: (teamPayload?: unknown) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function finish(teamPayload?: unknown) {
    setBusy(true);
    try {
      setError(null);
      await onComplete(teamPayload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to complete setup");
      setBusy(false);
    }
  }

  return (
    <main className="setup">
      <section className="panel setup-panel">
        <div className="page-head">
          <div>
            <h1>RaceWeek Strategist</h1>
            <p>
              Unofficial local-first fantasy motorsport strategy, powered by deterministic
              recommendations and optional bring-your-own AI explanations.
            </p>
          </div>
          <StatusBadge status="ok" label="Demo-ready" />
        </div>
        <div className="step-list">
          <Step title="1. Choose mode" detail="Demo mode uses synthetic fixture data and works offline after install." />
          <Step title="2. Configure AI" detail="Use the fake provider for tests, Ollama locally, or bring your own key later." />
          <Step title="3. Import team" detail="Manual JSON stays first-class; live connectors degrade gracefully." />
        </div>
        <div className="button-row" style={{ marginTop: 18 }}>
          <button className="button" type="button" disabled={busy} onClick={() => finish()}>
            <Upload size={16} aria-hidden="true" />
            Start demo mode
          </button>
          <button className="button secondary" type="button" disabled={busy} onClick={() => finish()}>
            Configure local Ollama
          </button>
          <button
            className="button secondary"
            type="button"
            disabled={busy}
            onClick={() => finish(manualTeamPayload)}
          >
            Import manual JSON
          </button>
        </div>
        {busy ? <StateNotice tone="loading" title="Preparing local workspace" /> : null}
        {error ? <StateNotice tone="error" title="Setup failed">{error}</StateNotice> : null}
        <p className="legal">
          RaceWeek Strategist is an unofficial fan-made fantasy analytics tool. It is not
          affiliated with, endorsed by, or sponsored by Formula 1, Formula One Management, or any
          team/constructor. Users are responsible for complying with the terms of the services they
          connect.
        </p>
      </section>
    </main>
  );
}

function Step({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="step-card">
      <h3>{title}</h3>
      <p>{detail}</p>
    </div>
  );
}
