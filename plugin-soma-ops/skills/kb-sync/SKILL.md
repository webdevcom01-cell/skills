---
name: kb-sync
description: Syncs Obsidian vault files into Agent Studio knowledge bases using True-Sync (ADD new, wait READY, DELETE old). Use this skill whenever the user wants to sync vault docs to agent KBs, update agent memory, keep KB in sync after editing instincts or evo-logs, run a KB refresh, or says things like "sync the KB", "update agent memory", "push vault to KB", "KB is out of date", "sync SOMA agents", "refresh agent knowledge", "sinkronizuj KB", "azuriraj KB", "sync instincts", or "uradi kb sync". Change detection uses SHA-256 hash comparison against stored contentHash so only actually changed files are re-ingested. Handles rate limiting, ADD-before-DELETE ordering, and per-document polling automatically; old KB sources are DELETED only after explicit user approval (fail-closed). Do NOT use for creating new agents or KBs from scratch (use agent-scaffolder), diagnosing broken flows (use agent-health-check), or editing agent prompts directly.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TodoWrite
  - mcp__agent-studio__as_list_knowledge_bases
  - mcp__agent-studio-db__as_list_knowledge_bases
  - mcp__agent-studio__as_add_kb_text
  - mcp__agent-studio-db__as_add_kb_text
  - mcp__agent-studio__as_get_kb_embedding_status
  - mcp__agent-studio-db__as_get_kb_embedding_status
  - mcp__obsidian__obsidian_list_notes
  - mcp__obsidian__obsidian_list_folders
  - mcp__obsidian__obsidian_read_note
---

# Skill: kb-sync
*Version: 1.1 | Based on: kb-sync-implementation-plan.md + kb-sync-critical-review.md (added DELETE approval gate)*
*1.2 (2026-08-22): Default Scope, Rate Limiting Reference, Tool Reference, and Error Handling Reference moved to references/reference-tables.md — file was approaching the repo's size limit. No behavior change.*
*Zero-hallucination implementation — every design decision grounded in live codebase reads*

---

## Trigger

Use this skill when the user wants to:
- Sync Obsidian vault files into Agent Studio knowledge bases
- Keep agent KB memory up to date after editing instincts, evo-logs, or other vault docs
- Check whether agents' KB documents are in sync with the vault
- Run a one-off or routine sync across all SOMA agents

Do NOT use this skill for:
- Creating a new agent or KB from scratch → use `agent-scaffolder`
- Diagnosing broken flows or embedding failures → use `agent-health-check`
- Editing agent prompts or flow nodes → use `as_patch_node_field` directly

---

## What This Skill Does

Performs a **True-Sync** between Obsidian vault files and Agent Studio knowledge bases:

1. Reads existing KB sources via HTTP GET (gets `contentHash` — SHA-256 of full ingested text)
2. Reads each Obsidian file and computes its SHA-256 locally
3. Compares hashes — skips files that are already in sync
4. For changed or missing files: **ADD new first → wait READY → DELETE old** (prevents KB gap)
5. Respects the 10 POST/min rate limit with a 7-second buffer between ADD operations
6. Reports per-agent: ADDED | UPDATED | SKIPPED | WARNINGS | ERRORS

**Critical design choices (all grounded in codebase analysis):**
- Change detection uses `KBSource.contentHash` from HTTP GET — NOT `as_search_knowledge_base` (which returns chunks, not full documents; chunk SHA-256 ≠ document SHA-256)
- Sync order is ADD→wait→DELETE (not DELETE→ADD) to prevent KB gap if ADD fails
- DELETE requires explicit user approval — a run-level confirmation gate (Step 5.0) before any source is deleted; fail-closed (skip deletes, keep duplicates) if not approved
- Timestamp comparison is NOT used — `customMetadata` is not stored by the ingest pipeline
- Field matching uses `source.name` from HTTP GET (not "title" — that is only an MCP input param)

---

## STEP 0 — Task List

Call TaskCreate for each step:
- "STEP 0 — Collect preconditions and verify scope"
- "STEP 1 — Discover Obsidian vault structure"
- "STEP 2 — Fetch KB metadata for all agents"
- "STEP 3 — Sync agent: Trend Intelligence"
- "STEP 4 — Sync agent: Hook Writer"
- "STEP 5 — Sync agent: Content Repurposer"
- "STEP 6 — Sync agent: Score Analyzer"
- "STEP 7 — Final report"

Mark each in_progress before starting, completed when done.

---

## STEP 1 — Collect Preconditions

**Before doing any work**, confirm the user has provided:

### Required inputs
1. **AGENT_STUDIO_URL** — the Railway production URL
   - Correct value: `https://agent-studio-production-c43e.up.railway.app`
   - Do NOT use `localhost:3000` — it is not accessible from the Cowork session
   - If not provided, ask the user: *"Please confirm your AGENT_STUDIO_URL (the Railway production URL, not localhost)"*

2. **AGENT_STUDIO_API_KEY** — an active API key from Agent Studio
   - User can find it at: Agent Studio → Settings → API Keys
   - If not provided, ask: *"Please provide your AGENT_STUDIO_API_KEY from Agent Studio Settings → API Keys"*

Store both as variables. Use them in every bash curl call:
```
AGENT_STUDIO_URL="https://agent-studio-production-c43e.up.railway.app"
AGENT_STUDIO_API_KEY="<key provided by user>"
```

**Do not proceed past Step 1 until both values are confirmed.**

### Optional scope override
Default scope is all 4 SOMA agents. If the user specifies a subset (e.g., "only TI and HW"), restrict to those agents.

---

## STEP 2 — Discover Obsidian Vault Structure

For each agent in scope, list the files that exist in its Obsidian folder.
This step prevents syncing files that don't exist and discovers new files automatically.

Use `obsidian_list_notes` for each agent folder:

```
obsidian_list_notes(folder="agents/trend-intelligence")
obsidian_list_notes(folder="agents/hook-writer")
obsidian_list_notes(folder="agents/content-repurposer")
obsidian_list_notes(folder="agents/score-analyzer")
```

**IMPORTANT — folder name mapping:**
Confirmed vault structure (verified 2026-05-16): `agents/{slug}` e.g. `agents/trend-intelligence`.
If `obsidian_list_notes` returns no results, call `obsidian_list_folders` to discover the actual structure before assuming any path.

For each note found, derive the KB source title using the naming convention:
```
KB title = "{agent-folder-slug}/{note-filename-without-extension}"
```

Where `agent-folder-slug` is the lowercase hyphenated version of the agent folder:
| Agent | KB title prefix |
|---|---|
| Trend Intelligence | `trend-intelligence` |
| Hook Writer | `hook-writer` |
| Content Repurposer | `content-repurposer` |
| Score Analyzer | `score-analyzer` |

**Example:** Obsidian note `agents/trend-intelligence/instincts.md` → KB title `trend-intelligence/instincts`

Store the discovered files per agent as:
```
ti_files = [ { obsidian_path: "...", kb_title: "trend-intelligence/instincts" }, ... ]
hw_files = [ ... ]
cr_files = [ ... ]
sa_files = [ ... ]
```

---

## STEP 3 — Fetch KB Metadata (MCP)

For each agent in scope, call:
```
as_list_knowledge_bases(agent_name: "<name>")
```

This returns: `{ bases: [...], count: N }` where each base has:
- `id` — KB ID (needed for as_add_kb_text and as_get_kb_embedding_status)
- `name` — KB name
- `embeddingStatus` — overall KB status

Store per agent: `{ kb_id, agent_id, kb_name, embeddingStatus }`

**Note:** `as_list_knowledge_bases` also returns `agentId` in its response — use that directly. Do NOT use the KB id as agent_id. They are different values.

If `count == 0` for an agent → log WARNING: "Agent {name} has no knowledge base. Skipping." and continue to next agent.

---

## STEP 4 — Fetch Existing KB Sources (bash curl)

For each agent that has a KB, fetch the current KB sources to get content hashes:

```bash
curl -s -X GET \
  "{AGENT_STUDIO_URL}/api/agents/{agent_id}/knowledge/sources" \
  -H "x-api-key: {AGENT_STUDIO_API_KEY}" \
  -H "Content-Type: application/json"
```

This returns an array of KBSource objects, each containing:
```json
{
  "id": "...",
  "name": "trend-intelligence/instincts",
  "status": "READY",
  "contentHash": "sha256hexstring...",
  "charCount": 1234,
  "createdAt": "...",
  "updatedAt": "..."
}
```

**Field name is `name` (not `title`, not `sourceTitle`).** Always match Obsidian files to KB sources by comparing `kb_title == source.name`.

Index the results by `name` for O(1) lookup:
```
kb_sources_index = { "trend-intelligence/instincts": { id, name, contentHash, status }, ... }
```

**⚠️ Legacy naming convention mismatch:** Before the `{agent-slug}/{filename}` convention
was adopted, KB sources were created with human-friendly names (e.g., `"TI Evo Log"`,
`"HW Instincts"`, `"CR Format Templates"`). These legacy sources will NOT match `kb_title`.
- They appear in `kb_sources_index` under their old name — lookup by `kb_title` misses them
- The file is treated as **Case A** (source not found by name) → ADD with correct new name only
- **⚠️ The old legacy source is NOT automatically deleted.** Case A (Step 5e) only ADDs —
  there is no DELETE step. The legacy source remains in the KB as a duplicate with the old name.
- The `contentHash: null` rule applies only to **Case B** (source found by name). It does NOT
  cover the name-mismatch scenario where lookup fails.
- **After first sync following naming convention migration:** both the new source (correct name)
  and the old legacy source (wrong name) will exist in the KB simultaneously. Manual cleanup
  is required: use `curl DELETE {AGENT_STUDIO_URL}/api/agents/{agent_id}/knowledge/sources/{legacy_id}`
  to remove each legacy source by its ID after confirming the new source is READY.
- Identify legacy source IDs from the `kb_sources_index` — they are the entries whose `name`
  does not match any `kb_title` in the discovered file list.

If the curl call fails (non-200 response), log ERROR for that agent and skip it.

---

## STEP 5 — Change Detection and Sync (per agent, per file)

### 5.0 — DELETE approval gate (MANDATORY before any DELETE)

This skill replaces old KB sources by deleting them (Step 5f‑iii). **No source is deleted without explicit user approval.**

- During change detection, collect every planned deletion as `{kb_title, old_source_id}`.
- **Before executing the FIRST DELETE this run**, present the full list and ask the user to confirm: *"These N old KB sources will be permanently deleted after their replacements are READY. Approve? (da / obriši / yes)"*.
- **Fail‑closed:** if the user does not explicitly approve, **skip ALL deletes** — keep the newly‑added versions and leave the old ones as duplicates, then report them under WARNINGS. (Adds are non‑destructive and may proceed; only deletes are gated.)
- One approval covers all deletes in this run; record it before proceeding.

---

For each file in the agent's discovered file list:

### 5a. Read Obsidian content
```
obsidian_read_note(path: "{obsidian_path}")
```
Store the content string.

### 5b. Compute SHA-256 of Obsidian content
Use bash to compute the hash:
```bash
echo -n "{content}" | sha256sum | cut -d' ' -f1
```

**IMPORTANT:** The `contentHash` stored in Agent Studio is computed by:
```typescript
createHash("sha256").update(text).digest("hex")
```
where `text` is the raw string content passed to the ingest pipeline. This is the **Node.js Buffer default encoding** (UTF-8). Use `echo -n` (no trailing newline) and pipe through `sha256sum` to match.

**⚠️ Leading whitespace sensitivity:** The hash is computed from the **exact bytes**
of the string, including any leading or trailing whitespace. If `obsidian_read_note`
prepends a `\n` to the content body (or if the original ingest included/excluded one),
hashes will diverge even when visible content appears identical.
- If a hash mismatch is unexpected on apparently-identical content → check for leading `\n`
- Strip leading whitespace before hashing if needed: `sed '1{/^$/d}' file` or use
  `.lstrip()` on the content string before writing to the temp file
- The stored `contentHash` reflects exactly what was passed to `as_add_kb_text` —
  match that byte-for-byte, including any leading newline the MCP tool may prepend

If content contains special characters, write to a temp file first:
```bash
cat > /tmp/kb_hash_input.txt << 'CONTENT_EOF'
{content}
CONTENT_EOF
sha256sum /tmp/kb_hash_input.txt | cut -d' ' -f1
```

Store as `obsidian_hash`.

### 5c. Look up existing KB source
Find entry in `kb_sources_index` where `source.name == kb_title`.

### 5d. Decision logic

**Case A — KB source does NOT exist (new file):**
→ Proceed to ADD (Step 5e)

**Case B — KB source exists AND `source.status == "READY"`:**
- If `source.contentHash == null` (legacy doc — ingested before contentHash was implemented) → treat as CHANGED → Proceed to UPDATE (Step 5f). Do NOT skip null-hash docs.
- If `obsidian_hash == source.contentHash` → log `SKIPPED: {kb_title} (in sync)` → continue to next file
- If `obsidian_hash != source.contentHash` → Proceed to UPDATE (Step 5f)

**Note on null contentHash:** All documents ingested before the contentHash feature was implemented have `contentHash: null`. Confirmed on 2026-05-16 with TI, HW, CR legacy sources. When null, hash comparison is impossible — always treat as stale and re-ingest.

**Case C — KB source exists AND `source.status != "READY"` (PENDING or PROCESSING or FAILED):**
→ log `WARNING: SKIPPED {kb_title} (status={status}, manual check needed)`
→ Do NOT attempt add or delete
→ Continue to next file

### 5e. ADD — New file (Case A)

```
as_add_kb_text(
  kb_id: "{kb_id}",
  text: "{obsidian_content}",
  title: "{kb_title}"
)
```

**Note on parameter names:**
- `as_add_kb_text` accepts `title` as the input parameter name
- Internally it maps to `{ name: title }` in the HTTP POST body
- The resulting `KBSource.name` will equal the `title` you passed
- ALWAYS use the `"{agent-folder-slug}/{filename-without-extension}"` convention

Store the returned `documentId` (= `KBSource.id`).

**Poll for READY status:**
```
Loop up to 30 times with 10s sleep:
  as_get_kb_embedding_status(
    kb_id: "{kb_id}",
    document_id: "{documentId}"
  )
  → Check returned status field
  → If "READY" → break
  → If "FAILED" → log ERROR: "Embedding failed for {kb_title}" → break
  → Otherwise → sleep 10s and retry
```

**IMPORTANT:** Use per-document polling with `document_id=documentId`, NOT aggregate polling. Aggregate polling is misleading if other documents in the KB are still processing.

If READY confirmed → log `ADDED: {kb_title}`

**Rate limit buffer:** After every successful `as_add_kb_text` call, wait 7 seconds before the next ADD operation. This prevents hitting the 10 POST/min rate limit (`checkRateLimit("kb-source:userId", 10)` with `WINDOW_MS=60000`).

### 5f. UPDATE — Changed file (Case B, hashes differ)

**Order is ADD → wait READY → DELETE (never DELETE → ADD).**
This ensures the KB never has a gap if the ADD fails.

**Step i — ADD new version:**
Same as 5e (ADD), but remember the `old_source_id = source.id` from the index.

**Step ii — Wait for READY** (same polling loop as 5e)

**Step iii — DELETE old version:**

> ⛔ **Gate:** Only proceed if the run‑level DELETE approval (Step 5.0) was granted. If not approved, SKIP this delete and log `PENDING-DELETE: {kb_title} (id={old_source_id}) — awaiting approval`, then continue.

```bash
curl -s -X DELETE \
  "{AGENT_STUDIO_URL}/api/agents/{agent_id}/knowledge/sources/{old_source_id}" \
  -H "x-api-key: {AGENT_STUDIO_API_KEY}"
```

Expected response: `{ "success": true }`

If DELETE fails:
- Log `WARNING: UPDATE {kb_title} — new version added but old version (id={old_source_id}) could not be deleted. Duplicate exists. Content is correct.`
- Do NOT retry DELETE automatically — leave for manual cleanup
- Continue to next file

If DELETE succeeds → log `UPDATED: {kb_title}`

**Rate limit buffer:** 7 seconds after each ADD (same as 5e).

---

## STEP 6 — Final Report Per Agent

After processing all files for an agent, output:

```
📋 {AGENT NAME} KB Sync Report
─────────────────────────────────
KB: {kb_name} ({kb_id})
Files checked: {N}

✅ ADDED:   {N} files
🔄 UPDATED: {N} files
⏭️  SKIPPED: {N} files (already in sync)
⚠️  WARNINGS: {N}
❌ ERRORS:  {N}

{List any warnings or errors with details}
```

After all agents, output an overall summary:
```
════════════════════════════════════════
KB SYNC COMPLETE
════════════════════════════════════════
Agents processed: {N}
Total ADDED:   {N}
Total UPDATED: {N}
Total SKIPPED: {N}
Total WARNINGS: {N}
Total ERRORS:   {N}

{If any ERRORS or WARNINGS: list them here with context}
════════════════════════════════════════
```

---

## Reference tables

**Read `references/reference-tables.md`** for: Default Scope (the 4 SOMA agents, their KB title prefix and Obsidian folder), Rate Limiting Reference (the 7s ADD buffer, 429 handling), Tool Reference (MCP and curl call signatures), and Error Handling Reference (the per-situation action table).

## Constraints

1. **Never use IDs from memory or previous sessions.** All agent IDs, KB IDs, and source IDs must come from live MCP/HTTP responses in the current session.

2. **Never delete a source without a confirmed READY new version.** ADD and poll first, then DELETE.

3. **Never compare using `as_search_knowledge_base`.** The tool returns semantic search chunks. Chunk hash ≠ document hash.

4. **Never skip the 7s rate limit buffer** between ADD operations. 10 consecutive ADDs will hit the rate limit and leave the KB in a partial state.

5. **Field name for matching is `source.name`** from HTTP GET response — not `source.title`, not `source.sourceTitle`.

6. **Obsidian folder paths must be verified** via `obsidian_list_notes` before assuming files exist. Do not hardcode file lists.
