import { MetricCard } from "@/components/metric-card";
import { PageHead } from "@/components/page-head";
import { StatusBadge } from "@/components/status";
import type { DashboardData } from "@/lib/api";
import { formatBudget } from "@/lib/format";

export function MyTeamsView({ data }: { data: DashboardData }) {
  const team = data.teams[0];
  return (
    <>
      <PageHead title="My Teams" detail="Current lineup, budget, free transfers, chips, and manual import controls." />
      <div className="grid two">
        <MetricCard label="Team" value={team.teamName} detail={`${team.assets.length} selected assets`} />
        <MetricCard label="Budget" value={`${formatBudget(team.budgetUsedMillions)} used`} detail={`${formatBudget(team.budgetRemainingMillions)} remaining`} />
      </div>
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Lineup</h2>
        <div className="transfer-list" style={{ marginTop: 12 }}>
          {team.assets.map((asset) => <span className="transfer-pill" key={asset.assetId}>{asset.assetId}</span>)}
        </div>
      </section>
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Chips</h2>
        <div className="status-strip" style={{ marginTop: 12 }}>
          {team.chips.map((chip) => <StatusBadge key={chip.chipName} status={chip.status === "available" ? "ok" : "stale"} label={`${chip.chipName}: ${chip.status}`} />)}
        </div>
      </section>
    </>
  );
}
