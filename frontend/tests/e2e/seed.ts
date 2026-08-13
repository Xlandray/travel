import { expect, type APIRequestContext, type Page } from "@playwright/test";

import { API_BASE } from "./preflight";

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || "admin@armonitex.com.tr";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || "Armonitex12345!";

export interface Customer {
  email: string;
  password: string;
}

function unique(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Sign a brand new customer up through the forms and leave them logged in. */
export async function registerAndLogIn(page: Page): Promise<Customer> {
  const customer = {
    email: `${unique("musteri")}@example.com`,
    password: unique("gizli-parola"),
  };

  await page.goto("/auth/register");
  await page.locator('input[name="full_name"]').fill("Test Müşteri");
  await page.locator('input[name="email"]').fill(customer.email);
  await page.locator('input[name="password"]').fill(customer.password);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/auth\/login/);

  await page.locator('input[name="email"]').fill(customer.email);
  await page.locator('input[name="password"]').fill(customer.password);
  await page.locator('button[type="submit"]').click();
  await expect(page).not.toHaveURL(/\/auth\/login/);

  return customer;
}

export interface SeededContent {
  title: string;
  slug: string;
  body: string;
}

/** Publish an article, so a test can check the server actually renders one. */
export async function seedPublishedContent(api: APIRequestContext): Promise<SeededContent> {
  const token = await adminToken(api);
  const suffix = Math.random().toString(36).slice(2, 10);
  const content = {
    title: `E2E Yazısı ${suffix}`,
    slug: `e2e-yazisi-${suffix}`,
    body: `Playwright tarafından yayımlandı (${suffix}).`,
  };

  const response = await api.post(`${API_BASE}/admin/contents`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { ...content, is_published: true },
  });
  if (!response.ok()) {
    throw new Error(`Could not seed content (${response.status()}): ${await response.text()}`);
  }
  return content;
}

export interface SeededDeparture {
  tourTitle: string;
  tourSlug: string;
  departureId: string;
  startDate: string;
  price: number;
}

export async function adminToken(api: APIRequestContext): Promise<string> {
  const response = await api.post(`${API_BASE}/auth/login`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  if (!response.ok()) {
    throw new Error(
      `Admin login failed (${response.status()}). Create the superuser first:\n` +
        `docker compose run --rm --no-deps -e ADMIN_EMAIL -e ADMIN_PASSWORD api ` +
        `python -m app.scripts.bootstrap_superuser`,
    );
  }
  const body = (await response.json()) as { access_token: string };
  return body.access_token;
}

/**
 * Create a tour and a departure for the test to use.
 *
 * These specs used to pick whichever tour happened to be in the database, so
 * they passed on a developer's machine and failed on any clean one — and when
 * they did pass they were asserting against data nobody controlled. A test that
 * needs a bookable tour should make one.
 */
export async function seedTourWithDeparture(api: APIRequestContext): Promise<SeededDeparture> {
  const token = await adminToken(api);
  const headers = { Authorization: `Bearer ${token}` };
  const suffix = Math.random().toString(36).slice(2, 10);
  const price = 4321;
  const startDate = "2030-06-01";

  const tourResponse = await api.post(`${API_BASE}/tours`, {
    headers,
    data: {
      title: `E2E Test Turu ${suffix}`,
      slug: `e2e-test-turu-${suffix}`,
      description: "Playwright tarafından oluşturuldu.",
      days: 3,
      nights: 2,
      is_active: true,
    },
  });
  if (!tourResponse.ok()) {
    throw new Error(`Could not seed a tour (${tourResponse.status()}): ${await tourResponse.text()}`);
  }
  const tour = (await tourResponse.json()) as { id: string; title: string; slug: string };

  const departureResponse = await api.post(`${API_BASE}/tour-departures`, {
    headers,
    data: {
      tour_id: tour.id,
      start_date: startDate,
      end_date: "2030-06-03",
      price,
      total_quota: 20,
      is_active: true,
    },
  });
  if (!departureResponse.ok()) {
    throw new Error(
      `Could not seed a departure (${departureResponse.status()}): ${await departureResponse.text()}`,
    );
  }
  const departure = (await departureResponse.json()) as { id: string };

  return {
    tourTitle: tour.title,
    tourSlug: tour.slug,
    departureId: departure.id,
    startDate,
    price,
  };
}
