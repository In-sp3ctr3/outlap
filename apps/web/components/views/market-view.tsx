"use client";

import { Ban, Lock } from "lucide-react";
import { useMemo, useState } from "react";

import { PageHead } from "@/components/page-head";
import type { FantasyAsset } from "@/lib/api";
import { formatBudget, formatPoints, riskLabel } from "@/lib/format";

export function MarketView({ assets }: { assets: FantasyAsset[] }) {
  const [filter, setFilter] = useState("");
  const [sort, setSort] = useState<"points" | "price" | "risk">("points");
  const visible = useMemo(() => {
    return assets
      .filter((asset) => asset.displayName.toLowerCase().includes(filter.toLowerCase()))
      .sort((a, b) => {
        if (sort === "price") return b.priceMillions - a.priceMillions;
        if (sort === "risk") return (b.riskScore ?? 0) - (a.riskScore ?? 0);
        return (b.fantasyPoints ?? 0) - (a.fantasyPoints ?? 0);
      });
  }, [assets, filter, sort]);

  return (
    <>
      <PageHead title="Market" detail="Prices, projected form inputs, ownership, value, and risk." />
      <section className="panel">
        <div className="grid two">
          <label className="field">
            Filter assets
            <input className="input" value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Driver Alpha" />
          </label>
          <label className="field">
            Sort
            <select className="select" value={sort} onChange={(event) => setSort(event.target.value as typeof sort)}>
              <option value="points">Recent points</option>
              <option value="price">Price</option>
              <option value="risk">Risk</option>
            </select>
          </label>
        </div>
      </section>
      <div className="table-wrap" style={{ marginTop: 16 }}>
        <table>
          <thead>
            <tr><th>Asset</th><th>Type</th><th>Constructor</th><th>Price</th><th>Recent points</th><th>Ownership</th><th>Risk</th><th>Controls</th></tr>
          </thead>
          <tbody>
            {visible.map((asset) => (
              <tr key={asset.assetId}>
                <td>{asset.displayName}</td>
                <td>{asset.assetType}</td>
                <td>{asset.constructorName}</td>
                <td>{formatBudget(asset.priceMillions)}</td>
                <td>{formatPoints(asset.fantasyPoints ?? 0)}</td>
                <td>{asset.ownershipPct ?? 0}%</td>
                <td>{riskLabel(asset.riskScore ?? 0)}</td>
                <td>
                  <div className="button-row">
                    <button className="button secondary" type="button"><Lock size={14} aria-hidden="true" />Lock</button>
                    <button className="button secondary" type="button"><Ban size={14} aria-hidden="true" />Ban</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
