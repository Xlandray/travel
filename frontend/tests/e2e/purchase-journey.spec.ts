import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { API_BASE } from "./preflight";
import { adminToken, seedTourWithDeparture, type SeededDeparture } from "./seed";

/**
 * The one journey nobody had ever driven end to end.
 *
 * The backend's booking and payment paths are covered in depth, down to the row
 * locking, but that proves the API is correct — not that a customer can reach
 * it. Every step here is a real click in a real browser, and the last assertion
 * goes back to the API to check the seats actually moved, so a UI that reports
 * success without booking anything cannot pass.
 *
 * It runs on desktop and on a phone viewport, because a booking form that
 * cannot be submitted on a phone is a booking form that does not work.
 */

function unique(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

async function seatsLeft(api: APIRequestContext, departureId: string): Promise<number> {
  const response = await api.get(`${API_BASE}/tour-departures/${departureId}`);
  expect(response.ok(), "could not read the departure back").toBeTruthy();
  const body = (await response.json()) as { available_seats: number };
  return body.available_seats;
}

/** Sign a brand new customer up through the forms and leave them logged in. */
async function registerAndLogIn(page: Page): Promise<string> {
  const email = `${unique("musteri")}@example.com`;
  const password = unique("gizli-parola");

  await page.goto("/auth/register");
  await page.locator('input[name="full_name"]').fill("Test Müşteri");
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/auth\/login/);

  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await expect(page).not.toHaveURL(/\/auth\/login/);

  return email;
}

/** The card form is theatre — nothing is sent to the API — but it is required. */
async function fillCardDetails(page: Page): Promise<void> {
  await page.getByPlaceholder("AD SOYAD").fill("TEST MUSTERI");
  await page.getByPlaceholder("0000 0000 0000 0000").fill("4242424242424242");
  await page.getByPlaceholder("AA/YY").fill("12/30");
  await page.getByPlaceholder("123").fill("123");
}

test.describe("Customer purchase journey", () => {
  let seeded: SeededDeparture;

  test.beforeAll(async ({ playwright }) => {
    const api = await playwright.request.newContext();
    try {
      seeded = await seedTourWithDeparture(api);
    } finally {
      await api.dispose();
    }
  });

  test("register, book seats and pay for them", async ({ page, request }) => {
    const before = await seatsLeft(request, seeded.departureId);

    await registerAndLogIn(page);

    await test.step("book two seats", async () => {
      await page.goto(`/checkout?departure=${seeded.departureId}`);
      await expect(page.getByText(seeded.tourTitle)).toBeVisible();

      await page.locator('input[type="number"]').fill("2");
      // The boarding point selector is deliberately left alone: a customer who
      // accepts what the form already shows them must be able to book.
      await page.getByRole("button", { name: /Rezervasyonu Onayla/i }).click();

      await expect(page).toHaveURL(/\/odeme\?booking=/, { timeout: 15_000 });
    });

    await test.step("pay", async () => {
      await fillCardDetails(page);
      await page.getByRole("button", { name: /Ödemeyi Tamamla/i }).click();
      await expect(page).toHaveURL(/\/profil\/rezervasyonlarim/, { timeout: 20_000 });
    });

    await test.step("the booking is listed as confirmed", async () => {
      await expect(page.getByText(seeded.tourTitle).first()).toBeVisible();
      await expect(page.getByText(/Onayland/i).first()).toBeVisible();
    });

    await test.step("the seats really left the departure", async () => {
      expect(await seatsLeft(request, seeded.departureId)).toBe(before - 2);
    });
  });

  test("a sold out departure tells the customer instead of pretending", async ({
    page,
    request,
  }) => {
    const solo = await seedTourWithDeparture(request);

    const token = await adminToken(request);
    const soldOut = await request.patch(`${API_BASE}/tour-departures/${solo.departureId}`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { available_seats: 0 },
    });
    expect(soldOut.ok(), await soldOut.text()).toBeTruthy();

    await registerAndLogIn(page);
    await page.goto(`/checkout?departure=${solo.departureId}`);
    await page.locator('input[type="number"]').fill("1");
    await page.getByRole("button", { name: /Rezervasyonu Onayla/i }).click();

    await expect(page).not.toHaveURL(/\/odeme/);
    await expect(page.getByText(/kontenjan|yetersiz|dolu/i).first()).toBeVisible();
  });
});
