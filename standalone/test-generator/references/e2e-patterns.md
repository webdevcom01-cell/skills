# E2E Test Patterns Reference

End-to-end testing patterns using Playwright for the Direct Solutions project.

---

## Playwright Configuration

### playwright.config.ts

```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "html",
  timeout: 30_000,
  expect: {
    timeout: 5000,
  },
  use: {
    baseURL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
  ],
  webServer: {
    command: "pnpm dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

---

## Auth Helpers

### e2e/helpers/auth.ts

```typescript
import { Page, expect } from "@playwright/test";

export const TEST_USER = {
  email: "test@example.com",
  password: "Test123!@#",
  name: "Test User",
};

export const TEST_ADMIN = {
  email: "admin@example.com",
  password: "Admin123!@#",
  name: "Admin User",
};

/**
 * Register a new user account
 */
export async function registerUser(
  page: Page,
  user: { email: string; password: string; name: string }
) {
  await page.goto("/signup");

  await page.getByLabel("Name").fill(user.name);
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password", { exact: true }).fill(user.password);
  await page.getByLabel("Confirm Password").fill(user.password);

  await page.getByRole("button", { name: "Create Account" }).click();

  // Wait for redirect to dashboard or onboarding
  await expect(page).toHaveURL(/\/(dashboard|onboarding)/, { timeout: 10000 });
}

/**
 * Log in with existing credentials
 */
export async function loginUser(
  page: Page,
  user: { email: string; password: string }
) {
  await page.goto("/login");

  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);

  await page.getByRole("button", { name: "Sign In" }).click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
}

/**
 * Log out current user
 */
export async function logoutUser(page: Page) {
  // Click user menu
  await page.getByRole("button", { name: /user menu/i }).click();

  // Click logout
  await page.getByRole("menuitem", { name: "Log Out" }).click();

  // Wait for redirect to login
  await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
}

/**
 * Check if user is authenticated by checking for user menu
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  try {
    await page.getByRole("button", { name: /user menu/i }).waitFor({
      timeout: 2000,
      state: "visible",
    });
    return true;
  } catch {
    return false;
  }
}
```

---

## Common Patterns

### 1. Page Navigation & Waiting

```typescript
import { test, expect } from "@playwright/test";

test("should navigate and wait for page load", async ({ page }) => {
  // Navigate
  await page.goto("/agents");

  // Wait for heading to be visible
  await expect(page.getByRole("heading", { name: "Agents" })).toBeVisible({
    timeout: 5000,
  });

  // Wait for specific element
  await page.getByTestId("agent-list").waitFor({ state: "visible" });

  // Wait for network idle
  await page.waitForLoadState("networkidle");
});
```

### 2. Role-Based Selectors (Preferred)

```typescript
test("should use accessible selectors", async ({ page }) => {
  // Headings
  const heading = page.getByRole("heading", { name: "Welcome" });
  await expect(heading).toBeVisible();

  // Buttons
  const button = page.getByRole("button", { name: "Create Agent" });
  await button.click();

  // Links
  const link = page.getByRole("link", { name: "View Details" });
  await link.click();

  // Form fields by label
  const nameInput = page.getByLabel("Agent Name");
  await nameInput.fill("Support Bot");

  // By placeholder
  const searchInput = page.getByPlaceholder("Search agents...");
  await searchInput.fill("support");

  // By text content
  const text = page.getByText("No agents found");
  await expect(text).toBeVisible();
});
```

### 3. Protected Route Testing

```typescript
import { test, expect } from "@playwright/test";

test.describe("Protected Routes", () => {
  test("should redirect to login when not authenticated", async ({ page }) => {
    // Try to access protected page
    await page.goto("/agents");

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });

    // Should show login form
    await expect(page.getByRole("heading", { name: "Sign In" })).toBeVisible();
  });

  test("should access protected page when authenticated", async ({ page }) => {
    // Login first
    await loginUser(page, TEST_USER);

    // Now access protected page
    await page.goto("/agents");

    // Should NOT redirect
    await expect(page).toHaveURL(/\/agents/);
    await expect(page.getByRole("heading", { name: "Agents" })).toBeVisible();
  });
});
```

### 4. Form Testing

```typescript
test("should submit form and show success", async ({ page }) => {
  await page.goto("/agents");

  // Open create dialog
  await page.getByRole("button", { name: "Create Agent" }).click();

  // Wait for dialog
  await expect(page.getByRole("dialog")).toBeVisible();

  // Fill form
  await page.getByLabel("Name").fill("Support Bot");
  await page.getByLabel("Description").fill("Customer support agent");

  // Submit
  await page.getByRole("button", { name: "Create" }).click();

  // Wait for success
  await expect(page.getByText("Agent created successfully")).toBeVisible({
    timeout: 5000,
  });

  // Dialog should close
  await expect(page.getByRole("dialog")).not.toBeVisible();
});
```

### 5. Form Validation Testing

```typescript
test("should show validation errors", async ({ page }) => {
  await page.goto("/agents");
  await page.getByRole("button", { name: "Create Agent" }).click();

  // Submit empty form
  await page.getByRole("button", { name: "Create" }).click();

  // Should show validation errors
  await expect(page.getByText("Name is required")).toBeVisible();
  await expect(page.getByText("Description is required")).toBeVisible();

  // Fill name only
  await page.getByLabel("Name").fill("A");

  // Should show length validation
  await expect(page.getByText("Name must be at least 3 characters")).toBeVisible();
});
```

### 6. Error State Testing

```typescript
test("should handle API errors gracefully", async ({ page }) => {
  // Mock API to return error
  await page.route("**/api/agents", (route) => {
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: "Internal server error" }),
    });
  });

  await page.goto("/agents");

  // Should show error message
  await expect(page.getByText(/something went wrong/i)).toBeVisible();

  // Should show retry button
  const retryButton = page.getByRole("button", { name: "Try Again" });
  await expect(retryButton).toBeVisible();
});
```

### 7. List & Data Table Testing

```typescript
test("should display and interact with data table", async ({ page }) => {
  await page.goto("/agents");

  // Wait for table to load
  const table = page.getByRole("table");
  await expect(table).toBeVisible({ timeout: 5000 });

  // Check table has data
  const rows = page.getByRole("row");
  const rowCount = await rows.count();
  expect(rowCount).toBeGreaterThan(1); // Header + at least 1 data row

  // Click on first data row
  const firstRow = rows.nth(1); // Skip header row
  await firstRow.click();

  // Should navigate to detail page
  await expect(page).toHaveURL(/\/agents\/[a-zA-Z0-9-]+/);
});
```

### 8. Search & Filtering

```typescript
test("should filter results by search", async ({ page }) => {
  await page.goto("/agents");

  // Wait for initial load
  await expect(page.getByRole("heading", { name: "Agents" })).toBeVisible();

  // Get initial count
  const initialRows = await page.getByRole("row").count();

  // Search
  await page.getByPlaceholder("Search agents...").fill("support");

  // Wait for filtered results
  await page.waitForTimeout(500); // Debounce

  // Should have fewer results
  const filteredRows = await page.getByRole("row").count();
  expect(filteredRows).toBeLessThanOrEqual(initialRows);

  // Should show matching results
  await expect(page.getByText(/support/i).first()).toBeVisible();
});
```

### 9. Dialog & Modal Testing

```typescript
test("should open and close dialog", async ({ page }) => {
  await page.goto("/agents");

  // Dialog should not be visible initially
  await expect(page.getByRole("dialog")).not.toBeVisible();

  // Open dialog
  await page.getByRole("button", { name: "Create Agent" }).click();

  // Dialog should be visible
  await expect(page.getByRole("dialog")).toBeVisible();

  // Close with cancel button
  await page.getByRole("button", { name: "Cancel" }).click();

  // Dialog should close
  await expect(page.getByRole("dialog")).not.toBeVisible();

  // Open again
  await page.getByRole("button", { name: "Create Agent" }).click();

  // Close with X button
  await page.getByLabel("Close").click();

  // Dialog should close
  await expect(page.getByRole("dialog")).not.toBeVisible();
});
```

### 10. Confirmation Dialog Testing

```typescript
test("should show confirmation before delete", async ({ page }) => {
  await page.goto("/agents");

  // Click delete on first agent
  await page.getByRole("button", { name: "Delete" }).first().click();

  // Confirmation dialog should appear
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await expect(page.getByText(/are you sure/i)).toBeVisible();

  // Cancel
  await page.getByRole("button", { name: "Cancel" }).click();

  // Dialog should close
  await expect(page.getByRole("alertdialog")).not.toBeVisible();

  // Try delete again
  await page.getByRole("button", { name: "Delete" }).first().click();

  // Confirm
  await page.getByRole("button", { name: "Delete", exact: true }).click();

  // Should show success message
  await expect(page.getByText("Agent deleted successfully")).toBeVisible({
    timeout: 5000,
  });
});
```

### 11. Loading States

```typescript
test("should show loading state", async ({ page }) => {
  // Slow down network to see loading
  await page.route("**/api/agents", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    await route.continue();
  });

  await page.goto("/agents");

  // Should show loading skeleton
  await expect(page.getByTestId("skeleton-loader")).toBeVisible();

  // Should hide after load
  await expect(page.getByTestId("skeleton-loader")).not.toBeVisible({
    timeout: 5000,
  });

  // Content should be visible
  await expect(page.getByRole("heading", { name: "Agents" })).toBeVisible();
});
```

### 12. Toast Notifications

```typescript
test("should show toast notification", async ({ page }) => {
  await page.goto("/agents");

  // Trigger action that shows toast
  await page.getByRole("button", { name: "Create Agent" }).click();
  await page.getByLabel("Name").fill("Support Bot");
  await page.getByRole("button", { name: "Create" }).click();

  // Toast should appear
  const toast = page.getByRole("status").or(page.getByRole("alert"));
  await expect(toast).toBeVisible({ timeout: 5000 });
  await expect(toast).toContainText(/created successfully/i);

  // Toast should auto-dismiss
  await expect(toast).not.toBeVisible({ timeout: 7000 });
});
```

---

## Test Organization

### File Structure

```
e2e/
├── helpers/
│   ├── auth.ts
│   └── fixtures.ts
├── auth.spec.ts
├── agents.spec.ts
├── flows.spec.ts
└── conversations.spec.ts
```

### Test Grouping

```typescript
import { test } from "@playwright/test";

test.describe("Agent Management", () => {
  test.beforeEach(async ({ page }) => {
    // Setup for all tests in this group
    await loginUser(page, TEST_USER);
    await page.goto("/agents");
  });

  test.describe("Create Agent", () => {
    test("should create agent with valid data", async ({ page }) => {
      // Test implementation
    });

    test("should show validation errors", async ({ page }) => {
      // Test implementation
    });
  });

  test.describe("Edit Agent", () => {
    test("should update agent name", async ({ page }) => {
      // Test implementation
    });
  });
});
```

---

## Best Practices

### 1. Use Accessibility Selectors
- Prefer `getByRole`, `getByLabel`, `getByText` over CSS selectors
- Use `getByTestId` only when necessary
- Avoid brittle selectors like class names

### 2. Wait Properly
- Use `toBeVisible()` with timeout instead of `waitForTimeout()`
- Use `waitForLoadState("networkidle")` for complex interactions
- Set appropriate timeouts for async operations

### 3. Handle Flakiness
- Add retries in CI (configured in playwright.config.ts)
- Use proper wait conditions
- Isolate tests (no shared state)
- Clean up after tests

### 4. Test Realistic User Flows
- Start from login
- Navigate like a real user
- Test complete workflows, not just isolated features
- Include error scenarios

### 5. Use Page Object Pattern (Optional)
```typescript
class AgentsPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/agents");
  }

  async createAgent(name: string, description: string) {
    await this.page.getByRole("button", { name: "Create Agent" }).click();
    await this.page.getByLabel("Name").fill(name);
    await this.page.getByLabel("Description").fill(description);
    await this.page.getByRole("button", { name: "Create" }).click();
  }

  async deleteAgent(name: string) {
    const row = this.page.getByRole("row", { name });
    await row.getByRole("button", { name: "Delete" }).click();
    await this.page.getByRole("button", { name: "Confirm" }).click();
  }
}
```
