import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.request.post("http://127.0.0.1:8000/api/v1/demo/reset");
  await page.goto("/");
  await page.evaluate(() => window.localStorage.clear());
});

test("demo first run reaches dashboard, optimizer, and fake AI", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await page.getByRole("button", { name: "Generate baseline" }).click();
  await expect(page.getByTestId("recommendation-card")).toBeVisible();

  await page.getByRole("link", { name: "Optimizer" }).click();
  await expect(page.getByRole("heading", { name: "Optimizer" })).toBeVisible();
  await page.getByRole("button", { name: "Run optimizer" }).click();
  await expect(page.getByText("Recommended move").first()).toBeVisible();

  await page.getByRole("link", { name: "AI Strategist" }).click();
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Fantasy account mutation: disabled.")).toBeVisible();
});

test("manual import style flow can filter market and compare recommendations", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await page.getByRole("link", { name: "Market" }).click();
  await page.getByLabel("Filter assets").fill("Foxtrot");
  await expect(page.getByText("Driver Foxtrot")).toBeVisible();

  await page.getByRole("link", { name: "Optimizer" }).click();
  await page.getByLabel("Strategy mode").selectOption("differential");
  await page.getByRole("button", { name: "Run optimizer" }).click();
  await page.getByRole("button", { name: "Compare" }).first().click();
  await expect(page.getByLabel("Comparison drawer")).toBeVisible();
});

test("data source failure shows degraded health and optimizer still works", async ({ page }) => {
  await page.getByRole("button", { name: "Start demo mode" }).click();
  await page.getByRole("link", { name: "Data Health" }).click();
  await page.getByRole("button", { name: "Simulate failed connector" }).click();
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
  await page.getByRole("link", { name: "Settings" }).click();
  await expect(page.getByText("No telemetry is enabled by default.")).toBeVisible();
});
