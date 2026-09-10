# Testing Patterns Reference

This document provides complete testing patterns used across the Direct Solutions project.

---

## API Route Test Pattern

Complete structure for testing Next.js App Router API routes with Vitest.

### Full Example Structure

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest, NextResponse } from "next/server";
import { GET, POST, PATCH, DELETE } from "@/app/api/agents/route";

// ============================================================================
// MOCKS
// ============================================================================

// Mock Prisma client
vi.mock("@/lib/prisma", () => ({
  prisma: {
    agent: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      findUniqueOrThrow: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },
    flow: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    $transaction: vi.fn(),
    $queryRaw: vi.fn(),
    $executeRaw: vi.fn(),
  },
}));

// Mock API auth
vi.mock("@/lib/api-auth", () => ({
  requireAuth: vi.fn(),
  isAuthError: vi.fn((result) => result instanceof NextResponse),
  requireRole: vi.fn(),
}));

// Mock usage tracking
vi.mock("@/lib/usage", () => ({
  checkPlanLimit: vi.fn(),
  trackUsage: vi.fn(),
  hasCredits: vi.fn(),
  CREDIT_COSTS: {
    MESSAGE: 1,
    VOICE_MINUTE: 10,
  },
}));

// Mock audit logging
vi.mock("@/lib/audit/log", () => ({
  logAudit: vi.fn(),
}));

// Mock rate limiting
vi.mock("@/lib/rate-limit", () => ({
  authEndpointRateLimit: vi.fn(),
}));

// ============================================================================
// MOCK CASTING
// ============================================================================

import { prisma } from "@/lib/prisma";
import { requireAuth, isAuthError } from "@/lib/api-auth";
import { checkPlanLimit, trackUsage } from "@/lib/usage";
import { logAudit } from "@/lib/audit/log";
import { authEndpointRateLimit } from "@/lib/rate-limit";

const mockPrisma = vi.mocked(prisma);
const mockRequireAuth = vi.mocked(requireAuth);
const mockCheckPlanLimit = vi.mocked(checkPlanLimit);
const mockTrackUsage = vi.mocked(trackUsage);
const mockLogAudit = vi.mocked(logAudit);
const mockRateLimit = vi.mocked(authEndpointRateLimit);

// ============================================================================
// HELPERS
// ============================================================================

function makeRequest(
  method: string,
  url: string,
  body?: unknown
): NextRequest {
  return new NextRequest(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
}

// ============================================================================
// FIXTURES
// ============================================================================

const mockAuth = {
  userId: "user-123",
  workspace: {
    id: "ws-123",
    name: "Test Workspace",
    plan: "PRO" as const,
  },
};

const mockAgent = {
  id: "agent-123",
  workspaceId: "ws-123",
  name: "Support Bot",
  description: "Customer support agent",
  status: "PUBLISHED",
  createdAt: new Date("2024-01-01"),
  updatedAt: new Date("2024-01-01"),
};

// ============================================================================
// TESTS
// ============================================================================

describe("GET /api/agents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return list of agents for authenticated user", async () => {
    // Setup mocks
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.agent.findMany.mockResolvedValue([mockAgent]);
    mockPrisma.agent.count.mockResolvedValue(1);

    // Make request
    const req = makeRequest("GET", "http://localhost:3000/api/agents");
    const response = await GET(req);

    // Assertions
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.agents).toHaveLength(1);
    expect(data.agents[0].id).toBe("agent-123");
    expect(data.pagination.total).toBe(1);

    // Verify auth was checked
    expect(mockRequireAuth).toHaveBeenCalledWith(req);

    // Verify query
    expect(mockPrisma.agent.findMany).toHaveBeenCalledWith({
      where: { workspaceId: "ws-123" },
      orderBy: { createdAt: "desc" },
      skip: 0,
      take: 20,
    });
  });

  it("should return 401 if not authenticated", async () => {
    // Setup auth to return error
    const authError = NextResponse.json(
      { error: "Unauthorized" },
      { status: 401 }
    );
    mockRequireAuth.mockResolvedValue(authError);

    // Make request
    const req = makeRequest("GET", "http://localhost:3000/api/agents");
    const response = await GET(req);

    // Assertions
    expect(response.status).toBe(401);
    const data = await response.json();
    expect(data.error).toBe("Unauthorized");
  });

  it("should handle pagination params", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.agent.findMany.mockResolvedValue([]);
    mockPrisma.agent.count.mockResolvedValue(0);

    const req = makeRequest(
      "GET",
      "http://localhost:3000/api/agents?page=2&limit=10"
    );
    await GET(req);

    expect(mockPrisma.agent.findMany).toHaveBeenCalledWith({
      where: { workspaceId: "ws-123" },
      orderBy: { createdAt: "desc" },
      skip: 10,
      take: 10,
    });
  });

  it("should return 500 on database error", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.agent.findMany.mockRejectedValue(new Error("DB error"));

    const req = makeRequest("GET", "http://localhost:3000/api/agents");
    const response = await GET(req);

    expect(response.status).toBe(500);
    const data = await response.json();
    expect(data.error).toBe("Failed to fetch agents");
  });
});

describe("POST /api/agents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create agent successfully", async () => {
    // Setup mocks
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockCheckPlanLimit.mockResolvedValue({
      allowed: true,
      limit: 10,
      current: 5,
    });
    mockPrisma.agent.create.mockResolvedValue(mockAgent);
    mockTrackUsage.mockResolvedValue(undefined);
    mockLogAudit.mockResolvedValue(undefined);

    // Make request
    const body = {
      name: "Support Bot",
      description: "Customer support agent",
    };
    const req = makeRequest("POST", "http://localhost:3000/api/agents", body);
    const response = await POST(req);

    // Assertions
    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data.id).toBe("agent-123");
    expect(data.name).toBe("Support Bot");

    // Verify plan limit was checked
    expect(mockCheckPlanLimit).toHaveBeenCalledWith(
      mockAuth.workspace,
      "AGENTS",
      1
    );

    // Verify audit log
    expect(mockLogAudit).toHaveBeenCalledWith(
      mockAuth.userId,
      mockAuth.workspace.id,
      {
        action: "CREATE",
        entityType: "AGENT",
        entityId: "agent-123",
      },
      req
    );
  });

  it("should return 400 on validation error", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);

    // Missing required field
    const body = { description: "No name" };
    const req = makeRequest("POST", "http://localhost:3000/api/agents", body);
    const response = await POST(req);

    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data.error).toContain("validation");
  });

  it("should return 403 when plan limit exceeded", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockCheckPlanLimit.mockResolvedValue({
      allowed: false,
      limit: 5,
      current: 5,
    });

    const body = { name: "Support Bot" };
    const req = makeRequest("POST", "http://localhost:3000/api/agents", body);
    const response = await POST(req);

    expect(response.status).toBe(403);
    const data = await response.json();
    expect(data.error).toContain("limit");
  });

  it("should return 409 on duplicate name", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockCheckPlanLimit.mockResolvedValue({
      allowed: true,
      limit: 10,
      current: 5,
    });

    // Simulate unique constraint violation
    const dbError: any = new Error("Unique constraint failed");
    dbError.code = "P2002";
    mockPrisma.agent.create.mockRejectedValue(dbError);

    const body = { name: "Support Bot" };
    const req = makeRequest("POST", "http://localhost:3000/api/agents", body);
    const response = await POST(req);

    expect(response.status).toBe(409);
    const data = await response.json();
    expect(data.error).toContain("already exists");
  });
});

describe("PATCH /api/agents/[id]", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should update agent successfully", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.agent.findUnique.mockResolvedValue(mockAgent);
    mockPrisma.agent.update.mockResolvedValue({
      ...mockAgent,
      name: "Updated Bot",
    });
    mockLogAudit.mockResolvedValue(undefined);

    const body = { name: "Updated Bot" };
    const req = makeRequest(
      "PATCH",
      "http://localhost:3000/api/agents/agent-123",
      body
    );
    const response = await PATCH(req, { params: { id: "agent-123" } });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.name).toBe("Updated Bot");
  });

  it("should return 404 if agent not found", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.agent.findUnique.mockResolvedValue(null);

    const body = { name: "Updated Bot" };
    const req = makeRequest(
      "PATCH",
      "http://localhost:3000/api/agents/agent-999",
      body
    );
    const response = await PATCH(req, { params: { id: "agent-999" } });

    expect(response.status).toBe(404);
    const data = await response.json();
    expect(data.error).toContain("not found");
  });
});

describe("DELETE /api/agents/[id]", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should delete agent successfully", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.agent.findUnique.mockResolvedValue(mockAgent);
    mockPrisma.agent.delete.mockResolvedValue(mockAgent);
    mockLogAudit.mockResolvedValue(undefined);

    const req = makeRequest(
      "DELETE",
      "http://localhost:3000/api/agents/agent-123"
    );
    const response = await DELETE(req, { params: { id: "agent-123" } });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.message).toContain("deleted");
  });

  it("should return 404 if agent not found", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.agent.findUnique.mockResolvedValue(null);

    const req = makeRequest(
      "DELETE",
      "http://localhost:3000/api/agents/agent-999"
    );
    const response = await DELETE(req, { params: { id: "agent-999" } });

    expect(response.status).toBe(404);
  });
});
```

---

## Handler Test Pattern

Complete structure for testing flow node handlers (runtime execution logic).

### Full Example Structure

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { notifyHandler } from "@/lib/runtime/handlers/notify-handler";
import type { RuntimeContext, FlowNode } from "@/types";

// ============================================================================
// MOCKS (if handler uses external dependencies)
// ============================================================================

// Example: if handler uses AI
vi.mock("ai", () => ({
  generateText: vi.fn(),
  embed: vi.fn(),
  embedMany: vi.fn(),
}));

vi.mock("@/lib/usage", () => ({
  trackUsage: vi.fn(),
  hasCredits: vi.fn(),
}));

// ============================================================================
// FACTORIES
// ============================================================================

function makeContext(overrides?: Partial<RuntimeContext>): RuntimeContext {
  return {
    conversationId: "conv-123",
    agentId: "agent-123",
    workspaceId: "ws-123",
    flowContent: { nodes: [], edges: [] },
    currentNodeId: "node-123",
    variables: {
      user_name: "Alice",
      user_email: "alice@example.com",
      order_number: "ORD-12345",
    },
    messageHistory: [
      { role: "user", content: "I need help with my order" },
    ],
    ...overrides,
  };
}

function makeNode(overrides?: Partial<FlowNode>): FlowNode {
  return {
    id: "node-123",
    type: "notify",
    position: { x: 0, y: 0 },
    data: {
      label: "Send Notification",
      message: "Hello {{user_name}}!",
      channel: "email",
      ...overrides?.data,
    },
    ...overrides,
  };
}

// ============================================================================
// TESTS
// ============================================================================

describe("notifyHandler", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should resolve template variables in message", async () => {
    const context = makeContext();
    const node = makeNode({
      data: {
        label: "Welcome",
        message: "Hello {{user_name}}, order {{order_number}} confirmed!",
        channel: "email",
      },
    });

    const result = await notifyHandler(context, node);

    expect(result.messages).toHaveLength(1);
    expect(result.messages[0].content).toBe(
      "Hello Alice, order ORD-12345 confirmed!"
    );
    expect(result.nextNodeId).toBe(null);
    expect(result.waitForInput).toBe(false);
  });

  it("should handle empty message gracefully", async () => {
    const context = makeContext();
    const node = makeNode({
      data: { label: "Empty", message: "", channel: "email" },
    });

    const result = await notifyHandler(context, node);

    expect(result.messages).toHaveLength(0);
    expect(result.nextNodeId).toBe(null);
  });

  it("should preserve variables if not updated", async () => {
    const context = makeContext();
    const node = makeNode();

    const result = await notifyHandler(context, node);

    expect(result.updatedVariables).toBeUndefined();
  });

  it("should handle missing template variables", async () => {
    const context = makeContext({ variables: {} });
    const node = makeNode({
      data: {
        label: "Missing Var",
        message: "Hello {{user_name}}!",
        channel: "email",
      },
    });

    const result = await notifyHandler(context, node);

    // Should replace with empty string or keep placeholder
    expect(result.messages[0].content).toMatch(/Hello /);
  });

  it("should set nextNodeId from edges if configured", async () => {
    const context = makeContext({
      flowContent: {
        nodes: [],
        edges: [{ id: "e1", source: "node-123", target: "node-456" }],
      },
    });
    const node = makeNode();

    const result = await notifyHandler(context, node);

    expect(result.nextNodeId).toBe("node-456");
  });
});
```

### Key Points for Handler Tests

1. **Factories are essential**: `makeContext` and `makeNode` reduce boilerplate
2. **Default sensible values**: Use realistic defaults that work for most tests
3. **Override only what you need**: Pass overrides for specific test cases
4. **Test variable resolution**: Most handlers use template variables
5. **Test flow control**: Verify `nextNodeId`, `waitForInput`, `updatedVariables`
6. **Test edge cases**: Empty values, missing data, malformed input
7. **Mock external deps**: AI, database, external APIs

---

## Unit Test Pattern

For pure library functions and utilities.

### Pure Functions (No Mocking)

```typescript
import { describe, it, expect } from "vitest";
import { resolveTemplate, parseVariables } from "@/lib/utils";

describe("resolveTemplate", () => {
  it("should replace single variable", () => {
    const result = resolveTemplate("Hello {{name}}", { name: "Alice" });
    expect(result).toBe("Hello Alice");
  });

  it("should replace multiple variables", () => {
    const result = resolveTemplate(
      "{{greeting}} {{name}}, order {{order}} is ready!",
      { greeting: "Hi", name: "Bob", order: "123" }
    );
    expect(result).toBe("Hi Bob, order 123 is ready!");
  });

  it("should handle missing variables", () => {
    const result = resolveTemplate("Hello {{name}}", {});
    expect(result).toBe("Hello ");
  });

  it("should handle no variables", () => {
    const result = resolveTemplate("Plain text", {});
    expect(result).toBe("Plain text");
  });
});

describe("parseVariables", () => {
  it("should extract variables from template", () => {
    const vars = parseVariables("Hello {{name}}, your {{item}} is ready!");
    expect(vars).toEqual(["name", "item"]);
  });

  it("should return empty array for no variables", () => {
    const vars = parseVariables("No variables here");
    expect(vars).toEqual([]);
  });

  it("should deduplicate variables", () => {
    const vars = parseVariables("{{name}} {{name}} {{name}}");
    expect(vars).toEqual(["name"]);
  });
});
```

### Functions with Dependencies

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { sendEmail } from "@/lib/email";

// Mock external service
vi.mock("@/lib/email/provider", () => ({
  emailProvider: {
    send: vi.fn(),
  },
}));

import { emailProvider } from "@/lib/email/provider";
const mockProvider = vi.mocked(emailProvider);

describe("sendEmail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should send email via provider", async () => {
    mockProvider.send.mockResolvedValue({ id: "msg-123" });

    const result = await sendEmail({
      to: "user@example.com",
      subject: "Test",
      body: "Hello",
    });

    expect(result.id).toBe("msg-123");
    expect(mockProvider.send).toHaveBeenCalledWith({
      to: "user@example.com",
      subject: "Test",
      body: "Hello",
    });
  });

  it("should throw on provider error", async () => {
    mockProvider.send.mockRejectedValue(new Error("Provider error"));

    await expect(
      sendEmail({
        to: "user@example.com",
        subject: "Test",
        body: "Hello",
      })
    ).rejects.toThrow("Provider error");
  });
});
```

---

## Test Organization Best Practices

### File Structure
- Place tests adjacent to source: `lib/utils.test.ts` next to `lib/utils.ts`
- Or mirror structure: `__tests__/lib/utils.test.ts` mirrors `lib/utils.ts`
- API routes: `app/api/agents/__tests__/route.test.ts`

### Naming Conventions
- Test files: `*.test.ts` or `*.test.tsx`
- Describe blocks: Match the entity being tested
- It blocks: Start with "should" and describe behavior

### Coverage Goals
- API routes: All status codes (200, 201, 400, 401, 403, 404, 409, 500)
- Handlers: Happy path + edge cases + error states
- Utils: All code paths + edge cases

### Mock Hygiene
- Always `vi.clearAllMocks()` in `beforeEach`
- Mock at module level (not inside tests)
- Cast mocks once after import
- Provide realistic mock data
