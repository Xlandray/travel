import { test, expect } from '@playwright/test';

test.describe('Çorlu Travel (Next.js) E2E Tests', () => {
  test('HomePage loads correctly with Header, Hero section and branding', async ({ page }) => {
    await page.goto('/');

    // Header check
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Logo check - ÇORLU TRAVEL branding
    const logoText = header.getByText('ÇORLU').first();
    await expect(logoText).toBeVisible();

    // Navigation links check in header
    await expect(header.getByRole('link', { name: 'Tüm Turlar' })).toBeVisible();
    await expect(header.getByRole('link', { name: 'Günübirlik' })).toBeVisible();
    await expect(header.getByRole('link', { name: 'İletişim' })).toBeVisible();

    // Hero / page heading check
    const heading = page.locator('h1');
    await expect(heading).toContainText('Yeni Maceralara Yelken Açın');

    // Tours section heading check
    const toursHeading = page.getByRole('heading', { level: 2, name: 'Öne Çıkan Turlar' });
    await expect(toursHeading).toBeVisible();
  });

  test('Navbar links navigate to respective routes', async ({ page }) => {
    await page.goto('/');

    const header = page.locator('header');
    const illetisimLink = header.getByRole('link', { name: 'İletişim' });
    await expect(illetisimLink).toHaveAttribute('href', '/iletisim');
  });
});
