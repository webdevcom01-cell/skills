---
name: soma-run
version: 1.3.1
description: >-
  End-to-end SOMA pipeline runner: validates input, runs Trend Intelligence, captures the output,
  writes evo-logs to Obsidian, and logs winners. One skill call replaces manual as_chat_with_agent +
  evo-log-writer + winners-log-logger. Default scope is TI only, because TI calls Hook Writer and Hook
  Writer calls Content Repurposer server-side — the full chain runs from one call. Running the
  external TI → HW → CR relay on top of that would execute HW twice and CR three times, so that scope
  is gated behind explicit confirmation until the call_agent nodes are removed (decision of
  2026-06-19). Triggers: "soma run", "pokreni pipeline", "run pipeline", "pokreni SOMA", "run SOMA",
  "run TI", "pokreni TI", "full pipeline run", "end-to-end run", "soma-run", "run the pipeline",
  "pusti kroz pipeline", "pusti trend kroz pipeline".
compatibility: Requires Agent Studio MCP (as_chat_with_agent, as_get_agent, as_get_recent_executions, as_list_agent_calls, as_list_agents) and Obsidian MCP (obsidian_create_note, obsidian_read_note, obsidian_update_note) -- runs Trend Intelligence end-to-end and writes evo-logs and winners directly, replacing separate as_chat_with_agent, evo-log-writer and winners-log-logger calls.
do_not_use_when:
  - "User wants to validate input only (use pipeline-input-validator)"
  - "User wants to log an existing run (use evo-log-writer)"
  - "User wants to sync KB content (use kb-sync)"
  - "User wants a health check (use agent-health-check)"
  - "User wants to fix kb_search wiring (use soma-memory-fix)"
allowed-tools:
  - TodoWrite
  - mcp__agent-studio__as_chat_with_agent
  - mcp__agent-studio-db__as_chat_with_agent
  - mcp__agent-studio__as_get_agent
  - mcp__agent-studio-db__as_get_agent
  - mcp__agent-studio__as_get_recent_executions
  - mcp__agent-studio-db__as_get_recent_executions
  - mcp__agent-studio__as_list_agent_calls
  - mcp__agent-studio-db__as_list_agent_calls
  - mcp__agent-studio__as_list_agents
  - mcp__agent-studio-db__as_list_agents
  - mcp__obsidian__obsidian_create_note
  - mcp__obsidian__obsidian_read_note
  - mcp__obsidian__obsidian_update_note
---

# Skill: soma-run

*Version: 1.3.1*
*Grounded in: live MCP audit 2026-05-16 — all tool schemas, evo-log formats, Obsidian*
*paths, and timeout values confirmed from live data. Zero values from memory.*
*Revised 2026-07-29: added the auto-chain conflict section and the scope gate below,*
*from live flow reads, two measured runs, and live heartbeat/goal checks. The orchestration*
*model itself is unchanged — see "Why this skill has not been rewritten to match".*
*1.3.0 (2026-08-22): architectural-conflict evidence, STEP 4 (TI run procedure), STEP 9*
*1.3.1 (2026-08-22): Added `compatibility:` frontmatter field describing Agent Studio/Obsidian MCP dependency. No behavior change.*
*report template, and the trailing reference tables moved to `references/` — SKILL.md*
*was 791 lines / ~7654 tokens, over the repo's own 500-line/5000-token limit (see*
*`skill-creator-pro/references/skill-writing-guide.md`). No behavioural change.*

---

## Purpose

Runs the full SOMA content pipeline in a single skill invocation:

```
[User input] → VALIDATE → TI → HW → CR → [Evo-logs + Winners-log]
```

Replaces the manual workflow of:
1. Running `as_chat_with_agent` for TI
2. Copy-pasting TI output into HW
3. Copy-pasting HW output into CR
4. Manually logging each run in Obsidian

---

## ⚠️ Known architectural conflict — read this before running FULL scope

**The agents already chain themselves server-side. This skill does not know that.**
TI calls HW internally, which calls CR internally, so calling only TI executes the
whole chain. Running `"TI+HW"` or `"FULL"` on top of that executes HW twice and CR
three times — triple cost, wrong stage logged. This is why STEP 1 defaults to scope
`"TI"` and gates any wider scope behind explicit user confirmation.

Read `references/architectural-conflict.md` now for the full evidence (measured run
timings, the retry-storm finding, and why the fix is a separate, already-decided
sprint). **Do not "fix" this skill by making it supervisory without reading that
decision record first.**

Consequence for STEP 4: **never call TI with a blocking wait** — transport caps at
60s while TI takes 68-113s server-side. Use fire-and-poll (STEP 4c).

---

## Hard rules — zero hallucination

- Never fabricate agent outputs, scores, hook text, or log entries
- Every evo-log entry must contain only data extracted from actual agent responses
- If an agent times out or returns an error → log `FAILED` — never invent a plausible output
- All Obsidian paths are fixed (confirmed 2026-05-16) — do NOT invent new paths
- `{ti_handoff}` must contain the complete `{ti_output}` verbatim in the `<<SOMA_CONTEXT_START>>` block — never send only the header
- `quality_score` must be calculated from actual extracted values (`{ti_trend}`, `{ti_confidence}`, `{ti_angle}` from STEP 4e) — never estimate from general TI output impression
- `platform_hint`, `audience_hint`, and `timing_signal` must be extracted verbatim from `{ti_output}` — never generate from memory or assumption

---

## Confirmed constants (live-verified 2026-05-16)

```
TIMEOUTS (schema values — see the client cap below before relying on them):
  TI  → timeout_seconds: 300   (fire-and-poll; client aborts at 60 s anyway)
  HW  → timeout_seconds: 120
  CR  → timeout_seconds: 120

CLIENT TRANSPORT CAP (measured 2026-07-29): 60 s, and an aborted request is
RETRIED automatically — each retry is another full server-side chain.

EVO-LOG PATHS:
  TI  → agents/trend-intelligence/evo-log.md
  HW  → agents/hook-writer/evo-log.md
  CR  → agents/content-repurposer/evo-log.md

WINNERS-LOG PATH:
  → agents/hook-writer/winners-log.md
  → Threshold: score ≥ 17/20

EVO-LOG FORMATS:
  TI: date | trend_found | confidence | angle_suggested | hook_writer_triggered
  HW: date | trend | platforms | scores | winner_platform | winner_score | flags
  CR: date | trend | platforms_completed | scores | flag | notes

WINNERS-LOG FORMAT:
  date | trend | platform | hook_text | score | pattern

HW SCORE PATTERN (regex): LI:\d+ X:\d+ YT:\d+ IG:\d+ TT:\d+
NOTE: This pattern matches SA output. SA is NOT in the active chain → pattern will NOT
      be found → UNSCORED path fires (see Step 5e). This is correct, not a regression.

SCORES FIELD VALUES:
  Scored (SA in chain)  → e.g. LI:19 X:18 YT:17 IG:17 TT:18
  UNSCORED (SA absent)  → UNSCORED — CR output returned quality_flags:[] but no per-hook
                           numerical scores
  quality_flags:[]      → PASS signal from CR (empty list = no violations detected)

ABORT SENTINELS (case-insensitive):
  - empty string or len < 50 characters
  - starts with "I cannot"
  - starts with "I don't have"
  - starts with "I'm unable"
  - starts with "I'm sorry, I"
  - contains "As an AI, I"

HANDOFF EVALUATION THRESHOLDS (TI → HW):
  required elements : topic ({ti_trend}), confidence ({ti_confidence}), angle ({ti_angle})
  quality_score     : count_present / 3
  quality_score=1.0 : PASS  → structured handoff, continue to HW
  quality_score≥0.33: WARN  → structured handoff with "not found" for missing, continue
  quality_score=0.0 : ABORT → stop pipeline, mark TI FAILED
  scope exception   : skip 4f and 4g entirely if pipeline_scope == "TI"

HW→CR handoff: pass {hw_output} verbatim — no structured handoff needed.
  CR receives formatted per-platform hooks; no analytical noise to filter.
```

---

## STEP 0 — Task List

Create tasks before starting:
- "VALIDATE — input gate"
- "TI — Trend Intelligence run + quality gate + handoff construction"
- "HW — Hook Writer run"
- "CR — Content Repurposer run"
- "LOG — Write evo-logs and winners-log"
- "REPORT — Final summary"

Mark each `in_progress` before starting, `completed` when done.

---

## STEP 1 — Determine Pipeline Scope

### Default scope is `"TI"` while the auto-chain conflict is open

Because TI calls HW and HW calls CR server-side (see the conflict section above), scope
`"TI"` already produces the full chain. It is the only scope that runs each agent exactly once.

| User says | Scope |
|---|---|
| "samo TI" / "run TI only" | `"TI"` |
| (anything else, including no scope stated) | `"TI"` — with the notice below |
| "TI i HW" / "TI and HW" / "stop before CR" | `"TI+HW"` — **blocked, requires confirmation** |
| "full pipeline" / "sve tri" / explicit request for FULL | `"FULL"` — **blocked, requires confirmation** |

Store as `pipeline_scope`: `"TI"` / `"TI+HW"` / `"FULL"`.

**When the user did not state a scope**, run `"TI"` and say once, in the final report:

> ℹ️ Pokrenut je scope `TI` — TI interno zove HW i CR, pa je lanac ipak kompletan.
> Pun `FULL` scope bi izvršio HW dvaput a CR triput. Detalji: `system/soma-run-double-orchestration-conflict.md`.

**When the user explicitly asks for `"TI+HW"` or `"FULL"`**, do not run it. Stop and ask:

> ⚠️ `FULL` scope bi ponovo pozvao HW i CR koje je TI već pozvao — HW bi se izvršio dvaput,
> CR triput, i logirao bi se pogrešan set hookova. Izmereno 2026-07-29, dva runa.
> Odluka od 2026-06-19 (`system/soma-run-double-orchestration-conflict.md`) je da se
> `call_agent` nodovi uklone iz TI i HW, i to još nije urađeno.
> Preporuka: scope `TI`. Da svejedno pustim `FULL`? (da/ne)

Proceed with the requested scope **only on an explicit "da" / "yes"**. Silence, ambiguity, or
no answer → run `"TI"`. This gate is fail-closed: the expensive, log-corrupting path requires
a positive confirmation, never a default.

---

## STEP 2 — VALIDATE: Input Gate

### 2a — Validator recommendation
Before running, check if the user has already run `pipeline-input-validator` on this
input. If they have not, recommend it:

> "💡 Preporučujem da prvo pokreneš `pipeline-input-validator` na ovom inputu. Ako je
> status PASS ili WARN+, nastavi sa soma-run. Nastavljamo svejedno?"

If user confirms (or if they already have a PASS/WARN+ result) → proceed to 2b.
If user has a WARN- or FAIL result → warn but allow override: "Input ima slab score.
Sigurno želiš da ga pustiš kroz pipeline?"

### 2b — Minimum input check
Extract the raw trend input from the user's message. Apply:

| Check | Abort condition |
|---|---|
| Empty | Input is empty or whitespace only → ABORT |
| Too short | Input is < 20 characters → ABORT: "Input je prekratak. Opiši trend konkretno." |
| Abort sentinel in input | Input contains an abort sentinel string → ABORT: "Input sadrži nevalidan sadržaj." |

If input passes → store as `{trend_input}`. Proceed to Step 3.

---

## STEP 3 — Generate run_id

Generate run ID using current date and time:
```
run_id = YYYY-MM-DD-HHMMSS   (e.g. 2026-05-16-143022)
```

Use today's actual date. Do not guess or fabricate. If unsure of current time,
use `YYYY-MM-DD` only as the run_id.

Store as `{run_id}`. This ID will appear in all three evo-log entries for this run.

---

## STEP 4 — TI: Run Trend Intelligence

Mark task in_progress. Read `references/ti-run-procedure.md` now and follow it in
full — this is the longest and most safety-critical step. It covers, in order:

- **4b** — build the TI message with the mandatory `Today is {YYYY-MM-DD}.` prefix
  (omitting it was a confirmed bug)
- **4c** — the fire-and-poll call pattern: record `{exec_before}`, send exactly ONE
  request, and on timeout **do NOT resend** — poll `as_get_recent_executions` instead.
  A timeout here is expected, not a failure
- **4c-bis** — confirm via `as_list_agent_calls` that the source actually fetched
  matches `{trend_input}`; discard and re-run if it doesn't
- **4d** — capture `{ti_output}`
- **4e** — validate against abort sentinels and extract `{ti_trend}`, `{ti_confidence}`,
  `{ti_angle}`
- **4f** — the Context Quality Gate: score PASS / WARN / ABORT and decide whether to
  proceed to HW (skipped entirely if `pipeline_scope == "TI"`)
- **4g** — construct the structured `{ti_handoff}` block carrying the complete verbatim
  `{ti_output}` (skipped if scope is `"TI"` or 4f resulted in ABORT)

---

## STEP 5 — HW: Run Hook Writer

*Skip if `pipeline_scope == "TI"`.*

### 5a — Mark task in_progress

### 5b — Call HW

Pass the structured handoff block as the message. `{ti_handoff}` contains a
parseable header with extracted signals plus the full TI context verbatim.

```
as_chat_with_agent(
  agent_name:     "Hook Writer",
  message:        {ti_handoff},
  timeout_seconds: 120
)
```

### 5c — Capture output

Store the full reply text as `{hw_output}`.

### 5d — Validate HW output

Check `{hw_output}` against abort sentinels:
- If ABORT → mark HW as `FAILED`. Log TI entry only. Stop pipeline.
  Report: "⛔ HW vrati nevalidan output. TI je logiran. Pipeline abortiran."
- If OK → proceed to 5e.

### 5e — Extract scores from HW output

Scan `{hw_output}` for the score pattern `LI:\d+ X:\d+ YT:\d+ IG:\d+ TT:\d+`.

- If pattern found → extract individual platform scores:
  ```
  {hw_scores_raw} = "LI:19 X:18 YT:17 IG:17 TT:18"   (example)
  {hw_scores} = { LI: 19, X: 18, YT: 17, IG: 17, TT: 18 }
  ```
- If pattern NOT found → set `{hw_scores_raw}` = `"UNSCORED"`, `{hw_scores}` = null.

Determine winner platform:
- If `{hw_scores}` is not null → find platform with highest score.
  Ties: prefer LinkedIn > X > YouTube > Instagram > TikTok.
  Store as `{hw_winner_platform}` and `{hw_winner_score}` (format: `"19/20"` including `/20` suffix — e.g., `"19/20"` for score 19).
- If `{hw_scores}` is null → `{hw_winner_platform}` = `"n/a"`, `{hw_winner_score}` = `"n/a"`.

Determine flags:
- If `{hw_scores}` is null → flag = `"UNSCORED"`
- If all platform scores identical → flag = `"SINGLE_HOOK_BUG"` (same hook on all platforms)
- If any quality violation detected (banned phrase / fabricated stat) → flag = `"QUALITY_VIOLATION"`
- If clean run → flag = `"none"`

Store as `{hw_flags}`.

---

## STEP 6 — CR: Run Content Repurposer

*Skip if `pipeline_scope == "TI"` or `pipeline_scope == "TI+HW"`.*

### 6a — Mark task in_progress

### 6b — Call CR

Pass the full HW output as the message. Do not summarize or truncate.

```
as_chat_with_agent(
  agent_name:     "Content Repurposer",
  message:        {hw_output},
  timeout_seconds: 120
)
```

### 6c — Capture output

Store the full reply text as `{cr_output}`.

### 6d — Validate CR output

Check `{cr_output}` against abort sentinels:
- If ABORT → mark CR as `FAILED`. Log TI and HW entries. Stop before CR log.
  Report: "⛔ CR vrati nevalidan output. TI i HW su logirani. CR nije logiran."
- If OK → proceed to 6e.

### 6e — Extract CR data

- Scan for score pattern `LI:\d+ X:\d+ YT:\d+ IG:\d+ TT:\d+` in `{cr_output}`.
  If found → store as `{cr_scores_raw}`.
  If not found → `{cr_scores_raw}` = `"UNSCORED"`.
- Count platforms completed: scan for platform-specific sections (LinkedIn, X/Twitter,
  YouTube, Instagram, TikTok). Count how many are present.
  Store as `{cr_platforms_completed}` = `"N/5"` (e.g., `"5/5"`).
- Determine CR flag:
  - If `{cr_scores_raw}` = `"UNSCORED"` AND `quality_flags: []` found in CR output
    → flag = `"none"` (quality gate PASSED — empty list = no violations)
  - If `{cr_scores_raw}` = `"UNSCORED"` AND `quality_flags` NOT found in CR output
    → flag = `"WARN"` (unable to determine pass/fail — manual review needed)
  - If `quality_flags` contains non-empty items → flag = `"QUALITY_VIOLATIONS"`
    (describe each violation in `{cr_notes}`)
  - If numerical scores present AND clean → flag = `"none"`
  Store as `{cr_flag}`.
- Notes: short 1-line summary of the run (e.g., "✅ CLEAN RUN" or specific issue).
  Store as `{cr_notes}`.

---

## STEP 7 — LOG: Write Evo-logs

### 7a — Read before write (mandatory)

Before writing to any evo-log, call `obsidian_read_note` on each target path to
confirm the note exists. If `obsidian_read_note` returns `"Note not found"` →
create the note first with `obsidian_create_note`, then proceed with append.

### 7b — Write TI evo-log

Call `obsidian_update_note`:
```
path:    "agents/trend-intelligence/evo-log.md"
mode:    "append"
content: "{run_id date} | {ti_trend} | {ti_confidence} | {ti_angle} | {ti_status}"
```

Real format example:
```
2026-05-16 | Anthropic Claude Sonnet 4 released | ⭐⭐⭐ | Self-improving AI agents | yes
```

### 7c — Write HW evo-log

*Skip if HW was not run or FAILED.*

Call `obsidian_update_note`:
```
path:    "agents/hook-writer/evo-log.md"
mode:    "append"
content: "{date} | {ti_trend} | all-5 (platform-specific) | {hw_scores_raw} | {hw_winner_platform} | {hw_winner_score} | {hw_flags}"
```

Real format examples:

Scored (SA in chain):
```
2026-05-16 | Anthropic Claude Sonnet 4 release | all-5 (platform-specific) | LI:19 X:18 YT:17 IG:17 TT:18 | LinkedIn | 19/20 | none
```

UNSCORED (standard — SA not in chain, CR returns quality_flags:[]):
```
2026-06-14 | Databricks Omnigent meta-harness | all-5 | UNSCORED — CR output returned quality_flags:[] but no per-hook numerical scores | n/a | n/a | UNSCORED
```

### 7d — Write CR evo-log

*Skip if CR was not run or FAILED.*

Call `obsidian_update_note`:
```
path:    "agents/content-repurposer/evo-log.md"
mode:    "append"
content: "{date} | {ti_trend} | {cr_platforms_completed} | {cr_scores_raw} | {cr_flag} | {cr_notes}"
```

Real format examples:

Scored (SA in chain):
```
2026-05-16 | Anthropic Claude Sonnet 4 release | 5/5 | LI:19 X:18 YT:17 IG:17 TT:18 | none | ✅ CLEAN RUN
```

Standard (CR returns quality_flags:[], no numerical scores):
```
2026-06-14 | Databricks Omnigent meta-harness | 5/5 | UNSCORED | none | ✅ CLEAN RUN — quality_flags:[]
```

---

## STEP 8 — LOG: Write Winners-log

*Skip if HW was not run, FAILED, or `{hw_scores}` is null.*

### 8a — Check threshold

For each platform in `{hw_scores}`:
- If score ≥ 17 → this platform qualifies for winners-log.

If no platform scores ≥ 17 → skip this step entirely.

### 8b — Extract winning hook text per platform

For each qualifying platform, scan `{hw_output}` to extract:
- `{hook_text}`: the actual hook text written for that platform
  (look for platform label like "**LinkedIn:**" or "HOOK_LINKEDIN:" followed by the hook)
- `{hook_pattern}`: the pattern type (P1, P2, P3, P4, P5, P6 — if visible in HW output)
  If pattern not identifiable → use `"unknown"`

### 8c — Read winners-log before writing

Call `obsidian_read_note` on `agents/hook-writer/winners-log.md`.
If not found → create first.

### 8d — Append one entry per winning platform

For each qualifying platform, call `obsidian_update_note`:
```
path:    "agents/hook-writer/winners-log.md"
mode:    "append"
content: "{date} | {ti_trend} | {platform} | {hook_text} | {score}/20 | {hook_pattern}"
```

Real format example:
```
2026-05-16 | Anthropic Claude Sonnet 4 release | LinkedIn | Human code isn't the bottleneck anymore — your AI agent is. | 19/20 | P1
```

---

## STEP 9 — REPORT: Final Summary

Read `references/report-template.md` now and fill it in from all data gathered in
STEPs 1–8 (step results, TI/HW/CR output summaries, logging status per evo-log and
winners-log). Append the FAILED-steps notice or the clean-completion line as appropriate.

## Error Recovery Guide, Tool Reference, Constraints Summary, Invocation Examples

Consult `references/reference-tables.md`: Error Recovery Guide (only if a step FAILED),
Tool Reference, Constraints Summary (date injection always present, `{ti_handoff}` for
TI→HW never raw `{ti_output}`, read-before-write per evo-log, winners threshold ≥17/20
per platform), and sample invocation phrases.
