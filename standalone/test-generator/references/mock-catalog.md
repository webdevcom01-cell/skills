# Mock Catalog Reference

Complete catalog of all mockable dependencies in the Direct Solutions project. Copy-paste these mock declarations as needed.

---

## 1. @/lib/prisma

The Prisma client with all models and operations.

### Full Mock Declaration

```typescript
vi.mock("@/lib/prisma", () => ({
  prisma: {
    // User & Auth models
    user: {
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
    account: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },
    session: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },

    // Core models
    workspace: {
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
      findUnique: vi.fn(),
      findUniqueOrThrow: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },
    conversation: {
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
    message: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      createMany: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },

    // Knowledge Base models
    knowledgeBase: {
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
    kBSource: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },
    kBChunk: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      createMany: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },

    // Channel models
    channel: {
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

    // API & Auth models
    apiKey: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },

    // Billing & Usage models
    usageRecord: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      createMany: vi.fn(),
      deleteMany: vi.fn(),
      aggregate: vi.fn(),
      groupBy: vi.fn(),
    },

    // Team & Collaboration models
    invitation: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },

    // Experimentation models
    experiment: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },
    experimentVariant: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      deleteMany: vi.fn(),
    },

    // Audit & Security models
    auditLog: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      createMany: vi.fn(),
      deleteMany: vi.fn(),
    },

    // Enterprise models
    ssoConfig: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    customLLMConfig: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    whiteLabelConfig: {
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },

    // Transaction & Raw Query support
    $transaction: vi.fn(),
    $queryRaw: vi.fn(),
    $executeRaw: vi.fn(),
  },
}));
```

### Minimal Mock (Common Models Only)

```typescript
vi.mock("@/lib/prisma", () => ({
  prisma: {
    workspace: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    agent: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    conversation: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    message: {
      findMany: vi.fn(),
      create: vi.fn(),
      createMany: vi.fn(),
    },
  },
}));
```

### Import & Cast

```typescript
import { prisma } from "@/lib/prisma";
const mockPrisma = vi.mocked(prisma);

// Usage in tests
mockPrisma.agent.findMany.mockResolvedValue([...]);
mockPrisma.agent.create.mockResolvedValue({...});
```

---

## 2. @/lib/api-auth

Authentication and authorization for API routes.

### Full Mock Declaration

```typescript
vi.mock("@/lib/api-auth", () => ({
  requireAuth: vi.fn(),
  isAuthError: vi.fn((result) => result instanceof NextResponse),
  requireRole: vi.fn(),
}));
```

### Import & Cast

```typescript
import { requireAuth, isAuthError, requireRole } from "@/lib/api-auth";

const mockRequireAuth = vi.mocked(requireAuth);
const mockIsAuthError = vi.mocked(isAuthError);
const mockRequireRole = vi.mocked(requireRole);
```

### Return Types

```typescript
// Success case
mockRequireAuth.mockResolvedValue({
  userId: "user-123",
  workspace: {
    id: "ws-123",
    name: "Test Workspace",
    plan: "PRO",
  },
});

// Error case (401)
mockRequireAuth.mockResolvedValue(
  NextResponse.json({ error: "Unauthorized" }, { status: 401 })
);

// Role check success
mockRequireRole.mockResolvedValue({
  userId: "user-123",
  workspace: {
    id: "ws-123",
    name: "Test Workspace",
    plan: "ENTERPRISE",
  },
  role: "ADMIN",
});

// Role check error (403)
mockRequireRole.mockResolvedValue(
  NextResponse.json({ error: "Forbidden" }, { status: 403 })
);
```

---

## 3. @/lib/usage

Usage tracking and plan limits.

### Full Mock Declaration

```typescript
vi.mock("@/lib/usage", () => ({
  checkPlanLimit: vi.fn(),
  trackUsage: vi.fn(),
  hasCredits: vi.fn(),
  CREDIT_COSTS: {
    MESSAGE: 1,
    VOICE_MINUTE: 10,
    KNOWLEDGE_QUERY: 2,
    AI_GENERATION: 5,
  },
}));
```

### Import & Cast

```typescript
import { checkPlanLimit, trackUsage, hasCredits, CREDIT_COSTS } from "@/lib/usage";

const mockCheckPlanLimit = vi.mocked(checkPlanLimit);
const mockTrackUsage = vi.mocked(trackUsage);
const mockHasCredits = vi.mocked(hasCredits);
```

### Return Types

```typescript
// Limit check - allowed
mockCheckPlanLimit.mockResolvedValue({
  allowed: true,
  limit: 100,
  current: 50,
});

// Limit check - exceeded
mockCheckPlanLimit.mockResolvedValue({
  allowed: false,
  limit: 10,
  current: 10,
});

// Track usage (void)
mockTrackUsage.mockResolvedValue(undefined);

// Has credits - yes
mockHasCredits.mockResolvedValue(true);

// Has credits - no
mockHasCredits.mockResolvedValue(false);
```

### Usage Examples

```typescript
// Check if workspace can create one more agent
expect(mockCheckPlanLimit).toHaveBeenCalledWith(
  { id: "ws-123", plan: "PRO" },
  "AGENTS",
  1
);

// Track message usage
expect(mockTrackUsage).toHaveBeenCalledWith(
  "ws-123",
  "MESSAGE",
  CREDIT_COSTS.MESSAGE
);
```

---

## 4. @/lib/audit/log

Audit logging for compliance and security.

### Full Mock Declaration

```typescript
vi.mock("@/lib/audit/log", () => ({
  logAudit: vi.fn(),
}));
```

### Import & Cast

```typescript
import { logAudit } from "@/lib/audit/log";
const mockLogAudit = vi.mocked(logAudit);
```

### Return Type

```typescript
// Always returns void
mockLogAudit.mockResolvedValue(undefined);
```

### Usage Examples

```typescript
// CREATE action
expect(mockLogAudit).toHaveBeenCalledWith(
  "user-123",
  "ws-123",
  {
    action: "CREATE",
    entityType: "AGENT",
    entityId: "agent-123",
    metadata: { name: "Support Bot" },
  },
  req
);

// UPDATE action with changes
expect(mockLogAudit).toHaveBeenCalledWith(
  "user-123",
  "ws-123",
  {
    action: "UPDATE",
    entityType: "AGENT",
    entityId: "agent-123",
    changes: {
      name: { old: "Old Name", new: "New Name" },
    },
  },
  req
);

// DELETE action
expect(mockLogAudit).toHaveBeenCalledWith(
  "user-123",
  "ws-123",
  {
    action: "DELETE",
    entityType: "AGENT",
    entityId: "agent-123",
  },
  req
);
```

---

## 5. @/lib/rate-limit

Rate limiting for API endpoints.

### Full Mock Declaration

```typescript
vi.mock("@/lib/rate-limit", () => ({
  authEndpointRateLimit: vi.fn(),
  publicEndpointRateLimit: vi.fn(),
  ipRateLimit: vi.fn(),
}));
```

### Import & Cast

```typescript
import { authEndpointRateLimit } from "@/lib/rate-limit";
const mockRateLimit = vi.mocked(authEndpointRateLimit);
```

### Return Types

```typescript
// Not rate limited
mockRateLimit.mockResolvedValue({
  success: true,
  limit: 100,
  remaining: 95,
  reset: Date.now() + 60000, // 1 minute from now
});

// Rate limited
mockRateLimit.mockResolvedValue({
  success: false,
  limit: 100,
  remaining: 0,
  reset: Date.now() + 60000,
});
```

### Usage Examples

```typescript
// Check rate limit for user
const rateLimitResult = await authEndpointRateLimit(req, "user-123");

if (!rateLimitResult.success) {
  return NextResponse.json(
    { error: "Too many requests" },
    {
      status: 429,
      headers: {
        "X-RateLimit-Limit": rateLimitResult.limit.toString(),
        "X-RateLimit-Remaining": rateLimitResult.remaining.toString(),
        "X-RateLimit-Reset": rateLimitResult.reset.toString(),
      },
    }
  );
}
```

---

## 6. ai (Vercel AI SDK)

AI generation and embeddings.

### Full Mock Declaration

```typescript
vi.mock("ai", () => ({
  generateText: vi.fn(),
  streamText: vi.fn(),
  embed: vi.fn(),
  embedMany: vi.fn(),
  tool: vi.fn(),
}));
```

### Import & Cast

```typescript
import { generateText, embed, embedMany } from "ai";

const mockGenerateText = vi.mocked(generateText);
const mockEmbed = vi.mocked(embed);
const mockEmbedMany = vi.mocked(embedMany);
```

### Return Types

```typescript
// Generate text
mockGenerateText.mockResolvedValue({
  text: "Generated response here",
  usage: {
    promptTokens: 10,
    completionTokens: 20,
    totalTokens: 30,
  },
  finishReason: "stop",
});

// Single embedding
mockEmbed.mockResolvedValue({
  embedding: [0.1, 0.2, 0.3, /* ... 1536 dimensions */],
  usage: {
    tokens: 5,
  },
});

// Multiple embeddings
mockEmbedMany.mockResolvedValue({
  embeddings: [
    [0.1, 0.2, 0.3, /* ... */],
    [0.4, 0.5, 0.6, /* ... */],
  ],
  usage: {
    tokens: 10,
  },
});
```

### Usage Examples

```typescript
// Generate text
expect(mockGenerateText).toHaveBeenCalledWith({
  model: expect.any(Object),
  messages: expect.arrayContaining([
    { role: "user", content: "Hello" },
  ]),
});

// Create embedding
expect(mockEmbed).toHaveBeenCalledWith({
  model: expect.any(Object),
  value: "Text to embed",
});
```

---

## 7. @/lib/ai

AI model utilities and wrappers.

### Full Mock Declaration

```typescript
vi.mock("@/lib/ai", () => ({
  getModelForWorkspace: vi.fn(),
  getModel: vi.fn(),
  getEmbeddingModel: vi.fn(),
}));
```

### Import & Cast

```typescript
import { getModelForWorkspace, getModel, getEmbeddingModel } from "@/lib/ai";

const mockGetModelForWorkspace = vi.mocked(getModelForWorkspace);
const mockGetModel = vi.mocked(getModel);
const mockGetEmbeddingModel = vi.mocked(getEmbeddingModel);
```

### Return Types

```typescript
// Model instance (mock object)
const mockModel = {
  provider: "openai",
  modelId: "gpt-4",
};

mockGetModelForWorkspace.mockResolvedValue(mockModel);
mockGetModel.mockReturnValue(mockModel);

// Embedding model
const mockEmbeddingModel = {
  provider: "openai",
  modelId: "text-embedding-3-small",
};

mockGetEmbeddingModel.mockReturnValue(mockEmbeddingModel);
```

---

## Common Mock Patterns

### Reset All Mocks

```typescript
import { beforeEach } from "vitest";

beforeEach(() => {
  vi.clearAllMocks();
});
```

### Mock Implementation

```typescript
// Simple return value
mockPrisma.agent.findUnique.mockResolvedValue(mockAgent);

// Conditional logic
mockPrisma.agent.findUnique.mockImplementation(async (args) => {
  if (args.where.id === "agent-123") {
    return mockAgent;
  }
  return null;
});

// Throw error
mockPrisma.agent.create.mockRejectedValue(new Error("Database error"));
```

### Verify Mock Calls

```typescript
// Called once
expect(mockPrisma.agent.findMany).toHaveBeenCalledOnce();

// Called with specific args
expect(mockPrisma.agent.create).toHaveBeenCalledWith({
  data: {
    workspaceId: "ws-123",
    name: "Support Bot",
  },
});

// Called with partial match
expect(mockLogAudit).toHaveBeenCalledWith(
  expect.any(String),
  expect.any(String),
  expect.objectContaining({
    action: "CREATE",
    entityType: "AGENT",
  }),
  expect.any(Object)
);

// Not called
expect(mockTrackUsage).not.toHaveBeenCalled();
```
