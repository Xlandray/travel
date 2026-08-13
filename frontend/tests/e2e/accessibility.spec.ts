import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { seedTourWithDeparture, type SeededDeparture } from "./seed";

/**
 * Stage 5's exit criterion asks for basic accessibility checks on the critical
 * journeys, so this scans the pages a customer has to get through to buy
 * something.
 *
 * `critical` violations fail the build. Those are the ones that stop somebody
 * outright — an unlabelled select is a control a screen reader user cannot
 * identify at all.
 *
 * `serious` is reported but does not fail, and today that is entirely
 * colour contrast. It is not an oversight in a component: the brand colour
 * itself (`--color-primary: #14b8a6`) sits at 2.49:1 against white, below even
 * the 3.0:1 large-text threshold, so every use of it is flagged — 55 nodes on
 * the landing page alone. Fixing it means darkening the brand (teal-700
 * `#0f766e` gives 5.47:1 and clears AA for normal text), which is a visual
 * identity decision, not a test fix. Promote `serious` to blocking here once
 * that decision is made.
 */

const BLOCKING = new Set(["critical"]);
const REPORTED = new Set(["serious"]);

function describe(violations: { impact?: string | null; id: string; help: string; nodes: { target: unknown[] }[] }[]): string {
  return violations
    .map(
      (violation) =>
        `[${violation.impact}] ${violation.id} x${violation.nodes.length}: ${violation.help}\n` +
        violation.nodes
          .slice(0, 3)
          .map((node) => `    ${node.target.join(" ")}`)
          .join("\n"),
    )
    .join("\n");
}

async function scan(page: Page, context: string): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();

  const reported = results.violations.filter((v) => REPORTED.has(v.impact ?? ""));
  if (reported.length > 0) {
    test.info().annotations.push({
      type: "accessibility (not blocking)",
      description: `${context}:\n${describe(reported)}`,
    });
  }

  const blocking = results.violations.filter((v) => BLOCKING.has(v.impact ?? ""));
  expect(
    blocking,
    `${context} has blocking accessibility violations:\n${describe(blocking)}`,
  ).toEqual([]);
}

test.describe("Accessibility of the purchase path", () => {
  let seeded: SeededDeparture;

  test.beforeAll(async ({ playwright }) => {
    const api = await playwright.request.newContext();
    try {
      seeded = await seedTourWithDeparture(api);
    } finally {
      await api.dispose();
    }
  });

  test("landing page", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("header")).toBeVisible();
    await scan(page, "the landing page");
  });

  test("tour detail page", async ({ page }) => {
    await page.goto(`/turlar/${seeded.tourSlug}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await scan(page, "the tour detail page");
  });

  test("checkout page", async ({ page }) => {
    await page.goto(`/checkout?departure=${seeded.departureId}`);
    await expect(page.locator("form")).toBeVisible();
    await scan(page, "the checkout page");
  });

  test("login page", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.locator("form")).toBeVisible();
    await scan(page, "the login page");
  });

  test("register page", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.locator("form")).toBeVisible();
    await scan(page, "the register page");
  });
});
