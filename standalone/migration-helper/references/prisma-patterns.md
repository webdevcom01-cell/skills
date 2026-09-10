# Prisma Schema Patterns

Complete model templates and patterns for the Direct Solutions project.

## Generator and Datasource

```prisma
generator client {
  provider        = "prisma-client"
  output          = "../src/generated/prisma"
  previewFeatures = ["postgresqlExtensions"]
}

datasource db {
  provider   = "postgresql"
  url        = env("DATABASE_URL")
  extensions = [pgvector(map: "vector")]
}
```

## 1. Standard Tenant-Scoped Model

Model with workspaceId, timestamps, and proper indexes:

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

  flows         Flow[]
  knowledgeBase KnowledgeBase?
  channels      Channel[]

  @@index([workspaceId])
  @@index([status])
}
```

## 2. Child Model with Parent Relation

Model with cascade delete and parent reference:

```prisma
model Flow {
  id          String   @id @default(cuid())
  name        String
  description String?
  isMain      Boolean  @default(false)
  isPublished Boolean  @default(false)
  nodes       Json     @default("[]")
  edges       Json     @default("[]")
  variables   Json     @default("{}")
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  agentId String
  agent   Agent  @relation(fields: [agentId], references: [id], onDelete: Cascade)

  workspaceId String
  workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  @@index([agentId])
  @@index([workspaceId])
  @@index([isPublished])
}
```

## 3. Junction/Pivot Model (Many-to-Many)

Model for many-to-many relationships with compound unique:

```prisma
model WorkspaceMember {
  id        String           @id @default(cuid())
  role      WorkspaceRole    @default(MEMBER)
  joinedAt  DateTime         @default(now())
  updatedAt DateTime         @updatedAt

  userId String
  user   User   @relation(fields: [userId], references: [id], onDelete: Cascade)

  workspaceId String
  workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  @@unique([userId, workspaceId])
  @@index([userId])
  @@index([workspaceId])
}
```

## 4. Model with Vector Field

Model with pgvector embeddings:

```prisma
model KBChunk {
  id        String                       @id @default(cuid())
  content   String                       @db.Text
  embedding Unsupported("vector(1536)")?
  tokens    Int                          @default(0)
  metadata  Json?
  createdAt DateTime                     @default(now())

  sourceId String
  source   KBSource @relation(fields: [sourceId], references: [id], onDelete: Cascade)

  @@index([sourceId])
}
```

**Important**: Vector fields must be:
- `Unsupported("vector(1536)")` for OpenAI embeddings (or 768/3072 for other models)
- Always optional (`?`)
- Requires raw SQL for similarity search operations

## 5. Model with JSON Config

Model with JSON configuration fields:

```prisma
model Channel {
  id          String      @id @default(cuid())
  type        ChannelType
  name        String
  isActive    Boolean     @default(true)
  config      Json        @default("{}")
  voiceConfig Json?
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt

  agentId String
  agent   Agent  @relation(fields: [agentId], references: [id], onDelete: Cascade)

  workspaceId String
  workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  conversations Conversation[]

  @@unique([agentId, type])
  @@index([agentId])
  @@index([workspaceId])
  @@index([type])
}
```

## 6. One-to-One Model

Model with one-to-one relationship using @unique on foreign key:

```prisma
model KnowledgeBase {
  id          String   @id @default(cuid())
  name        String
  description String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  agentId String        @unique
  agent   Agent         @relation(fields: [agentId], references: [id], onDelete: Cascade)

  workspaceId String
  workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  sources KBSource[]

  @@index([workspaceId])
}
```

**Key**: The `@unique` on `agentId` enforces one-to-one relationship.

## 7. Enum Declaration Pattern

```prisma
enum AgentStatus {
  DRAFT
  PUBLISHED
  PAUSED
}

enum ChannelType {
  WEB
  WHATSAPP
  VOICE
  EMAIL
  API
}

enum WorkspaceRole {
  OWNER
  ADMIN
  MEMBER
}

enum SubscriptionStatus {
  ACTIVE
  CANCELED
  PAST_DUE
  TRIALING
}
```

**Conventions**:
- Enum name: PascalCase
- Enum values: UPPER_SNAKE_CASE

## 8. Model with Compound Indexes

Model with multiple compound indexes for query optimization:

```prisma
model Conversation {
  id        String   @id @default(cuid())
  status    String   @default("active")
  metadata  Json?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  agentId String
  agent   Agent  @relation(fields: [agentId], references: [id], onDelete: Cascade)

  channelId String
  channel   Channel @relation(fields: [channelId], references: [id], onDelete: Cascade)

  workspaceId String
  workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  messages Message[]

  @@index([agentId, createdAt(sort: Desc)])
  @@index([channelId, createdAt(sort: Desc)])
  @@index([workspaceId, status])
  @@index([status])
}
```

## 9. Self-Referencing Model

Model with self-referencing relationship:

```prisma
model Comment {
  id        String   @id @default(cuid())
  content   String   @db.Text
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  userId String
  user   User   @relation(fields: [userId], references: [id], onDelete: Cascade)

  parentId String?
  parent   Comment?  @relation("CommentThread", fields: [parentId], references: [id], onDelete: Cascade)
  replies  Comment[] @relation("CommentThread")

  workspaceId String
  workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

  @@index([parentId])
  @@index([userId])
  @@index([workspaceId])
}
```

## 10. Model with Optional Unique Fields

Model with optional unique constraint:

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

  @@index([email])
}
```

## Adding Relations to Workspace Model

When adding a new tenant-scoped model, update the Workspace model:

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
  // ADD NEW RELATION HERE
  notifications  Notification[]  // Example

  @@index([ownerId])
  @@index([slug])
}
```

## Available Prisma Field Types

- `String` - Variable length text
- `Int` - Integer number
- `Float` - Floating point number
- `Boolean` - True/false
- `DateTime` - Date and time
- `Json` - JSON data
- `BigInt` - Large integer
- `Bytes` - Binary data
- `Decimal` - Precise decimal number
- `Unsupported("type")` - Database-specific types (like vector)

## Prisma Attributes Reference

### Field Attributes
- `@id` - Primary key
- `@default(value)` - Default value (cuid(), now(), uuid(), autoincrement(), etc.)
- `@unique` - Unique constraint
- `@db.Text` - Map to TEXT column (for long strings)
- `@updatedAt` - Auto-update timestamp
- `@relation(fields: [...], references: [...], onDelete: Cascade)` - Define relation

### Block Attributes
- `@@id([field1, field2])` - Compound primary key
- `@@unique([field1, field2])` - Compound unique constraint
- `@@index([field1, field2])` - Index for query performance
- `@@map("table_name")` - Custom table name

### OnDelete Behaviors
- `Cascade` - Delete related records (most common for child records)
- `SetNull` - Set foreign key to null
- `Restrict` - Prevent deletion
- `NoAction` - Database default behavior
