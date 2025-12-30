import { test, expect } from "@playwright/test";
import { NewIdeaPage, IdeaDetailPage } from "../helpers/page-objects";
import { testIdeas } from "../fixtures/test-data";

test.describe("Capture Hunch - New Idea Creation via Chat", () => {
  test("user can describe a hunch and have it captured as a new idea", async ({
    page,
  }) => {
    const newIdeaPage = new NewIdeaPage(page);

    // Navigate to new idea page
    await newIdeaPage.goto();
    await newIdeaPage.waitForLoad();

    // Send initial hunch message
    await newIdeaPage.sendChatMessage(testIdeas.hunch.message);

    // Wait for agent response
    await newIdeaPage.waitForAssistantResponse();

    // Verify we got a response
    const messages = await newIdeaPage.getMessages();
    await expect(messages).toHaveCount(2); // user message + assistant response
  });

  test("home page shows list of existing ideas", async ({ page }) => {
    await page.goto("/");

    // Wait for page to load
    await page.waitForSelector("h1");

    // Check page title
    await expect(page.locator("h1")).toContainText("Ideas");

    // Check for New Idea button/link
    await expect(page.locator('a[href="/ideas/new"]')).toBeVisible();
  });

  test("user can navigate from home to new idea page", async ({ page }) => {
    await page.goto("/");

    // Click New Idea
    await page.click('a[href="/ideas/new"]');

    // Verify we're on new idea page
    await expect(page).toHaveURL("/ideas/new");

    // Verify chat interface is present
    await expect(page.locator("textarea")).toBeVisible();
  });
});
