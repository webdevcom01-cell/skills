# Example: E2E Test

Complete Playwright E2E test file for testing the agent management page. This example shows realistic user flows with proper selectors, waits, and assertions.

---

## File: e2e/agents.spec.ts

```typescript
import { test, expect } from "@playwright/test";
import { loginUser, TEST_USER, registerUser } from "./helpers/auth";

// ============================================================================
// TEST DATA
// ============================================================================

const TEST_AGENT = {
  name: "Support Bot",
  description: "Automated customer support agent",
};

const UPDATED_AGENT = {
  name: "Updated Support Bot",
  description: "Enhanced customer support with AI",
};

// ============================================================================
// SETUP
// ============================================================================

test.describe("Agent Management", () => {
  // Ensure user is logged in before each test
  test.beforeEach(async ({ page }) => {
    await loginUser(page, TEST_USER);
  });

  // --------------------------------------------------------------------------
  // Page Load Tests
  // --------------------------------------------------------------------------

  test.describe("Page Load", () => {
    test("should load agents page successfully", async ({ page }) => {
      await page.goto("/agents");

      // Verify page heading
      await expect(
        page.getByRole("heading", { name: "Agents" })
      ).toBeVisible({ timeout: 5000 });

      // Verify navigation is visible
      await expect(page.getByRole("navigation")).toBeVisible();

      // Verify create button is visible
      await expect(
        page.getByRole("button", { name: "Create Agent" })
      ).toBeVisible();
    });

    test("should display agents list", async ({ page }) => {
      await page.goto("/agents");

      // Wait for page to load
      await expect(
        page.getByRole("heading", { name: "Agents" })
      ).toBeVisible();

      // Should show either agents or empty state
      const agentCards = page.getByTestId("agent-card");
      const emptyState = page.getByText(/no agents yet/i);

      // One of these should be visible
      await expect(
        agentCards.first().or(emptyState)
      ).toBeVisible({ timeout: 5000 });
    });

    test("should show loading state initially", async ({ page }) => {
      // Slow down network to see loading state
      await page.route("**/api/agents*", async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await route.continue();
      });

      await page.goto("/agents");

      // Should show skeleton loaders
      await expect(page.getByTestId("skeleton-loader")).toBeVisible();

      // Should hide after load
      await expect(page.getByTestId("skeleton-loader")).not.toBeVisible({
        timeout: 5000,
      });
    });
  });

  // --------------------------------------------------------------------------
  // Create Agent Tests
  // --------------------------------------------------------------------------

  test.describe("Create Agent", () => {
    test("should create new agent successfully", async ({ page }) => {
      await page.goto("/agents");

      // Click create button
      await page.getByRole("button", { name: "Create Agent" }).click();

      // Dialog should open
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(
        page.getByRole("heading", { name: "Create Agent" })
      ).toBeVisible();

      // Fill form
      await page.getByLabel("Name").fill(TEST_AGENT.name);
      await page
        .getByLabel("Description")
        .fill(TEST_AGENT.description);

      // Submit
      await page.getByRole("button", { name: "Create", exact: true }).click();

      // Wait for success toast
      await expect(
        page.getByText(/agent created successfully/i)
      ).toBeVisible({ timeout: 5000 });

      // Dialog should close
      await expect(page.getByRole("dialog")).not.toBeVisible();

      // New agent should appear in list
      await expect(page.getByText(TEST_AGENT.name)).toBeVisible();
    });

    test("should show validation errors for empty form", async ({ page }) => {
      await page.goto("/agents");

      // Open create dialog
      await page.getByRole("button", { name: "Create Agent" }).click();

      // Submit without filling
      await page.getByRole("button", { name: "Create", exact: true }).click();

      // Should show validation errors
      await expect(page.getByText(/name is required/i)).toBeVisible();

      // Dialog should remain open
      await expect(page.getByRole("dialog")).toBeVisible();
    });

    test("should show validation error for short name", async ({ page }) => {
      await page.goto("/agents");

      await page.getByRole("button", { name: "Create Agent" }).click();

      // Fill with invalid data
      await page.getByLabel("Name").fill("AB"); // Too short

      // Try to submit
      await page.getByRole("button", { name: "Create", exact: true }).click();

      // Should show length validation error
      await expect(
        page.getByText(/name must be at least 3 characters/i)
      ).toBeVisible();
    });

    test("should cancel agent creation", async ({ page }) => {
      await page.goto("/agents");

      await page.getByRole("button", { name: "Create Agent" }).click();

      // Fill form
      await page.getByLabel("Name").fill(TEST_AGENT.name);

      // Cancel
      await page.getByRole("button", { name: "Cancel" }).click();

      // Dialog should close
      await expect(page.getByRole("dialog")).not.toBeVisible();

      // Agent should NOT be created
      await expect(page.getByText(TEST_AGENT.name)).not.toBeVisible();
    });

    test("should close dialog with X button", async ({ page }) => {
      await page.goto("/agents");

      await page.getByRole("button", { name: "Create Agent" }).click();

      // Close with X button
      await page.getByLabel("Close").click();

      // Dialog should close
      await expect(page.getByRole("dialog")).not.toBeVisible();
    });
  });

  // --------------------------------------------------------------------------
  // View Agent Tests
  // --------------------------------------------------------------------------

  test.describe("View Agent", () => {
    test("should navigate to agent detail page", async ({ page }) => {
      await page.goto("/agents");

      // Wait for agents to load
      await expect(
        page.getByRole("heading", { name: "Agents" })
      ).toBeVisible();

      // Click on first agent
      const firstAgent = page.getByTestId("agent-card").first();
      await firstAgent.waitFor({ state: "visible" });
      await firstAgent.click();

      // Should navigate to detail page
      await expect(page).toHaveURL(/\/agents\/[a-zA-Z0-9-]+/, {
        timeout: 5000,
      });

      // Agent details should be visible
      await expect(
        page.getByRole("heading", { name: /support bot|faq bot/i })
      ).toBeVisible();
    });

    test("should display agent information", async ({ page }) => {
      await page.goto("/agents");

      // Navigate to first agent
      const firstAgent = page.getByTestId("agent-card").first();
      await firstAgent.waitFor({ state: "visible" });
      const agentName = await firstAgent
        .getByRole("heading")
        .textContent();
      await firstAgent.click();

      // Wait for detail page
      await expect(page).toHaveURL(/\/agents\/[a-zA-Z0-9-]+/);

      // Should show agent name
      await expect(page.getByRole("heading", { name: agentName! })).toBeVisible();

      // Should show tabs or sections
      await expect(
        page.getByRole("tab", { name: /overview|settings|flows/i })
      ).toBeVisible();
    });
  });

  // --------------------------------------------------------------------------
  // Edit Agent Tests
  // --------------------------------------------------------------------------

  test.describe("Edit Agent", () => {
    test("should update agent name and description", async ({ page }) => {
      await page.goto("/agents");

      // Open first agent
      const firstAgent = page.getByTestId("agent-card").first();
      await firstAgent.waitFor({ state: "visible" });
      await firstAgent.click();

      // Wait for detail page
      await expect(page).toHaveURL(/\/agents\/[a-zA-Z0-9-]+/);

      // Open edit dialog (or navigate to edit form)
      await page.getByRole("button", { name: /edit|settings/i }).click();

      // Update name
      const nameInput = page.getByLabel("Name");
      await nameInput.clear();
      await nameInput.fill(UPDATED_AGENT.name);

      // Update description
      const descInput = page.getByLabel("Description");
      await descInput.clear();
      await descInput.fill(UPDATED_AGENT.description);

      // Save
      await page.getByRole("button", { name: /save|update/i }).click();

      // Should show success message
      await expect(
        page.getByText(/agent updated successfully/i)
      ).toBeVisible({ timeout: 5000 });

      // Updated name should be visible
      await expect(
        page.getByRole("heading", { name: UPDATED_AGENT.name })
      ).toBeVisible();
    });

    test("should cancel agent edit", async ({ page }) => {
      await page.goto("/agents");

      const firstAgent = page.getByTestId("agent-card").first();
      await firstAgent.waitFor({ state: "visible" });
      const originalName = await firstAgent
        .getByRole("heading")
        .textContent();
      await firstAgent.click();

      await expect(page).toHaveURL(/\/agents\/[a-zA-Z0-9-]+/);

      // Open edit
      await page.getByRole("button", { name: /edit|settings/i }).click();

      // Change name
      const nameInput = page.getByLabel("Name");
      await nameInput.clear();
      await nameInput.fill("Changed Name");

      // Cancel
      await page.getByRole("button", { name: "Cancel" }).click();

      // Original name should still be displayed
      await expect(
        page.getByRole("heading", { name: originalName! })
      ).toBeVisible();
    });
  });

  // --------------------------------------------------------------------------
  // Delete Agent Tests
  // --------------------------------------------------------------------------

  test.describe("Delete Agent", () => {
    test("should delete agent with confirmation", async ({ page }) => {
      await page.goto("/agents");

      // Get first agent name for verification
      const firstAgent = page.getByTestId("agent-card").first();
      await firstAgent.waitFor({ state: "visible" });
      const agentName = await firstAgent
        .getByRole("heading")
        .textContent();

      // Click delete button on agent card
      const deleteButton = firstAgent.getByRole("button", { name: /delete/i });
      await deleteButton.click();

      // Confirmation dialog should appear
      await expect(page.getByRole("alertdialog")).toBeVisible();
      await expect(page.getByText(/are you sure/i)).toBeVisible();
      await expect(
        page.getByText(/this action cannot be undone/i)
      ).toBeVisible();

      // Confirm deletion
      await page
        .getByRole("button", { name: "Delete", exact: true })
        .click();

      // Should show success message
      await expect(
        page.getByText(/agent deleted successfully/i)
      ).toBeVisible({ timeout: 5000 });

      // Agent should be removed from list
      await expect(page.getByText(agentName!)).not.toBeVisible();
    });

    test("should cancel agent deletion", async ({ page }) => {
      await page.goto("/agents");

      const firstAgent = page.getByTestId("agent-card").first();
      await firstAgent.waitFor({ state: "visible" });
      const agentName = await firstAgent
        .getByRole("heading")
        .textContent();

      // Click delete
      const deleteButton = firstAgent.getByRole("button", { name: /delete/i });
      await deleteButton.click();

      // Confirmation dialog appears
      await expect(page.getByRole("alertdialog")).toBeVisible();

      // Cancel
      await page.getByRole("button", { name: "Cancel" }).click();

      // Dialog should close
      await expect(page.getByRole("alertdialog")).not.toBeVisible();

      // Agent should still be visible
      await expect(page.getByText(agentName!)).toBeVisible();
    });
  });

  // --------------------------------------------------------------------------
  // Search & Filter Tests
  // --------------------------------------------------------------------------

  test.describe("Search & Filter", () => {
    test("should filter agents by search query", async ({ page }) => {
      await page.goto("/agents");

      // Wait for agents to load
      const agentCards = page.getByTestId("agent-card");
      await agentCards.first().waitFor({ state: "visible", timeout: 5000 });

      // Get initial count
      const initialCount = await agentCards.count();

      // Search
      await page.getByPlaceholder(/search/i).fill("support");

      // Wait for filter to apply (debounce)
      await page.waitForTimeout(500);

      // Should show filtered results
      const filteredCount = await agentCards.count();
      expect(filteredCount).toBeLessThanOrEqual(initialCount);

      // Verify results contain search term
      const firstResult = agentCards.first();
      const text = await firstResult.textContent();
      expect(text?.toLowerCase()).toContain("support");
    });

    test("should show empty state for no results", async ({ page }) => {
      await page.goto("/agents");

      // Search for non-existent agent
      await page
        .getByPlaceholder(/search/i)
        .fill("nonexistentagentnamethatdoesnotexist");

      // Wait for filter
      await page.waitForTimeout(500);

      // Should show empty state
      await expect(
        page.getByText(/no agents found|no results/i)
      ).toBeVisible();
    });

    test("should clear search and show all agents", async ({ page }) => {
      await page.goto("/agents");

      // Search
      await page.getByPlaceholder(/search/i).fill("support");
      await page.waitForTimeout(500);

      // Clear search
      await page.getByPlaceholder(/search/i).clear();
      await page.waitForTimeout(500);

      // Should show all agents again
      const agentCards = page.getByTestId("agent-card");
      const count = await agentCards.count();
      expect(count).toBeGreaterThan(0);
    });
  });

  // --------------------------------------------------------------------------
  // Pagination Tests
  // --------------------------------------------------------------------------

  test.describe("Pagination", () => {
    test("should navigate to next page", async ({ page }) => {
      await page.goto("/agents");

      // Check if pagination exists
      const nextButton = page.getByRole("button", { name: /next/i });

      if (await nextButton.isVisible()) {
        // Click next page
        await nextButton.click();

        // URL should update with page param
        await expect(page).toHaveURL(/[?&]page=2/);

        // Should show different agents
        await expect(page.getByTestId("agent-card").first()).toBeVisible();
      } else {
        // Skip test if no pagination (not enough data)
        test.skip();
      }
    });

    test("should navigate to previous page", async ({ page }) => {
      // Start on page 2
      await page.goto("/agents?page=2");

      // Click previous
      const prevButton = page.getByRole("button", { name: /previous/i });
      await prevButton.click();

      // Should go to page 1
      await expect(page).toHaveURL(/\/agents(?:\?page=1)?$/);

      // Should show agents
      await expect(page.getByTestId("agent-card").first()).toBeVisible();
    });
  });

  // --------------------------------------------------------------------------
  // Error Handling Tests
  // --------------------------------------------------------------------------

  test.describe("Error Handling", () => {
    test("should handle API error gracefully", async ({ page }) => {
      // Mock API to return error
      await page.route("**/api/agents*", (route) => {
        route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ error: "Internal server error" }),
        });
      });

      await page.goto("/agents");

      // Should show error message
      await expect(
        page.getByText(/something went wrong|failed to load/i)
      ).toBeVisible({ timeout: 5000 });

      // Should show retry button
      await expect(
        page.getByRole("button", { name: /try again|retry/i })
      ).toBeVisible();
    });

    test("should retry after error", async ({ page }) => {
      let requestCount = 0;

      // Mock API to fail first time, succeed second time
      await page.route("**/api/agents*", (route) => {
        requestCount++;
        if (requestCount === 1) {
          route.fulfill({
            status: 500,
            body: JSON.stringify({ error: "Server error" }),
          });
        } else {
          route.continue();
        }
      });

      await page.goto("/agents");

      // Should show error
      await expect(page.getByText(/failed to load/i)).toBeVisible();

      // Click retry
      await page.getByRole("button", { name: /try again|retry/i }).click();

      // Should load successfully
      await expect(
        page.getByRole("heading", { name: "Agents" })
      ).toBeVisible();
      await expect(
        page.getByTestId("agent-card").first()
      ).toBeVisible({ timeout: 5000 });
    });
  });
});

// ============================================================================
// UNAUTHENTICATED TESTS
// ============================================================================

test.describe("Unauthenticated Access", () => {
  test("should redirect to login when not authenticated", async ({ page }) => {
    // Try to access agents page without logging in
    await page.goto("/agents");

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });

    // Should show login form
    await expect(
      page.getByRole("heading", { name: /sign in|log in/i })
    ).toBeVisible();
  });

  test("should access agents page after login", async ({ page }) => {
    // Try to access protected page
    await page.goto("/agents");

    // Redirects to login
    await expect(page).toHaveURL(/\/login/);

    // Login
    await page.getByLabel("Email").fill(TEST_USER.email);
    await page.getByLabel("Password").fill(TEST_USER.password);
    await page.getByRole("button", { name: /sign in/i }).click();

    // Should redirect to agents page
    await expect(page).toHaveURL(/\/agents/, { timeout: 10000 });
    await expect(
      page.getByRole("heading", { name: "Agents" })
    ).toBeVisible();
  });
});
```

---

## Key Takeaways

1. **Auth setup**: Use `beforeEach` to ensure user is logged in for protected routes
2. **Realistic selectors**: Prefer `getByRole`, `getByLabel`, `getByPlaceholder` for accessibility
3. **Proper waits**: Use `toBeVisible({ timeout })` instead of hard waits
4. **Complete flows**: Test full user journeys (create → verify → delete)
5. **Error scenarios**: Test API errors, validation errors, network failures
6. **Confirmation dialogs**: Test both confirm and cancel paths
7. **Search & filter**: Test filtering, empty states, clearing filters
8. **Pagination**: Test navigation between pages
9. **Loading states**: Mock slow requests to verify loading indicators
10. **Unauthenticated access**: Test redirects and protected routes
11. **Clean assertions**: Check for specific text, URLs, visibility states
12. **Test isolation**: Each test should be independent (no shared state)
