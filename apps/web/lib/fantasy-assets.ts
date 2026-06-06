import type { FantasyAsset } from "./api";

const FALLBACK_TEAM_COLORS = [
  "#2dd4bf",
  "#60a5fa",
  "#f97316",
  "#a78bfa",
  "#f43f5e",
  "#84cc16",
  "#eab308",
  "#38bdf8",
];

export function assetTypeLabel(assetType: FantasyAsset["assetType"]): "driver" | "team" {
  return assetType === "constructor" ? "team" : "driver";
}

export function assetAbbreviation(
  asset: Pick<FantasyAsset, "displayName" | "shortName" | "abbreviation" | "assetType">,
): string {
  const explicit = asset.abbreviation?.trim() || asset.shortName?.trim();
  if (explicit) return explicit.toUpperCase();

  const words = asset.displayName
    .replace(/[^a-zA-Z0-9 ]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
  if (words.length >= 2) {
    return words
      .slice(0, asset.assetType === "constructor" ? 3 : 2)
      .map((word) => word[0])
      .join("")
      .toUpperCase();
  }
  return (words[0] ?? asset.displayName).slice(0, 3).toUpperCase();
}

export function assetTeamColor(asset: FantasyAsset): string {
  const provided = [
    asset.teamColor,
    asset.teamColour,
    asset.constructorColor,
    asset.constructorColour,
    asset.colorHex,
  ].find(isSafeColor);
  if (provided) return provided;

  const key = asset.constructorName ?? asset.displayName ?? asset.assetId;
  return FALLBACK_TEAM_COLORS[hashString(key) % FALLBACK_TEAM_COLORS.length];
}

export function assetDisplayName(asset: FantasyAsset | undefined): string {
  return asset?.displayName ?? "Unknown asset";
}

function isSafeColor(value: string | null | undefined): value is string {
  if (!value) return false;
  return /^#[0-9a-fA-F]{6}$/.test(value.trim());
}

function hashString(value: string): number {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}
