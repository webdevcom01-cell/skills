# Example: New Model Migration

Complete walkthrough for adding a "Notification" model to the schema.

## Scenario

Add a notification system to alert users about important events:
- Agent published
- Conversation assigned
- Workflow completed
- Credits running low

## Step 1: Read Current Schema

```bash
# Read the current schema to understand structure
cat prisma/schema.prisma
```

## Step 2: Add Model to Schema

Add the following to `prisma/schema.prisma`:

```prisma
// Add enum for notification types
enum NotificationType {
  AGENT_PUBLISHED
  CONVERSATION_ASSIGNED
  WORKFLOW_COMPLETED
  CREDITS_LOW
  SYSTEM
}

// Add Notification model
model Notification {
  id        String           @id @default(cuid())
  type      NotificationType
  title     String
  message   String?          @db.Text
  isRead    Boolean          @default(false)
  metadata  Json?
  createdAt DateTime         @default(now())
  updatedAt DateTime         @updatedAt

  userId String
  user   User   @relation(fields: [userId], references: [id], onDelete: Cascade)

  workspaceId String
  workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  // Optional: Link to specific agent if notification is about an agent
  agentId String?
  agent   Agent?  @relation(fields: [agentId], references: [id], onDelete: Cascade)

  @@index([userId, isRead])
  @@index([userId, createdAt(sort: Desc)])
  @@index([workspaceId])
  @@index([agentId])
  @@index([type])
}
```

## Step 3: Update Related Models

Add relation to User model:

```prisma
model User {
  id                String    @id @default(cuid())
  email             String    @unique
  name              String?
  image             String?
  emailVerified     DateTime?
  stripeCustomerId  String?   @unique
  subscriptionTier  String    @default("free")
  credits           Int       @default(100)
  creditsUsed       Int       @default(0)
  createdAt         DateTime  @default(now())
  updatedAt         DateTime  @updatedAt

  accounts         Account[]
  sessions         Session[]
  workspaces       WorkspaceMember[]
  ownedWorkspaces  Workspace[]
  notifications    Notification[]  // ADD THIS LINE

  @@index([email])
}
```

Add relation to Workspace model:

```prisma
model Workspace {
  id          String   @id @default(cuid())
  name        String
  slug        String   @unique
  image       String?
  plan        String   @default("free")
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  ownerId String
  owner   User   @relation(fields: [ownerId], references: [id], onDelete: Cascade)

  members        WorkspaceMember[]
  agents         Agent[]
  flows          Flow[]
  channels       Channel[]
  conversations  Conversation[]
  knowledgeBases KnowledgeBase[]
  notifications  Notification[]  // ADD THIS LINE

  @@index([ownerId])
  @@index([slug])
}
```

Add optional relation to Agent model (if notifications can link to agents):

```prisma
model Agent {
  id           String      @id @default(cuid())
  name         String
  description  String?
  avatar       String?
  status       AgentStatus @default(DRAFT)
  systemPrompt String?     @db.Text
  model        String      @default("gpt-4o-mini")
  temperature  Float       @default(0.7)
  createdAt    DateTime    @default(now())
  updatedAt    DateTime    @updatedAt

  workspaceId String
  workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  flows          Flow[]
  knowledgeBase  KnowledgeBase?
  channels       Channel[]
  notifications  Notification[]  // ADD THIS LINE

  @@index([workspaceId])
  @@index([status])
}
```

## Step 4: Run Migration

```bash
cd ~/direct-solutions
pnpm dlx prisma migrate dev --name add-notification-model
```

This will:
1. Generate SQL migration file
2. Apply migration to database
3. Regenerate Prisma Client

Expected output:
```
Environment variables loaded from .env
Prisma schema loaded from prisma/schema.prisma
Datasource "db": PostgreSQL database

Applying migration `20260212000000_add_notification_model`

The following migration(s) have been created and applied from new schema changes:

migrations/
  └─ 20260212000000_add_notification_model/
    └─ migration.sql

Your database is now in sync with your schema.

✔ Generated Prisma Client
```

## Step 5: Create RLS Policies (Optional)

Create `prisma/migrations/20260212000001_add_notification_rls/migration.sql`:

```sql
-- Enable Row Level Security on Notification table
ALTER TABLE "Notification" ENABLE ROW LEVEL SECURITY;

-- DROP existing policies if any
DROP POLICY IF EXISTS "Notification_select_policy" ON "Notification";
DROP POLICY IF EXISTS "Notification_insert_policy" ON "Notification";
DROP POLICY IF EXISTS "Notification_update_policy" ON "Notification";
DROP POLICY IF EXISTS "Notification_delete_policy" ON "Notification";

-- SELECT: Users can view their own notifications or workspace notifications
CREATE POLICY "Notification_select_policy" ON "Notification"
  FOR SELECT
  USING (
    "userId" = auth.uid()
    OR EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Notification"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
    )
  );

-- INSERT: Service role can create notifications (or workspace admins)
CREATE POLICY "Notification_insert_policy" ON "Notification"
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Notification"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
        AND "WorkspaceMember"."role" IN ('OWNER', 'ADMIN')
    )
  );

-- UPDATE: Users can mark their own notifications as read
CREATE POLICY "Notification_update_policy" ON "Notification"
  FOR UPDATE
  USING (
    "userId" = auth.uid()
  )
  WITH CHECK (
    "userId" = auth.uid()
  );

-- DELETE: Users can delete their own notifications
CREATE POLICY "Notification_delete_policy" ON "Notification"
  FOR DELETE
  USING (
    "userId" = auth.uid()
  );

-- Add performance indexes
CREATE INDEX IF NOT EXISTS idx_notification_user_read
  ON "Notification" ("userId", "isRead");

CREATE INDEX IF NOT EXISTS idx_notification_user_created
  ON "Notification" ("userId", "createdAt" DESC);

-- GIN index for full-text search on notification content
CREATE INDEX IF NOT EXISTS idx_notification_content_gin
  ON "Notification"
  USING GIN (to_tsvector('english', "title" || ' ' || COALESCE("message", '')));
```

Apply RLS migration:

```bash
pnpm dlx prisma migrate dev --name add-notification-rls
```

## Step 6: Update Validation Schemas

Add to `src/lib/validations.ts`:

```typescript
import { z } from 'zod';

// Notification validation schemas
export const createNotificationSchema = z.object({
  type: z.enum([
    'AGENT_PUBLISHED',
    'CONVERSATION_ASSIGNED',
    'WORKFLOW_COMPLETED',
    'CREDITS_LOW',
    'SYSTEM',
  ]),
  title: z.string().min(1, 'Title is required').max(200),
  message: z.string().max(1000).optional(),
  userId: z.string().cuid(),
  workspaceId: z.string().cuid(),
  agentId: z.string().cuid().optional(),
  metadata: z.record(z.any()).optional(),
});

export const updateNotificationSchema = z.object({
  isRead: z.boolean().optional(),
  metadata: z.record(z.any()).optional(),
});

export const getNotificationsQuerySchema = z.object({
  userId: z.string().cuid().optional(),
  workspaceId: z.string().cuid().optional(),
  isRead: z.boolean().optional(),
  type: z
    .enum([
      'AGENT_PUBLISHED',
      'CONVERSATION_ASSIGNED',
      'WORKFLOW_COMPLETED',
      'CREDITS_LOW',
      'SYSTEM',
    ])
    .optional(),
  limit: z.number().int().min(1).max(100).default(20),
  offset: z.number().int().min(0).default(0),
});

export type CreateNotificationInput = z.infer<typeof createNotificationSchema>;
export type UpdateNotificationInput = z.infer<typeof updateNotificationSchema>;
export type GetNotificationsQuery = z.infer<typeof getNotificationsQuerySchema>;
```

## Step 7: Update TypeScript Types (Optional)

Add to `src/types/index.ts`:

```typescript
import type { Notification, NotificationType } from '@/generated/prisma/client';

// Notification with relations
export type NotificationWithRelations = Notification & {
  user: {
    id: string;
    name: string | null;
    email: string;
    image: string | null;
  };
  workspace: {
    id: string;
    name: string;
    slug: string;
  };
  agent?: {
    id: string;
    name: string;
  } | null;
};

// Notification list response
export type NotificationListResponse = {
  notifications: NotificationWithRelations[];
  total: number;
  hasMore: boolean;
};
```

## Step 8: Verify Migration

```bash
# Regenerate Prisma Client
pnpm dlx prisma generate

# Check database
pnpm dlx prisma studio
```

## Step 9: Create API Endpoints (Example)

Create `src/app/api/notifications/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import {
  createNotificationSchema,
  getNotificationsQuerySchema
} from '@/lib/validations';

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const query = getNotificationsQuerySchema.parse({
      userId: searchParams.get('userId') || session.user.id,
      workspaceId: searchParams.get('workspaceId') || undefined,
      isRead: searchParams.get('isRead') ? searchParams.get('isRead') === 'true' : undefined,
      type: searchParams.get('type') || undefined,
      limit: searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : 20,
      offset: searchParams.get('offset') ? parseInt(searchParams.get('offset')!) : 0,
    });

    const where = {
      userId: query.userId,
      ...(query.workspaceId && { workspaceId: query.workspaceId }),
      ...(query.isRead !== undefined && { isRead: query.isRead }),
      ...(query.type && { type: query.type }),
    };

    const [notifications, total] = await Promise.all([
      prisma.notification.findMany({
        where,
        include: {
          user: {
            select: { id: true, name: true, email: true, image: true },
          },
          workspace: {
            select: { id: true, name: true, slug: true },
          },
          agent: {
            select: { id: true, name: true },
          },
        },
        orderBy: { createdAt: 'desc' },
        take: query.limit,
        skip: query.offset,
      }),
      prisma.notification.count({ where }),
    ]);

    return NextResponse.json({
      notifications,
      total,
      hasMore: total > query.offset + query.limit,
    });
  } catch (error) {
    console.error('GET /api/notifications error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const data = createNotificationSchema.parse(body);

    const notification = await prisma.notification.create({
      data,
      include: {
        user: {
          select: { id: true, name: true, email: true, image: true },
        },
        workspace: {
          select: { id: true, name: true, slug: true },
        },
        agent: {
          select: { id: true, name: true },
        },
      },
    });

    return NextResponse.json(notification, { status: 201 });
  } catch (error) {
    console.error('POST /api/notifications error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

## Summary

You've successfully:
1. Added Notification model with proper relations and indexes
2. Created migration with `pnpm dlx prisma migrate dev`
3. Added RLS policies for security
4. Created Zod validation schemas
5. Added TypeScript types
6. Created API endpoints

The notification system is now ready to use!
