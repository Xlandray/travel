import { test, expect } from '@playwright/test';

test.describe('Armonitex Vitrini (Next.js) E2E Tests', () => {
  test('HomePage loads correctly with Header, Hero section and branding', async ({ page }) => {
    await page.goto('/');
    
    // Header check
    const header = page.locator('header');
    await expect(header).toBeVisible();
    
    // Logo check - UPDATE & ARMONITEX SVG badge logo
    const logoText = header.getByText('ARMONİTEX').first();
    await expect(logoText).toBeVisible();

    // Navigation links check in header
    await expect(header.getByRole('link', { name: 'Kurumsal' })).toBeVisible();
    await expect(header.getByRole('link', { name: 'Haberler' })).toBeVisible();
    await expect(header.getByRole('link', { name: 'İletişim' })).toBeVisible();

    // Hero Page heading check
    const heading = page.locator('h1');
    await expect(heading).toContainText('Dijital Baskı');

    // Contents section heading check
    const contentsHeading = page.getByRole('heading', { level: 2, name: 'Güncel Duyurular ve İçerikler' });
    await expect(contentsHeading).toBeVisible();
  });

  test('Navbar links navigate to respective section routes', async ({ page }) => {
    await page.goto('/');
    
    const header = page.locator('header');
    const iceriklerLink = header.getByRole('link', { name: 'Haberler' });
    await expect(iceriklerLink).toHaveAttribute('href', '/icerikler');
  });
});
