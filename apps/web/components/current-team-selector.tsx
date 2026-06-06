"use client";

import { CheckCircle2, Copy, RotateCcw, Save, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  AssetChoice,
  REQUIRED_DRIVERS,
  REQUIRED_TEAMS,
  SelectionSummary,
  TEAM_SLOTS,
  TeamDraftFields,
  TeamSlotTabs,
  currentEventId,
  initialDrafts,
  isCompleteDraft,
  selectedAssets,
  type SlotDraft,
} from "@/components/current-team-selector.parts";
import { StateNotice } from "@/components/state-notice";
import { StatusBadge } from "@/components/status";
import type { DashboardData, FantasyAsset } from "@/lib/api";
import { saveOnboardingTeams } from "@/lib/api";
import { assetTypeLabel } from "@/lib/fantasy-assets";

export function CurrentTeamSelector({
  data,
  onImported,
}: {
  data: DashboardData;
  onImported: () => Promise<void>;
}) {
  const market = data.assets;
  const marketReady = market.length > 0;
  const eventId = currentEventId(data);
  const [activeSlot, setActiveSlot] = useState(1);
  const [drafts, setDrafts] = useState<SlotDraft[]>(() => initialDrafts(data.teams));
  const [filter, setFilter] = useState("");
  const [assetType, setAssetType] = useState<"driver" | "constructor">("driver");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const teamsKey = data.teams
    .map((team) => `${team.slot ?? 1}:${team.teamSnapshotId}:${team.assets.map((asset) => asset.assetId).join("|")}`)
    .join(";");

  useEffect(() => {
    setDrafts(initialDrafts(data.teams));
    setMessage(null);
    setError(null);
  }, [teamsKey, data.teams]);

  const assetsById = useMemo(() => new Map(market.map((asset) => [asset.assetId, asset])), [market]);
  const currentDraft = drafts.find((draft) => draft.slot === activeSlot) ?? drafts[0];
  const currentAssets = selectedAssets(currentDraft.selectedIds, assetsById);
  const currentDrivers = currentAssets.filter((asset) => asset.assetType === "driver");
  const currentTeams = currentAssets.filter((asset) => asset.assetType === "constructor");
  const completeDrafts = drafts.filter((draft) => isCompleteDraft(draft, assetsById));
  const canCopyTeamOne = isCompleteDraft(drafts[0], assetsById);
  const canSave = marketReady && Boolean(eventId) && completeDrafts.length === TEAM_SLOTS.length && !busy;
  const visibleAssets = useMemo(() => {
    const normalizedFilter = filter.trim().toLowerCase();
    return market
      .filter((asset) => asset.assetType === assetType)
      .filter((asset) =>
        [asset.displayName, asset.shortName, asset.abbreviation, asset.constructorName, asset.assetId]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(normalizedFilter),
      )
      .sort((a, b) => a.displayName.localeCompare(b.displayName));
  }, [assetType, filter, market]);

  function updateDraft(slot: number, update: (draft: SlotDraft) => SlotDraft) {
    setMessage(null);
    setError(null);
    setDrafts((current) => current.map((draft) => (draft.slot === slot ? update(draft) : draft)));
  }

  function toggleAsset(asset: FantasyAsset) {
    updateDraft(activeSlot, (draft) => {
      if (draft.selectedIds.includes(asset.assetId)) {
        return {
          ...draft,
          selectedIds: draft.selectedIds.filter((assetId) => assetId !== asset.assetId),
        };
      }
      const selected = selectedAssets(draft.selectedIds, assetsById);
      const countForType = selected.filter((item) => item.assetType === asset.assetType).length;
      const limit = asset.assetType === "driver" ? REQUIRED_DRIVERS : REQUIRED_TEAMS;
      if (countForType >= limit) {
        setMessage(`Remove a ${assetTypeLabel(asset.assetType)} from Team ${activeSlot} before adding another.`);
        return draft;
      }
      return { ...draft, selectedIds: [...draft.selectedIds, asset.assetId] };
    });
  }

  function copyTeamOneToAllSlots() {
    const base = drafts[0];
    setDrafts((current) =>
      current.map((draft) => ({
        ...draft,
        selectedIds: [...base.selectedIds],
      })),
    );
    setMessage("Copied Team 1 selections to Teams 2 and 3.");
    setError(null);
  }

  async function saveSelection() {
    if (!eventId) {
      setError("A current event ID is needed before teams can be saved.");
      return;
    }
    if (!canSave) {
      setError("Complete Teams 1, 2, and 3 with 5 drivers and 2 teams each.");
      return;
    }
    setBusy(true);
    try {
      setError(null);
      setMessage(null);
      await saveOnboardingTeams({
        eventId,
        teams: drafts.map((draft) => ({
          slot: draft.slot,
          teamName: draft.teamName.trim() || `Team ${draft.slot}`,
          assetIds: draft.selectedIds,
          costCapMillions: 100,
          freeTransfers: draft.freeTransfers,
          transferPenaltyPoints: 10,
        })),
      });
      setMessage("Saved Teams 1, 2, and 3 from the loaded market catalog.");
      await onImported();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save team selections");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel current-team-selector" aria-labelledby="current-team-selector-title">
      <div className="page-head">
        <div>
          <h2 id="current-team-selector-title">Current team selector</h2>
          <p>Select your three active fantasy teams from the loaded market catalog.</p>
        </div>
        <StatusBadge status={completeDrafts.length === 3 ? "real_current" : "partial"} label={`${completeDrafts.length} / 3 ready`} />
      </div>
      {!marketReady ? (
        <StateNotice tone="empty" title="Market catalog needed">
          Sync the Fantasy catalog or provide market data first. The selector needs asset IDs, names, types, colors, and prices before setup can finish.
        </StateNotice>
      ) : null}
      {marketReady ? (
        <>
          <TeamSlotTabs activeSlot={activeSlot} assetsById={assetsById} drafts={drafts} onSelect={setActiveSlot} />
          <TeamDraftFields activeSlot={activeSlot} currentDraft={currentDraft} onUpdate={updateDraft} />
          <SelectionSummary drivers={currentDrivers} teams={currentTeams} />
          <div className="selector-toolbar">
            <label className="field selector-search">
              Search catalog
              <span className="input-with-icon">
                <Search size={16} aria-hidden="true" />
                <input
                  className="input"
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                  placeholder="Driver or team name"
                />
              </span>
            </label>
            <div className="segmented-control" aria-label="Asset type">
              {(["driver", "constructor"] as const).map((type) => (
                <button
                  aria-pressed={assetType === type}
                  className="button secondary"
                  key={type}
                  type="button"
                  onClick={() => setAssetType(type)}
                >
                  {assetTypeLabel(type)}
                </button>
              ))}
            </div>
          </div>
          {visibleAssets.length === 0 ? (
            <StateNotice tone="empty" title="No catalog assets match this search" />
          ) : (
            <div className="asset-catalog-grid" aria-label="Fantasy market catalog">
              {visibleAssets.map((asset) => (
                <AssetChoice
                  asset={asset}
                  key={asset.assetId}
                  selected={currentDraft.selectedIds.includes(asset.assetId)}
                  onToggle={() => toggleAsset(asset)}
                />
              ))}
            </div>
          )}
          <div className="button-row">
            <button className="button secondary" type="button" disabled={!canCopyTeamOne} onClick={copyTeamOneToAllSlots}>
              <Copy size={16} aria-hidden="true" />
              Copy Team 1 to all
            </button>
            <button className="button" type="button" disabled={!canSave} onClick={saveSelection}>
              <Save size={16} aria-hidden="true" />
              Save all teams
            </button>
            <button
              className="button secondary"
              type="button"
              onClick={() => {
                setDrafts(initialDrafts(data.teams));
                setMessage(null);
                setError(null);
              }}
            >
              <RotateCcw size={16} aria-hidden="true" />
              Reset selection
            </button>
          </div>
        </>
      ) : null}
      {busy ? <StateNotice tone="loading" title="Saving selected teams" /> : null}
      {message ? (
        <div className="empty success" role="status">
          <CheckCircle2 size={16} aria-hidden="true" />
          {message}
        </div>
      ) : null}
      {error ? <StateNotice tone="error" title="Team selection failed">{error}</StateNotice> : null}
    </section>
  );
}
