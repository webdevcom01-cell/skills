---
name: soma-run
version: 1.2.2
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
do_not_use_when:
  - "User wants to validate input only (use pipeline-input-validator)"
  - "User wants to log an existing run (use evo-log-writer)"
  - "User wants to sync KB content (use kb-sync)"
  - "User wants a health check (use agent-health-check)"
  - "User wants to fix kb_search wiring (use soma-memory-fix)"
---

# Skill: soma-run

*Version: 1.2.2*
*Grounded in: live MCP audit 2026-05-16 — all tool schemas, evo-log formats, Obsidian*
*paths, and timeout values confirmed from live data. Zero values from memory.*
*Revised 2026-07-29: added the auto-chain conflict section and the scope gate below,*
*from live flow reads, two measured runs, and live heartbeat/goal checks. The orchestration*
*model itself is unchanged — see "Why this skill has not been rewritten to match".*

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

Verified by reading the live flows and by two measured runs on 2026-07-29
(`2026-07-29-154101`, `2026-07-29-155852`):

- `Trend Intelligence` contains a `call_agent` node targeting `Hook Writer`
  (`targetAgentId: cmp832hkithbhj9suiqgmjqpw`, `timeoutSeconds: 300`, `onError: continue`)
- `Hook Writer` contains `call_agent-cr` targeting `Content Repurposer`
- `Content Repurposer` has no `call_agent` nodes — it is terminal

The IDs quoted in this section are **evidence of what was observed on 2026-07-29**, not lookup
keys. Never paste them into a tool call — resolve agents by name (`as_get_agent`,
`as_list_agents`) and re-read the flows, because an agent recreated in a cleanup gets a new ID
while the name stays.

Calling **only TI** therefore executes the whole chain. Measured, nested, in both runs:

| agent | run 1 | run 2 |
|---|---|---|
| TI | 96.5 s | 113.8 s |
| HW (nested inside TI) | 51.0 s | 50.9 s |
| CR (nested inside HW) | 31.0 s | 30.6 s |

HW and CR deviated by **less than 0.5 s** between the two runs — a stable pattern, not chance.

**Consequence for this skill:** STEP 5b and STEP 6b call HW and CR again, externally. TI has
already called both. Completing those steps means **HW executes twice and CR three times** —
triple cost, three different sets of hooks, and the wrong set logged. This is the exact
failure reproduced on 2026-06-19 (`HW → BLOCKED wrong_count 0/5`, `CR → BLOCKED missing_trend`):
the gates were working correctly, they were being fed the wrong stage's output.

### What to do until this is resolved

**Do NOT run `pipeline_scope: "FULL"` or `"TI+HW"`.** Run scope `"TI"` — it produces the
complete chain anyway. See STEP 1.

### Why this skill has not been rewritten to match

The decision was already made and is recorded in the vault:
`system/soma-run-double-orchestration-conflict.md` (2026-06-19, status `decided`).

The chosen fix is **Option 2 — remove the `call_agent` nodes from TI and HW**, planned as a
separate sprint, so that external stage-by-stage orchestration (which `soma-run`,
`evo-log-writer`, `winners-log-logger`, `pipeline-input-validator`, `pipeline-debug` and
`soma-performance-review` all assume) becomes the single source of truth about who drives
the pipeline.

The same document names the opposite fix — keep internal chaining, rewrite `soma-run` to call
only TI and parse the final posts — but makes it conditional on the pipeline needing to run
autonomously via scheduler/heartbeat without a skill. Checked live on 2026-07-29: TI
(`cmpnu72fy0008p401ixaaehq8`) has **no heartbeat configured** and **no goals linked**; Hook
Writer (`cmp832hkithbhj9suiqgmjqpw`) has **no heartbeat configured**. That condition is not
met, so the inverse rewrite is not the correct change today.

**Do not "fix" this skill by making it supervisory without revisiting that decision document first.**

### One more measured limit — and it is worse than a lost response

The MCP client aborts at **60 s** regardless of `timeout_seconds` (the schema accepts up to
300). TI takes 68-113 s. So **every** blocking call to TI times out client-side while the
server-side run completes normally.

Measured again on 2026-07-29 (18:37-18:49 UTC), and this time the follow-on effect was
observed: **the client retries the aborted request, and each retry launches another full
server-side chain.** Two user requests produced **six** TI runs, six HW calls and six CR
calls - 18 agent executions.

Worse, the retries are not equivalent to the first attempt:

| attempt | source actually fetched | correct |
|---|---|---|
| request 1, try 1 | `anthropic.com/news/claude-science-ai-workbench` | yes |
| request 2, try 1 | `openai.com/index/the-next-evolution-of-the-agents-sdk/` | yes |
| 4 retries | `anthropic.com/research/diff-tool` (in neither input) | no |

Both first attempts honoured the URL in the message. All four retries lost it, fell back to
`search_results`, and picked the `PRI[0]` domain - the exact failure mode patched that same
morning. Every one of those runs still reached `READY_FOR_REVIEW` with clean, grounded posts
about the wrong article. No gate catches this, because nothing about the output is malformed.

**Therefore: never call TI with a blocking wait from this client.** Use fire-and-poll
(STEP 4c). Full evidence: `system/mcp-chat-timeout-retry-storm-2026-07-29.md`.

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

### 4a — Mark task in_progress

### 4b — Build TI message

Construct the message as follows (date injection is mandatory):
```
Today is {YYYY-MM-DD}. {trend_input}
```

Example:
```
Today is 2026-05-16. Anthropic released Claude Sonnet 4 — 40% SWE-bench improvement.
```

**CRITICAL:** The `Today is {date}` prefix MUST be included. Without it, TI runs without
date context and may misclassify freshness. This was confirmed as a bug on 2026-05-15.

### 4c — Call TI (fire-and-poll — do NOT wait for the reply)

Before sending, record the current latest execution id:

```
as_get_recent_executions(agent_name: "Trend Intelligence", limit: 1)
```

Store it as `{exec_before}`. Then send exactly ONE request:

```
as_chat_with_agent(
  agent_name:     "Trend Intelligence",
  message:        "Today is {YYYY-MM-DD}. {trend_input}",
  timeout_seconds: 300
)
```

**A timeout here is expected, not a failure.** The client aborts at 60 s; the run keeps
going server-side. When the tool returns a timeout error:

- do **NOT** send the message again — a second send is a second full chain
- wait ~120 s, then poll `as_get_recent_executions(agent_name: "Trend Intelligence", limit: 3)`
- the run whose `startedAt` is after `{exec_before}` is yours; wait until its `status` leaves
  `RUNNING`

If more than one new execution appears, the client retried underneath. Keep **only the
earliest** one — later retries lose the URL from the message (see the measured limit section
above) and must not be logged as trends.

### 4c-bis — Confirm the source that was actually fetched

```
as_list_agent_calls(callee_agent_name: "Security Supervisor", since_hours: 1, limit: 5)
```

The `inputPreview` of the call belonging to your run begins with `Title: ... URL Source: ...`.
If that URL is not the one in `{trend_input}`, the run is grounded in the wrong article →
mark the run `DISCARD`, do not log it, and re-run. This check costs one call and is the only
thing standing between a wrong-topic run and the winners-log.

### 4d — Capture output

Store the full reply text as `{ti_output}`. If the reply never arrived (timeout), read the
outcome from `as_get_recent_executions` `outputPreview` instead — and if that is truncated,
log the run as `RESPONSE_NOT_RECEIVED` rather than reconstructing it (see Hard rules).

### 4e — Validate TI output

Check `{ti_output}` against abort sentinels:
- If ABORT condition matched → mark TI as `FAILED`, log entry with flag `ABORT`, stop pipeline.
  Report: "⛔ TI vrati prazan ili nevalidan output. Pipeline abortiran. Provjeri agent ili input."
- If OK → extract from TI output:
  - `{ti_trend}`: the trend name/title TI identified (first sentence or headline)
  - `{ti_confidence}`: confidence rating (look for ⭐ symbols — ⭐⭐⭐ = HIGH, ⭐⭐ = MED, ⭐ = LOW/EVERGREEN)
  - `{ti_angle}`: the content angle TI suggested
  - Set `{ti_status}` = `"yes"` (hook_writer_triggered)

### 4f — Evaluate TI output quality (Context Quality Gate)

*Skip entirely if `pipeline_scope == "TI"` — no HW run means no handoff needed.*

Before passing context to HW, evaluate whether `{ti_output}` contains the three
elements HW needs to generate quality hooks. Implements the EVALUATE phase of
iterative context retrieval.

**Element check — use values already extracted in 4e:**

| Element | Variable | Present if |
|---|---|---|
| topic | `{ti_trend}` | non-empty AND len > 5 chars |
| confidence | `{ti_confidence}` | contains at least one ⭐ |
| angle | `{ti_angle}` | non-empty AND len > 10 chars |

```
topic_present      = {ti_trend} non-empty AND len({ti_trend}) > 5
confidence_present = {ti_confidence} contains "⭐"
angle_present      = {ti_angle} non-empty AND len({ti_angle}) > 10

quality_score = (topic_present + confidence_present + angle_present) / 3
```

**Note:** `{ti_angle}` extraction is best-effort — TI output is unstructured LLM text.
`angle_present = True` confirms the field was populated, not that the content is a
valid angle. False positives are possible but acceptable — the full `{ti_output}` in
the `<<SOMA_CONTEXT_START>>` block remains available for HW regardless.

**Decision logic:**

```
quality_score = 1.0  → {ti_quality_status} = "PASS"
                        → proceed to 4g
quality_score ≥ 0.33 → {ti_quality_status} = "WARN: missing [topic|confidence|angle]"
                        (list only the missing elements)
                        → proceed to 4g with "not found" for missing elements
quality_score = 0.0  → {ti_quality_status} = "ABORT"
                        → mark TI as FAILED, do not proceed to HW or 4g
                        Report: "⛔ TI output ne sadrži nijedan potreban element
                        (topic/confidence/angle). Pipeline abortiran —
                        provjeri TI sistem prompt i KB wiring."
```

Store `{ti_quality_status}` for use in STEP 9 report. Do NOT write to TI evo-log
(TI evo-log format has no notes field — adding one would break existing parsers).

### 4g — Construct structured handoff: TI → HW

*Skip entirely if `pipeline_scope == "TI"` — no HW run means no handoff needed.*
*Skip if `{ti_quality_status}` = "ABORT" — pipeline already stopped in 4f.*

Build a structured handoff block that gives HW both a parseable header and the full
original TI context. Implements the REFINE phase of iterative context retrieval.

**Extraction rules for optional fields (scan `{ti_output}`):**

| Field | What to scan for | If not found |
|---|---|---|
| `platform_hint` | Platform names: LinkedIn, X, Twitter, YouTube, Instagram, TikTok, TT, LI, IG | `"not specified"` |
| `audience_hint` | Audience words: founders, developers, marketers, engineers, CTOs, product managers | `"not specified"` |
| `timing_signal` | Urgency words: breaking, just released, announced today, this week, trending now | `"not specified"` |

If found → extract the surrounding sentence (verbatim from `{ti_output}`).
If not found → use `"not specified"`. Never generate these values from memory.

**Construct `{ti_handoff}`:**

```
<<SOMA_HANDOFF_START>>
TREND: {ti_trend}
CONFIDENCE: {ti_confidence}
ANGLE: {ti_angle}
PLATFORM_HINT: {platform_hint}
AUDIENCE_HINT: {audience_hint}
TIMING: {timing_signal}
<<SOMA_CONTEXT_START>>
{ti_output}
<<SOMA_HANDOFF_END>>
```

Store result as `{ti_handoff}`.

**Critical:** `{ti_output}` between `<<SOMA_CONTEXT_START>>` and `<<SOMA_HANDOFF_END>>`
must be the complete, verbatim TI output. Never truncate or summarize.
The `<<...>>` delimiters are chosen to avoid collision with TI output content
(TI uses standard markdown, not angle-bracket delimiters).

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

After all steps complete, output the final report:

```
🚀 SOMA RUN — COMPLETE
══════════════════════════════════════════
Run ID   : {run_id}
Scope    : {pipeline_scope}
Input    : {trend_input (first 80 chars)}
══════════════════════════════════════════

STEP RESULTS:
  TI         → {✅ COMPLETED | ⛔ FAILED | ⏭️ SKIPPED}
  TI Quality → {PASS | WARN: [missing elements] | ABORT | N/A (scope=TI)}
  HW         → {✅ COMPLETED | ⛔ FAILED | ⏭️ SKIPPED}
  CR         → {✅ COMPLETED | ⛔ FAILED | ⏭️ SKIPPED}

══════════════════════════════════════════
TI OUTPUT SUMMARY:
  Trend      : {ti_trend}
  Confidence : {ti_confidence}
  Angle      : {ti_angle}

HW OUTPUT SUMMARY:
  Scores     : {hw_scores_raw}
  Winner     : {hw_winner_platform} ({hw_winner_score}/20)
  Flags      : {hw_flags}

CR OUTPUT SUMMARY:
  Platforms  : {cr_platforms_completed}
  Scores     : {cr_scores_raw}
  Flag       : {cr_flag}
  Notes      : {cr_notes}

══════════════════════════════════════════
LOGGING:
  TI evo-log  → {✅ written | ⛔ failed}
  HW evo-log  → {✅ written | ⛔ failed | ⏭️ skipped}
  CR evo-log  → {✅ written | ⛔ failed | ⏭️ skipped}
  Winners-log → {✅ N entries written | ⏭️ no hooks ≥17 | ⏭️ skipped}
══════════════════════════════════════════
```

If any step FAILED, add after the report:
```
⚠️ Neke faze nisu završene. Provjeri agent status u Agent Studio.
```

If full pipeline completed cleanly:
```
✅ Pipeline završen. Možeš pokrenuti soma-performance-review za historijski pregled.
```

---

## STEP 10 — Error Recovery Guide

Include this only in the report if a FAILED step occurred:

| Failed step | Likely cause | Action |
|---|---|---|
| TI FAILED (timeout) | Client 60 s cap — run is probably alive | NE slati ponovo. Poll `as_get_recent_executions`; povećanje `timeout_seconds` ne pomaže |
| Više novih TI execution-a nego poslanih zahtjeva | Client retry storm | Zadrži najraniji, ostale označi `DISCARD` — retry gubi URL iz poruke |
| TI FAILED (abort sentinel) | Agent misconfigured | Pokreni agent-health-check |
| TI FAILED (quality gate 0.0) | TI output bez topic/confidence/angle | Provjeri TI sistem prompt i KB wiring |
| TI WARN (quality gate < 1.0) | TI output nepotpun | Pipeline nastavio sa degraded handoff — provjeri TI instincts i KB |
| HW FAILED (timeout) | Large TI output | Pokušaj ponovo — HW timeout je 120s |
| HW FAILED (abort sentinel) | Bad handoff content | Provjeri {ti_handoff} — potvrdi da {ti_output} nije bio prazan ili malformiran |
| CR FAILED (any) | Pokušaj ponovo | CR rijetko faila na validan HW output |
| Evo-log write failed | Obsidian MCP nedostupan | Provjeri Obsidian MCP konekciju |

---

## Tool Reference

| Tool | Used for | Key params |
|---|---|---|
| `as_chat_with_agent` | Run TI / HW / CR | `agent_name`, `message`, `timeout_seconds` |
| `obsidian_read_note` | Read evo-log before write | `path` |
| `obsidian_update_note` | Append evo-log entry | `path`, `mode: "append"`, `content` |
| `obsidian_create_note` | Create evo-log if missing | `path`, `body` |

---

## Constraints Summary

| Constraint | Rule |
|---|---|
| Date injection | ALWAYS prefix TI message with "Today is YYYY-MM-DD." |
| TI→HW handoff | Always use `{ti_handoff}` — contains structured header + full `{ti_output}` verbatim. Never pass raw `{ti_output}` to HW. |
| HW→CR handoff | Pass raw `{hw_output}` to CR verbatim — no structured handoff needed. |
| Abort on sentinel | Check every agent output before passing downstream |
| Log only real data | Never write fabricated scores, trends, or hook text to evo-log |
| Read before write | Always `obsidian_read_note` before `obsidian_update_note` |
| Timeouts | TI: 180s | HW: 120s | CR: 120s — never use defaults |
| Winners threshold | Score ≥ 17/20 per platform — not just the overall winner |

---

## Invocation examples

```
"soma run — Claude Sonnet 4 released, SWE-bench +40%"
"pokreni pipeline — https://anthropic.com/news/claude-sonnet-4"
"run SOMA — samo TI"
"pusti trend kroz pipeline: OpenAI GPT-5 Turbo announced"
"soma-run — TI i HW samo, bez CR"
"run the pipeline on this: Anthropic released Claude 4 Opus today"
```
