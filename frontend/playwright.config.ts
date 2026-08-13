import { defineConfig, devices } from "@playwright/test";

/**
 * The suite runs against the docker compose stack, not a server Playwright
 * starts itself.
 *
 * The previous config ran `next start` on port 3000 with
 * `reuseExistingServer: true`, so it silently tested whatever was already
 * listening there — on a machine with another project up, it tested that
 * project. `globalSetup` now refuses to run unless the web app and the API
 * both answer and the page really is this site.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  retries: 1,
  globalSetup: "./tests/e2e/preflight.ts",
  // Claude ajanının logları analiz edebilmesi için JSON çıktısı zorunludur
  reporter: [["list"], ["json", { outputFile: "agent-report/test-results.json" }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:3010",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
