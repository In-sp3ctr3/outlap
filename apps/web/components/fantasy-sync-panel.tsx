"use client";

import { KeyRound, RefreshCw, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { StateNotice } from "@/components/state-notice";
import { StatusBadge } from "@/components/status";
import type { FantasyReadOnlyStatus } from "@/lib/api";
import { loadFantasyReadOnlyStatus, syncFantasyGame } from "@/lib/api";

export function FantasySyncPanel({ onSynced }: { onSynced: () => Promise<void> }) {
  const [status, setStatus] = useState<FantasyReadOnlyStatus | null>(null);
  const [gamePeriodId, setGamePeriodId] = useState("");
  const [season, setSeason] = useState(new Date().getFullYear());
  const [leagueId, setLeagueId] = useState("");
  const [userGlobalId, setUserGlobalId] = useState("");
  const [slot, setSlot] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    loadFantasyReadOnlyStatus()
      .then((nextStatus) => {
        if (active) setStatus(nextStatus);
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Unable to read Fantasy connector status");
      });
    return () => {
      active = false;
    };
  }, []);

  async function runSync() {
    const trimmedGamePeriod = gamePeriodId.trim();
    if (!trimmedGamePeriod) {
      setError("Game period ID is required for Fantasy sync.");
      return;
    }
    setBusy(true);
    try {
      setError(null);
      setMessage(null);
      const result = await syncFantasyGame({
        gamePeriodId: trimmedGamePeriod,
        season,
        leagueId: emptyToUndefined(leagueId),
        userGlobalId: emptyToUndefined(userGlobalId),
        slot: slot ? Number(slot) : undefined,
      });
      setMessage(`${result.message} Assets ${result.assetCount} · scores ${result.scoreCount} · teams ${result.teamCount}.`);
      await onSynced();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sync Fantasy data");
    } finally {
      setBusy(false);
    }
  }

  const tokenConfigured = Boolean(status?.sessionTokenConfigured);
  const readyForCatalog = Boolean(status?.baseUrlConfigured && status?.gameVersionConfigured);

  return (
    <section className="panel fantasy-sync-panel" aria-labelledby="fantasy-sync-panel-title">
      <div className="page-head">
        <div>
          <h2 id="fantasy-sync-panel-title">Fantasy read-only sync</h2>
          <p>{status?.message ?? "Checking connector status."}</p>
        </div>
        <div className="status-stack">
          <StatusBadge status={readyForCatalog ? "real_current" : "missing"} label={readyForCatalog ? "Catalog endpoint ready" : "Endpoint config needed"} />
          <StatusBadge status={tokenConfigured ? "real_current" : "partial"} label={tokenConfigured ? "Token configured" : "Token needed for picked teams"} />
        </div>
      </div>
      <div className="sync-facts">
        <span>
          <ShieldCheck size={16} aria-hidden="true" />
          Fantasy account mutation: disabled
        </span>
        <span>
          <KeyRound size={16} aria-hidden="true" />
          {tokenConfigured ? "Read-only token detected locally" : "Set FANTASY_SESSION_TOKEN or RACEWEEK_FANTASY_SESSION_TOKEN for user teams"}
        </span>
      </div>
      <div className="grid two sync-form-grid">
        <label className="field">
          Game period ID
          <input
            className="input"
            value={gamePeriodId}
            onChange={(event) => setGamePeriodId(event.target.value)}
            placeholder="Current Fantasy game period"
          />
        </label>
        <label className="field">
          Season
          <input
            className="input"
            min={2020}
            type="number"
            value={season}
            onChange={(event) => setSeason(Number(event.target.value) || new Date().getFullYear())}
          />
        </label>
        <label className="field">
          League ID
          <input className="input" value={leagueId} onChange={(event) => setLeagueId(event.target.value)} />
        </label>
        <label className="field">
          User global ID
          <input className="input" value={userGlobalId} onChange={(event) => setUserGlobalId(event.target.value)} />
        </label>
        <label className="field">
          Picked-team slot
          <select className="select" value={slot} onChange={(event) => setSlot(event.target.value)}>
            <option value="">Catalog only</option>
            <option value="1">Team 1</option>
            <option value="2">Team 2</option>
            <option value="3">Team 3</option>
          </select>
        </label>
      </div>
      <div className="button-row">
        <button className="button" type="button" disabled={busy || !gamePeriodId.trim()} onClick={runSync}>
          <RefreshCw size={16} aria-hidden="true" />
          Sync Fantasy data
        </button>
      </div>
      {message ? <StateNotice tone="info" title="Fantasy sync complete">{message}</StateNotice> : null}
      {error ? <StateNotice tone="error" title="Fantasy sync unavailable">{error}</StateNotice> : null}
    </section>
  );
}

function emptyToUndefined(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}
