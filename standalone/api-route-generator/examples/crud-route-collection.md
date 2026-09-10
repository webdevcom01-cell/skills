# Example: CRUD Collection Route (GET + POST)

Complete working example for a collection route. Replace `${Entity}` / `${entity}` / `${entities}` with the actual model name.

## File: `src/app/api/${entities}/route.ts`

```typescript
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAuth, isAuthError } from "@/lib/api-auth";
import { create${Entity}Schema } from "@/lib/validations";
import { checkPlanLimit } from "@/lib/usage";
import { logAudit } from "@/lib/audit/log";
import { authEndpointRateLimit } from "@/lib/rate-limit";
import { parsePagination, paginatedResponse } from "@/lib/pagination";

// GET /api/${entities} — List ${entities} for the user's workspace
export async function GET(req: NextRequest) {
  try {
    const workspaceId = req.nextUrl.searchParams.get("workspaceId") ?? undefined;
    const authResult = await requireAuth(workspaceId);
    if (isAuthError(authResult)) return authResult;

    const { page, limit, skip } = parsePagination(req.nextUrl);

    const where = { workspaceId: authResult.workspace.id };

    const [${entities}, total] = await Promise.all([
      prisma.${entity}.findMany({
        where,
        select: {
          id: true,
          name: true,
          // Add model-specific fields here
          createdAt: true,
          updatedAt: true,
        },
        orderBy: { updatedAt: "desc" },
        skip,
        take: limit,
      }),
      prisma.${entity}.count({ where }),
    ]);

    return NextResponse.json(paginatedResponse(${entities}, total, page, limit));
  } catch (error) {
    console.error("GET /api/${entities} error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch ${entities}" },
      { status: 500 }
    );
  }
}

// POST /api/${entities} — Create a new ${entity}
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
    const parsed = create${Entity}Schema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { success: false, error: parsed.error.issues[0].message },
        { status: 400 }
      );
    }

    // Check plan limit for ${entities}
    const limitCheck = await checkPlanLimit(authResult.workspace.id, "${entities}");
    if (!limitCheck.allowed) {
      return NextResponse.json(
        {
          success: false,
          error: `${Entity} limit reached. Your plan allows ${limitCheck.limit} ${entity}${limitCheck.limit === 1 ? "" : "s"}.`,
        },
        { status: 403 }
      );
    }

    const ${entity} = await prisma.${entity}.create({
      data: {
        ...parsed.data,
        workspaceId: authResult.workspace.id,
      },
    });

    await logAudit(authResult.userId, authResult.workspace.id, {
      action: "${entity}.create",
      entityType: "${entity}",
      entityId: ${entity}.id,
      metadata: { name: parsed.data.name },
    }, req);

    return NextResponse.json({ success: true, data: ${entity} }, { status: 201 });
  } catch (error) {
    console.error("POST /api/${entities} error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to create ${entity}" },
      { status: 500 }
    );
  }
}
```
