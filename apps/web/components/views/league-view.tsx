"use client";

import { useEffect, useState } from "react";

import { MetricCard } from "@/components/metric-card";
import { PageHead } from "@/components/page-head";
import { loadLeagueAnalysis } from "@/lib/api";

export function LeagueView() {
  const [analysis, setAnalysis] = useState<Awaited<ReturnType<typeof loadLeagueAnalysis>> | null>(null);

  useEffect(() => {
    void loadLeagueAnalysis().then(setAnalysis);
  }, []);

  return (
    <>
      <PageHead title="League" detail="Rival overlap, differentials, and catch-up strategy." />
      {!analysis ? <div className="loading">Loading league analysis...</div> : null}
      {analysis ? (
        <div className="grid two">
          <MetricCard label="Rank / gap" value={`P${analysis.userRank} · ${analysis.gapToLeader} pts`} detail="Demo league" />
          <section className="panel">
            <h2>Catch-up plan</h2>
            {analysis.catchUpPlan.map((item) => <p key={item}>{item}</p>)}
          </section>
          <AssetList title="Common picks" assetIds={analysis.commonAssetIds} />
          <AssetList title="Differentials" assetIds={analysis.differentialAssetIds} empty="No unique assets in the current snapshot." />
        </div>
      ) : null}
    </>
  );
}

function AssetList({ title, assetIds, empty }: { title: string; assetIds: string[]; empty?: string }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {assetIds.length ? (
        <div className="transfer-list">{assetIds.map((assetId) => <span className="transfer-pill" key={assetId}>{assetId}</span>)}</div>
      ) : (
        <div className="empty">{empty ?? "No assets found."}</div>
      )}
    </section>
  );
}
