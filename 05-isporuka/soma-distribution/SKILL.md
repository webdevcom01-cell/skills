---
name: soma-distribution
version: 0.1.1
description: Takes SOMA Content Repurposer output (5 platform posts marked READY_FOR_REVIEW) through a human approval gate and turns approved posts into a publish-ready bundle - one formatted file per platform (LinkedIn, X, YouTube, Instagram, TikTok) plus a scheduling manifest - and logs the batch to Obsidian. If a social/scheduling MCP is connected it hands off; otherwise it produces the bundle for manual posting. The SOMA pipeline stops at READY_FOR_REVIEW with no distribution step - this is that step. Use when the user says "publish", "distribute", "objavi", "rasporedi postove", "schedule posts", "spremi za objavu", "posalji na platforme", "approve and post", "izvezi postove", or after a CR run when posts are ready. Do NOT use to generate or score content (use soma-run / soma-score-analyzer) - it never rewrites post copy, only formats, gates, and routes. Never auto-publishes without approval.
compatibility: Requires Agent Studio MCP (as_chat_with_agent, as_search_knowledge_base) and Obsidian MCP (obsidian_read_note, obsidian_update_note) -- reads Content Repurposer output marked READY_FOR_REVIEW and, after human approval, writes the publish-ready bundle.
do_not_use_when:
  - User wants to generate or rewrite the posts (use soma-run / Content Repurposer)
  - User wants to score the posts (use soma-score-analyzer)
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - TodoWrite
  - mcp__agent-studio__as_chat_with_agent
  - mcp__agent-studio-db__as_chat_with_agent
  - mcp__agent-studio__as_search_knowledge_base
  - mcp__agent-studio-db__as_search_knowledge_base
  - mcp__obsidian__obsidian_read_note
  - mcp__obsidian__obsidian_update_note
---

# SOMA Distribution

## What this skill does

The pipeline ends at `READY_FOR_REVIEW` — five platform-native posts sitting in a review
queue with nowhere to go. This skill is the last mile: it shows you the posts, takes your
approval (per platform), and packages the approved ones into a publish-ready bundle plus a
scheduling manifest. It logs every batch so distribution history lives alongside the evo-logs.

It deliberately does **not** touch the words. Copy was already written by CR and (ideally)
scored by the Score Analyzer; rewriting here would bypass those quality gates.

## Hard rules (do not break)

1. **Approval gate is mandatory.** Nothing leaves the review queue without explicit per-post
   approval. "Approve all" is allowed but must be a deliberate choice, never the default.
2. **Never edit the copy.** Format, wrap, and attach metadata only. If a post violates a
   platform limit, flag it back for review — do not silently trim. (Trimming hooks is exactly
   the kind of `char_limit` violation the HW/CR gates exist to catch.)
3. **Verify the channel before claiming a post is scheduled.** If routing to an MCP, confirm
   the tool returned success. Never report "posted/scheduled" on an unverified call.
4. **No real publishing action on the user's behalf beyond what they approved** — and if any
   connected tool actually posts live, surface the exact destination and time first.
5. **Log every batch** to Obsidian so there's an auditable distribution trail.

## Workflow

### STEP 0 — Task list
Create: "INGEST", "VALIDATE LIMITS", "REVIEW + APPROVE", "BUILD BUNDLE", "ROUTE", "LOG", "REPORT".

### STEP 1 — Ingest the posts
Accept CR output from the conversation (pasted), a soma-run result, or a re-run
(`as_chat_with_agent(agent_name:"Content Repurposer", ...)`). Parse into per-platform posts:
`{LinkedIn, X, YouTube, Instagram, TikTok}`, each with `full_post`, optional `status`, and
optional score (if soma-score-analyzer ran). Mark any missing platform `MISSING`.

### STEP 2 — Validate platform limits (flag, never fix)
Don't hardcode limits here — they drift, and SOMA already keeps the authoritative format
rules in the KB. The **hook** limits live in the Hook Writer KB `agent-card` (LinkedIn ≤210,
X ≤280, YouTube ≤150, TikTok ≤12 words). The **full-post** conventions (what CR expands a
hook into) live in the Content Repurposer KB as `format-templates.md` — load it as the source
of truth for post length/structure per platform:
```
as_search_knowledge_base(kb_id:"cmpsknkbo0001pbofdslfjsw3", query:"format templates per platform post length structure", top_k:5)
```
Check each approved post against those loaded rules and flag any violation for review. If a
post is over → list it and ask the user to send it back to CR or approve as-is. **Never
auto-trim** — silently cutting a post is exactly the `char_limit` failure the HW/CR gates
exist to prevent.

### STEP 3 — Review + approve
Present each post compactly (platform, score if known, full copy, any limit flag). Ask:
**"Koje postove odobravaš za distribuciju? (sve / lista platformi / nijedan)"**
Record `{approved}` set. Only approved posts continue.

### STEP 4 — Build the distribution bundle
For each approved platform, write a clean file into the current working/output directory
(the session's outputs folder — use an absolute path, not a bare relative one, so the user
can actually find it):
```
<output_dir>/distribution/<run_id>/<platform>.md
```
Each file: the verbatim post body, plus a small front-matter block with `platform`, `trend`,
`score` (if known), `pattern`, `suggested_time`, and `status: APPROVED`. Also write:
```
distribution/<run_id>/manifest.json
```
listing every approved post with `{platform, file, suggested_time, status}` so a scheduler
(human or MCP) can consume it in one read.

**Suggested timing** is a recommendation only — derive from any timing signal in the trend
(e.g. "breaking" → ASAP) or default to the user's stated cadence. Never invent a precise
timestamp and present it as fixed; label it "suggested".

### STEP 5 — Route (optional, only if a channel is connected)
Search for a connected distribution channel before claiming you can publish:
- Check available MCP tools / the connector registry for a scheduler or social platform.
- If found and the user opts in → hand off each approved post via that tool, then verify the
  tool's success response per post.
- If none found → the bundle from Step 4 **is** the deliverable; tell the user it's ready for
  manual posting or for a scheduler they connect later. Do not pretend a channel exists.

### STEP 6 — Log the batch
```
obsidian_read_note("agents/content-repurposer/distribution-log.md")   # create if missing
obsidian_update_note(
  path: "agents/content-repurposer/distribution-log.md", mode: "append",
  content: "{date} | {trend} | approved: {approved_platforms} | routed: {channel or 'bundle-only'} | run_id {run_id}"
)
```

### STEP 7 — Report
```
📤 DISTRIBUTION — COMPLETE
Trend     : {trend}
Approved  : {k}/5 platforms ({list})
Held back : {list + reason}  (or: none)
Bundle    : distribution/{run_id}/  ({k} files + manifest.json)
Routed to : {channel}  (or: bundle only — connect a scheduler to auto-post)
Logged    : distribution-log.md ✅
```

## Invocation examples
```
"objavi odobrene postove sa poslednjeg CR run-a"
"spremi distribution bundle za Claude Opus 4.5 trend"
"approve and schedule — sve platforme osim TikToka"
"izvezi postove za ručno objavljivanje, nemam scheduler"
"distribute, ali prvo mi pokaži postove da odobrim"
```

## Tool reference
| Tool | Used for |
|---|---|
| `as_chat_with_agent` | Optional CR re-run to fetch posts |
| `as_search_knowledge_base` | Load CR `format-templates.md` as post-format source of truth |
| Write (file) | Build per-platform bundle + manifest.json |
| connector registry / social MCP | Optional routing (verify success) |
| `obsidian_read_note` / `obsidian_update_note` | Distribution log |

## Versioning
| Version | Date | Notes |
|---|---|---|
| v0.2 | 2026-06-26 | P2: load CR `format-templates.md` as post-format source of truth instead of hardcoded limits; P3: absolute output path; invocation examples |
| v0.1 | 2026-06-26 | Initial — adds the missing last-mile step after READY_FOR_REVIEW |
