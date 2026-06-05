"use client";

import { RotateCw } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHead } from "@/components/page-head";
import { StateNotice } from "@/components/state-notice";
import { StatusBadge } from "@/components/status";
import type { DashboardData, loadRaceIntelligence } from "@/lib/api";
import { loadRaceIntelligence as fetchRaceIntelligence } from "@/lib/api";

export function RaceWeekView({ data }: { data: DashboardData }) {
  const [intelligence, setIntelligence] = useState<Awaited<ReturnType<typeof loadRaceIntelligence>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    setIntelligence(null);
    void fetchRaceIntelligence(data.race.meetingKey)
      .then(setIntelligence)
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "Unable to load race-week data");
      });
  }, [data.race.meetingKey]);

  return (
    <>
      <PageHead title="Race Week" detail="Session timeline, weather, news, and race-control context." />
      {error ? <StateNotice tone="error" title="Race-week intelligence unavailable">{error}</StateNotice> : null}
      {!intelligence && !error ? (
        <StateNotice tone="loading" title="Loading race-week intelligence" />
      ) : null}
      {intelligence ? (
        <div className="grid two">
          <section className="panel">
            <h2>Data freshness</h2>
            <div className="status-strip" style={{ marginTop: 12 }}>
              {data.dataSources.map((source) => (
                <StatusBadge
                  key={source.source}
                  status={source.status}
                  label={`${source.source}: ${source.freshness}`}
                />
              ))}
            </div>
            {data.dataSources
              .filter((source) => source.status !== "ok")
              .map((source) => (
                <p key={source.source}>{source.message}</p>
              ))}
          </section>
          <section className="panel">
            <h2>Event timeline</h2>
            {intelligence.sessions.map((session) => (
              <p key={session.sessionKey}>
                <strong>{session.sessionName}</strong> · {session.status} · {new Date(session.startsAt).toLocaleString()}
              </p>
            ))}
            <button className="button secondary" type="button" onClick={() => window.location.assign("/optimizer")}>
              <RotateCw size={16} aria-hidden="true" />
              Rerun projections
            </button>
          </section>
          <section className="panel">
            <h2>Weather and race control</h2>
            {intelligence.weather.map((item) => (
              <p key={item.summary}>{item.summary} Rain chance {item.rainfallChancePct}%.</p>
            ))}
            {intelligence.raceControl.map((item) => (
              <p key={item.message}>{item.flag}: {item.message}</p>
            ))}
          </section>
          <section className="panel">
            <h2>News risk strip</h2>
            {intelligence.news.map((item) => (
              <p key={item.title}>
                <strong>{item.title}</strong>
                <br />
                {item.summary}
              </p>
            ))}
          </section>
        </div>
      ) : null}
    </>
  );
}
