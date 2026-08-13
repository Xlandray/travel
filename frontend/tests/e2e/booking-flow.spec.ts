import { expect, test } from "@playwright/test";

import { seedTourWithDeparture, type SeededDeparture } from "./seed";

// The booking path from the customer's side: a tour is listed, its departure
// details are the real ones from the API, and booking without a session sends
// you to the login page instead of quietly failing.
test.describe("Travel Booking Flow E2E Tests", () => {
  let seeded: SeededDeparture;

  test.beforeAll(async ({ playwright }) => {
    const api = await playwright.request.newContext();
    try {
      seeded = await seedTourWithDeparture(api);
    } finally {
      await api.dispose();
    }
  });

  test("Home page lists a tour that links to its detail page", async ({ page }) => {
    await page.goto("/");

    await expect(page.locator("header")).toBeVisible();
    await expect(page.getByRole("heading", { level: 2 }).filter({ hasText: "Turlar" })).toBeVisible();

    // The call to action is a link, not a button, and its label is translated —
    // so match the destination, which is what the test actually cares about.
    const detailLinks = page.locator('a[href^="/turlar/"]');
    await expect(detailLinks.first()).toBeVisible();
  });

  test("Checkout page shows the seeded departure, not placeholder data", async ({ page }) => {
    await page.goto(`/checkout?departure=${seeded.departureId}`);

    await expect(page.getByText("Sefer Özet Kartı")).toBeVisible();
    await expect(page.getByText(seeded.tourTitle)).toBeVisible();

    // The date is rendered more than once on this page (summary and detail),
    // which is fine — the assertion is that it is the seeded one.
    await expect(page.getByText(seeded.startDate).first()).toBeVisible();

    const priceText = seeded.price.toLocaleString("tr-TR");
    await expect(page.getByText(`${priceText} ₺`).first()).toBeVisible();

    await expect(page.locator("select")).toBeVisible();
  });

  test("Checkout page uses semantic design tokens", async ({ page }) => {
    await page.goto(`/checkout?departure=${seeded.departureId}`);

    const form = page.locator("form");
    await expect(form).toBeVisible();

    const formClass = (await form.getAttribute("class")) || "";
    expect(formClass).toContain("card-token");

    const heading = page.getByRole("heading", { level: 1 });
    const headingClass = (await heading.getAttribute("class")) || "";
    expect(headingClass).toContain("text-main-token");
  });

  test("Booking without a session redirects to login, keeping the redirect target", async ({
    page,
  }) => {
    await page.goto(`/checkout?departure=${seeded.departureId}`);

    await page.locator('input[type="number"]').fill("1");
    await page.getByRole("button", { name: /Rezervasyonu Onayla/i }).click();

    await expect(page).toHaveURL(/\/auth\/login\?redirect=/);
  });
});
