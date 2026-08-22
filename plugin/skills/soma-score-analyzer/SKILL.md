---
name: soma-score-analyzer
version: 0.1.0
description: >
  Restores the missing 4th stage of the SOMA pipeline (TI → HW → CR → Score Analyzer).
  Scores Content Repurposer output per platform on the SOMA 20-point rubric, writes the
  real scores back into evo-logs (replacing UNSCORED), and feeds winners-log for hooks
  scoring ≥17/20 — closing the feedback loop that SOMA Evolution Advisor keeps flagging
  as "scoring missing since 2026-06-14". Use whenever a CR run finished UNSCORED, when the
  user says "score this output", "oceni postove", "skoruj output", "zašto je UNSCORED",
  "popravi scoring", "feed winners-log", "score analyzer", "missing scoring", "oceni hookove",
  "izračunaj score", or after any soma-run that returned UNSCORED. Also use to scaffold a
  persistent Score Analyzer agent into the live chain (Appendix A). Do NOT use to run the
  pipeline (use soma-run), to log an already-scored run (use evo-log-writer /
  winners-log-logger), or to review historical performance (use soma-performance-review).
do_not_use_when:
  - User wants to run the full pipeline (use soma-run)
  - User wants to log an already-scored run (use evo-log-writer or winners-log-logger)
  - User wants a historical performance report (use soma-performance-review)
allowed-tools:
  - TodoWrite
  - mcp__agent-studio__as_search_knowledge_base
  - mcp__agent-studio-db__as_search_knowledge_base
  - mcp__agent-studio__as_chat_with_agent
  - mcp__agent-studio-db__as_chat_with_agent
  - mcp__agent-studio__as_inspect_flow
  - mcp__agent-studio-db__as_inspect_flow
  - mcp__agent-studio__as_update_flow
  - mcp__agent-studio-db__as_update_flow
  - mcp__agent-studio__as_add_kb_text
  - mcp__agent-studio-db__as_add_kb_text
  - mcp__obsidian__obsidian_read_note
  - mcp__obsidian__obsidian_update_note
  - mcp__obsidian__obsidian_create_note
---

# SOMA Score Analyzer

## What this skill does

The SOMA pipeline was designed as **TI → HW → CR → Score Analyzer (SA)**, but the SA
agent was never deployed into the live chain. Because of that, every run ends `UNSCORED`,
`winners-log.md` stops growing, and `SOMA Evolution Advisor` has no scored data to learn
from — it has flagged *"Content Repurposer scoring missing since 2026-06-14"* across four
consecutive evolution reports.

This skill fills that gap. It takes the 5 platform posts a CR run produced, scores each on
the **SOMA scoring rubric loaded from the live KB** (never invented), writes the real
scores back into the evo-logs, and appends every hook ≥17/20 to winners-log. The result is
the same data the missing SA agent would have produced.

**Important — know the real root cause first.** Early runs (e.g. 2026-05-15/16) *were*
scored: the `LI:19 X:18 YT:17 IG:17 TT:18` values came **inline inside the HW/CR
ai_response payload**, not from a separate SA agent. Scoring went `UNSCORED` "since
2026-06-14", which coincides with the HW flow rework ("8 nodes post 2026-06-14 fix" in the
DESIGN_SPEC). So the most likely cause is a **regression** that stopped HW/CR from emitting
scores — not merely the absence of the SA agent. This skill is a **compensating control**
that restores the scored data, but Step 0.5 first checks whether the upstream regression
should be fixed at the source. Treat external scoring as the stopgap and the flow fix as the
durable cure.

## Hard rules — zero hallucination

1. **Never invent the rubric.** Load the scoring rubric from the Hook Writer KB before
   scoring (Step 1). If you cannot retrieve it, STOP and ask the user — do not score from a
   guessed rubric. A fabricated rubric silently corrupts every downstream learning loop.
2. **Score only real content.** Every score must trace to actual text in the CR/HW output.
   If a platform post is missing, mark it `MISSING`, do not estimate a score.
3. **Winners threshold is exactly ≥17/20 per platform** (live-confirmed in soma-run). Not
   the overall winner — each qualifying platform gets its own winners-log row.
4. **Read before write.** Always `obsidian_read_note` an evo-log/winners-log before
   `obsidian_update_note` (append). Create the note if missing.
5. **Append, never overwrite.** Use `mode: "append"`. The one exception (replacing a prior
   `UNSCORED` evo-log line) is handled in Step 5b and requires explicit user confirmation.
6. **`as_update_flow` is irreversible** — Appendix A (scaffolding the persistent SA agent)
   must `as_inspect_flow` backup first and `dry_run=true` before any live apply.

## Confirmed constants (live-verified this session, 2026-06-26)

```
PIPELINE AGENTS (real IDs):
  Trend Intelligence  cmpnu72fy0008p401ixaaehq8
  Hook Writer         cmp832hkithbhj9suiqgmjqpw   KB: cmj2xfhpxnihi5ohkfiubtzqm
  Content Repurposer  cgfnroihfs8ma03wsmp9bvbhq   KB: cmpsknkbo0001pbofdslfjsw3

EVO-LOG PATHS:
  HW  → agents/hook-writer/evo-log.md
  CR  → agents/content-repurposer/evo-log.md
WINNERS-LOG PATH:
  → agents/hook-writer/winners-log.md
  → Threshold: per-platform score ≥ 17/20

HW SCORE PATTERN (regex): LI:\d+ X:\d+ YT:\d+ IG:\d+ TT:\d+
PLATFORMS: LinkedIn (LI), X (X), YouTube (YT), Instagram (IG), TikTok (TT)
WINNERS-LOG FORMAT: date | trend | platform | hook_text | score/20 | pattern
```

## Workflow

### STEP 0 — Task list
Create: "REGRESSION CHECK", "LOAD RUBRIC", "GATHER OUTPUT", "SCORE", "WRITE EVO-LOG",
"WRITE WINNERS", "REPORT".

### STEP 0.5 — Regression check (decide stopgap vs source fix)
Before scoring externally, check whether HW/CR simply stopped emitting scores. Inspect the
two agents' ai_response nodes:
```
as_inspect_flow(agent_id:"cmp832hkithbhj9suiqgmjqpw", node_type:"ai_response")   # HW
as_inspect_flow(agent_id:"cgfnroihfs8ma03wsmp9bvbhq", node_type:"ai_response")   # CR
```
Read the prompts: do they still instruct the model to output per-platform scores
(`LI:.. X:.. ...`)? Compare against a recent run's payload.
- **If the prompt no longer asks for scores** → this is the 2026-06-14 regression. Tell the
  user the durable fix is to restore the scoring instruction via `soma-agent-debugger`
  (Mode 1 → Mode 2), and that this skill will meanwhile score the current output as a stopgap.
- **If the prompt still asks for scores but the model omitted them** → flaky output; external
  scoring here is the right call.
Record `{root_cause}` = `"regression"` | `"flaky"` | `"by_design (SA never wired)"`. Continue
to scoring either way — but surface `{root_cause}` in the final report so it isn't forgotten.

### STEP 1 — Assemble the scoring rubric (mandatory, anti-hallucination)
The rubric is **not a single clean document** — it is spread across several HW KB sources.
Run multiple queries and assemble, rather than expecting one "20-point" doc:
```
as_search_knowledge_base(kb_id:"cmj2xfhpxnihi5ohkfiubtzqm", query:"scoring calibration dimensions PF UF platform fit urgency", top_k:5)
as_search_knowledge_base(kb_id:"cmj2xfhpxnihi5ohkfiubtzqm", query:"gate validation banned phrases character word limits", top_k:5)
as_search_knowledge_base(kb_id:"cmj2xfhpxnihi5ohkfiubtzqm", query:"DESIGN_SPEC scoring how hooks scored 20", top_k:3)
```
Expect to find, across `agent-card` / `instincts` / `DESIGN_SPEC`: scoring dimensions
(Platform Fit **PF** is described as the most critical, Urgency **UF** often traded for
specificity, plus per-platform pattern fit), hard gate rules (banned phrases like
enhance/boost/transform/game-changer; char/word limits LinkedIn ≤210, X ≤280, YouTube ≤150,
TikTok ≤12 words), and calibration notes ("any hook <14 → switch pattern", "P3 best on
YouTube, P1 on LinkedIn"). Assemble these into `{rubric}` and echo the dimensions + their
point weights back to the user to confirm before scoring.

If none of the queries return usable scoring criteria → STOP:
> "⛔ Ne mogu da sklopim scoring rubriku iz KB. Reci mi dimenzije i bodove, ili dodaj jasnu
> rubriku u HW KB (as_add_kb_text) — neću da izmišljam ocene."

**Scope note:** the HW rubric scores **hooks**. CR produces **full posts**. When scoring CR
output, score the *hook line* of each post against `{rubric}`; judge the post body only on
the CR-side conventions (format-templates in the CR KB), and say which you scored.

### STEP 2 — Gather the content to score
Three input modes:
- **From a fresh soma-run** — user pastes the CR output, or points to it. Use it verbatim.
- **From history** — user names a trend/date. Read the relevant evo-log line and, if the
  full post text isn't in the log, ask the user for the CR output (the log stores summaries,
  not full posts).
- **Re-run** — if needed, call CR live: `as_chat_with_agent(agent_name:"Content Repurposer",
  message:{hw_output}, timeout_seconds:120)`.

Store the 5 platform posts as `{posts}` (one per platform). Mark any absent platform `MISSING`.

### STEP 3 — Score each platform
For each platform post, apply `{rubric}` dimension by dimension. For each dimension cite the
specific text that earned or lost points — scores must be defensible, not vibes.

Produce per platform:
```
{platform}: <total>/20  | breakdown: <dim1 a/max>, <dim2 b/max>, ...  | pattern: P1..P6 | notes
```

Build `{scores_raw}` in the canonical pattern: `LI:19 X:18 YT:17 IG:16 TT:18`.
Determine `{winner_platform}` / `{winner_score}` (ties: LI > X > YT > IG > TT).

### STEP 4 — Determine flags
- All five platforms identical hook text → `SINGLE_HOOK_BUG`.
- Any banned phrase / fabricated stat detected against rubric → `QUALITY_VIOLATION` (name it).
- Clean → `none`.
Store as `{flags}`.

### STEP 5 — Write scores into evo-logs

**5a — HW evo-log (append a scored line if this run was not previously scored):**
```
obsidian_read_note("agents/hook-writer/evo-log.md")   # create if missing
obsidian_update_note(
  path: "agents/hook-writer/evo-log.md", mode: "append",
  content: "{date} | {trend} | all-5 (platform-specific) | {scores_raw} | {winner_platform} | {winner_score}/20 | {flags}"
)
```

**5b — Supersede a prior UNSCORED line (default = append; replace only on request):**
`obsidian_update_note` in `append` mode cannot edit an existing line. So the **default** is to
append a new scored line whose notes field reads `supersedes UNSCORED entry {date}` — history
stays intact and the latest line is authoritative. Only if the user explicitly asks to rewrite
history: read the whole note, replace the single `UNSCORED` line in the text, and write the
full modified body back with `obsidian_update_note(mode: "replace")`.

**"Read the whole note" is not one call.** `obsidian_read_note` returns at most
`line_limit` lines — default **300**, max 500 — plus `total_lines`, `has_more` and
`next_line_offset`. An evo-log past 300 lines returns only its first page, and writing
that back with `replace` destroys the rest. Before any replace:
1. Call with `line_offset=0, line_limit=500`.
2. While `has_more == true`, call again with `line_offset = next_line_offset` and
   append each `body`.
3. Verify the assembled line count equals `total_lines`. If it does not, STOP — do
   not write.
4. Save the assembled original body to a sibling note (e.g. `<path>.bak`) before
   writing, so a botched replace is recoverable.

Confirm the diff with the user before writing — a botched whole-note write loses the log.

**5c — CR evo-log:**
```
content: "{date} | {trend} | {platforms_completed} | {scores_raw} | {flags} | scored by score-analyzer skill"
```

### STEP 6 — Write winners-log (per-platform ≥17)
For each platform with score ≥17:
```
obsidian_read_note("agents/hook-writer/winners-log.md")   # create if missing
obsidian_update_note(
  path: "agents/hook-writer/winners-log.md", mode: "append",
  content: "{date} | {trend} | {platform} | {hook_text} | {score}/20 | {pattern}"
)
```
`{hook_text}` must be the verbatim hook for that platform. `{pattern}` = P1..P6 if visible,
else `unknown`. If no platform ≥17 → skip and say so.

### STEP 7 — Report
```
🎯 SCORE ANALYZER — COMPLETE
Trend     : {trend}
Rubric    : loaded from HW KB ({n} dimensions)
Scores    : {scores_raw}
Winner    : {winner_platform} ({winner_score}/20)
Flags     : {flags}
Root cause: {root_cause}   ← if "regression", recommend soma-agent-debugger as durable fix
Evo-logs  : HW ✅ | CR ✅
Winners   : {k} entr(y/ies) ≥17 written  (or: none ≥17)
```
Suggest: "Pokreni soma-performance-review za osvežen pregled, sada kad scoring opet teče."
If `{root_cause}` == `"regression"`, also: "Trajni fix je da vratiš scoring instrukciju u
HW/CR prompt — pokreni soma-agent-debugger. Dotle ovaj skill skoruje ručno."

---

## Appendix A — Scaffold a persistent Score Analyzer agent (optional)

Scoring by skill fixes the data gap immediately. To make it permanent inside the live chain,
deploy an SA agent between CR and the logs. This is irreversible flow surgery — proceed only
on explicit request and with backups.

1. **Backup** CR flow: `as_inspect_flow(agent_id:"cgfnroihfs8ma03wsmp9bvbhq")` → save JSON.
2. **Do not hand-build the flow.** `as_create_agent` + `as_update_flow` flow construction is
   exactly what `safe-agent-builder` does with a deterministic gate baked in and a
   bad-input smoke test — delegate the whole agent build to it. Target shape to request:
   `kb_search (HW KB rubric) → ai_response (score per rubric, out=sa_scores) →
   function-validator (assert LI/X/YT/IG/TT all present & 0–20) → condition-gate →
   pass-emitter`, model `gpt-4.1-mini` (OPENAI is the only key set — see soma-model-preflight).
3. **Seed** its KB with the rubric (`as_add_kb_text`).
4. **Wire** CR → SA: add a `call_agent` node to CR targeting the SA agent. Run
   `as_update_flow` with `dry_run=true` first; confirm node/edge counts; only then apply.
5. **Smoke test** both a high-quality input (expect ≥17 somewhere) and a deliberately weak
   one (expect low scores, no false winners). Add a regression eval suite with
   `runOnDeploy:true` (1 PASS case, 1 low-score case) per soma-agent-debugger.

Hand the structural build to `safe-agent-builder` if you want the deterministic gate baked
in from the start.

## Tool reference
| Tool | Used for |
|---|---|
| `as_search_knowledge_base` | Load rubric from HW KB |
| `as_chat_with_agent` | Optional CR re-run |
| `obsidian_read_note` / `obsidian_update_note` / `obsidian_create_note` | Evo-logs + winners-log |
| `as_inspect_flow` / `as_create_agent` / `as_update_flow` / `as_add_kb_text` | Appendix A only |

## Invocation examples
```
"oceni ovaj CR output — Claude Opus 4.5 trend"
"score this output, winners-log je prazan od 14.06"
"zašto je poslednji run UNSCORED?"
"skoruj i feed winners-log za poslednji soma-run"
"score analyzer — proveri prvo da nije regresija u HW flow-u"
```

## Versioning
| Version | Date | Notes |
|---|---|---|
| v0.2 | 2026-06-26 | Regression-check step; assemble fragmented rubric; supersede-vs-replace mechanism; firmer safe-agent-builder delegation; invocation examples |
| v0.1 | 2026-06-26 | Initial — grounded in live audit; restores SA scoring stage |
