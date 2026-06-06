"use client";

import { RotateCw } from "lucide-react";
import { useEffect, useState } from "react";

import { FreshnessDomainRow } from "@/components/freshness";
import { PageHead } from "@/components/page-head";
import { StateNotice } from "@/components/state-notice";
import type { DashboardData, loadRaceSessions } from "@/lib/api";
import { loadRaceSessions as fetchRaceSessions, syncRaceContext } from "@/lib/api";

export function RaceWeekView({
  data,
  onRefresh,
}: {
  data: DashboardData;
  onRefresh: () => Promise<void>;
}) {
  const [sessions, setSessions] = useState<Awaited<ReturnType<typeof loadRaceSessions>>["items"]>([]);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    if (!data.race?.meetingKey) return;
    setError(null);
    setSessions([]);
    void fetchRaceSessions(data.race.meetingKey)
      .then((result) => setSessions(result.items))
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "Unable to load race-week data");
      });
  }, [data.race?.meetingKey]);

  async function syncRace() {
    setSyncing(true);
    try {
      setError(null);
      await syncRaceContext({ season: 2026, meetingKey: data.race?.meetingKey });
      await onRefresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sync race context");
    } finally {
      setSyncing(false);
    }
  }

  const raceFreshness = data.freshness.filter((item) => item.key.startsWith("race."));

  return (
    <>
      <PageHead
        title="Race Week"
        detail="Public OpenF1/Jolpica context, session timeline, and freshness."
        action={
          <button className="button" type="button" disabled={syncing} onClick={syncRace}>
            <RotateCw size={16} aria-hidden="true" />
            Sync race context
          </button>
        }
      />
      {error ? <StateNotice tone="error" title="Race-week intelligence unavailable">{error}</StateNotice> : null}
      {!data.race ? <StateNotice tone="empty" title="No public race context synced yet" /> : null}
      <div className="grid two">
        <section className="panel">
          <h2>Race freshness</h2>
          <div className="freshness-list">
            {raceFreshness.map((item) => (
              <FreshnessDomainRow item={item} key={item.key} />
            ))}
          </div>
        </section>
        {data.race ? (
          <section className="panel">
            <h2>Event timeline</h2>
            {sessions.map((session) => (
              <p key={session.sessionKey}>
                <strong>{session.sessionName}</strong>
                {session.startsAt ? ` · ${new Date(session.startsAt).toLocaleString()}` : ""}
              </p>
            ))}
            <button className="button secondary" type="button" onClick={() => window.location.assign("/optimizer")}>
              <RotateCw size={16} aria-hidden="true" />
              Rerun projections
            </button>
          </section>
        ) : null}
      </div>
    </>
  );
}
