import { expect, test } from "@playwright/test";

const settingsTeamImportPayload = {
  teamSnapshotId: "team_settings_import_01",
  teamName: "Settings Import Team",
  eventId: "event_demo_01",
  slot: 1,
  costCapMillions: 100,
  budgetUsedMillions: 99,
  budgetRemainingMillions: 1,
  freeTransfers: 2,
  transferPenaltyPoints: 10,
  capturedAt: "2026-06-05T00:00:00Z",
  sourceSnapshotId: "snapshot_settings_import_team_01",
  assets: [
    { assetId: "asset_driver_alpha", assetType: "driver", boostMultiplier: 2 },
    { assetId: "asset_driver_bravo", assetType: "driver", boostMultiplier: 1 },
    { assetId: "asset_driver_charlie", assetType: "driver", boostMultiplier: 1 },
    { assetId: "asset_driver_delta", assetType: "driver", boostMultiplier: 1 },
    { assetId: "asset_driver_echo", assetType: "driver", boostMultiplier: 1 },
    { assetId: "asset_constructor_two", assetType: "constructor", boostMultiplier: 1 },
    { assetId: "asset_constructor_three", assetType: "constructor", boostMultiplier: 1 },
  ],
  chips: [
    { chipName: "wildcard", status: "available" },
    { chipName: "limitless", status: "available" },
    { chipName: "no_negative", status: "available" },
    { chipName: "autopilot", status: "available" },
    { chipName: "3x_boost", status: "available" },
    { chipName: "final_fix", status: "available" },
  ],
};

test.beforeEach(async ({ page }) => {
  await page.request.post("http://127.0.0.1:8000/api/v1/demo/reset");
  await page.goto("/");
  await page.evaluate(() => window.localStorage.clear());
});

test("demo first run reaches dashboard, optimizer, and fake AI", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("Next event", { exact: true })).toBeVisible();
  await expect(page.getByText("Budget / transfers")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Data health" })).toBeVisible();
  await page.getByRole("button", { name: "Generate baseline" }).click();
  await expect(page.getByTestId("recommendation-card")).toBeVisible();

  await page.getByRole("link", { name: "Optimizer" }).click();
  await expect(page.getByRole("heading", { name: "Optimizer" })).toBeVisible();
  await page.getByRole("button", { name: "Run optimizer" }).click();
  await expect(page.getByText("Recommended move").first()).toBeVisible();

  await page.getByRole("link", { name: "AI Strategist" }).click();
  await expect(page.getByLabel("Provider")).toContainText("OpenAI");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Fantasy account mutation: disabled.")).toBeVisible();
});

test("setup wizard can import manual team JSON", async ({ page }) => {
  await page.getByRole("button", { name: "Import manual JSON" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("Manual Import Team")).toBeVisible();
});

test("manual import style flow can filter market and compare recommendations", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await page.getByRole("link", { name: "Market" }).click();
  await page.getByLabel("Filter assets").fill("Foxtrot");
  await expect(page.getByText("Driver Foxtrot")).toBeVisible();
  await page.getByLabel("Sort").selectOption("price");
  await expect(page.getByRole("columnheader", { name: "Price" })).toBeVisible();
  await page.getByRole("button", { name: "Lock" }).first().click();
  await expect(page.getByText("Locked")).toBeVisible();
  await page.getByRole("button", { name: "Compare" }).first().click();
  await expect(page.getByLabel("Asset comparison").getByText("Driver Foxtrot")).toBeVisible();
  await page.getByLabel("Filter assets").fill("");
  await page.getByRole("button", { name: "Compare" }).first().click();
  await expect(page.getByLabel("Asset comparison").getByText("Driver Alpha")).toBeVisible();

  await page.getByRole("link", { name: "Optimizer" }).click();
  await page.getByLabel("Strategy mode").selectOption("differential");
  await page.getByRole("button", { name: "Lock current core" }).click();
  await page.getByRole("button", { name: "Ban risky assets" }).click();
  await expect(page.getByText(/Active constraints:/)).toBeVisible();
  await page.getByRole("button", { name: "Run optimizer" }).click();
  await page.getByRole("button", { name: "Compare" }).first().click();
  await expect(page.getByLabel("Comparison drawer")).toBeVisible();
});

test("data source failure shows degraded health and optimizer still works", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await page.getByRole("link", { name: "Data Health" }).click();
  await page.getByRole("button", { name: "Simulate failed connector" }).click();
  await expect(page.getByText("OpenF1 demo connector unavailable")).toBeVisible();

  await page.getByRole("link", { name: "Race Week" }).click();
  await expect(page.getByRole("heading", { name: "Event timeline" })).toBeVisible();
  await expect(page.getByText("Rain chance")).toBeVisible();
  await expect(page.getByText("No penalties pending in demo snapshot.")).toBeVisible();
  await expect(page.getByText("Driver Foxtrot shows strong race simulation pace")).toBeVisible();
  await expect(page.getByText(/openf1: stale/)).toBeVisible();
  await expect(page.getByText("OpenF1 demo connector unavailable")).toBeVisible();

  await page.getByRole("link", { name: "Optimizer" }).click();
  await page.getByRole("button", { name: "Run optimizer" }).click();
  await expect(page.getByText("Data source degraded").first()).toBeVisible();
});

test("provider failure falls back to deterministic recommendation context", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await page.getByRole("link", { name: "AI Strategist" }).click();
  await page.getByLabel("Provider").selectOption("fake-fail");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Provider failed")).toBeVisible();
  await expect(page.getByText("Fantasy account mutation: disabled.")).toBeVisible();
});

test("mobile navigation keeps primary routes reachable", async ({ page, isMobile }) => {
  test.skip(!isMobile, "mobile project only");
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await page.getByRole("link", { name: "League" }).click();
  await expect(page.getByRole("heading", { name: "League" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Catch-up plan" })).toBeVisible();
  await page.getByRole("link", { name: "Settings" }).click();
  await expect(page.getByText("No telemetry is enabled by default.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Data sources" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Import/export" })).toBeVisible();
});

test("settings can test the deterministic provider", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await page.getByRole("link", { name: "Settings" }).click();
  await page
    .locator(".provider-row")
    .filter({ hasText: "Fake deterministic provider" })
    .getByRole("button", { name: "Test" })
    .click();
  await expect(page.getByText("Fake provider is available for deterministic tests.")).toBeVisible();
});

test("settings can import manual team JSON", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await page.getByRole("link", { name: "Settings" }).click();
  await page.getByLabel("Team import JSON").fill(JSON.stringify(settingsTeamImportPayload));
  await page.getByRole("button", { name: "Import team JSON" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("Settings Import Team")).toBeVisible();
});
