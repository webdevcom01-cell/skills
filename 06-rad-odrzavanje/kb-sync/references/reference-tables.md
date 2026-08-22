# Reference tables — scope, rate limiting, tools, error handling

Loaded from `kb-sync/SKILL.md` — read as needed: Default Scope for the 4 SOMA agents and their KB title/folder conventions, Rate Limiting Reference for the 7s ADD buffer and 429 handling, Tool Reference for MCP/curl call signatures, Error Handling Reference for the per-situation action table. Verbatim from the skill body, moved here only because the combined SKILL.md was approaching the repo's line-count budget.

---

## Default Scope

### SOMA Production Agents

| Agent Name | KB Title Prefix | Obsidian Folder |
|---|---|---|
| Trend Intelligence | `trend-intelligence` | `agents/trend-intelligence` |
| Hook Writer | `hook-writer` | `agents/hook-writer` |
| Content Repurposer | `content-repurposer` | `agents/content-repurposer` |
| Score Analyzer | `score-analyzer` | `agents/score-analyzer` |

**Files typically present per agent:**
- `instincts.md` → KB title: `{prefix}/instincts`
- `evo-log.md` → KB title: `{prefix}/evo-log`
- Hook Writer additionally: `winners-log.md` → `hook-writer/winners-log`

These are discovered dynamically via `obsidian_list_notes` — do not assume files exist without checking.

---

## Rate Limiting Reference

Confirmed from `src/lib/rate-limit.ts` + `sources/route.ts`:
- Limit: **10 POST requests per 60 seconds** per user
- Scope: `checkRateLimit("kb-source:{userId}", 10)`
- Window: sliding 60-second window

**Required mitigation:**
- Wait **7 seconds after each `as_add_kb_text` call** before the next one
- If a `429 Too Many Requests` response is received anyway (can happen due to other concurrent KB operations):
  - Wait 60 seconds
  - Retry the failed ADD once
  - If still 429 → log ERROR: "Rate limit exceeded for {kb_title}. Retry manually."
  - Continue to next file

---

## Tool Reference

### MCP Tools (via AgentStack MCP)
| Tool | Purpose |
|---|---|
| `as_list_knowledge_bases(agent_name)` | Get kb_id and agent_id for an agent |
| `as_add_kb_text(kb_id, content, title)` | Add/ingest a text document into a KB |
| `as_get_kb_embedding_status(kb_id, document_id)` | Poll embedding status for ONE document |

### Obsidian MCP Tools
| Tool | Purpose |
|---|---|
| `obsidian_list_notes(folder)` | Discover files in a vault folder |
| `obsidian_list_folders` | Discover folder structure if paths are unknown |
| `obsidian_read_note(path)` | Read full content of a note |

### Bash (curl) — Required for operations not exposed by MCP
| Operation | Command |
|---|---|
| GET KB sources (with contentHash) | `GET {URL}/api/agents/{agentId}/knowledge/sources` |
| DELETE a KB source | `DELETE {URL}/api/agents/{agentId}/knowledge/sources/{sourceId}` |
| Compute SHA-256 | `sha256sum` (or write to temp file first) |

**Auth header for all curl calls:** `-H "x-api-key: {AGENT_STUDIO_API_KEY}"`

### Tools NOT to use for this skill
- `as_search_knowledge_base` — returns chunks, NOT full documents. SHA-256 of chunks ≠ SHA-256 of original text. Do NOT use for change detection.
- Timestamp / `customMetadata` comparison — `customMetadata` is NOT stored by the ingest pipeline. Timestamps in KBSource reflect ingestion time, not Obsidian modification time.

---

## Error Handling Reference

| Situation | Action |
|---|---|
| AGENT_STUDIO_URL or API_KEY missing | Stop, ask user before proceeding |
| `as_list_knowledge_bases` returns count=0 | Log WARNING, skip agent |
| HTTP GET sources fails | Log ERROR, skip agent |
| `obsidian_read_note` fails | Log ERROR for that file, continue |
| `as_add_kb_text` fails | Log ERROR, do NOT attempt DELETE, continue |
| Embedding status = FAILED after polling | Log ERROR: embedding failed, continue |
| DELETE fails after successful ADD | Log WARNING (duplicate exists, content correct), continue |
| HTTP 429 on ADD | Wait 60s, retry once; if still 429 → log ERROR, continue |
| KB source status != READY | Log WARNING: skip file, leave for manual check |

---
