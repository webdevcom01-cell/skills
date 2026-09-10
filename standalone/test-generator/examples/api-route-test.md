# Example: API Route Test

Complete, production-ready test file for API routes. This example tests `GET /api/templates` and `POST /api/templates` endpoints.

---

## File: app/api/templates/__tests__/route.test.ts

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest, NextResponse } from "next/server";
import { GET, POST } from "@/app/api/templates/route";

// ============================================================================
// MOCKS
// ============================================================================

// Mock Prisma client with template-related models
vi.mock("@/lib/prisma", () => ({
  prisma: {
    template: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    agent: {
      findUnique: vi.fn(),
    },
    workspace: {
      findUnique: vi.fn(),
    },
  },
}));

// Mock authentication
vi.mock("@/lib/api-auth", () => ({
  requireAuth: vi.fn(),
  isAuthError: vi.fn((result) => result instanceof NextResponse),
}));

// Mock usage tracking
vi.mock("@/lib/usage", () => ({
  checkPlanLimit: vi.fn(),
  trackUsage: vi.fn(),
}));

// Mock audit logging
vi.mock("@/lib/audit/log", () => ({
  logAudit: vi.fn(),
}));

// ============================================================================
// IMPORTS & MOCK CASTING
// ============================================================================

import { prisma } from "@/lib/prisma";
import { requireAuth } from "@/lib/api-auth";
import { checkPlanLimit, trackUsage } from "@/lib/usage";
import { logAudit } from "@/lib/audit/log";

const mockPrisma = vi.mocked(prisma);
const mockRequireAuth = vi.mocked(requireAuth);
const mockCheckPlanLimit = vi.mocked(checkPlanLimit);
const mockTrackUsage = vi.mocked(trackUsage);
const mockLogAudit = vi.mocked(logAudit);

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Create a NextRequest for testing
 */
function makeRequest(
  method: string,
  url: string,
  body?: unknown
): NextRequest {
  return new NextRequest(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "User-Agent": "test-agent",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

// ============================================================================
// FIXTURES
// ============================================================================

/**
 * Mock authenticated user context
 */
const mockAuth = {
  userId: "user-123",
  workspace: {
    id: "ws-123",
    name: "Test Workspace",
    plan: "PRO" as const,
  },
};

/**
 * Mock template data
 */
const mockTemplate = {
  id: "tpl-123",
  workspaceId: "ws-123",
  name: "Welcome Message",
  description: "Greet new users",
  category: "ONBOARDING",
  content: {
    nodes: [
      {
        id: "start-1",
        type: "start",
        position: { x: 0, y: 0 },
        data: { label: "Start" },
      },
      {
        id: "msg-1",
        type: "message",
        position: { x: 0, y: 100 },
        data: {
          label: "Welcome",
          message: "Hello {{user_name}}! Welcome to our service.",
        },
      },
    ],
    edges: [
      {
        id: "e1",
        source: "start-1",
        target: "msg-1",
      },
    ],
  },
  tags: ["welcome", "onboarding"],
  isPublic: false,
  usageCount: 5,
  createdAt: new Date("2024-01-01T00:00:00Z"),
  updatedAt: new Date("2024-01-01T00:00:00Z"),
};

/**
 * Mock template list (public + workspace templates)
 */
const mockTemplateList = [
  mockTemplate,
  {
    id: "tpl-456",
    workspaceId: null, // Public template
    name: "FAQ Bot",
    description: "Answer frequently asked questions",
    category: "SUPPORT",
    content: { nodes: [], edges: [] },
    tags: ["faq", "support"],
    isPublic: true,
    usageCount: 150,
    createdAt: new Date("2024-01-01T00:00:00Z"),
    updatedAt: new Date("2024-01-01T00:00:00Z"),
  },
];

// ============================================================================
// TESTS: GET /api/templates
// ============================================================================

describe("GET /api/templates", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return list of templates for authenticated user", async () => {
    // Setup mocks
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.template.findMany.mockResolvedValue(mockTemplateList);
    mockPrisma.template.count.mockResolvedValue(2);

    // Make request
    const req = makeRequest("GET", "http://localhost:3000/api/templates");
    const response = await GET(req);

    // Assertions
    expect(response.status).toBe(200);
    const data = await response.json();

    expect(data.templates).toHaveLength(2);
    expect(data.templates[0].id).toBe("tpl-123");
    expect(data.pagination).toEqual({
      total: 2,
      page: 1,
      limit: 20,
      pages: 1,
    });

    // Verify auth was checked
    expect(mockRequireAuth).toHaveBeenCalledWith(req);

    // Verify database query included both public and workspace templates
    expect(mockPrisma.template.findMany).toHaveBeenCalledWith({
      where: {
        OR: [
          { isPublic: true },
          { workspaceId: "ws-123" },
        ],
      },
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
    const req = makeRequest("GET", "http://localhost:3000/api/templates");
    const response = await GET(req);

    // Assertions
    expect(response.status).toBe(401);
    const data = await response.json();
    expect(data.error).toBe("Unauthorized");

    // Prisma should not be called
    expect(mockPrisma.template.findMany).not.toHaveBeenCalled();
  });

  it("should handle pagination parameters", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.template.findMany.mockResolvedValue([]);
    mockPrisma.template.count.mockResolvedValue(0);

    // Request page 2 with limit 10
    const req = makeRequest(
      "GET",
      "http://localhost:3000/api/templates?page=2&limit=10"
    );
    await GET(req);

    // Should calculate correct skip value
    expect(mockPrisma.template.findMany).toHaveBeenCalledWith({
      where: expect.any(Object),
      orderBy: { createdAt: "desc" },
      skip: 10, // (page 2 - 1) * limit 10
      take: 10,
    });
  });

  it("should filter by category", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.template.findMany.mockResolvedValue([mockTemplate]);
    mockPrisma.template.count.mockResolvedValue(1);

    const req = makeRequest(
      "GET",
      "http://localhost:3000/api/templates?category=ONBOARDING"
    );
    await GET(req);

    expect(mockPrisma.template.findMany).toHaveBeenCalledWith({
      where: {
        OR: [{ isPublic: true }, { workspaceId: "ws-123" }],
        category: "ONBOARDING",
      },
      orderBy: { createdAt: "desc" },
      skip: 0,
      take: 20,
    });
  });

  it("should filter by search query", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.template.findMany.mockResolvedValue([mockTemplate]);
    mockPrisma.template.count.mockResolvedValue(1);

    const req = makeRequest(
      "GET",
      "http://localhost:3000/api/templates?search=welcome"
    );
    await GET(req);

    expect(mockPrisma.template.findMany).toHaveBeenCalledWith({
      where: {
        OR: [{ isPublic: true }, { workspaceId: "ws-123" }],
        AND: [
          {
            OR: [
              { name: { contains: "welcome", mode: "insensitive" } },
              { description: { contains: "welcome", mode: "insensitive" } },
            ],
          },
        ],
      },
      orderBy: { createdAt: "desc" },
      skip: 0,
      take: 20,
    });
  });

  it("should return empty list when no templates found", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.template.findMany.mockResolvedValue([]);
    mockPrisma.template.count.mockResolvedValue(0);

    const req = makeRequest("GET", "http://localhost:3000/api/templates");
    const response = await GET(req);

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.templates).toEqual([]);
    expect(data.pagination.total).toBe(0);
  });

  it("should return 500 on database error", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockPrisma.template.findMany.mockRejectedValue(
      new Error("Database connection failed")
    );

    const req = makeRequest("GET", "http://localhost:3000/api/templates");
    const response = await GET(req);

    expect(response.status).toBe(500);
    const data = await response.json();
    expect(data.error).toBe("Failed to fetch templates");
  });
});

// ============================================================================
// TESTS: POST /api/templates
// ============================================================================

describe("POST /api/templates", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create template successfully", async () => {
    // Setup mocks
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockCheckPlanLimit.mockResolvedValue({
      allowed: true,
      limit: 20,
      current: 5,
    });
    mockPrisma.template.create.mockResolvedValue(mockTemplate);
    mockTrackUsage.mockResolvedValue(undefined);
    mockLogAudit.mockResolvedValue(undefined);

    // Request body
    const body = {
      name: "Welcome Message",
      description: "Greet new users",
      category: "ONBOARDING",
      content: {
        nodes: [
          {
            id: "start-1",
            type: "start",
            position: { x: 0, y: 0 },
            data: { label: "Start" },
          },
        ],
        edges: [],
      },
      tags: ["welcome", "onboarding"],
    };

    // Make request
    const req = makeRequest("POST", "http://localhost:3000/api/templates", body);
    const response = await POST(req);

    // Assertions
    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data.id).toBe("tpl-123");
    expect(data.name).toBe("Welcome Message");

    // Verify plan limit was checked
    expect(mockCheckPlanLimit).toHaveBeenCalledWith(
      mockAuth.workspace,
      "TEMPLATES",
      1
    );

    // Verify template was created
    expect(mockPrisma.template.create).toHaveBeenCalledWith({
      data: {
        workspaceId: "ws-123",
        name: "Welcome Message",
        description: "Greet new users",
        category: "ONBOARDING",
        content: body.content,
        tags: ["welcome", "onboarding"],
        isPublic: false,
      },
    });

    // Verify audit log
    expect(mockLogAudit).toHaveBeenCalledWith(
      mockAuth.userId,
      mockAuth.workspace.id,
      {
        action: "CREATE",
        entityType: "TEMPLATE",
        entityId: "tpl-123",
        metadata: { name: "Welcome Message" },
      },
      req
    );
  });

  it("should return 400 on validation error - missing name", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);

    // Missing required field
    const body = {
      description: "Missing name",
      content: { nodes: [], edges: [] },
    };

    const req = makeRequest("POST", "http://localhost:3000/api/templates", body);
    const response = await POST(req);

    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data.error).toContain("validation");
    expect(data.details).toBeDefined();

    // Database should not be called
    expect(mockPrisma.template.create).not.toHaveBeenCalled();
  });

  it("should return 400 on validation error - invalid content", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);

    // Invalid content structure
    const body = {
      name: "Test Template",
      content: { invalid: "structure" }, // Missing nodes and edges
    };

    const req = makeRequest("POST", "http://localhost:3000/api/templates", body);
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

    const body = {
      name: "Test Template",
      content: { nodes: [], edges: [] },
    };

    const req = makeRequest("POST", "http://localhost:3000/api/templates", body);
    const response = await POST(req);

    expect(response.status).toBe(403);
    const data = await response.json();
    expect(data.error).toContain("Template limit reached");
    expect(data.limit).toBe(5);
    expect(data.current).toBe(5);

    // Database should not be called
    expect(mockPrisma.template.create).not.toHaveBeenCalled();
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
    dbError.meta = { target: ["workspaceId", "name"] };
    mockPrisma.template.create.mockRejectedValue(dbError);

    const body = {
      name: "Duplicate Template",
      content: { nodes: [], edges: [] },
    };

    const req = makeRequest("POST", "http://localhost:3000/api/templates", body);
    const response = await POST(req);

    expect(response.status).toBe(409);
    const data = await response.json();
    expect(data.error).toContain("already exists");
  });

  it("should return 500 on database error", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockCheckPlanLimit.mockResolvedValue({
      allowed: true,
      limit: 10,
      current: 5,
    });
    mockPrisma.template.create.mockRejectedValue(
      new Error("Database connection failed")
    );

    const body = {
      name: "Test Template",
      content: { nodes: [], edges: [] },
    };

    const req = makeRequest("POST", "http://localhost:3000/api/templates", body);
    const response = await POST(req);

    expect(response.status).toBe(500);
    const data = await response.json();
    expect(data.error).toBe("Failed to create template");
  });

  it("should handle optional fields", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockCheckPlanLimit.mockResolvedValue({
      allowed: true,
      limit: 10,
      current: 5,
    });
    mockPrisma.template.create.mockResolvedValue(mockTemplate);
    mockLogAudit.mockResolvedValue(undefined);

    // Minimal body (only required fields)
    const body = {
      name: "Minimal Template",
      content: { nodes: [], edges: [] },
    };

    const req = makeRequest("POST", "http://localhost:3000/api/templates", body);
    const response = await POST(req);

    expect(response.status).toBe(201);

    // Verify defaults were applied
    expect(mockPrisma.template.create).toHaveBeenCalledWith({
      data: {
        workspaceId: "ws-123",
        name: "Minimal Template",
        description: "",
        category: "CUSTOM",
        content: body.content,
        tags: [],
        isPublic: false,
      },
    });
  });

  it("should sanitize template name", async () => {
    mockRequireAuth.mockResolvedValue(mockAuth);
    mockCheckPlanLimit.mockResolvedValue({
      allowed: true,
      limit: 10,
      current: 5,
    });
    mockPrisma.template.create.mockResolvedValue(mockTemplate);
    mockLogAudit.mockResolvedValue(undefined);

    // Name with extra whitespace
    const body = {
      name: "  Template  with   spaces  ",
      content: { nodes: [], edges: [] },
    };

    const req = makeRequest("POST", "http://localhost:3000/api/templates", body);
    await POST(req);

    // Should trim and normalize whitespace
    expect(mockPrisma.template.create).toHaveBeenCalledWith({
      data: expect.objectContaining({
        name: "Template with spaces",
      }),
    });
  });
});
```

---

## Key Takeaways

1. **Complete mock setup**: Mock all dependencies at the top (prisma, api-auth, usage, audit/log)
2. **Helper functions**: `makeRequest` reduces boilerplate
3. **Fixtures**: Reusable mock data for consistent testing
4. **Comprehensive coverage**: Test success (200/201), validation (400), auth (401), plan limits (403), not found (404), conflicts (409), errors (500)
5. **Clear structure**: Group related tests with `describe` blocks
6. **Verify side effects**: Check that audit logs, usage tracking were called
7. **Edge cases**: Test optional fields, sanitization, defaults
8. **Error simulation**: Mock Prisma errors with specific error codes
9. **Clean setup**: Always `vi.clearAllMocks()` in `beforeEach`
