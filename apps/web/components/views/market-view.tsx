"use client";

import { Ban, Lock, Scale } from "lucide-react";
import { useMemo, useState } from "react";

import { PageHead } from "@/components/page-head";
import { StateNotice } from "@/components/state-notice";
import type { FantasyAsset } from "@/lib/api";
import { formatBudget, formatPoints, riskLabel } from "@/lib/format";

export function MarketView({ assets }: { assets: FantasyAsset[] }) {
  const [filter, setFilter] = useState("");
  const [sort, setSort] = useState<"points" | "price" | "risk">("points");
  const [lockedAssetIds, setLockedAssetIds] = useState<string[]>([]);
  const [bannedAssetIds, setBannedAssetIds] = useState<string[]>([]);
  const [comparedAssetIds, setComparedAssetIds] = useState<string[]>([]);
  const visible = useMemo(() => {
    return assets
      .filter((asset) => asset.displayName.toLowerCase().includes(filter.toLowerCase()))
      .sort((a, b) => {
        if (sort === "price") return b.priceMillions - a.priceMillions;
        if (sort === "risk") return (b.riskScore ?? 0) - (a.riskScore ?? 0);
        return (b.fantasyPoints ?? 0) - (a.fantasyPoints ?? 0);
      });
  }, [assets, filter, sort]);
  const comparedAssets = useMemo(
    () =>
      comparedAssetIds
        .map((assetId) => assets.find((asset) => asset.assetId === assetId))
        .filter((asset): asset is FantasyAsset => Boolean(asset)),
    [assets, comparedAssetIds],
  );

  function toggleAsset(assetId: string, mode: "ban" | "lock") {
    const setPrimary = mode === "lock" ? setLockedAssetIds : setBannedAssetIds;
    const setOpposite = mode === "lock" ? setBannedAssetIds : setLockedAssetIds;
    setPrimary((current) =>
      current.includes(assetId)
        ? current.filter((item) => item !== assetId)
        : [...current, assetId],
    );
    setOpposite((current) => current.filter((item) => item !== assetId));
  }

  function toggleComparison(assetId: string) {
    setComparedAssetIds((current) => {
      if (current.includes(assetId)) return current.filter((item) => item !== assetId);
      return [...current.slice(-1), assetId];
    });
  }

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
                <td>
                  {riskLabel(asset.riskScore ?? 0)}
                  {lockedAssetIds.includes(asset.assetId) ? <span className="badge">Locked</span> : null}
                  {bannedAssetIds.includes(asset.assetId) ? <span className="badge bad">Banned</span> : null}
                </td>
                <td>
                  <div className="button-row">
                    <button
                      aria-pressed={lockedAssetIds.includes(asset.assetId)}
                      className="button secondary"
                      type="button"
                      onClick={() => toggleAsset(asset.assetId, "lock")}
                    >
                      <Lock size={14} aria-hidden="true" />Lock
                    </button>
                    <button
                      aria-pressed={bannedAssetIds.includes(asset.assetId)}
                      className="button secondary"
                      type="button"
                      onClick={() => toggleAsset(asset.assetId, "ban")}
                    >
                      <Ban size={14} aria-hidden="true" />Ban
                    </button>
                    <button
                      aria-pressed={comparedAssetIds.includes(asset.assetId)}
                      className="button secondary"
                      type="button"
                      onClick={() => toggleComparison(asset.assetId)}
                    >
                      <Scale size={14} aria-hidden="true" />Compare
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {visible.length === 0 ? (
        <StateNotice tone="empty" title="No assets match the current filter" />
      ) : null}
      <section className="panel" aria-label="Asset comparison" style={{ marginTop: 16 }}>
        <h2>Asset comparison</h2>
        {comparedAssets.length === 0 ? (
          <StateNotice tone="empty" title="Select up to two market assets to compare" />
        ) : (
          <div className="comparison-grid">
            {comparedAssets.map((asset) => (
              <article className="comparison-item" key={asset.assetId}>
                <h3>{asset.displayName}</h3>
                <p>Price {formatBudget(asset.priceMillions)}</p>
                <p>Recent points {formatPoints(asset.fantasyPoints ?? 0)}</p>
                <p>Ownership {asset.ownershipPct ?? 0}%</p>
                <p>Risk {riskLabel(asset.riskScore ?? 0)}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
