import { expect, test, type APIRequestContext } from "@playwright/test";

import { API_BASE } from "./preflight";
import { registerAndLogIn, type Customer } from "./seed";

/**
 * Signing out everywhere, driven the way a worried customer would drive it.
 *
 * The backend suite proves the token version stops a revoked token; what it
 * cannot prove is that the button exists, is reachable, and is wired to the
 * right endpoint. So this test holds a second session for the same account —
 * the stand-in for the one somebody else has — and checks it is dead after the
 * click, which is the only outcome that makes the feature worth having.
 */

async function tokenFor(api: APIRequestContext, customer: Customer): Promise<string> {
  const response = await api.post(`${API_BASE}/auth/login`, {
    data: { email: customer.email, password: customer.password },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  const body = (await response.json()) as { access_token: string };
  return body.access_token;
}

async function statusOfMe(api: APIRequestContext, token: string): Promise<number> {
  const response = await api.get(`${API_BASE}/users/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.status();
}

test.describe("Signing out of every device", () => {
  test("kills a session the customer is not holding", async ({ page, request }) => {
    const customer = await registerAndLogIn(page);

    // The session on the "other device". It is a real login, so it is
    // indistinguishable from the browser's own as far as the API is concerned.
    const elsewhere = await tokenFor(request, customer);
    expect(await statusOfMe(request, elsewhere)).toBe(200);

    await page.goto("/profil/rezervasyonlarim");
    await page.getByRole("button", { name: /Tüm Cihazlarda Oturumu Kapat/i }).click();

    await expect(page).toHaveURL(/\/auth\/login/, { timeout: 15_000 });
    expect(
      await statusOfMe(request, elsewhere),
      "the other device was still signed in after signing out everywhere",
    ).toBe(401);
  });

  test("logging in again afterwards works", async ({ page, request }) => {
    const customer = await registerAndLogIn(page);

    await page.goto("/profil/rezervasyonlarim");
    await page.getByRole("button", { name: /Tüm Cihazlarda Oturumu Kapat/i }).click();
    await expect(page).toHaveURL(/\/auth\/login/, { timeout: 15_000 });

    // Revocation ends sessions; it must not cost the customer their account.
    expect(await statusOfMe(request, await tokenFor(request, customer))).toBe(200);
  });
});
