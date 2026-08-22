---
name: pipeline-debug
version: 1.2.0
description: >-
  Reactive diagnostic skill for the SOMA pipeline (TI → HW → CR → Score Analyzer). Accepts a problem
  description, runs structured multi-dimensional checks, maps evidence to root cause via explicit
  IF-THEN rules, applies trivial fixes ONLY after explicit user confirmation (MUTATES production via
  as_patch_node_field), and delivers a prioritized debug report. Replaces 5–8 manual MCP calls with
  one structured investigation. Triggers: "pipeline-debug", "debug pipeline", "pipeline se srušio",
  "pipeline broke", "pipeline failed", "pipeline ne radi", "TI ne radi", "HW timeout", "CR ne radi",
  "prazan output", "empty output", "scores dropping", "quality dropped", "debug TI", "debug HW",
  "debug CR", "šta je pokvareno u pipeline-u", "zašto pipeline ne radi", "provjeri SOMA", "istražii
  grešku".
do_not_use_when:
  - "User wants a preventive system-wide check before running (use agent-health-check)"
  - "User wants to fix KB wiring across all agents (use soma-memory-fix)"
  - "User wants to sync Obsidian vault to KB (use kb-sync)"
  - "User wants to run the pipeline (use soma-run)"
  - "User asks about AI Nekretnine CG agents (different architecture — not in scope)"
allowed-tools:
  - Read
  - Glob
  - Grep
  - TodoWrite
  - mcp__agent-studio__as_health_check
  - mcp__agent-studio-db__as_health_check
  - mcp__agent-studio__as_get_recent_executions
  - mcp__agent-studio-db__as_get_recent_executions
  - mcp__agent-studio__as_list_agent_calls
  - mcp__agent-studio-db__as_list_agent_calls
  - mcp__agent-studio__as_get_agent_call_log
  - mcp__agent-studio-db__as_get_agent_call_log
  - mcp__agent-studio__as_find_broken_flows
  - mcp__agent-studio-db__as_find_broken_flows
  - mcp__agent-studio__as_inspect_flow
  - mcp__agent-studio-db__as_inspect_flow
  - mcp__agent-studio__as_list_knowledge_bases
  - mcp__agent-studio-db__as_list_knowledge_bases
  - mcp__agent-studio__as_patch_node_field
  - mcp__agent-studio-db__as_patch_node_field
  - mcp__obsidian__obsidian_read_note
---

# Skill: pipeline-debug

*Version: 1.2.0*
*Grounded in: live MCP schema audit 2026-05-17, forensic plan review, confirmed tool*
*behaviours from agent-health-check and soma-memory-fix live sessions.*
*Zero values from memory. All tool parameter names confirmed from live schemas.*
*1.2.0: STEP 9–11 and reference tables moved to `references/` — SKILL.md was 873*
*lines / ~8470 tokens, over the repo's own 500-line/5000-token limit (see*
*`skill-creator-pro/references/skill-writing-guide.md`). No behavioural change.*

---

## Purpose

Diagnoses why the SOMA pipeline (TI → HW → CR → Score Analyzer) failed or degraded.
Takes a problem description, runs targeted multi-dimensional checks, and returns:
- Root cause classification (from an explicit IF-THEN table — not LLM inference)
- Evidence for each finding
- Trivial fixes applied ONLY after explicit confirmation (see 10a.5)
- Manual fix instructions for non-trivial issues

**Key architectural fact (confirmed 2026-05-16):**
SOMA is an externally-orchestrated pipeline. `soma-run` skill calls agents via
`as_chat_with_agent` (human-to-agent). These are NOT A2A calls. Therefore:
- `as_list_agent_calls` / `as_get_agent_call_log` return 0 results for SOMA runs
- `as_get_recent_executions` IS the correct tool for SOMA execution history
- A2A tools are retained as supplementary checks for internal `call_agent` nodes only

---

## Hard rules — zero hallucination

- Root cause is determined ONLY by the explicit IF-THEN table in Step 9 — never by LLM inference
- Fix commands use ONLY node_ids and kb_ids obtained from live MCP calls in this session
- Apply a fix ONLY after (a) all Step 10 pre-conditions are met AND (b) the user explicitly confirms the exact patch — never without confirmation, never speculatively
- If a tool call fails → report UNKNOWN for that dimension, do NOT guess the result
- Evo-log parsing uses fixed field positions (documented below) — never free-form text analysis

---

## Confirmed constants (live-verified)

```
SOMA PRODUCTION SCOPE:
  Primary pipeline : Trend Intelligence (TI), Hook Writer (HW), Content Repurposer (CR)
  Secondary        : Score Analyzer (execution check only — no evo-log, different arch)

EVO-LOG PATHS (confirmed):
  TI  → agents/trend-intelligence/evo-log.md
  HW  → agents/hook-writer/evo-log.md
  CR  → agents/content-repurposer/evo-log.md

EVO-LOG PIPE-FIELD POSITIONS (0-indexed, confirmed from soma-run v1.1.0):
  TI fields: [0]date | [1]INPUT:... | [2]trend_found | [3]confidence | [4]angle | [5]triggered
  HW fields: [0]date | [1]trend | [2]platforms | [3]scores | [4]winner | [5]winner_score | [6]flags
  CR fields: [0]date | [1]trend | [2]platforms_completed | [3]scores | [4]flag | [5]notes

QUALITY TRIGGER KEYWORDS (case-insensitive):
  "quality", "scores", "score", "dropping", "evo-log", "UNSCORED",
  "violations", "hook quality", "platform", "degradation"

TIMEOUT TRIGGER KEYWORDS:
  "timeout", "slow", "stuck", "hanging", "waiting", "RUNNING", "ne odgovara"

CRASH TRIGGER KEYWORDS:
  "crashed", "failed", "FAILED", "error", "ne radi", "pokvareno", "srušio"

EMPTY OUTPUT TRIGGER KEYWORDS:
  "empty output", "prazan output", "ništa ne vraća", "blank", "nema outputa"

EXECUTION STATUS VALUES (confirmed from schema):
  as_get_recent_executions: PENDING | RUNNING | COMPLETED | FAILED | CANCELLED

A2A CALL STATUS VALUES (confirmed from schema):
  as_list_agent_calls: SUBMITTED | WORKING | INPUT_REQUIRED | COMPLETED | FAILED

TIMEOUT ANOMALY THRESHOLD:
  If RUNNING status and duration > 5 minutes → classify as TIMEOUT

QUALITY DEGRADATION THRESHOLD:
  2 consecutive UNSCORED entries in HW evo-log → QUALITY_DEGRADATION
  OR cr_flag = "QUALITY_VIOLATIONS" in 2 of last 5 CR entries

TRIVIAL FIX ELIGIBILITY — apply ONLY after user confirmation (see Step 10):
  1. Missing outputVariable: only when the suggested fix resolves to a concrete
     node_id + field_name + field_value (see 10b); otherwise manual
  2. KB unwired (knowledgeBaseId missing) + exactly 1 KB exists for that agent
```

---

## STEP 0 — Task List

Create tasks before starting:
- "PARSE — Input analysis and symptom detection"
- "D0+D1 — Infrastructure and execution status"
- "D4+D5 — Flow integrity checks"
- "D6 — KB status"
- "D7 — Evo-log analysis (conditional)"
- "ROOT CAUSE — IF-THEN mapping"
- "CONFIRM & APPLY — propose trivial fixes, apply only after explicit user confirmation"
- "REPORT — Debug report"

Mark each `in_progress` before starting, `completed` when done.

---

## STEP 1 — Parse Input and Detect Symptom Profile

Extract from user's message:

### 1a — Agent scope
Detect if user named a specific agent:
- Mentions "TI" / "Trend Intelligence" → scope to TI (+ cascade check for HW/CR)
- Mentions "HW" / "Hook Writer" → scope to HW (+ check TI as upstream cause)
- Mentions "CR" / "Content Repurposer" → scope to CR (+ check HW as upstream)
- Mentions "Score Analyzer" → secondary scope only
- No specific agent → full SOMA scope (all 4 agents)

Store as `{debug_scope}`: `"TI"` / `"HW"` / `"CR"` / `"SCORE"` / `"FULL"`.

### 1b — Symptom type detection
Scan message for keyword groups (case-insensitive):

| Detected keyword group | Symptom type | D7 triggered? |
|---|---|---|
| Quality trigger keywords | `QUALITY` | Yes (Standard mode) |
| Timeout trigger keywords | `TIMEOUT` | No |
| Crash trigger keywords | `CRASH` | No |
| Empty output trigger keywords | `EMPTY_OUTPUT` | No |
| No keyword match | `UNKNOWN` | No (Deep only) |

Store as `{symptom_type}`. Store D7 flag as `{d7_in_standard}` = true/false.

### 1c — Time reference
If user mentions a specific time ("u 14:30", "sat ago", "zadnji run", "yesterday"):
- Store as `{time_reference}` = user-provided string
- Use as context note in report (cannot filter MCP calls by time — no timestamp filters on D1)
- If no time reference → use default: "last 10 executions per agent"

### 1d — Determine diagnostic depth
```
Default depth: STANDARD
Escalate to DEEP if (evaluated at end of Step 8):
  - STANDARD found 0 issues AND symptom_type != UNKNOWN (user reported a real problem)
  - STANDARD found only WARNINGs AND symptom_type = CRASH
  - All D0-D6 checks pass but user explicitly says "deep" / "detaljno" / "sve provjeri"
```

---

## STEP 2 — D0: Infrastructure Check

Mark task in_progress.

Call:
```
as_health_check()
```

Takes no parameters. Returns basic DB connection counts.

**Classification:**
- Call succeeded → `{d0_status}` = `REACHABLE`
- Call failed / exception → `{d0_status}` = `DOWN`

If DOWN → immediately halt all further steps. Report:
```
🔴 INFRA DOWN — MCP server cannot reach database.
No agent diagnostics possible. Check AgentStack MCP configuration.
```

If REACHABLE → proceed to Step 3.

---

## STEP 3 — D1: Execution Status Per Agent

Run all 4 agent checks **in parallel**:

```
as_get_recent_executions(agent_name: "Trend Intelligence",    limit: 10)
as_get_recent_executions(agent_name: "Hook Writer",           limit: 10)
as_get_recent_executions(agent_name: "Content Repurposer",    limit: 10)
as_get_recent_executions(agent_name: "Score Analyzer",        limit: 5)
```

For agents outside `{debug_scope}`, still run but mark as "context only" (to detect cascading).

For each agent, extract and store:
- `{agent}_last_status`: most recent execution status (COMPLETED / FAILED / RUNNING / PENDING / CANCELLED)
- `{agent}_last_timestamp`: timestamp of most recent execution (if available)
- `{agent}_consecutive_failed`: count of consecutive FAILED entries at top of results
- `{agent}_execution_count`: total executions returned (0 = never ran)
- `{agent}_has_running`: true if any execution has status=RUNNING

**Edge cases:**
- If tool call fails → `{agent}_d1_status` = `UNKNOWN` — continue with other agents
- If returns empty array → `{agent}_execution_count` = 0, `{agent}_last_status` = `NEVER_RAN`

### D1b — Supplementary A2A check (for internal call_agent nodes)

Call:
```
as_list_agent_calls(since_hours: 24, limit: 20)
```

This shows calls between agents via internal `call_agent` flow nodes. Useful if any SOMA
agent internally routes to another via `call_agent`. Store as `{a2a_calls}`.

If `{a2a_calls}` is empty → normal (SOMA is externally orchestrated). Do not flag.
If `{a2a_calls}` contains FAILED entries → note in report as supplementary finding.

---

## STEP 4 — D4: Static Flow Check

Call:
```
as_find_broken_flows()
```

Scans ALL agents for 4 known patterns:
1. `ai_response` with no `outputVariable` — result permanently lost
2. `ai_response` with empty prompt — model gets no instructions
3. `call_agent` targeting non-existent agent
4. `sandbox_verify` with mismatched `inputVariable`

Store full `issues` array as `{d4_issues}`.

Filter `{d4_issues}` to SOMA agents only (TI, HW, CR, Score Analyzer) for report.
Keep non-SOMA findings as informational only (don't include in SOMA report).

**Not from the schema:** `as_find_broken_flows` documents only that it "returns a list of issues per agent with severity and suggested fixes". Field names such as `.fix`, `.issue` and `.severity` are this skill's own shorthand for that response, NOT documented keys — read the actual response before indexing into it.
Store the `fix` string as-is for reference. It is a SUGGESTION of unspecified shape, not four named keys — see 10b before using it to build a patch.

---

## STEP 5 — D5: Flow Config Inspection

Run `as_inspect_flow` for agents that meet any of these conditions:
- Agent appears in `{d4_issues}` (broken flow detected)
- Agent has `{agent}_last_status` = FAILED or NEVER_RAN
- `{debug_scope}` targets this agent specifically
- All agents if `{debug_scope}` = FULL and ≥1 anomaly detected in D1/D4

Call per qualifying agent:
```
as_inspect_flow(agent_name: "<agent_name>")
```

Returns full `nodes[]` and `edges[]`.

For each agent inspected, extract:
- `{agent}_kb_search_nodes`: all nodes where `node.type == "kb_search"`
  - For each: `node.id`, `node.data.knowledgeBaseId` (null/empty = unwired)
- `{agent}_prompt_nodes`: all `ai_response` nodes
  - For each: `node.id`, `node.data.prompt` (empty string = broken)
- `{agent}_model`: model configured on main ai_response node
- `{agent}_input_mapping`: inputMapping config (for cascading analysis)

**What D5 checks that D4 does NOT:**
- `kb_search` nodes with missing `knowledgeBaseId` (KB unwired — auto-fixable)
- Prompt content that is technically non-empty but placeholder/incomplete
- Model configuration

---

## STEP 6 — D6: KB Embedding Status

Run for agents that have `kb_search` nodes (from D5) or are KB-based:
Primary KB agents (confirmed): Trend Intelligence, Hook Writer, Content Repurposer
Score Analyzer: check only if D5 reveals a kb_search node.

```
as_list_knowledge_bases(agent_name: "Trend Intelligence")
as_list_knowledge_bases(agent_name: "Hook Writer")
as_list_knowledge_bases(agent_name: "Content Repurposer")
```

For each, store:
- `{agent}_kb_embedding_status`: empty | processing | ready | partial_failure | failed
- `{agent}_kb_document_count`: total documents
- `{agent}_kb_id`: KB ID (needed for auto-fix in Step 10)
- `{agent}_kb_count`: number of KBs returned (0 = no KB at all)

**Cross-reference with D5:**
For each agent:
- If `kb_embedding_status` = empty AND `kb_search_nodes` exist → KB_DEAD (CRITICAL)
- If `kb_embedding_status` = empty AND no `kb_search_nodes` → KB_UNSEEDED (WARN)
- If `kb_count` = 0 AND `kb_search_nodes` exist → KB_MISSING (CRITICAL)

---

## STEP 7 — D7: Evo-log Pattern Analysis (Conditional)

**Run D7 if:**
- `{d7_in_standard}` = true (quality keywords detected in Step 1), OR
- Depth escalated to DEEP

**Skip D7 if:**
- `{d7_in_standard}` = false AND depth = STANDARD

### 7a — Read all three evo-logs (read-before-analyze)

```
obsidian_read_note("agents/trend-intelligence/evo-log.md")
obsidian_read_note("agents/hook-writer/evo-log.md")
obsidian_read_note("agents/content-repurposer/evo-log.md")
```

If any note returns "Note not found" → log as WARN: "Evo-log missing for {agent}."

### 7b — Parse HW evo-log for QUALITY_DEGRADATION

For each entry line in HW evo-log body (lines starting with "20" are entries):
1. Split by " | " (with spaces)
2. Extract field [6] (0-indexed) = `flags`
3. Build ordered list of last 5 entries: `hw_recent_flags[]`

**Detection rule:**
```
consecutive_unscored = 0
for entry in hw_recent_flags (newest first):
  if "UNSCORED" in entry.flags:
    consecutive_unscored += 1
  else:
    break

if consecutive_unscored >= 2:
  → set {hw_quality_degradation} = true
  → set {hw_unscored_count} = consecutive_unscored
```

### 7c — Parse CR evo-log for violation pattern

For each entry in CR evo-log (last 5):
1. Split by " | "
2. Extract field [4] = `flag`
3. Count entries where flag contains "QUALITY_VIOLATIONS"

If count >= 2 → `{cr_quality_violations}` = true.

### 7d — Parse TI evo-log for DRIFT pattern

For each entry in TI evo-log (last 5):
1. Split by " | "
2. Check if field [2] (trend_found) contains "[DRIFT from input]"
3. Count DRIFT occurrences

If count >= 2 → `{ti_drift_pattern}` = true (TI consistently redirecting from inputs).

---

## STEP 8 — Escalation Check

After Steps 2–7 complete, evaluate whether to escalate to DEEP:

```
issues_found = count of all CRITICAL + MAJOR findings so far

Escalate to DEEP if:
  a) issues_found == 0 AND symptom_type != "UNKNOWN"
     (user reported problem but Standard found nothing)
  b) issues_found > 0 AND all findings are WARN only AND symptom_type == "CRASH"
     (crash reported but only warnings found — something is hidden)
  c) User input contains "deep" / "detaljno" / "sve" / "full"

If escalating to DEEP:
  - Run D7 if not already run
  - Run as_get_agent_call_log for each SOMA agent (limit: 10, status omitted):
    as_get_agent_call_log(agent_name: "Trend Intelligence",    limit: 10)
    as_get_agent_call_log(agent_name: "Hook Writer",           limit: 10)
    as_get_agent_call_log(agent_name: "Content Repurposer",    limit: 10)
  - Run as_inspect_flow for ALL 4 SOMA agents (not just anomalous ones)
  Note: as_get_agent_call_log has no time filter — returns most recent N entries.
  Output preview is limited to 300 chars — useful for detecting empty/sentinel outputs only.
```

---

## STEP 9 — Root Cause Mapping (IF-THEN Table)

**CRITICAL: All root cause classification uses ONLY this table. No free-form LLM reasoning.**

Read `references/root-cause-rules.md` now and evaluate every rule in it against the
data gathered in Steps 2–8. Evaluate all rules — multiple can fire simultaneously —
and process in priority order: CRITICAL rules (C1–C8) first, then MAJOR (M1–M3),
then WARNING (W1–W8), then the CLEAN fallback if nothing fired. That file also
defines `{root_cause}` for the CLEAN case, which re-triggers the Step 8 escalation
check.

---

## STEP 10 — Apply Trivial Fixes (after explicit confirmation)

Eligible fixes from Step 9 are applied ONLY after the user confirms the exact patch.
This step **MUTATES production** via `as_patch_node_field`.

Read `references/apply-trivial-fixes.md` now before proposing or applying any
patch. It defines: which fixes are trivial-eligible vs. permanently manual, the
pre-fix safety checks (running-agent guard, pre-patch re-read), the mandatory
confirmation gate (10a.5 — fail-closed, apply nothing without explicit "da"/"yes"),
the exact `as_patch_node_field` call shape for FLOW_BROKEN and KB_UNWIRED fixes,
and post-patch verification.

Never skip the confirmation gate and never invent a `node_id` or `field_name` —
both must come from a live MCP call made this session.

---

## STEP 11 — Generate Debug Report

Read `references/report-template.md` now and fill in the template from all data
gathered in Steps 1–10: header fields, execution status summary, findings grouped
by severity (CRITICAL/MAJOR/WARN) with rule ID, evidence and fix per finding, the
root cause hypothesis, the auto-fix log, and numbered next steps. That file also
has the CLEAN-result, auto-fixes-applied, and DEEP-mode variant footers.

---

## Diagnostic Dimension Summary, Tool Reference, Constraints Summary

Consult `references/reference-tables.md` as needed — not required for every run.
It has: which MCP tool covers which diagnostic dimension (D0/D1/D1b/D4/D5/D6/D7)
and why, the expected MCP call count per depth (STANDARD 7–16 calls, DEEP up to
22), full tool parameter reference, excluded tools and why, and the constraints
summary table (root cause source, fix-ID source, auto-apply guardrails, etc.) —
useful as a final self-check before closing out a run.

---

## Invocation Examples

```
"pipeline-debug"
"debug pipeline — HW timeout jutros u 10h"
"zašto pipeline ne radi? scores dropping"
"pipeline se srušio — provjeri sve"
"debug TI — ne vraća ništa"
"CR daje prazan output od jučer"
"pipeline-debug — deep"
"šta je pokvareno u SOMA-i?"
"provjeri SOMA — quality je pala"
```
