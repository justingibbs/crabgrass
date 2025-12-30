import { Page, expect } from "@playwright/test";

/**
 * Page object for the Home page (ideas list)
 */
export class HomePage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/");
  }

  async waitForLoad() {
    await this.page.waitForSelector("h1");
  }

  async clickNewIdea() {
    await this.page.click('a[href="/ideas/new"]');
  }

  async getIdeaCards() {
    return this.page.locator("[data-testid='idea-card']");
  }

  async clickIdeaByTitle(title: string) {
    await this.page.click(`text=${title}`);
  }
}

/**
 * Page object for the New Idea page
 */
export class NewIdeaPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/ideas/new");
  }

  async waitForLoad() {
    await this.page.waitForSelector("textarea");
  }

  async sendChatMessage(message: string) {
    const textarea = this.page.locator("textarea");
    await textarea.fill(message);
    await this.page.click('button[type="submit"]');
  }

  async waitForAssistantResponse() {
    // Wait for loading to finish
    await this.page.waitForFunction(() => {
      const buttons = document.querySelectorAll('button[type="submit"]');
      return buttons.length > 0 && !buttons[0].querySelector(".animate-spin");
    });
  }

  async getMessages() {
    return this.page.locator(".rounded-lg.p-3");
  }
}

/**
 * Page object for the Idea Detail page
 */
export class IdeaDetailPage {
  constructor(private page: Page) {}

  async goto(ideaId: string) {
    await this.page.goto(`/ideas/${ideaId}`);
  }

  async waitForLoad() {
    await this.page.waitForSelector("[data-testid='idea-canvas']", {
      timeout: 10000,
    }).catch(() => {
      // Fallback - wait for canvas sections
      return this.page.waitForSelector(".border.border-border.rounded-lg");
    });
  }

  // Canvas sections
  async getSummarySection() {
    return this.page.locator("text=Summary").first().locator("..");
  }

  async getChallengeSection() {
    return this.page.locator("text=Challenge").first().locator("..");
  }

  async getApproachSection() {
    return this.page.locator("text=Approach").first().locator("..");
  }

  async getCoherentActionsSection() {
    return this.page.locator("text=Coherent Actions").first().locator("..");
  }

  // Editing
  async editSection(sectionTitle: string, newContent: string) {
    const section = this.page.locator(`text=${sectionTitle}`).first().locator("..");
    await section.locator('button[aria-label*="Edit"]').click();
    const textarea = section.locator("textarea");
    await textarea.fill(newContent);
    await section.locator('button[aria-label="Save"]').click();
  }

  // Actions
  async addAction(content: string) {
    await this.page.fill('input[placeholder="Add a new action..."]', content);
    await this.page.click('button:has-text("+")');
  }

  async getActionItems() {
    return this.page.locator("li.flex.items-start.gap-2");
  }

  // Chat
  async sendChatMessage(message: string) {
    const textarea = this.page.locator("textarea");
    await textarea.fill(message);
    await this.page.click('button[type="submit"]');
  }

  async waitForAssistantResponse() {
    await this.page.waitForFunction(() => {
      const buttons = document.querySelectorAll('button[type="submit"]');
      return buttons.length > 0 && !buttons[0].querySelector(".animate-spin");
    });
  }

  // Suggestions
  async getSuggestionBox() {
    return this.page.locator("[data-testid='suggestion-box']");
  }

  async acceptSuggestion() {
    await this.page.click("[data-testid='accept-suggestion']");
  }

  async rejectSuggestion() {
    await this.page.click("[data-testid='reject-suggestion']");
  }

  // Similar Ideas
  async getSimilarIdeasPanel() {
    return this.page.locator("text=Similar Ideas").first().locator("..");
  }

  async getSimilarIdeaItems() {
    return this.page.locator("[data-testid='similar-idea-item']");
  }
}
