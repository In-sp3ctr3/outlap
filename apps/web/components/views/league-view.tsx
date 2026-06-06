"use client";

import { useEffect, useState } from "react";

import { ImportWizard } from "@/components/import-wizard";
import { MetricCard } from "@/components/metric-card";
import { PageHead } from "@/components/page-head";
import { StateNotice } from "@/components/state-notice";
import { loadLeagueTable } from "@/lib/api";

export function LeagueView({ onRefresh }: { onRefresh: () => Promise<void> }) {
  const [league, setLeague] = useState<Awaited<ReturnType<typeof loadLeagueTable>>["items"][0] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    void loadLeagueTable()
      .then((result) => setLeague(result.items[0] ?? null))
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "Unable to load league table");
      });
  }, []);

  return (
    <>
      <PageHead title="League" detail="Rival overlap, differentials, and catch-up strategy." />
      {error ? <StateNotice tone="error" title="League table unavailable">{error}</StateNotice> : null}
      {!league && !error ? (
        <>
          <StateNotice tone="empty" title="No real league table imported" />
          <ImportWizard onImported={onRefresh} />
        </>
      ) : null}
      {league ? (
        <div className="grid two">
          <MetricCard label="League rows" value={String(league.rivals.length)} detail={league.leagueId} />
          <section className="panel">
            <h2>Imported standings</h2>
            {league.rivals.map((row) => (
              <p key={`${row.rank}-${row.teamName}`}>
                P{row.rank ?? "?"} · {row.teamName} · {row.points} pts
              </p>
            ))}
          </section>
        </div>
      ) : null}
    </>
  );
}
