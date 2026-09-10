# Example: CRUD Detail Route (GET + PATCH + DELETE)

Complete working example for a detail route. Replace `${Entity}` / `${entity}` / `${entities}` with the actual model name.

## File: `src/app/api/${entities}/[id]/route.ts`

```typescript
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAuth, isAuthError } from "@/lib/api-auth";
import { update${Entity}Schema } from "@/lib/validations";
import { logAudit } from "@/lib/audit/log";

type RouteParams = { params: Promise<{ id: string }> };

// GET /api/${entities}/[id] — ${Entity} detail
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const authResult = await requireAuth();
    if (isAuthError(authResult)) return authResult;

    const ${entity} = await prisma.${entity}.findFirst({
      where: { id, workspaceId: authResult.workspace.id },
    });

    if (!${entity}) {
      return NextResponse.json(
        { success: false, error: "${Entity} not found" },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true, data: ${entity} });
  } catch (error) {
    console.error("GET /api/${entities}/[id] error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch ${entity}" },
      { status: 500 }
    );
  }
}

// PATCH /api/${entities}/[id] — Update ${entity}
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const authResult = await requireAuth();
    if (isAuthError(authResult)) return authResult;

    // Verify ownership
    const existing = await prisma.${entity}.findFirst({
      where: { id, workspaceId: authResult.workspace.id },
    });

    if (!existing) {
      return NextResponse.json(
        { success: false, error: "${Entity} not found" },
        { status: 404 }
      );
    }

    const body = await req.json();
    const parsed = update${Entity}Schema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { success: false, error: parsed.error.issues[0].message },
        { status: 400 }
      );
    }

    const ${entity} = await prisma.${entity}.update({
      where: { id },
      data: parsed.data,
    });

    await logAudit(authResult.userId, authResult.workspace.id, {
      action: "${entity}.update",
      entityType: "${entity}",
      entityId: id,
      changes: { after: parsed.data },
    }, req);

    return NextResponse.json({ success: true, data: ${entity} });
  } catch (error) {
    console.error("PATCH /api/${entities}/[id] error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to update ${entity}" },
      { status: 500 }
    );
  }
}

// DELETE /api/${entities}/[id] — Delete ${entity}
export async function DELETE(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const authResult = await requireAuth();
    if (isAuthError(authResult)) return authResult;

    // Verify ownership
    const existing = await prisma.${entity}.findFirst({
      where: { id, workspaceId: authResult.workspace.id },
    });

    if (!existing) {
      return NextResponse.json(
        { success: false, error: "${Entity} not found" },
        { status: 404 }
      );
    }

    // Check for active dependent resources before deleting
    // Uncomment and adapt if entity has dependent children:
    // const activeChildren = await prisma.childModel.count({
    //   where: { ${entity}Id: id, status: "ACTIVE" },
    // });
    //
    // if (activeChildren > 0) {
    //   return NextResponse.json(
    //     { success: false, error: "Cannot delete ${entity} with active resources" },
    //     { status: 409 }
    //   );
    // }

    await prisma.${entity}.delete({ where: { id } });

    await logAudit(authResult.userId, authResult.workspace.id, {
      action: "${entity}.delete",
      entityType: "${entity}",
      entityId: id,
      metadata: { name: existing.name },
    }, req);

    return NextResponse.json({ success: true, data: { id } });
  } catch (error) {
    console.error("DELETE /api/${entities}/[id] error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to delete ${entity}" },
      { status: 500 }
    );
  }
}
```
