"use client";

import { AlertTriangle, CheckCircle2, CircleHelp, Database, RefreshCw } from "lucide-react";

import { StatusBadge } from "@/components/status";
import type { DataFreshness } from "@/lib/api";

export function FreshnessPanelCompact({
  items,
  onAction,
}: {
  items: DataFreshness[];
  onAction?: (item: DataFreshness) => void;
}) {
  const blocking = items.filter((item) => item.isBlocking && item.status !== "real_current");
  const current = items.filter((item) => item.status === "real_current").length;
  return (
    <section className="panel freshness-panel" aria-labelledby="freshness-compact-title">
      <div className="page-head">
        <div>
          <h2 id="freshness-compact-title">Data Freshness</h2>
          <p>
            {current} current · {blocking.length} blocking · {items.length - current} need attention
          </p>
        </div>
        <StatusBadge status={blocking.length ? "missing" : "real_current"} label={blocking.length ? "Needs data" : "Ready"} />
      </div>
      <div className="freshness-grid">
        {items
          .filter((item) =>
            [
              "race.current_meeting",
              "fantasy.market",
              "fantasy.user_team",
              "fantasy.scores",
              "fantasy.league",
            ].includes(item.key),
          )
          .map((item) => (
            <FreshnessDomainRow item={item} compact key={item.key} onAction={onAction} />
          ))}
      </div>
    </section>
  );
}

export function FreshnessDomainRow({
  item,
  compact = false,
  onAction,
}: {
  item: DataFreshness;
  compact?: boolean;
  onAction?: (item: DataFreshness) => void;
}) {
  const Icon =
    item.status === "real_current"
      ? CheckCircle2
      : item.status === "missing"
        ? CircleHelp
        : item.status === "error"
          ? AlertTriangle
          : Database;
  return (
    <article className={`freshness-row ${compact ? "compact" : ""}`}>
      <div className="freshness-row-main">
        <Icon size={18} aria-hidden="true" />
        <div>
          <h3>{item.label}</h3>
          <p>{item.message}</p>
        </div>
      </div>
      <div className="freshness-row-meta">
        <StatusBadge status={item.status} label={item.status.replace("_", " ")} />
        <span>{item.recordCount} rows</span>
        {item.lastSuccessAt ? <span>{new Date(item.lastSuccessAt).toLocaleString()}</span> : null}
        {item.remediation && onAction ? (
          <button className="button secondary" type="button" onClick={() => onAction?.(item)}>
            <RefreshCw size={14} aria-hidden="true" />
            {item.remediation.label}
          </button>
        ) : null}
      </div>
    </article>
  );
}
