"use client";

import { Bot } from "lucide-react";
import { useState } from "react";

import { PageHead } from "@/components/page-head";
import { StateNotice } from "@/components/state-notice";
import { StatusBadge } from "@/components/status";
import { chat, type DashboardData, type RecommendationRun } from "@/lib/api";

export function AiStrategistView({
  providers,
  recommendation,
}: {
  providers: DashboardData["providers"];
  recommendation: RecommendationRun | null;
}) {
  const [provider, setProvider] = useState("fake");
  const [message, setMessage] = useState("Compare the top two recommendations.");
  const [response, setResponse] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    setBusy(true);
    try {
      setError(null);
      const result = await chat(provider, message, recommendation?.recommendationRunId);
      setResponse(result.message);
      setStatus(result.status);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to send strategy chat");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead title="AI Strategist" detail="Read-only explanation layer over deterministic optimizer output." />
      <section className="panel">
        <div className="grid two">
          <label className="field">
            Provider
            <select className="select" value={provider} onChange={(event) => setProvider(event.target.value)}>
              {providers.map((item) => (
                <option key={item.providerName} value={item.providerName}>
                  {item.displayName}
                  {item.enabled ? "" : " (not configured)"}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Prompt
            <textarea className="textarea" value={message} onChange={(event) => setMessage(event.target.value)} />
          </label>
        </div>
        <div className="button-row" style={{ marginTop: 14 }}>
          <button className="button" type="button" disabled={busy} onClick={send}><Bot size={16} aria-hidden="true" />Send</button>
          <StatusBadge status="ok" label="Read-only tools" />
        </div>
      </section>
      {busy ? <StateNotice tone="loading" title="Waiting for provider response" /> : null}
      {error ? <StateNotice tone="error" title="Strategy chat failed">{error}</StateNotice> : null}
      {response ? (
        <section className="panel" style={{ marginTop: 16 }} aria-live="polite">
          <StatusBadge status={status === "fallback" ? "degraded" : "ok"} label={status ?? "ok"} />
          <p>{response}</p>
          <p>Fantasy account mutation: disabled.</p>
        </section>
      ) : null}
    </>
  );
}
