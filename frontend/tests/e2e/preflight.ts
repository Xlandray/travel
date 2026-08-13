import { request } from "@playwright/test";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081/api/v1";
export const WEB_BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:3010";

/**
 * Refuse to run against the wrong stack.
 *
 * The config used to start `next start` on port 3000 with reuseExistingServer,
 * which meant the suite silently ran against whatever happened to be listening
 * there. On a machine with another project running it tested that project
 * instead and reported six failures that had nothing to do with this codebase —
 * and it could just as easily have reported passes. Checking the title up front
 * turns "wrong app" into one clear message instead of a wall of selector
 * errors.
 */
async function assertTravelSite(): Promise<void> {
  const context = await request.newContext();
  try {
    const response = await context.get(WEB_BASE, { timeout: 15_000 });
    if (!response.ok()) {
      throw new Error(`${WEB_BASE} answered ${response.status()}.`);
    }
    const html = await response.text();
    // [\s\S] rather than the `s` flag: the project's tsconfig target predates it.
    const title = /<title>([\s\S]*?)<\/title>/i.exec(html)?.[1] ?? "";
    if (!/travel|tur\b|seyahat/i.test(title)) {
      throw new Error(
        `${WEB_BASE} is serving something else (<title>${title}</title>). ` +
          `Start this project's web container and point PLAYWRIGHT_TEST_BASE_URL at it.`,
      );
    }
  } finally {
    await context.dispose();
  }
}

async function assertApi(): Promise<void> {
  const context = await request.newContext();
  try {
    const response = await context.get(`${API_BASE}/tours`, { timeout: 15_000 });
    if (!response.ok()) {
      throw new Error(`${API_BASE}/tours answered ${response.status()}.`);
    }
  } finally {
    await context.dispose();
  }
}

export default async function globalSetup(): Promise<void> {
  try {
    await assertTravelSite();
    await assertApi();
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(
      `E2E preflight failed: ${detail}\n` +
        `The suite needs the whole stack running: docker compose up -d --build\n` +
        `Web ${WEB_BASE}, API ${API_BASE}.`,
    );
  }
}
