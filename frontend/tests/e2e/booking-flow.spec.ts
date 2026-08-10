import { test, expect } from '@playwright/test';

// Core booking flow tests: these catch the exact regressions that were
// silently passing before (hardcoded fallback data, missing API wiring,
// ad-hoc dark theme colors violating ADR-0007).
test.describe('Travel Booking Flow E2E Tests', () => {
  test('Home page shows tours fetched from the backend API', async ({ page }) => {
    await page.goto('/');

    // Header branding
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Tour section must render a grid of tour cards
    const tourSection = page.getByRole('heading', { level: 2 }).filter({ hasText: 'Turlar' });
    await expect(tourSection).toBeVisible();

    // At least one tour card must be rendered with an "Detayları İncele" action
    const inspectButtons = page.getByRole('button', { name: /Detayları İncele/i });
    await expect(inspectButtons.first()).toBeVisible();
  });

  test('Checkout page loads real departure data from the API (no fallback)', async ({ page }) => {
    // Fetch a real departure id from the API first
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081/api/v1';
    const toursRes = await page.request.get(`${apiBase}/tours`);
    expect(toursRes.ok()).toBeTruthy();
    const tours = await toursRes.json();
    expect(Array.isArray(tours)).toBeTruthy();
    expect(tours.length).toBeGreaterThan(0);

    const tourWithDeparture = tours.find(
      (t: { departures?: { id: string }[] }) => t.departures && t.departures.length > 0
    );
    expect(tourWithDeparture).toBeTruthy();
    const departureId = tourWithDeparture.departures[0].id;

    await page.goto(`/checkout?departure=${departureId}`);

    // The summary card must show the REAL tour title fetched from the API
    await expect(
      page.getByText('Sefer Özet Kartı')
    ).toBeVisible();
    await expect(
      page.getByText(tourWithDeparture.title)
    ).toBeVisible();

    // Departure dates must be populated (not the hardcoded 2026-09-01 default)
    const departure = tourWithDeparture.departures[0];
    await expect(
      page.getByText(departure.start_date)
    ).toBeVisible();

    // Price must reflect the real tour price, not a hardcoded 6500 default
    const priceText = departure.price.toLocaleString('tr-TR');
    await expect(
      page.getByText(`${priceText} ₺`).first()
    ).toBeVisible();

    // Boarding point selector must be populated
    const boardingSelect = page.locator('select');
    await expect(boardingSelect).toBeVisible();
  });

  test('Checkout page uses semantic design tokens (ADR-0007, no ad-hoc dark theme)', async ({ page }) => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081/api/v1';
    const toursRes = await page.request.get(`${apiBase}/tours`);
    expect(toursRes.ok()).toBeTruthy();
    const tours = await toursRes.json();
    const tourWithDeparture = tours.find(
      (t: { departures?: { id: string }[] }) => t.departures && t.departures.length > 0
    );
    const departureId = tourWithDeparture.departures[0].id;

    await page.goto(`/checkout?departure=${departureId}`);

    const form = page.locator('form');
    await expect(form).toBeVisible();

    // The reservation form must use the token-based card, NOT the dark slate card
    const formClass = await form.getAttribute('class') || '';
    expect(formClass).toContain('card-token');
    expect(formClass).not.toContain('bg-slate-900');
    expect(formClass).not.toContain('bg-slate-950');

    // Heading must use main text token, not white-on-dark
    const heading = page.getByRole('heading', { level: 1 });
    const headingClass = await heading.getAttribute('class') || '';
    expect(headingClass).toContain('text-main-token');
    expect(headingClass).not.toContain('text-white');
  });

  test('Unauthenticated booking attempt redirects to login preserving redirect param', async ({ page }) => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081/api/v1';
    const toursRes = await page.request.get(`${apiBase}/tours`);
    const tours = await toursRes.json();
    const tourWithDeparture = tours.find(
      (t: { departures?: { id: string }[] }) => t.departures && t.departures.length > 0
    );
    const departureId = tourWithDeparture.departures[0].id;

    await page.goto(`/checkout?departure=${departureId}`);

    // Fill the form and submit without a token -> must redirect to login
    await page.locator('input[type="number"]').fill('1');
    await page.getByRole('button', { name: /Rezervasyonu Onayla/i }).click();

    await expect(page).toHaveURL(/\/auth\/login\?redirect=/);
  });
});
