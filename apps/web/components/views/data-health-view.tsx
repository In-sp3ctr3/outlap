"use client";

import { ShieldCheck } from "lucide-react";
import { useState } from "react";

import { MetricCard } from "@/components/metric-card";
import { PageHead } from "@/components/page-head";
import { StatusBadge } from "@/components/status";
import type { DashboardData } from "@/lib/api";
import { simulateDataFailure } from "@/lib/api";

export function DataHealthView({ data, onRefresh }: { data: DashboardData; onRefresh: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);

  async function failSource() {
    setBusy(true);
    await simulateDataFailure();
    await onRefresh();
    setBusy(false);
  }

  return (
    <>
      <PageHead
        title="Data Health"
        detail="Connector status, freshness, fallback path, and license notes."
        action={<button className="button warn" type="button" disabled={busy} onClick={failSource}><ShieldCheck size={16} aria-hidden="true" />Simulate failed connector</button>}
      />
      <div className="grid">
        {data.dataSources.map((source) => (
          <section className="panel" key={source.source}>
            <div className="page-head">
              <div>
                <h2>{source.source}</h2>
                <p>{source.message}</p>
              </div>
              <StatusBadge status={source.status} label={source.freshness} />
            </div>
            <div className="grid three">
              <MetricCard label="Connector" value={source.connectorVersion} detail={source.licenseNote} />
              <MetricCard label="Severity" value={source.severity} />
              <MetricCard label="Action" value={source.actionRequired ?? "None"} />
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
