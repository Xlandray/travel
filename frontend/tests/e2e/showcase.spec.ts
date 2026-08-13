import { expect, test, type Page } from "@playwright/test";

/**
 * On a phone the navigation lives behind the menu toggle, so a spec that just
 * looks for the links passes on desktop and fails on mobile for a reason that
 * is not a bug. Opening the menu when the toggle is there covers both layouts
 * and exercises the mobile navigation as well.
 */
async function openNavigation(page: Page): Promise<void> {
  const toggle = page.getByRole("button", { name: "Menü" });
  if (await toggle.isVisible()) {
    await toggle.click();
  }
}

test.describe("Çorlu Travel (Next.js) E2E Tests", () => {
  test("HomePage loads correctly with Header, Hero section and branding", async ({ page }) => {
    await page.goto("/");

    const header = page.locator("header");
    await expect(header).toBeVisible();
    await expect(header.getByText("ÇORLU").first()).toBeVisible();

    await openNavigation(page);
    for (const label of ["Tüm Turlar", "Günübirlik", "İletişim"]) {
      await expect(page.getByRole("link", { name: label }).first()).toBeVisible();
    }

    await expect(page.locator("h1")).toContainText("Yeni Maceralara Yelken Açın");
    await expect(page.getByRole("heading", { level: 2, name: "Öne Çıkan Turlar" })).toBeVisible();
  });

  test("Navbar links navigate to respective routes", async ({ page }) => {
    await page.goto("/");

    await openNavigation(page);
    const contact = page.getByRole("link", { name: "İletişim" }).first();
    await expect(contact).toHaveAttribute("href", "/iletisim");

    await contact.click();
    await expect(page).toHaveURL(/\/iletisim/);
  });
});
