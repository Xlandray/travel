import { expect, test } from "@playwright/test";

import { seedPublishedContent } from "./seed";

/**
 * Pages the server renders have to be able to reach the API.
 *
 * They could not. Server components read `NEXT_PUBLIC_API_URL`, which holds
 * the URL a *browser* should use — inside the container that is the container
 * itself, so every one of those fetches was refused. Each call site swallowed
 * the failure and returned an empty list, so nothing anywhere said the API was
 * unreachable: a published article simply 404'd and the list said there were
 * none.
 *
 * Nothing in the suite covered these pages, because every other test drives
 * the browser, where the variable is correct. This one publishes an article
 * through the API and asks the server to render it.
 */

test.describe("Server-rendered pages reach the API", () => {
  test("a published article is served at its own URL", async ({ page, request }) => {
    const content = await seedPublishedContent(request);

    const response = await page.goto(`/icerik/${content.slug}`);

    expect(response?.status(), "the article page did not render").toBe(200);
    await expect(page.getByRole("heading", { name: content.title })).toBeVisible();
    await expect(page.getByText(content.body)).toBeVisible();
  });

  test("an article that does not exist is still a 404", async ({ page }) => {
    // The fix must not turn every miss into a page — a slug nobody published
    // has to stay unfound.
    const response = await page.goto("/icerik/boyle-bir-yazi-yok-12345");
    expect(response?.status()).toBe(404);
  });
});
