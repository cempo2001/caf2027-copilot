import { defineConfig } from "@playwright/test";

/**
 * E2E (QA Agent, CLAUDE.md 7.7) — cio SAR tok kroz pravi UI, na oba jezika.
 *
 * Preduslovi (lokalno): docker compose (postgres, redis, minio, clamav),
 * backend na :8765 i frontend na :3000 već pokrenuti. Testovi NE podižu
 * servere sami — rade protiv onoga što developer već ima upaljeno.
 *
 * Browser: na Windows-u se koristi instalirani Microsoft Edge (potpisan,
 * prolazi Application Control), pa `npx playwright install` nije potreban.
 * Drugdje (CI) postaviti E2E_BROWSER_CHANNEL ili instalirati Chromium.
 */
const channel =
  process.env.E2E_BROWSER_CHANNEL || (process.platform === "win32" ? "msedge" : undefined);

export default defineConfig({
  testDir: "./e2e",
  timeout: 5 * 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    channel,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
