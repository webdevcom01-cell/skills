# Example: pgvector Migration

Complete walkthrough for adding vector embeddings to enable semantic search.

## Scenario

Add vector embeddings to the KBChunk model to enable semantic search over knowledge base content.

## Prerequisites

Ensure pgvector extension is enabled in your database:

```sql
-- Check if pgvector is available
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Enable pgvector (run in Supabase SQL editor or psql)
CREATE EXTENSION IF NOT EXISTS vector;
```

## Step 1: Update Prisma Schema

Ensure datasource includes pgvector extension:

```prisma
datasource db {
  provider   = "postgresql"
  url        = env("DATABASE_URL")
  extensions = [pgvector(map: "vector")]
}
```

## Step 2: Add Vector Field to Model

Update the KBChunk model in `prisma/schema.prisma`:

```prisma
model KBChunk {
  id        String                       @id @default(cuid())
  content   String                       @db.Text
  embedding Unsupported("vector(1536)")?  // ADD THIS LINE - OpenAI ada-002 embeddings
  tokens    Int                          @default(0)
  metadata  Json?
  createdAt DateTime                     @default(now())

  sourceId String
  source   KBSource @relation(fields: [sourceId], references: [id], onDelete: Cascade)

  @@index([sourceId])
}
```

**Vector Dimensions**:
- `vector(1536)` - OpenAI text-embedding-ada-002, text-embedding-3-small
- `vector(3072)` - OpenAI text-embedding-3-large
- `vector(768)` - Sentence Transformers (all-MiniLM-L6-v2)
- `vector(384)` - Smaller sentence transformers models

**Important**: Vector fields must ALWAYS be optional (`?`) in Prisma.

## Step 3: Create Migration

```bash
cd ~/direct-solutions
pnpm dlx prisma migrate dev --name add-vector-embeddings
```

This generates the SQL migration but **does not create the vector index** yet.

## Step 4: Add HNSW Index (Manual SQL)

Create `prisma/migrations/20260212000001_add_vector_index/migration.sql`:

```sql
-- Create HNSW index for fast vector similarity search
-- Using cosine distance (most common for normalized embeddings)
CREATE INDEX IF NOT EXISTS idx_kbchunk_embedding_hnsw
  ON "KBChunk"
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (faster to build, slower queries)
-- Uncomment if you have very large datasets and want faster indexing
-- CREATE INDEX IF NOT EXISTS idx_kbchunk_embedding_ivfflat
--   ON "KBChunk"
--   USING ivfflat (embedding vector_cosine_ops)
--   WITH (lists = 100);
```

Apply the index migration:

```bash
pnpm dlx prisma migrate dev --name add-vector-index
```

### HNSW Index Parameters

- **`m`** (default: 16): Maximum number of connections per layer
  - Lower = faster build, less memory, lower recall
  - Higher = slower build, more memory, higher recall
  - Recommended: 16-32

- **`ef_construction`** (default: 64): Size of dynamic candidate list during construction
  - Lower = faster build, lower recall
  - Higher = slower build, higher recall
  - Recommended: 64-128

### Distance Operators

```sql
-- Cosine distance (1 - cosine similarity) - MOST COMMON
embedding <=> query_vector

-- L2 distance (Euclidean distance)
embedding <-> query_vector

-- Inner product (negative dot product)
embedding <#> query_vector
```

## Step 5: Update Database Helper Functions

Create `src/lib/knowledge/embeddings.ts`:

```typescript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

/**
 * Generate embeddings for text using OpenAI
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  try {
    const response = await openai.embeddings.create({
      model: 'text-embedding-3-small', // or text-embedding-ada-002
      input: text,
      encoding_format: 'float',
    });

    return response.data[0].embedding;
  } catch (error) {
    console.error('Error generating embedding:', error);
    throw new Error('Failed to generate embedding');
  }
}

/**
 * Generate embeddings for multiple texts (batch)
 */
export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  try {
    const response = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: texts,
      encoding_format: 'float',
    });

    return response.data.map((item) => item.embedding);
  } catch (error) {
    console.error('Error generating embeddings:', error);
    throw new Error('Failed to generate embeddings');
  }
}
```

## Step 6: Create Vector Search Function

Create `src/lib/knowledge/search.ts`:

```typescript
import { prisma } from '@/lib/prisma';
import { generateEmbedding } from './embeddings';
import type { Prisma } from '@/generated/prisma/client';

export interface SearchResult {
  id: string;
  content: string;
  similarity: number;
  tokens: number;
  metadata: any;
  source: {
    id: string;
    name: string;
    type: string;
  };
}

/**
 * Semantic search using vector similarity
 */
export async function searchKnowledgeBase(
  query: string,
  sourceIds?: string[],
  limit: number = 10,
  threshold: number = 0.7
): Promise<SearchResult[]> {
  // Generate embedding for query
  const queryEmbedding = await generateEmbedding(query);

  // Convert embedding to Postgres vector format
  const vectorString = `[${queryEmbedding.join(',')}]`;

  // Build WHERE clause
  const whereConditions: string[] = [];
  const params: any[] = [vectorString, limit];
  let paramIndex = 3;

  if (sourceIds && sourceIds.length > 0) {
    whereConditions.push(`"sourceId" = ANY($${paramIndex})`);
    params.push(sourceIds);
    paramIndex++;
  }

  const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';

  // Raw SQL query using pgvector
  const results = await prisma.$queryRaw<Array<{
    id: string;
    content: string;
    tokens: number;
    metadata: any;
    similarity: number;
    source_id: string;
    source_name: string;
    source_type: string;
  }>>`
    SELECT
      c.id,
      c.content,
      c.tokens,
      c.metadata,
      1 - (c.embedding <=> ${vectorString}::vector) AS similarity,
      s.id as source_id,
      s.name as source_name,
      s.type as source_type
    FROM "KBChunk" c
    JOIN "KBSource" s ON s.id = c."sourceId"
    ${Prisma.raw(whereClause)}
    WHERE c.embedding IS NOT NULL
      AND 1 - (c.embedding <=> ${vectorString}::vector) >= ${threshold}
    ORDER BY c.embedding <=> ${vectorString}::vector
    LIMIT ${limit}
  `;

  return results.map((row) => ({
    id: row.id,
    content: row.content,
    similarity: row.similarity,
    tokens: row.tokens,
    metadata: row.metadata,
    source: {
      id: row.source_id,
      name: row.source_name,
      type: row.source_type,
    },
  }));
}

/**
 * Hybrid search combining vector similarity and full-text search
 */
export async function hybridSearch(
  query: string,
  sourceIds?: string[],
  limit: number = 10
): Promise<SearchResult[]> {
  const queryEmbedding = await generateEmbedding(query);
  const vectorString = `[${queryEmbedding.join(',')}]`;

  const whereConditions: string[] = [];
  if (sourceIds && sourceIds.length > 0) {
    whereConditions.push(`"sourceId" = ANY($3)`);
  }
  const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';

  const params = sourceIds && sourceIds.length > 0
    ? [vectorString, limit, sourceIds]
    : [vectorString, limit];

  // Combine vector similarity (70%) and text search (30%)
  const results = await prisma.$queryRaw<Array<{
    id: string;
    content: string;
    tokens: number;
    metadata: any;
    similarity: number;
    source_id: string;
    source_name: string;
    source_type: string;
  }>>`
    SELECT
      c.id,
      c.content,
      c.tokens,
      c.metadata,
      (
        0.7 * (1 - (c.embedding <=> ${vectorString}::vector)) +
        0.3 * ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', ${query}))
      ) AS similarity,
      s.id as source_id,
      s.name as source_name,
      s.type as source_type
    FROM "KBChunk" c
    JOIN "KBSource" s ON s.id = c."sourceId"
    ${Prisma.raw(whereClause)}
    WHERE c.embedding IS NOT NULL
    ORDER BY similarity DESC
    LIMIT ${limit}
  `;

  return results.map((row) => ({
    id: row.id,
    content: row.content,
    similarity: row.similarity,
    tokens: row.tokens,
    metadata: row.metadata,
    source: {
      id: row.source_id,
      name: row.source_name,
      type: row.source_type,
    },
  }));
}
```

## Step 7: Update Chunk Creation

Update `src/lib/knowledge/chunking.ts`:

```typescript
import { prisma } from '@/lib/prisma';
import { generateEmbeddings } from './embeddings';

export async function createChunks(
  sourceId: string,
  chunks: Array<{ content: string; tokens: number; metadata?: any }>
) {
  // Generate embeddings for all chunks
  const embeddings = await generateEmbeddings(chunks.map((c) => c.content));

  // Create chunks with embeddings
  await prisma.kBChunk.createMany({
    data: chunks.map((chunk, index) => ({
      sourceId,
      content: chunk.content,
      tokens: chunk.tokens,
      metadata: chunk.metadata || {},
      // Convert embedding array to Postgres vector string
      embedding: `[${embeddings[index].join(',')}]` as any,
    })),
  });
}
```

## Step 8: Create API Endpoint

Create `src/app/api/knowledge/search/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from '@/lib/auth';
import { searchKnowledgeBase, hybridSearch } from '@/lib/knowledge/search';
import { z } from 'zod';

const searchSchema = z.object({
  query: z.string().min(1).max(500),
  sourceIds: z.array(z.string().cuid()).optional(),
  limit: z.number().int().min(1).max(50).default(10),
  threshold: z.number().min(0).max(1).default(0.7),
  mode: z.enum(['vector', 'hybrid']).default('vector'),
});

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { query, sourceIds, limit, threshold, mode } = searchSchema.parse(body);

    const results = mode === 'hybrid'
      ? await hybridSearch(query, sourceIds, limit)
      : await searchKnowledgeBase(query, sourceIds, limit, threshold);

    return NextResponse.json({
      results,
      query,
      count: results.length,
    });
  } catch (error) {
    console.error('POST /api/knowledge/search error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

## Step 9: Backfill Existing Data (Optional)

Create a script to generate embeddings for existing chunks:

```typescript
// scripts/backfill-embeddings.ts
import { prisma } from '../src/lib/prisma';
import { generateEmbeddings } from '../src/lib/knowledge/embeddings';

async function backfillEmbeddings() {
  console.log('Fetching chunks without embeddings...');

  const chunks = await prisma.kBChunk.findMany({
    where: { embedding: null },
    select: { id: true, content: true },
  });

  console.log(`Found ${chunks.length} chunks to process`);

  const batchSize = 100;
  for (let i = 0; i < chunks.length; i += batchSize) {
    const batch = chunks.slice(i, i + batchSize);
    console.log(`Processing batch ${i / batchSize + 1}/${Math.ceil(chunks.length / batchSize)}`);

    const embeddings = await generateEmbeddings(batch.map((c) => c.content));

    await Promise.all(
      batch.map((chunk, index) =>
        prisma.kBChunk.update({
          where: { id: chunk.id },
          data: {
            embedding: `[${embeddings[index].join(',')}]` as any,
          },
        })
      )
    );
  }

  console.log('Backfill complete!');
}

backfillEmbeddings().catch(console.error);
```

Run the backfill:

```bash
npx tsx scripts/backfill-embeddings.ts
```

## Performance Tips

1. **Batch embedding generation**: Process 100-500 texts at once
2. **Use HNSW index**: Better recall than IVFFlat for most use cases
3. **Set similarity threshold**: Filter low-quality results (0.7+ is good)
4. **Monitor token usage**: OpenAI charges per token for embeddings
5. **Cache frequent queries**: Store common query embeddings
6. **Use hybrid search**: Combine vector + text search for best results

## Monitoring Vector Performance

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'KBChunk';

-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('KBChunk'));

-- Explain query plan
EXPLAIN ANALYZE
SELECT id, content, 1 - (embedding <=> '[0.1,0.2,...]'::vector) AS similarity
FROM "KBChunk"
ORDER BY embedding <=> '[0.1,0.2,...]'::vector
LIMIT 10;
```

## Summary

You've successfully:
1. Added vector field to KBChunk model
2. Created HNSW index for fast similarity search
3. Implemented embedding generation
4. Created semantic search functions
5. Built API endpoint for vector search
6. Set up backfill script for existing data

Your knowledge base now supports semantic search!
