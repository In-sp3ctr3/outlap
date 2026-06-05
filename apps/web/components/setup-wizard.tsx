"use client";

import { Upload } from "lucide-react";

import { StatusBadge } from "@/components/status";

export function SetupWizard({ onComplete }: { onComplete: () => Promise<void> }) {
  async function finish() {
    await onComplete();
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
          <button className="button" type="button" onClick={finish}>
            <Upload size={16} aria-hidden="true" />
            Start demo mode
          </button>
          <button className="button secondary" type="button" onClick={finish}>
            Configure local Ollama
          </button>
          <button className="button secondary" type="button" onClick={finish}>
            Import manual JSON
          </button>
        </div>
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
