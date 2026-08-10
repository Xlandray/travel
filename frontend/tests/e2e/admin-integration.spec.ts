import { test, expect } from '@playwright/test';

test.describe('Armonitex Full-Stack E2E Integration Tests', () => {
  test('FastAPI backend health and tours API returns real data', async ({ request }) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081/api/v1';

    // Tours list must actually return HTTP 200 with an array payload
    const response = await request.get(`${apiUrl}/tours`);
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();

    // A production-ready backend must expose at least one tour with a departure
    const tourWithDeparture = data.find(
      (t: { departures?: { id: string }[] }) => t.departures && t.departures.length > 0
    );
    expect(tourWithDeparture, 'Expected at least one tour with an active departure').toBeTruthy();
  });

  test('Refine admin panel reachability check', async ({ page }) => {
    const adminUrl = process.env.ADMIN_PANEL_URL || 'http://localhost:5181';
    await page.goto(adminUrl, { timeout: 30000 });
    await expect(page).toHaveTitle(/Armonitex|Refine|React/i);
  });
});
