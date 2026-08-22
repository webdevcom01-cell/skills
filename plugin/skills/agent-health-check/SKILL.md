---
name: agent-health-check
description: >
  Runs a structured health check across the Agent Studio AgentStack system and produces
  a scored report with prioritized fixes. Covers 5 dimensions: broken flows (all agents),
  model availability, memory wiring (kb_search nodes), KB embedding status, and duplicate
  agent names. Uses 3 global MCP calls + per-agent calls only for production-scoped agents.
  Triggers: "health check", "system status", "check agents", "što je pokvareno", "šta ne radi",
  "agent health", "provjeri agente", "provjeri sistem", "status sistema", "health report",
  "before I run pipeline", "nešto ne radi u pipeline-u", "pipeline fails", "pipeline ne radi",
  "da li je sve ok", "is everything ok", "system check", "provjeri sve agente".
  Do NOT use for: running agents, fixing a specific known issue (use as_patch_node_field directly),
  adding KB documents, or scaffolding new agents.
allowed-tools:
  - TodoWrite
  - mcp__agent-studio__as_diagnose_models
  - mcp__agent-studio-db__as_diagnose_models
  - mcp__agent-studio__as_find_broken_flows
  - mcp__agent-studio-db__as_find_broken_flows
  - mcp__agent-studio__as_get_kb_embedding_status
  - mcp__agent-studio-db__as_get_kb_embedding_status
  - mcp__agent-studio__as_inspect_flow
  - mcp__agent-studio-db__as_inspect_flow
  - mcp__agent-studio__as_list_agents
  - mcp__agent-studio-db__as_list_agents
  - mcp__agent-studio__as_list_knowledge_bases
  - mcp__agent-studio-db__as_list_knowledge_bases
---

# Skill: agent-health-check
*Version: 1.1 | Based on: agent-health-check-implementation-plan.md + agent-health-check-critical-review.md*
*1.1 (2026-08-22): STEP 6 report format moved to references/report-format.md — file was approaching the repo's size limit. No behavior change.*

---

## Trigger

Use this skill when the user wants to:
- Check if the system is healthy before running a pipeline
- Find out what's broken across agents
- Get a status overview of all production agents
- Verify KB memory is correctly wired after scaffolding

Do NOT use this skill for:
- Fixing a specific already-known issue → use `as_patch_node_field` directly
- Running an agent → use `as_chat_with_agent`
- Scaffolding a new agent → use the agent-scaffolder skill

---

## What This Skill Does

Executes a two-phase health check and produces a structured scored report:

**Phase 1 — Global (3 parallel MCP calls, all 55 agents):**
- D0: Broken Flows — `as_find_broken_flows()`
- A: Model Availability — `as_diagnose_models()`
- Base list — `as_list_agents(limit:200)`

**Phase 2 — Per-agent (production scope only):**
- B: Memory Wiring — `as_inspect_flow(agent, kb_search)` per production agent
- C: KB Embedding Status — `as_list_knowledge_bases(agent)` per production agent
- F: Duplicate Agent Names — derived from Phase 1 base list, no extra calls

**Output:** Scored health report (0–100, relative %) + prioritized fix list.

---

## STEP 0 — Task List

Call TaskCreate for each step:
- "Phase 1 — Global diagnostic calls"
- "Phase 2 — Per-agent KB checks"
- "Analysis and scoring"
- "Generate health report"

Mark each in_progress before starting, completed when done.

---

## STEP 1 — Determine Scope

### Default production scope (use unless user says otherwise)

The following agents are known production agents that require KB health checks.
This list is based on confirmed forensic analysis of the system — all others are
templates or inactive agents without KBs.

```
SOMA pipeline:
  - "Trend Intelligence" (TI)
  - "Hook Writer" (HW)
  - "Content Repurposer" (CR)
  - "Score Analyzer"

AI Nekretnine CG:
  - "NLU Chat Agent — AI Nekretnine CG"
  - "Master Orchestrator — AI Nekretnine CG"
  - "Due Diligence Agent — AI Nekretnine CG"
  - "Market Intelligence Agent — AI Nekretnine CG"
  - "Property Analysis Agent — eKatastar CG"
  - "eKatastar Data Agent"
```

### Scope override

If user specifies agents by name (e.g., "check only SOMA agents"), restrict Phase 2 to
those agents only. Phase 1 always runs on all agents regardless of scope.

---

## STEP 2 — Phase 1: Global Calls (run all 3 in parallel)

Call all three simultaneously:

### Call 1 — D0: Broken Flows
```
as_find_broken_flows()
```
Returns: `{ scanned: N, issueCount: N, errors: N, warnings: N, issues: [...] }`

Each issue contains:
- `agent`: agent name (string)
- `severity`: "WARN" confirmed from actual data (2026-05-16, 10 issues scanned). Other values may exist — treat any non-WARN severity as CRITICAL.
- `issue`: human-readable description
- `fix`: suggested fix command

Store full `issues` array as `broken_flow_issues`.

**What this tool checks (confirmed from tool description):**
1. `ai_response` nodes with no `outputVariable` — result is permanently lost
2. `ai_response` nodes with an empty prompt — model gets no instructions
3. `call_agent` nodes targeting non-existent agents
4. `sandbox_verify` nodes whose `inputVariable` doesn't match any upstream `outputVariable`

**What this tool does NOT check:** `kb_search` nodes missing `knowledgeBaseId`. That is covered in Phase 2, Dimension B.

### Call 2 — A: Model Availability
```
as_diagnose_models()
```
Returns: API key status map + list of agents that will fail due to missing keys.

Store as `model_diagnosis`.

### Call 3 — Base Agent List
```
as_list_agents(limit: 200)
```
Returns array of agents, each with: `id`, `name`, `model`, `isPublic`, `category`, `hasFlow`, `createdAt`.

**IMPORTANT — confirmed fact:** All 55 agents have `category: null`. Do not attempt to filter by category. It will not work.

Store as `all_agents`.

After Phase 1 completes, extract duplicate names from `all_agents`:
```
group all_agents by name
flag any name that appears more than once → duplicate_agents[]
```
Store as `duplicate_agents`.

---

## STEP 3 — Phase 2: Per-Agent KB Checks

For each agent in the production scope list, run 2 calls **sequentially per agent**
(these calls depend on knowing the agent name/ID from Phase 1):

### Call A — Memory Wiring (Dimension B)
```
as_inspect_flow(agent_name: "<name>", node_type: "kb_search")
```
Returns: `{ nodes: [...], edges: [...] }`

For each node in `nodes`:
- Check if `node.data.knowledgeBaseId` exists and is non-empty
- If missing or empty → Memory Wiring issue

### Call B — KB Embedding Status (Dimension C)
```
as_list_knowledge_bases(agent_name: "<name>")
```
Returns: `{ bases: [...], count: N }`

Each base contains:
- `id`: KB ID string
- `name`: KB name
- `embeddingStatus`: one of `"empty"`, `"processing"`, `"ready"`, `"partial_failure"`, `"failed"`
- `statusBreakdown`: `{ ready: N, pending: N, processing: N, failed: N }`
- `documentCount`: total documents

**IMPORTANT — confirmed from tool schema:** `as_list_knowledge_bases` already returns full
embedding breakdown. Do NOT call `as_get_kb_embedding_status` separately — it is redundant.

**Severity mapping for embeddingStatus:**
| embeddingStatus | Severity | Reason |
|---|---|---|
| `ready` | ✅ OK | All documents embedded and searchable |
| `processing` | ⚠️ WARNING | Temporary — retry in 60s |
| `partial_failure` | ⚠️ WARNING | Some documents failed, memory degraded |
| `empty` | ❌ CRITICAL | KB exists but has no documents — agent runs without memory |
| `failed` | ❌ CRITICAL | Embedding permanently broken |

If `count: 0` (no KB at all for this agent):
- This is an informational note, NOT an automatic error
- Only flag as CRITICAL if the agent's flow also has a `kb_search` node (from Memory Wiring check)

---

## STEP 4 — Analysis

Collect all issues into a single list. For each issue, record:
- `dimension`: D0 / A / B / C / F
- `severity`: CRITICAL or WARNING
- `agent`: which agent is affected (or "system-wide" for model/duplicate issues)
- `description`: human-readable problem statement
- `fix`: concrete action to resolve (if determinable)

### Dimension D0 — Broken Flows
Map from `broken_flow_issues`:
- `severity: "WARN"` → our WARNING (only confirmed value from actual data — 2026-05-16)
- Any other severity value → our CRITICAL (treat unknown values conservatively)

Use the `fix` field from the tool response verbatim — do not invent fix commands.

### Dimension A — Model Availability
From `model_diagnosis`:
- Any agent listed as "will fail" → CRITICAL
- API key listed as "NOT SET" → include in report (informational — only critical if agents use that model)

### Dimension B — Memory Wiring
For each production agent:
- `kb_search` node exists AND `knowledgeBaseId` is missing or empty → CRITICAL
- Generate fix command ONLY if `as_list_knowledge_bases` returned a KB for this agent:
  ```
  Fix: as_patch_node_field
    node_id: <node_id from inspect_flow>
    field_name: knowledgeBaseId
    field_value: "<kb_id from list_knowledge_bases>"
  ```
- If no KB exists for the agent → flag as: "Manual fix required: create KB first, then set knowledgeBaseId"
- Do NOT invent KB IDs. Only use IDs returned by `as_list_knowledge_bases`.

### Dimension C — KB Embedding Status
For each production agent with a KB:
- Apply severity mapping from Step 3
- For `partial_failure`: include `statusBreakdown` in report so user knows how many docs are affected
- For `processing`: note timestamp and suggest re-running health check in 60s

### Dimension F — Duplicate Agent Names
From `duplicate_agents`:
- Each duplicate name → WARNING
- Include both agent IDs in the report
- Risk: `call_agent` nodes that reference by name may call wrong agent non-deterministically

---

## STEP 5 — Scoring

Use relative scoring (not absolute penalty formula — confirmed in critical review):

```
total_checks = count of all individual checks performed
passing_checks = total_checks - count(CRITICAL issues) - count(WARNING issues)
score = round((passing_checks / total_checks) * 100)
```

Categories:
| Score | Status |
|---|---|
| 90–100 | ✅ HEALTHY |
| 70–89 | ⚠️ DEGRADED |
| 50–69 | ⚠️ AT RISK |
| 0–49 | ❌ CRITICAL |

If no production agents could be checked (Phase 2 entirely failed): report score as N/A with error.

---

## STEP 6 — Generate Report

**Read `references/report-format.md`** for the exact report layout (header block, CRITICAL/WARNING/OK sections, prioritized action list) and the exact fix-command format for each of the three fix types (Memory Wiring, model, outputVariable). Follow it exactly — do not vary the format.

## Constraints and Rules

1. **No invented data.** Every KB ID, agent ID, node ID in fix commands must come from a real
   MCP tool response in this session. Never use IDs from memory or previous sessions.

2. **No invented tool calls.** Only call tools that exist: `as_find_broken_flows`,
   `as_diagnose_models`, `as_list_agents`, `as_inspect_flow`, `as_list_knowledge_bases`.
   Do NOT call `as_get_kb_embedding_status` for health checks — it is redundant.
   Do NOT call `as_list_knowledge_bases()` without agent_id or agent_name — it requires one.

3. **D0 fix commands come from the tool, not from Claude.**
   `as_find_broken_flows` returns a `fix` field per issue. Use that verbatim.
   Do not rephrase or invent alternative fix approaches.

4. **If a tool call fails**, report the failure in the health report under the relevant
   dimension with status "UNKNOWN — tool call failed: <error>". Do not guess the result.

5. **Phase 1 runs on all agents** (as_find_broken_flows scans everything automatically).
   Phase 2 runs only on production scope. Never expand Phase 2 to all agents manually —
   that would result in 100+ sequential calls.

6. **Score is relative.** Do not use the absolute penalty formula from the original plan.
   It was replaced in the critical review due to mathematical collapse with 55 agents.
