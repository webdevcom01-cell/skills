# API Route Patterns Reference

Complete code patterns extracted from the canonical API routes in Direct Solutions.

## Source Files

- `src/app/api/agents/route.ts` — Collection route (GET + POST)
- `src/app/api/agents/[id]/route.ts` — Detail route (GET + PATCH + DELETE)

## Collection Route Pattern (GET + POST)

### GET — List with Pagination

```typescript
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAuth, isAuthError } from "@/lib/api-auth";
import { parsePagination, paginatedResponse } from "@/lib/pagination";

// GET /api/entities — List entities for the user's workspace
export async function GET(req: NextRequest) {
  try {
    const workspaceId = req.nextUrl.searchParams.get("workspaceId") ?? undefined;
    const authResult = await requireAuth(workspaceId);
    if (isAuthError(authResult)) return authResult;

    const { page, limit, skip } = parsePagination(req.nextUrl);

    const where = { workspaceId: authResult.workspace.id };

    const [entities, total] = await Promise.all([
      prisma.entity.findMany({
        where,
        select: {
          id: true,
          name: true,
          // ... fields
          updatedAt: true,
        },
        orderBy: { updatedAt: "desc" },
        skip,
        take: limit,
      }),
      prisma.entity.count({ where }),
    ]);

    return NextResponse.json(paginatedResponse(entities, total, page, limit));
  } catch (error) {
    console.error("GET /api/entities error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch entities" },
      { status: 500 }
    );
  }
}
```

### POST — Create with Rate Limit + Plan Check

```typescript
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAuth, isAuthError } from "@/lib/api-auth";
import { createEntitySchema } from "@/lib/validations";
import { checkPlanLimit } from "@/lib/usage";
import { logAudit } from "@/lib/audit/log";
import { authEndpointRateLimit } from "@/lib/rate-limit";

// POST /api/entities — Create a new entity
export async function POST(req: NextRequest) {
  try {
    // Rate limiting: 10 requests per minute
    const rateLimitResult = await authEndpointRateLimit(req, 10);
    if (!rateLimitResult.success) {
      return NextResponse.json(
        { success: false, error: "Rate limit exceeded" },
        { status: 429 }
      );
    }

    const workspaceId = req.nextUrl.searchParams.get("workspaceId") ?? undefined;
    const authResult = await requireAuth(workspaceId);
    if (isAuthError(authResult)) return authResult;

    const body = await req.json();
    const parsed = createEntitySchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { success: false, error: parsed.error.issues[0].message },
        { status: 400 }
      );
    }

    // Check plan limit
    const limitCheck = await checkPlanLimit(authResult.workspace.id, "entities");
    if (!limitCheck.allowed) {
      return NextResponse.json(
        {
          success: false,
          error: `Entity limit reached. Your plan allows ${limitCheck.limit} entit${limitCheck.limit === 1 ? "y" : "ies"}.`,
        },
        { status: 403 }
      );
    }

    const entity = await prisma.entity.create({
      data: {
        ...parsed.data,
        workspaceId: authResult.workspace.id,
      },
    });

    await logAudit(authResult.userId, authResult.workspace.id, {
      action: "entity.create",
      entityType: "entity",
      entityId: entity.id,
      metadata: { name: parsed.data.name },
    }, req);

    return NextResponse.json({ success: true, data: entity }, { status: 201 });
  } catch (error) {
    console.error("POST /api/entities error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to create entity" },
      { status: 500 }
    );
  }
}
```

## Detail Route Pattern (GET + PATCH + DELETE)

### Type Declaration

```typescript
type RouteParams = { params: Promise<{ id: string }> };
```

### GET — Single Entity

```typescript
// GET /api/entities/[id] — Entity detail
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const authResult = await requireAuth();
    if (isAuthError(authResult)) return authResult;

    const entity = await prisma.entity.findFirst({
      where: { id, workspaceId: authResult.workspace.id },
    });

    if (!entity) {
      return NextResponse.json(
        { success: false, error: "Entity not found" },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true, data: entity });
  } catch (error) {
    console.error("GET /api/entities/[id] error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch entity" },
      { status: 500 }
    );
  }
}
```

### PATCH — Update

```typescript
// PATCH /api/entities/[id] — Update entity
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const authResult = await requireAuth();
    if (isAuthError(authResult)) return authResult;

    // Verify ownership
    const existing = await prisma.entity.findFirst({
      where: { id, workspaceId: authResult.workspace.id },
    });

    if (!existing) {
      return NextResponse.json(
        { success: false, error: "Entity not found" },
        { status: 404 }
      );
    }

    const body = await req.json();
    const parsed = updateEntitySchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { success: false, error: parsed.error.issues[0].message },
        { status: 400 }
      );
    }

    const entity = await prisma.entity.update({
      where: { id },
      data: parsed.data,
    });

    await logAudit(authResult.userId, authResult.workspace.id, {
      action: "entity.update",
      entityType: "entity",
      entityId: id,
      changes: { after: parsed.data },
    }, req);

    return NextResponse.json({ success: true, data: entity });
  } catch (error) {
    console.error("PATCH /api/entities/[id] error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to update entity" },
      { status: 500 }
    );
  }
}
```

### DELETE — With Active Resource Check

```typescript
// DELETE /api/entities/[id] — Delete entity
export async function DELETE(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const authResult = await requireAuth();
    if (isAuthError(authResult)) return authResult;

    // Verify ownership
    const existing = await prisma.entity.findFirst({
      where: { id, workspaceId: authResult.workspace.id },
    });

    if (!existing) {
      return NextResponse.json(
        { success: false, error: "Entity not found" },
        { status: 404 }
      );
    }

    // Check for active dependent resources before deleting
    const activeChildren = await prisma.childModel.count({
      where: { entityId: id, status: "ACTIVE" },
    });

    if (activeChildren > 0) {
      return NextResponse.json(
        {
          success: false,
          error: "Cannot delete entity with active children",
        },
        { status: 409 }
      );
    }

    await prisma.entity.delete({ where: { id } });

    await logAudit(authResult.userId, authResult.workspace.id, {
      action: "entity.delete",
      entityType: "entity",
      entityId: id,
      metadata: { name: existing.name },
    }, req);

    return NextResponse.json({ success: true, data: { id } });
  } catch (error) {
    console.error("DELETE /api/entities/[id] error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to delete entity" },
      { status: 500 }
    );
  }
}
```

## Auth Helper Types

From `src/lib/api-auth.ts`:

```typescript
interface AuthResult {
  userId: string;
  role: "OWNER" | "ADMIN" | "EDITOR" | "VIEWER";
  workspace: {
    id: string;
    name: string;
    plan: string;
  };
}

// requireAuth returns AuthResult | NextResponse
// isAuthError is a type guard: (result) => result is NextResponse
// requireRole checks minimum role level and returns null | NextResponse
```

## Pagination Helper Types

From `src/lib/pagination.ts`:

```typescript
// parsePagination(url: URL) => { page: number, limit: number, skip: number }
// Default: page=1, limit=20, max limit=100

// paginatedResponse(data, total, page, limit) returns:
// { success: true, data: T[], pagination: { page, limit, total, totalPages, hasMore } }
```

## Rate Limit Helper

From `src/lib/rate-limit.ts`:

```typescript
// authEndpointRateLimit(request, limit, windowMs = 60_000)
// Returns { success: boolean, limit: number, remaining: number, reset: number }
```

## Audit Log Helper

From `src/lib/audit/log.ts`:

```typescript
// logAudit(userId, workspaceId, { action, entityType, entityId, metadata?, changes? }, req)
// Actions follow pattern: "entity.verb" (e.g., "agent.create", "agent.update", "agent.delete")
```
