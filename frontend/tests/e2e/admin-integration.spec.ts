import { expect, test } from "@playwright/test";

import { API_BASE } from "./preflight";
import { seedTourWithDeparture } from "./seed";

test.describe("Armonitex Full-Stack E2E Integration Tests", () => {
  test("A tour created through the API is served to the customer site", async ({ request }) => {
    const seeded = await seedTourWithDeparture(request);

    const response = await request.get(`${API_BASE}/tours`);
    expect(response.status()).toBe(200);

    const data = (await response.json()) as { slug: string; departures?: { id: string }[] }[];
    expect(Array.isArray(data)).toBeTruthy();

    const created = data.find((tour) => tour.slug === seeded.tourSlug);
    expect(created, "the seeded tour is missing from the public list").toBeTruthy();
    expect(created?.departures?.some((d) => d.id === seeded.departureId)).toBeTruthy();
  });

  test("An unpublished tour stays off the public list", async ({ request }) => {
    const response = await request.get(`${API_BASE}/tours`);
    const data = (await response.json()) as { is_active?: boolean }[];
    expect(data.every((tour) => tour.is_active !== false)).toBeTruthy();
  });

  test("Refine admin panel reachability check", async ({ page }) => {
    const adminUrl = process.env.ADMIN_PANEL_URL || "http://localhost:5181";
    await page.goto(adminUrl, { timeout: 30000 });
    await expect(page).toHaveTitle(/Armonitex|Refine|React/i);
  });
});
