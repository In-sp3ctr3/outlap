import { describe, expect, it } from "vitest";

import type { FantasyAsset } from "./api";
import { assetAbbreviation, assetTeamColor, assetTypeLabel } from "./fantasy-assets";

describe("fantasy asset display helpers", () => {
  it("uses API short names before deriving a safe abbreviation", () => {
    const asset = {
      assetId: "asset_driver_one",
      assetType: "driver",
      displayName: "Driver One",
      shortName: "D1",
      priceMillions: 12,
    } satisfies FantasyAsset;

    expect(assetAbbreviation(asset)).toBe("D1");
  });

  it("derives readable driver initials when short names are missing", () => {
    const asset = {
      assetId: "asset_driver_two",
      assetType: "driver",
      displayName: "Driver Two",
      priceMillions: 11,
    } satisfies FantasyAsset;

    expect(assetAbbreviation(asset)).toBe("DT");
  });

  it("uses API-provided team color fields before deterministic fallback colors", () => {
    const asset = {
      assetId: "asset_driver_three",
      assetType: "driver",
      displayName: "Driver Three",
      constructorName: "Example Racing",
      priceMillions: 10,
      teamColor: "#123abc",
    } satisfies FantasyAsset;

    expect(assetTeamColor(asset)).toBe("#123abc");
  });

  it("keeps fallback colors stable per constructor", () => {
    const first = {
      assetId: "asset_driver_alpha",
      assetType: "driver",
      displayName: "Driver Alpha",
      constructorName: "North Star",
      priceMillions: 9,
    } satisfies FantasyAsset;
    const second = {
      assetId: "asset_driver_beta",
      assetType: "driver",
      displayName: "Driver Beta",
      constructorName: "North Star",
      priceMillions: 8,
    } satisfies FantasyAsset;

    expect(assetTeamColor(first)).toBe(assetTeamColor(second));
  });

  it("labels constructors as teams in user-facing selection controls", () => {
    expect(assetTypeLabel("constructor")).toBe("team");
    expect(assetTypeLabel("driver")).toBe("driver");
  });
});
