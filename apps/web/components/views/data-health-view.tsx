"use client";

import { Database, RefreshCw } from "lucide-react";
import { useState } from "react";

import { FantasySyncPanel } from "@/components/fantasy-sync-panel";
import { FreshnessDomainRow } from "@/components/freshness";
import { ImportWizard } from "@/components/import-wizard";
import { PageHead } from "@/components/page-head";
import { StateNotice } from "@/components/state-notice";
import type { DashboardData } from "@/lib/api";
import { backfillFantasyScores, syncRaceContext } from "@/lib/api";

export function DataHealthView({ data, onRefresh }: { data: DashboardData; onRefresh: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [backfillBusy, setBackfillBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function syncRace() {
    setBusy(true);
    try {
      setError(null);
      setMessage(null);
      await syncRaceContext({ season: 2026 });
      await onRefresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sync race context");
    } finally {
      setBusy(false);
    }
  }

  async function backfillScores() {
    const event = parseEventId(data.teams[0]?.eventId ?? data.appStatus.currentEventId ?? data.race?.eventId);
    setBackfillBusy(true);
    try {
      setError(null);
      setMessage(null);
      const result = await backfillFantasyScores({
        season: event.season,
        throughRound: event.round,
        eventId: event.eventId,
      });
      setMessage(result.message);
      await onRefresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to backfill historical form");
    } finally {
      setBackfillBusy(false);
    }
  }

  return (
    <>
      <PageHead
        title="Data Freshness"
        detail="Real-data status, source mode, row counts, age, and remediation actions."
        action={
          <div className="button-row">
            <button className="button" type="button" disabled={busy} onClick={syncRace}>
              <RefreshCw size={16} aria-hidden="true" />
              Sync race context
            </button>
            <button className="button secondary" type="button" disabled={backfillBusy || data.assets.length === 0} onClick={backfillScores}>
              <RefreshCw size={16} aria-hidden="true" />
              Backfill historical form
            </button>
          </div>
        }
      />
      {error ? <StateNotice tone="error" title="Data-source action failed">{error}</StateNotice> : null}
      {message ? <StateNotice tone="info" title="Data-source action complete">{message}</StateNotice> : null}
      <section className="panel">
        <div className="page-head">
          <div>
            <h2>Freshness center</h2>
            <p>Overall status: {data.overallStatus.replace("_", " ")}</p>
          </div>
          <Database size={24} aria-hidden="true" />
        </div>
        <div className="freshness-list">
          {data.freshness.map((item) => (
            <FreshnessDomainRow item={item} key={item.key} />
          ))}
        </div>
      </section>
      <div style={{ marginTop: 16 }}>
        <FantasySyncPanel onSynced={onRefresh} />
      </div>
      <div style={{ marginTop: 16 }}>
        <ImportWizard onImported={onRefresh} />
      </div>
    </>
  );
}

function parseEventId(eventId: string | undefined): { season: number; round?: number; eventId?: string } {
  const match = eventId?.match(/^event_(\d{4})_(\d{1,2})$/);
  if (!match) return { season: 2026 };
  return {
    season: Number(match[1]),
    round: Number(match[2]),
    eventId,
  };
}
