"use client";

import { ArrowRight, Database, Play, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { setDataMode } from "@/lib/api";

export function SplashPage() {
  const router = useRouter();
  const [busyMode, setBusyMode] = useState<"demo" | "real" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function chooseMode(mode: "demo" | "real") {
    setBusyMode(mode);
    try {
      setError(null);
      await setDataMode(mode);
      router.push(mode === "demo" ? "/dashboard" : "/onboarding");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to set data mode");
    } finally {
      setBusyMode(null);
    }
  }

  return (
    <main className="splash-shell">
      <section className="splash-rail" aria-label="Setup steps">
        <div className="splash-wordmark">
          <span>Raceweek</span>
          <strong>Strategist</strong>
        </div>
        {["Data Mode", "Import / Connect", "Team Import", "Review & Finish"].map((step, index) => (
          <div className={`splash-step ${index === 0 ? "active" : ""}`} key={step}>
            <span>{index + 1}</span>
            {step}
          </div>
        ))}
      </section>
      <section className="splash-stage">
        <div className="splash-backdrop" aria-hidden="true" />
        <div className="splash-content">
          <p className="eyebrow">1. Choose your data mode</p>
          <h1>Your unofficial race-week fantasy strategy cockpit</h1>
          <p>
            Start with demo data, or bring your current market prices, team state,
            transfers, chips, and race context into a local-first workspace.
          </p>
          {error ? <p className="splash-error">{error}</p> : null}
          <div className="mode-card-stack" role="list" aria-label="Data mode choices">
            <button
              className="mode-card selected"
              disabled={busyMode !== null}
              type="button"
              onClick={() => void chooseMode("demo")}
            >
              <span className="mode-card-icon">
                <Play size={18} aria-hidden="true" />
              </span>
              <span>
                <strong>Demo Data</strong>
                <small>Use realistic sample data to explore every route and control.</small>
              </span>
              <ArrowRight size={16} aria-hidden="true" />
            </button>
            <button
              className="mode-card"
              disabled={busyMode !== null}
              type="button"
              onClick={() => void chooseMode("real")}
            >
              <span className="mode-card-icon">
                <Database size={18} aria-hidden="true" />
              </span>
              <span>
                <strong>Real Data</strong>
                <small>Import or sync market, team, chips, budget, and league state.</small>
              </span>
              <ArrowRight size={16} aria-hidden="true" />
            </button>
          </div>
          <div className="splash-privacy">
            <ShieldCheck size={16} aria-hidden="true" />
            Local-first. Read-only fantasy sync. No account mutation.
          </div>
        </div>
      </section>
    </main>
  );
}
