# Row Level Security (RLS) Templates

SQL templates for implementing Row Level Security policies in PostgreSQL with Supabase.

## 1. Enable RLS on a Table

```sql
-- Enable RLS on the table
ALTER TABLE "TableName" ENABLE ROW LEVEL SECURITY;

-- Drop existing policies (if updating)
DROP POLICY IF EXISTS "TableName_select_policy" ON "TableName";
DROP POLICY IF EXISTS "TableName_insert_policy" ON "TableName";
DROP POLICY IF EXISTS "TableName_update_policy" ON "TableName";
DROP POLICY IF EXISTS "TableName_delete_policy" ON "TableName";
```

## 2. Workspace-Scoped RLS Policies

Complete set of policies for workspace-scoped resources:

```sql
-- Enable RLS
ALTER TABLE "Agent" ENABLE ROW LEVEL SECURITY;

-- SELECT: Users can view agents in their workspace
CREATE POLICY "Agent_select_policy" ON "Agent"
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Agent"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
    )
  );

-- INSERT: Users can create agents in their workspace
CREATE POLICY "Agent_insert_policy" ON "Agent"
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Agent"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
        AND "WorkspaceMember"."role" IN ('OWNER', 'ADMIN')
    )
  );

-- UPDATE: Users can update agents in their workspace (OWNER/ADMIN only)
CREATE POLICY "Agent_update_policy" ON "Agent"
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Agent"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
        AND "WorkspaceMember"."role" IN ('OWNER', 'ADMIN')
    )
  );

-- DELETE: Users can delete agents in their workspace (OWNER/ADMIN only)
CREATE POLICY "Agent_delete_policy" ON "Agent"
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Agent"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
        AND "WorkspaceMember"."role" IN ('OWNER', 'ADMIN')
    )
  );
```

## 3. Public Read Policy (for Published Resources)

Allow public read access to published agents via widget:

```sql
-- Enable RLS
ALTER TABLE "Agent" ENABLE ROW LEVEL SECURITY;

-- Public SELECT for published agents
CREATE POLICY "Agent_public_select_policy" ON "Agent"
  FOR SELECT
  USING (
    status = 'PUBLISHED'
    OR EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Agent"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
    )
  );

-- Authenticated INSERT only
CREATE POLICY "Agent_insert_policy" ON "Agent"
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Agent"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
        AND "WorkspaceMember"."role" IN ('OWNER', 'ADMIN')
    )
  );

-- Authenticated UPDATE only
CREATE POLICY "Agent_update_policy" ON "Agent"
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Agent"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
        AND "WorkspaceMember"."role" IN ('OWNER', 'ADMIN')
    )
  );

-- Authenticated DELETE only
CREATE POLICY "Agent_delete_policy" ON "Agent"
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM "WorkspaceMember"
      WHERE "WorkspaceMember"."workspaceId" = "Agent"."workspaceId"
        AND "WorkspaceMember"."userId" = auth.uid()
        AND "WorkspaceMember"."role" IN ('OWNER', 'ADMIN')
    )
  );
```

## 4. GIN Index for Full-Text Search

Create GIN index with tsvector for text search:

```sql
-- Add tsvector column (optional, or use expression index)
ALTER TABLE "KBChunk" ADD COLUMN content_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

-- Create GIN index on tsvector column
CREATE INDEX idx_kbchunk_content_tsv ON "KBChunk" USING GIN (content_tsv);

-- OR: Create expression-based GIN index (no extra column needed)
CREATE INDEX idx_kbchunk_content_gin ON "KBChunk"
  USING GIN (to_tsvector('english', content));

-- Usage example:
-- SELECT * FROM "KBChunk"
-- WHERE to_tsvector('english', content) @@ to_tsquery('english', 'search & query');
```

## 5. HNSW Index for Vector Similarity Search

Create HNSW index for pgvector embeddings:

```sql
-- Create HNSW index for cosine similarity
CREATE INDEX idx_kbchunk_embedding_hnsw ON "KBChunk"
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (faster build, slower query)
CREATE INDEX idx_kbchunk_embedding_ivfflat ON "KBChunk"
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Usage example:
-- SELECT * FROM "KBChunk"
-- ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
-- LIMIT 10;
```

**HNSW Parameters**:
- `m`: Max connections per layer (16 is good default, higher = better recall but slower)
- `ef_construction`: Size of dynamic candidate list (64-128 is good)

**Distance Operators**:
- `<=>` - Cosine distance (1 - cosine similarity)
- `<->` - L2 distance (Euclidean)
- `<#>` - Inner product

## 6. Partial Unique Index

Create unique index with WHERE clause:

```sql
-- Only one main flow per agent
CREATE UNIQUE INDEX idx_flows_agent_main ON "Flow" ("agentId")
  WHERE "isMain" = true;

-- Only one active subscription per user
CREATE UNIQUE INDEX idx_subscriptions_user_active ON "Subscription" ("userId")
  WHERE "status" = 'ACTIVE';

-- Unique email only for verified users
CREATE UNIQUE INDEX idx_users_email_verified ON "User" (LOWER("email"))
  WHERE "emailVerified" IS NOT NULL;
```

## 7. Complete Example: New Table with RLS + Indexes

```sql
-- Enable RLS on new table
ALTER TABLE "Notification" ENABLE ROW LEVEL SECURITY;

-- SELECT: Users can view their own notifications
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

-- INSERT: System can create notifications (service role)
CREATE POLICY "Notification_insert_policy" ON "Notification"
  FOR INSERT
  WITH CHECK (true); -- Service role bypass, or add specific logic

-- UPDATE: Users can mark their notifications as read
CREATE POLICY "Notification_update_policy" ON "Notification"
  FOR UPDATE
  USING ("userId" = auth.uid());

-- DELETE: Users can delete their notifications
CREATE POLICY "Notification_delete_policy" ON "Notification"
  FOR DELETE
  USING ("userId" = auth.uid());

-- Add indexes for performance
CREATE INDEX idx_notification_user_read ON "Notification" ("userId", "isRead");
CREATE INDEX idx_notification_workspace ON "Notification" ("workspaceId");
CREATE INDEX idx_notification_created ON "Notification" ("createdAt" DESC);

-- GIN index for full-text search on notification content
CREATE INDEX idx_notification_content_gin ON "Notification"
  USING GIN (to_tsvector('english', "title" || ' ' || COALESCE("message", '')));
```

## 8. Bypass RLS for Service Role

When using service role (admin operations):

```sql
-- Grant service role bypass
GRANT ALL ON "TableName" TO service_role;

-- Or in application code, use service role client:
-- const { data } = await supabase.from('TableName').select()
-- This bypasses RLS when using service_role key
```

## 9. Child Record Policies (Inherit from Parent)

```sql
-- Enable RLS on child table
ALTER TABLE "Message" ENABLE ROW LEVEL SECURITY;

-- SELECT: Users can view messages in conversations they have access to
CREATE POLICY "Message_select_policy" ON "Message"
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM "Conversation"
      JOIN "WorkspaceMember" ON "WorkspaceMember"."workspaceId" = "Conversation"."workspaceId"
      WHERE "Conversation"."id" = "Message"."conversationId"
        AND "WorkspaceMember"."userId" = auth.uid()
    )
  );

-- INSERT: Users can create messages in conversations they have access to
CREATE POLICY "Message_insert_policy" ON "Message"
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "Conversation"
      JOIN "WorkspaceMember" ON "WorkspaceMember"."workspaceId" = "Conversation"."workspaceId"
      WHERE "Conversation"."id" = "Message"."conversationId"
        AND "WorkspaceMember"."userId" = auth.uid()
    )
  );
```

## 10. Testing RLS Policies

```sql
-- Test as specific user
SET LOCAL role TO authenticated;
SET LOCAL request.jwt.claim.sub TO 'user-id-here';

-- Run test query
SELECT * FROM "Agent";

-- Reset
RESET role;
RESET request.jwt.claim.sub;
```

## Best Practices

1. **Always enable RLS** on tables with sensitive data
2. **Use indexes** on columns used in RLS policies (workspaceId, userId)
3. **Test policies** with different user roles before deploying
4. **Use service role** sparingly and only for admin operations
5. **Combine with Prisma RLS** using Prisma middleware or query filters
6. **Monitor performance** - Complex RLS policies can slow down queries
7. **Document policies** - Comment SQL to explain business logic
8. **Version control** - Keep RLS SQL in migration files or scripts
