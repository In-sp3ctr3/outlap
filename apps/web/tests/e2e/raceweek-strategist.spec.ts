import { expect, type Page, test } from "@playwright/test";

const marketCsv = [
  "season,round,asset_kind,asset_name,team_name,price_m,fantasy_points_total,selection_percent",
  "2026,8,driver,Driver One,Example Racing,12.1,44,12%",
  "2026,8,driver,Driver Two,Example Racing,11.2,40,15%",
  "2026,8,driver,Driver Three,Example Racing,10.3,36,18%",
  "2026,8,driver,Driver Four,Example Racing,9.4,30,9%",
  "2026,8,driver,Driver Five,Example Racing,8.5,28,8%",
  "2026,8,constructor,Constructor One,,22.4,68,32%",
  "2026,8,constructor,Constructor Two,,18.4,52,22%",
].join("\n");

test.beforeEach(async ({ page }) => {
  await page.request.post("http://127.0.0.1:8000/api/v1/data/reset", {
    data: { scope: "all" },
  });
  await page.goto("/");
});

test("splash separates demo and real-data entry paths", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Your unofficial race-week fantasy strategy cockpit" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Demo Data/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Real Data/ })).toBeVisible();

  await page.getByRole("button", { name: /Real Data/ }).click();
  await expect(page).toHaveURL(/\/onboarding$/);
  await expect(page.getByRole("heading", { name: "Real Data Setup" })).toBeVisible();
  await expect(page.getByText("No fantasy market prices")).toBeVisible();
});

test("real-data onboarding selects three current teams from market data", async ({ page }) => {
  await chooseRealMode(page);
  await expect(page.getByRole("heading", { name: "Real Data Setup" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Real data onboarding" })).toBeVisible();
  await expect(page.getByText("No fantasy market prices")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Fantasy read-only sync" })).toBeVisible();
  await expect(page.getByText("Fantasy account mutation: disabled")).toBeVisible();

  await importCsv(page, "market_prices", marketCsv);
  await expect(page.getByText("Imported 7 market_prices rows.")).toBeVisible();

  await selectCurrentLineup(page);
  await expect(page.getByRole("tab", { name: /Team 1/ })).toBeVisible();

  await page.getByRole("link", { name: "Dashboard" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Data Freshness" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Generate baseline" })).toBeEnabled();
});

test("market and optimizer use imported real data", async ({ page }) => {
  await chooseRealMode(page);
  await importCsv(page, "market_prices", marketCsv);
  await selectCurrentLineup(page);

  await page.getByRole("link", { name: "Market" }).click();
  await page.getByLabel("Filter assets").fill("Driver One");
  const driverOneRow = page.getByRole("row", { name: /Driver One/ });
  await expect(driverOneRow).toBeVisible();
  await driverOneRow.getByRole("button", { name: /Compare Driver One/ }).click();
  await expect(page.getByLabel("Asset comparison").getByText("Driver One")).toBeVisible();

  await page.getByRole("link", { name: "Optimizer" }).click();
  await expect(page.getByRole("heading", { name: "Optimizer" })).toBeVisible();
  await page.getByRole("button", { name: "Run optimizer" }).click();
  await expect(page.getByTestId("recommendation-card").first()).toBeVisible();
});

test("data freshness center exposes all real-data domains", async ({ page }) => {
  await chooseRealMode(page);
  await importCsv(page, "market_prices", marketCsv);
  await page.getByRole("link", { name: "Data Health" }).click();

  await expect(page.getByRole("heading", { name: "Data Freshness" })).toBeVisible();
  await expect(page.getByText("Fantasy market prices has 7 real imported record")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Race calendar / schedule" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "User fantasy team" })).toBeVisible();
});

test("provider failure falls back without fantasy mutation", async ({ page }) => {
  await page.getByRole("button", { name: /Demo Data/ }).click();
  await page.getByRole("link", { name: "AI Strategist" }).click();
  await page.getByLabel("Provider").selectOption("fake-fail");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Provider failed")).toBeVisible();
  await expect(page.getByText("Fantasy account mutation: disabled.")).toBeVisible();
});

test("mobile navigation keeps primary real-data routes reachable", async ({ page, isMobile }) => {
  test.skip(!isMobile, "mobile project only");
  await chooseRealMode(page);
  await page.getByRole("link", { name: "League" }).click();
  await expect(page.getByRole("heading", { name: "League" })).toBeVisible();
  await expect(page.getByText("No real league table imported")).toBeVisible();
  await page.getByRole("link", { name: "Settings" }).click();
  await expect(page.getByText("No telemetry is enabled by default.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Data freshness" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Import/export" })).toBeVisible();
});

async function chooseRealMode(page: Page) {
  await page.getByRole("button", { name: /Real Data/ }).click();
  await expect(page).toHaveURL(/\/onboarding$/);
}

async function importCsv(page: Page, templateType: string, rawText: string) {
  const wizard = page.getByRole("region", { name: "Manual CSV import" }).last();
  await expect(wizard).toBeVisible();
  await wizard.getByLabel("Template").selectOption(templateType);
  await wizard.getByLabel("CSV text").fill(rawText);
  const previewButton = wizard.getByRole("button", { name: "Preview import" });
  await expect(previewButton).toBeEnabled();
  await previewButton.click();
  await expect(wizard.getByText("No validation messages")).toBeVisible();
  const confirmButton = wizard.getByRole("button", { name: "Confirm import" });
  await expect(confirmButton).toBeEnabled();
  await confirmButton.click();
}

async function selectCurrentLineup(page: Page) {
  const selector = page.getByLabel("Current team selector");
  const catalog = selector.getByLabel("Fantasy market catalog");
  await expect(selector.getByRole("heading", { name: "Current team selector" })).toBeVisible();
  for (const name of ["Driver One", "Driver Two", "Driver Three", "Driver Four", "Driver Five"]) {
    const asset = catalog.getByRole("button", { name: new RegExp(name) });
    await expect(asset).toBeVisible();
    await asset.click();
  }
  await selector.getByRole("button", { name: /^team$/i }).click();
  await expect(selector.getByText("5 / 5 drivers")).toBeVisible();
  await expect(selector.getByText("Driver One")).toBeVisible();
  for (const name of ["Constructor One", "Constructor Two"]) {
    const asset = catalog.getByRole("button", { name: new RegExp(name) });
    await expect(asset).toBeVisible();
    await asset.click();
  }
  const copyButton = selector.getByRole("button", { name: "Copy Team 1 to all" });
  await expect(copyButton).toBeEnabled();
  await copyButton.click();
  const saveButton = selector.getByRole("button", { name: "Save all teams" });
  await expect(saveButton).toBeEnabled();
  await saveButton.click();
  await expect(page.getByText("Saved Teams 1, 2, and 3")).toBeVisible();
}
