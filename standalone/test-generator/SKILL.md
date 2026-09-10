---
name: test-generator
description: This skill should be used when the user asks to "generate tests", "write tests for", "create test file", "test this", "add tests", "unit test", "e2e test", "test coverage", or needs comprehensive test files for API routes, runtime handlers, library functions, or E2E flows.
version: 1.0.0
---

# Test Generator

Generate comprehensive test files for API routes, runtime handlers, library functions, and E2E flows. Tests follow project conventions: Vitest for unit/integration, Playwright for E2E.

## Auto-Detection by File Path

Determine test type from the source file location:

| Source Pattern | Test Type | Test Location |
|---|---|---|
| `src/app/api/**/route.ts` | API route test | `src/app/api/**/__tests__/route.test.ts` |
| `src/lib/runtime/handlers/*.ts` | Handler test | `src/lib/runtime/handlers/__tests__/*.test.ts` |
| `src/lib/**/*.ts` | Unit test | `src/lib/**/__tests__/*.test.ts` |
| `src/components/**/*.tsx` | Component test | `src/components/**/__tests__/*.test.tsx` |
| "e2e" keyword | Playwright test | `e2e/*.spec.ts` |

## Coverage Requirements

Every test file must cover these scenarios (where applicable):

- **Happy path** — successful operation with valid input
- **Validation (400)** — missing/invalid fields, boundary values
- **Auth (401)** — unauthenticated user
- **Forbidden (403)** — wrong workspace or insufficient role
- **Not found (404)** — entity does not exist or wrong workspace
- **Conflict (409)** — delete with active dependencies
- **Server error (500)** — database/external service failure
- **Edge cases** — empty lists, pagination boundaries, concurrent operations

## Generation Workflow

1. **Read the source file** to understand the function signature, dependencies, and logic paths.
2. **Identify dependencies** that need mocking (Prisma, auth, external services).
3. **Check existing test patterns** in `src/app/api/agents/__tests__/route.test.ts` and `src/lib/runtime/handlers/__tests__/message-handler.test.ts`.
4. **Generate the test file** with factories, mocks, and comprehensive test cases.

## Vitest Configuration

```typescript
// vitest.config.ts
{
  test: {
    globals: true,
    environment: "node",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    setupFiles: ["./src/test-setup.ts"],
  }
}
```

The setup file at `src/test-setup.ts` provides:
- Environment variables for DATABASE_URL, AUTH_SECRET, AUTH_URL, NEXT_PUBLIC_APP_URL
- Global Prisma mock with all model methods

## API Route Test Pattern

### Mock Declaration Order

Always declare mocks before importing the modules being tested:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest, NextResponse } from "next/server";
import { GET, POST } from "../route";

// Mock dependencies BEFORE importing mocked modules
vi.mock("@/lib/api-auth", () => ({
  requireAuth: vi.fn(),
  isAuthError: vi.fn((result) => result instanceof NextResponse),
}));

vi.mock("@/lib/prisma", () => ({
  prisma: {
    entity: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

// Additional mocks as needed
vi.mock("@/lib/usage", () => ({ checkPlanLimit: vi.fn() }));
vi.mock("@/lib/audit/log", () => ({ logAudit: vi.fn() }));
vi.mock("@/lib/rate-limit", () => ({
  authEndpointRateLimit: vi.fn().mockResolvedValue({ success: true }),
}));

// Import mocked modules for type-safe assertions
import { requireAuth, isAuthError } from "@/lib/api-auth";
import { prisma } from "@/lib/prisma";
```

### Type-Safe Mock Casting

```typescript
const mockRequireAuth = requireAuth as unknown as ReturnType<typeof vi.fn>;
const mockIsAuthError = isAuthError as unknown as ReturnType<typeof vi.fn>;
const mockPrisma = prisma as unknown as {
  entity: {
    findMany: ReturnType<typeof vi.fn>;
    count: ReturnType<typeof vi.fn>;
    create: ReturnType<typeof vi.fn>;
    // ... all used methods
  };
};
```

### Request Factory

```typescript
function makeRequest(
  url: string,
  options?: { method?: string; body?: object }
): NextRequest {
  return new NextRequest(url, {
    method: options?.method || "GET",
    body: options?.body ? JSON.stringify(options.body) : undefined,
    headers: options?.body ? { "content-type": "application/json" } : undefined,
  });
}
```

### Auth Fixture

```typescript
const mockAuth = {
  userId: "user-1",
  workspace: {
    id: "ws-1",
    name: "Test Workspace",
    plan: "PRO" as const,
  },
};

beforeEach(() => {
  vi.clearAllMocks();
  mockIsAuthError.mockImplementation((result) => result instanceof NextResponse);
});
```

### Auth Error Simulation

```typescript
it("returns 401 when unauthenticated", async () => {
  const authError = NextResponse.json(
    { error: "Unauthorized" },
    { status: 401 }
  );
  mockRequireAuth.mockResolvedValue(authError);

  const req = makeRequest("http://localhost:3000/api/entities");
  const response = await GET(req);
  expect(response.status).toBe(401);
});
```

## Handler Test Pattern

### Context Factory

```typescript
import type { RuntimeContext } from "../../types";
import type { FlowNode } from "@/types";

function makeContext(overrides: Partial<RuntimeContext> = {}): RuntimeContext {
  return {
    conversationId: "conv-1",
    agentId: "agent-1",
    workspaceId: "workspace-1",
    flowContent: { nodes: [], edges: [], variables: [] },
    currentNodeId: "node-1",
    variables: { user_name: "Alice", order_id: "12345" },
    messageHistory: [],
    ...overrides,
  };
}
```

### Node Factory

```typescript
function makeNode(overrides: Partial<FlowNode["data"]> = {}): FlowNode {
  return {
    id: "test-node-1",
    type: "node_type",
    position: { x: 0, y: 0 },
    data: {
      label: "Test Node",
      // node-specific default data
      ...overrides,
    },
  };
}
```

### Handler Assertions

```typescript
it("returns expected messages and routing", async () => {
  const result = await handler(makeNode(), makeContext());

  expect(result.messages).toEqual([
    { role: "assistant", content: "Expected message" },
  ]);
  expect(result.nextNodeId).toBe(null);
  expect(result.waitForInput).toBe(false);
});
```

## Playwright E2E Pattern

```typescript
import { test, expect } from "@playwright/test";

test.describe("Feature Name", () => {
  test("page loads correctly", async ({ page }) => {
    await page.goto("/path");
    await expect(page.getByRole("heading", { name: /title/i })).toBeVisible();
  });

  test("user interaction works", async ({ page }) => {
    await page.goto("/path");
    await page.getByLabel("Field").fill("value");
    await page.getByRole("button", { name: /submit/i }).click();
    await expect(page).toHaveURL(/\/expected/);
  });

  test("error state displays correctly", async ({ page }) => {
    await page.goto("/path");
    await page.getByRole("button", { name: /action/i }).click();
    await expect(page.getByText(/error/i)).toBeVisible({ timeout: 5000 });
  });
});
```

## References

See `references/testing-patterns.md` for complete patterns.
See `references/mock-catalog.md` for the full mock catalog.
See `references/e2e-patterns.md` for Playwright patterns and config.
See `examples/` for annotated test file examples.
