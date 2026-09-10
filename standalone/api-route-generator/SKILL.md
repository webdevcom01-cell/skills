---
name: api-route-generator
description: This skill should be used when the user asks to "generate api route", "create api endpoint", "new api route", "crud api", "scaffold api", "api for [entity]", "route for [model]", or needs a new Next.js App Router API endpoint with auth, validation, pagination, and multi-tenancy.
version: 1.0.0
---

# API Route Generator

Generate production-ready Next.js App Router API routes following project conventions. Every generated route includes authentication, validation, pagination, multi-tenancy, rate limiting, audit logging, and error handling.

## Workflow

1. **Read the Prisma schema** to understand the target model, its fields, relations, and indexes.
2. **Check existing validations** in `src/lib/validations.ts` for relevant Zod schemas. Create new schemas if none exist.
3. **Generate the collection route** (`route.ts`) with GET (list + pagination) and POST (create + plan limit check).
4. **Generate the detail route** (`[id]/route.ts`) with GET (single), PATCH (update), and DELETE (with active resource check).
5. **Add Zod schemas** to `src/lib/validations.ts` if not already present — both `create` and `update` (via `.partial()`).
6. **Optionally generate tests** using the test-generator skill.

## Import Order

Always follow this exact import order:

```typescript
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAuth, isAuthError } from "@/lib/api-auth";
import { someSchema } from "@/lib/validations";
import { checkPlanLimit } from "@/lib/usage";
import { logAudit } from "@/lib/audit/log";
import { authEndpointRateLimit } from "@/lib/rate-limit";
import { parsePagination, paginatedResponse } from "@/lib/pagination";
```

Only include imports that are actually used in the file.

## Authentication Guard

Every route handler must start with the auth guard pattern:

```typescript
const workspaceId = req.nextUrl.searchParams.get("workspaceId") ?? undefined;
const authResult = await requireAuth(workspaceId);
if (isAuthError(authResult)) return authResult;
```

For detail routes where workspaceId is not needed from query params:

```typescript
const authResult = await requireAuth();
if (isAuthError(authResult)) return authResult;
```

## Dynamic Route Params

For routes with path params like `[id]`, declare the type and await the params:

```typescript
type RouteParams = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, { params }: RouteParams) {
  const { id } = await params;
  // ...
}
```

## Validation Pattern

Use Zod `safeParse` for all request body validation:

```typescript
const body = await req.json();
const parsed = createEntitySchema.safeParse(body);

if (!parsed.success) {
  return NextResponse.json(
    { success: false, error: parsed.error.issues[0].message },
    { status: 400 }
  );
}
```

## Response Envelope

All responses must use the standard envelope:

- **Success (single):** `{ success: true, data: entity }`
- **Success (list):** Use `paginatedResponse(data, total, page, limit)` which returns `{ success: true, data: [], pagination: { page, limit, total, totalPages, hasMore } }`
- **Created:** `{ success: true, data: entity }` with status `201`
- **Error:** `{ success: false, error: "Human-readable message" }` with appropriate status code

## Multi-Tenancy

Every tenant-scoped query MUST include `workspaceId` from the auth result:

```typescript
const where = { workspaceId: authResult.workspace.id };
```

For detail routes, always verify ownership before update/delete:

```typescript
const existing = await prisma.entity.findFirst({
  where: { id, workspaceId: authResult.workspace.id },
});
if (!existing) {
  return NextResponse.json(
    { success: false, error: "Entity not found" },
    { status: 404 }
  );
}
```

## Rate Limiting (POST only)

Apply rate limiting on write operations:

```typescript
const rateLimitResult = await authEndpointRateLimit(req, 10);
if (!rateLimitResult.success) {
  return NextResponse.json(
    { success: false, error: "Rate limit exceeded" },
    { status: 429 }
  );
}
```

## Plan Limit Check (POST only)

Check plan limits before creating resources:

```typescript
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
```

## Audit Logging

Log create, update, and delete actions:

```typescript
await logAudit(authResult.userId, authResult.workspace.id, {
  action: "entity.create",
  entityType: "entity",
  entityId: entity.id,
  metadata: { name: parsed.data.name },
}, req);
```

For updates, include `changes: { after: parsed.data }`.

## Delete Constraints

Before deleting, check for active child resources:

```typescript
const activeChildren = await prisma.childModel.count({
  where: { parentId: id, status: "ACTIVE" },
});

if (activeChildren > 0) {
  return NextResponse.json(
    { success: false, error: "Cannot delete entity with active children" },
    { status: 409 }
  );
}
```

## Error Handling

Every handler wraps its body in try-catch with a specific error log:

```typescript
try {
  // handler logic
} catch (error) {
  console.error("METHOD /api/path error:", error);
  return NextResponse.json(
    { success: false, error: "Failed to [action] [entity]" },
    { status: 500 }
  );
}
```

## Pagination Pattern (GET collection)

```typescript
const { page, limit, skip } = parsePagination(req.nextUrl);

const where = { workspaceId: authResult.workspace.id };

const [entities, total] = await Promise.all([
  prisma.entity.findMany({
    where,
    orderBy: { updatedAt: "desc" },
    skip,
    take: limit,
  }),
  prisma.entity.count({ where }),
]);

return NextResponse.json(paginatedResponse(entities, total, page, limit));
```

## Zod Schema Conventions

When adding schemas to `src/lib/validations.ts`:

- Create schema: `export const createEntitySchema = z.object({ ... });`
- Update schema: `export const updateEntitySchema = createEntitySchema.partial();`
- Type exports: `export type CreateEntityInput = z.infer<typeof createEntitySchema>;`
- String fields: `.min(1, "Field is required").max(100)`
- Optional strings: `.max(500).optional()`
- Enums: `z.enum(["VALUE_A", "VALUE_B"])`
- Numbers with range: `z.number().min(0).max(100).default(50)`
- Nested objects: `z.object({ ... })`
- JSON catch-all: `z.record(z.string(), z.unknown()).optional().default({})`

## File Placement

Routes go under `src/app/api/[entity-plural]/`:
- Collection: `src/app/api/entities/route.ts` (GET + POST)
- Detail: `src/app/api/entities/[id]/route.ts` (GET + PATCH + DELETE)

## References

See `references/api-patterns.md` for complete code templates extracted from the canonical agent routes.
See `references/zod-schema-patterns.md` for Zod schema patterns from the validations file.
See `examples/crud-route-collection.md` and `examples/crud-route-detail.md` for full working examples.
