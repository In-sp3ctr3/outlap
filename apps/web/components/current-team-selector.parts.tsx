"use client";

import type { DashboardData, FantasyAsset, TeamSnapshot } from "@/lib/api";
import { assetAbbreviation, assetDisplayName, assetTeamColor, assetTypeLabel } from "@/lib/fantasy-assets";
import { formatBudget, formatPoints } from "@/lib/format";

export const REQUIRED_DRIVERS = 5;
export const REQUIRED_TEAMS = 2;
export const TEAM_SLOTS = [1, 2, 3] as const;

export type SlotDraft = {
  slot: number;
  teamName: string;
  selectedIds: string[];
  freeTransfers: number;
};

export function AssetChoice({
  asset,
  selected,
  onToggle,
}: {
  asset: FantasyAsset;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      aria-pressed={selected}
      className="asset-choice"
      style={{ borderColor: selected ? assetTeamColor(asset) : undefined }}
      type="button"
      onClick={onToggle}
    >
      <span className="asset-token" style={{ backgroundColor: assetTeamColor(asset) }}>
        {assetAbbreviation(asset)}
      </span>
      <span className="asset-choice-main">
        <strong>{asset.displayName}</strong>
        <span>
          {assetTypeLabel(asset.assetType)}
          {asset.constructorName ? ` · ${asset.constructorName}` : ""}
        </span>
      </span>
      <span className="asset-choice-meta">
        <span>{formatBudget(asset.priceMillions)}</span>
        <span>{asset.fantasyPoints == null ? "points unknown" : formatPoints(asset.fantasyPoints)}</span>
      </span>
    </button>
  );
}

export function SelectionSummary({ drivers, teams }: { drivers: FantasyAsset[]; teams: FantasyAsset[] }) {
  const budgetUsed = [...drivers, ...teams].reduce((total, asset) => total + asset.priceMillions, 0);
  return (
    <div className="selection-summary" aria-live="polite">
      <div>
        <strong>
          {drivers.length} / {REQUIRED_DRIVERS} drivers
        </strong>
        <SelectedAssetPills assets={drivers} />
      </div>
      <div>
        <strong>
          {teams.length} / {REQUIRED_TEAMS} teams
        </strong>
        <SelectedAssetPills assets={teams} />
      </div>
      <div>
        <strong>Budget used</strong>
        <p>{formatBudget(budgetUsed)}</p>
      </div>
      <div>
        <strong>Bank at 100M cap</strong>
        <p>{formatBudget(100 - budgetUsed)}</p>
      </div>
    </div>
  );
}

export function TeamSlotTabs({
  drafts,
  activeSlot,
  assetsById,
  onSelect,
}: {
  drafts: SlotDraft[];
  activeSlot: number;
  assetsById: Map<string, FantasyAsset>;
  onSelect: (slot: number) => void;
}) {
  return (
    <div className="team-slot-tabs" role="tablist" aria-label="Fantasy team slots">
      {drafts.map((draft) => (
        <button
          aria-selected={activeSlot === draft.slot}
          className="button secondary"
          key={draft.slot}
          role="tab"
          type="button"
          onClick={() => onSelect(draft.slot)}
        >
          Team {draft.slot}
          <span className={isCompleteDraft(draft, assetsById) ? "badge good" : "badge warn"}>
            {draftProgressLabel(draft, assetsById)}
          </span>
        </button>
      ))}
    </div>
  );
}

export function TeamDraftFields({
  currentDraft,
  activeSlot,
  onUpdate,
}: {
  currentDraft: SlotDraft;
  activeSlot: number;
  onUpdate: (slot: number, update: (draft: SlotDraft) => SlotDraft) => void;
}) {
  return (
    <div className="grid two">
      <label className="field">
        Team name
        <input
          className="input"
          value={currentDraft.teamName}
          onChange={(event) =>
            onUpdate(activeSlot, (draft) => ({ ...draft, teamName: event.target.value }))
          }
        />
      </label>
      <label className="field">
        Free transfers
        <input
          className="input"
          min={0}
          type="number"
          value={currentDraft.freeTransfers}
          onChange={(event) =>
            onUpdate(activeSlot, (draft) => ({
              ...draft,
              freeTransfers: Math.max(0, Number(event.target.value) || 0),
            }))
          }
        />
      </label>
    </div>
  );
}

export function initialDrafts(teams: TeamSnapshot[]): SlotDraft[] {
  return TEAM_SLOTS.map((slot) => {
    const team = teams.find((item) => item.slot === slot) ?? teams[slot - 1];
    return {
      slot,
      teamName: team?.teamName ?? `Team ${slot}`,
      selectedIds: team?.assets.map((asset) => asset.assetId) ?? [],
      freeTransfers: team?.freeTransfers ?? 2,
    };
  });
}

export function selectedAssets(ids: string[], assetsById: Map<string, FantasyAsset>): FantasyAsset[] {
  return ids.map((assetId) => assetsById.get(assetId)).filter((asset): asset is FantasyAsset => Boolean(asset));
}

export function isCompleteDraft(draft: SlotDraft, assetsById: Map<string, FantasyAsset>): boolean {
  const assets = selectedAssets(draft.selectedIds, assetsById);
  return (
    assets.filter((asset) => asset.assetType === "driver").length === REQUIRED_DRIVERS &&
    assets.filter((asset) => asset.assetType === "constructor").length === REQUIRED_TEAMS
  );
}

export function draftProgressLabel(draft: SlotDraft, assetsById: Map<string, FantasyAsset>): string {
  const assets = selectedAssets(draft.selectedIds, assetsById);
  const drivers = assets.filter((asset) => asset.assetType === "driver").length;
  const teams = assets.filter((asset) => asset.assetType === "constructor").length;
  return `${drivers}/${REQUIRED_DRIVERS} D · ${teams}/${REQUIRED_TEAMS} T`;
}

export function currentEventId(data: DashboardData): string | null {
  return data.teams[0]?.eventId ?? data.appStatus.currentEventId ?? data.race?.eventId ?? null;
}

function SelectedAssetPills({ assets }: { assets: FantasyAsset[] }) {
  if (assets.length === 0) return <p>No selections yet.</p>;
  return (
    <div className="transfer-list">
      {assets.map((asset) => (
        <span className="transfer-pill asset-pill" key={asset.assetId}>
          <span className="mini-swatch" style={{ backgroundColor: assetTeamColor(asset) }} />
          {assetAbbreviation(asset)} · {assetDisplayName(asset)}
        </span>
      ))}
    </div>
  );
}
