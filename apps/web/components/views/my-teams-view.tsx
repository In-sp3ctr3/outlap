import { MetricCard } from "@/components/metric-card";
import { PageHead } from "@/components/page-head";
import { RealDataOnboarding } from "@/components/real-data-onboarding";
import { StateNotice } from "@/components/state-notice";
import { StatusBadge } from "@/components/status";
import type { DashboardData } from "@/lib/api";
import { assetAbbreviation, assetDisplayName, assetTeamColor, assetTypeLabel } from "@/lib/fantasy-assets";
import { formatBudget } from "@/lib/format";

export function MyTeamsView({
  data,
  onRefresh,
}: {
  data: DashboardData;
  onRefresh: () => Promise<void>;
}) {
  const team = data.teams[0];
  if (!team) {
    return (
      <>
        <PageHead title="My Teams" detail="Three current teams, budget, free transfers, chips, and catalog-based selection." />
        <StateNotice tone="empty" title="No real team snapshot imported">
          Load market data, then choose Teams 1, 2, and 3 from the catalog.
        </StateNotice>
        <RealDataOnboarding data={data} onRefresh={onRefresh} />
      </>
    );
  }
  const assetsById = new Map(data.assets.map((asset) => [asset.assetId, asset]));
  return (
    <>
      <PageHead title="My Teams" detail="Three current teams, budget, free transfers, chips, and catalog-based selection." />
      <div className="grid three">
        <MetricCard label="Team 1" value={team.teamName} detail={`${team.assets.length} selected assets`} />
        <MetricCard label="Saved teams" value={`${data.teams.length} / 3`} detail="Team slots ready for strategy" />
        <MetricCard label="Budget" value={`${formatBudget(team.budgetUsedMillions)} used`} detail={`${formatBudget(team.budgetRemainingMillions)} remaining`} />
      </div>
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Lineups</h2>
        {data.teams.map((savedTeam) => (
          <div className="team-lineup-block" key={savedTeam.teamSnapshotId}>
            <h3>Team {savedTeam.slot ?? 1}: {savedTeam.teamName}</h3>
            <div className="lineup-grid" style={{ marginTop: 12 }}>
              {savedTeam.assets.map((teamAsset) => {
                const asset = assetsById.get(teamAsset.assetId);
                return (
                  <article className="lineup-asset" key={`${savedTeam.teamSnapshotId}-${teamAsset.assetId}`}>
                    <span className="asset-token" style={{ backgroundColor: asset ? assetTeamColor(asset) : undefined }}>
                      {asset ? assetAbbreviation(asset) : "??"}
                    </span>
                    <span>
                      <strong>{assetDisplayName(asset)}</strong>
                      <small>
                        {assetTypeLabel(teamAsset.assetType === "constructor" ? "constructor" : "driver")}
                        {asset?.constructorName ? ` · ${asset.constructorName}` : ""}
                      </small>
                    </span>
                  </article>
                );
              })}
            </div>
          </div>
        ))}
      </section>
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Chips</h2>
        <div className="status-strip" style={{ marginTop: 12 }}>
          {team.chips.map((chip) => <StatusBadge key={chip.chipName} status={chip.status === "available" ? "ok" : "stale"} label={`${chip.chipName}: ${chip.status}`} />)}
        </div>
      </section>
      <div style={{ marginTop: 16 }}>
        <RealDataOnboarding data={data} onRefresh={onRefresh} />
      </div>
    </>
  );
}
