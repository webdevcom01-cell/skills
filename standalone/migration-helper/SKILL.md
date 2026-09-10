---
name: migration-helper
description: This skill should be used when the user asks to "create migration", "add model", "schema change", "new table", "database migration", "prisma migrate", "add field", "add column", "modify schema", or needs to generate Prisma schema changes with proper indexing and multi-tenancy.
version: 1.0.0
---

# Migration Helper Skill

This skill helps generate Prisma schema changes with proper indexing, multi-tenancy patterns, and RLS policies for the Direct Solutions project.

## Project Configuration

- **Stack**: Prisma v7 + PostgreSQL + pgvector extension
- **Generator**: `prisma-client` outputting to `../src/generated/prisma`
- **Preview Features**: `postgresqlExtensions`
- **Multi-tenancy**: All tenant-scoped models include `workspaceId`
- **Commands**:
  - Generate: `pnpm dlx prisma generate`
  - Migrate: `pnpm dlx prisma migrate dev --name <migration-name>`
- **Schema Location**: `prisma/schema.prisma`

## Workflow

1. **Read current schema**: Use Read tool to examine `prisma/schema.prisma`
2. **Determine changes**: Identify what models/fields/relations need to be added
3. **Generate schema additions**: Apply proper patterns and conventions
4. **Run migration**: Execute `pnpm dlx prisma migrate dev --name <migration-name>`
5. **Optionally generate RLS SQL**: Create RLS policies for security
6. **Verify**: Run `pnpm dlx prisma generate` to ensure schema is valid

## Schema Conventions

### IDs and Timestamps
- IDs: `@id @default(cuid())`
- Created timestamp: `createdAt DateTime @default(now())`
- Updated timestamp: `updatedAt DateTime @updatedAt`

### Multi-tenancy Pattern
For ALL tenant-scoped models, include:
```prisma
workspaceId String
workspace   Workspace @relation(fields: [workspaceId], references: [id], onDelete: Cascade)

@@index([workspaceId])
```

### Field Types
- **Long text**: `String @db.Text`
- **Vector embeddings**: `Unsupported("vector(1536)")? ` (always optional, requires raw SQL for operations)
- **JSON fields**: `Json @default("{}")` or `Json?`
- **Enums**: PascalCase names, UPPER_SNAKE_CASE values

### Relations
- **Cascade deletes**: Always use `onDelete: Cascade` on child relations
- **One-to-one**: Use `@unique` on the foreign key field
- **Many-to-many**: Use junction table with compound unique constraint

### Indexes
- Always index `workspaceId` on tenant-scoped models
- Index foreign keys for better query performance
- Use compound indexes for common query patterns: `@@index([field1, field2])`
- Add status/type indexes where relevant: `@@index([status])`, `@@index([type])`

### Unique Constraints
- Single field: `@unique`
- Multiple fields: `@@unique([field1, field2])`
- Optional unique: `fieldName String? @unique`

## Migration Naming

Use kebab-case descriptive names:
- `add-user-email`
- `create-notification-model`
- `add-status-index`
- `add-vector-embeddings`
- `create-analytics-tables`

## Post-Migration Tasks

1. **Update validations**: Add Zod schemas to `src/lib/validations.ts`
2. **Update types**: Add TypeScript types to `src/types/index.ts` if needed
3. **Generate client**: Run `pnpm dlx prisma generate`
4. **Test queries**: Verify database operations work correctly

## RLS Security

For production deployments, generate RLS policies:
1. Enable RLS on new tables
2. Create workspace-scoped policies using `auth.uid()`
3. Add public read policies for published resources
4. Create proper indexes (GIN for text search, HNSW for vectors)

## Common Patterns

Refer to:
- `references/prisma-patterns.md` for model templates
- `references/rls-templates.md` for security policies
- `examples/new-model-migration.md` for complete workflow example
- `examples/pgvector-migration.md` for vector embedding example
