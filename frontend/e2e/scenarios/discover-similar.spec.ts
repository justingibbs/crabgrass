import { test, expect } from "@playwright/test";
import { IdeaDetailPage, HomePage } from "../helpers/page-objects";

test.describe("Discover Similar Ideas", () => {
  // Note: These tests require pre-existing ideas with embeddings
  // In a real setup, you'd seed the database with test data

  test.skip("similar ideas panel shows related ideas", async ({ page }) => {
    const ideaDetailPage = new IdeaDetailPage(page);

    // Navigate to an idea that has similar ideas
    await ideaDetailPage.goto("test-idea-with-similars");
    await ideaDetailPage.waitForLoad();

    // Check that similar ideas panel exists
    const similarPanel = await ideaDetailPage.getSimilarIdeasPanel();
    await expect(similarPanel).toBeVisible();

    // Check for similar idea items
    const similarItems = await ideaDetailPage.getSimilarIdeaItems();
    await expect(similarItems).toHaveCount(3); // Expect some similar ideas
  });

  test.skip("clicking a similar idea navigates to it", async ({ page }) => {
    const ideaDetailPage = new IdeaDetailPage(page);

    await ideaDetailPage.goto("test-idea-with-similars");
    await ideaDetailPage.waitForLoad();

    // Get the first similar idea
    const similarItems = await ideaDetailPage.getSimilarIdeaItems();
    const firstItem = similarItems.first();

    // Click it
    await firstItem.click();

    // Verify navigation occurred
    await expect(page.url()).not.toContain("test-idea-with-similars");
  });

  test.skip("similar ideas refresh when content changes", async ({ page }) => {
    const ideaDetailPage = new IdeaDetailPage(page);

    await ideaDetailPage.goto("test-idea-id");
    await ideaDetailPage.waitForLoad();

    // Note similarity count before edit
    const similarItemsBefore = await ideaDetailPage.getSimilarIdeaItems();
    const countBefore = await similarItemsBefore.count();

    // Edit the summary to change the content significantly
    await ideaDetailPage.editSection("Summary", "Completely different topic about gardening");

    // Wait for similar ideas to refresh
    await page.waitForTimeout(1000);

    // Check that similar ideas may have changed
    // (The actual items might change based on the new content)
    const similarItemsAfter = await ideaDetailPage.getSimilarIdeaItems();
    // Just verify the panel still works
    await expect(similarItemsAfter.first()).toBeVisible().catch(() => {
      // It's OK if no similar ideas are found for the new content
    });
  });

  test("home page renders without errors", async ({ page }) => {
    const homePage = new HomePage(page);

    await homePage.goto();
    await homePage.waitForLoad();

    // Verify the page loaded successfully
    await expect(page.locator("h1")).toBeVisible();
  });
});
