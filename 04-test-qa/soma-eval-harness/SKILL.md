---
name: soma-eval-harness
version: 1.2.0
description: >-
  Evaluates SOMA pipeline reliability (TI → HW → CR) by re-running real logged trends k times, grading
  each trial with structural + quality graders, scoring by correctness (polarity-aware), and reporting
  consistency with pass/regression detection. Separate from soma-run (agent harness) — read-only on
  production evo-logs. Triggers (en/sr): "eval harness", "run eval", "capability eval", "regression
  eval", "test pipeline reliability", "provjeri pouzdanost pipeline-a", "pokreni eval", "regresijski
  eval", "da li je pipeline stabilan", "koliko je pipeline pouzdan", "testiraj agente eval". Triggers:
  "soma eval", "evaluiraj pipeline".
do_not_use_when:
  - "User wants to run a production pipeline (use soma-run)"
  - "User wants to log an existing run (use evo-log-writer / winners-log-logger)"
  - "User wants a historical summary of past runs (use soma-performance-review)"
  - "User wants a pre-run system check (use agent-health-check)"
  - "User wants to fix kb_search wiring (use soma-memory-fix)"
  - "User wants to update agent instincts (use instincts-updater)"
---

# Skill: soma-eval-harness

*Version: 1.2.0*
*Grounded in: live vault + skill audit 2026-06-21 — ti_handoff block, abort sentinels,*
*evo-log paths/schemas, CR flag vocabulary, char limits, and dataset composition all*
*confirmed from real files (soma-run SKILL.md + agents/*/evo-log.md). Zero values from memory.*

---

## Purpose

Measures whether the SOMA content pipeline produces **correct, consistent** output, by
re-running real logged trends through TI → HW → CR `k` times and grading each trial.

```
[Eval task + expected_grade] → RUN k=5 trials (direct as_chat_with_agent)
  → GRADE (G1–G4 structural + M1,M2 quality) → SCORE correctness (polarity-aware)
  → COMPUTE consistency → DETECT graduation/regression → REPORT (system/evals/)
```

This is an **eval harness**, separate from the agent harness (`soma-run`). It calls
agents directly, never via soma-run, and never writes to production evo-logs.

---

## Hard rules — zero hallucination (11)

1. Every trial output comes from a real `as_chat_with_agent` call — never invented.
2. G1–G4 and M2 results derive from real agent output in this session — never estimated.
3. M1 score comes from a real LLM judge call with the exact rubric — never assumed.
4. `correct_count` / `consistency` computed from real `trial_correct` values — never rounded/estimated.
5. **Abort sentinel = FAIL** (a measured behavioral outcome), surfaced through the relevant structural grader. Never ERROR, never TIMEOUT.
6. **TIMEOUT and ERROR** are excluded from `valid_trials` — never counted as FAIL or PASS.
7. `trend_input` is **verbatim** from the TI `## Entries` `trend_found` field — never paraphrased or fabricated.
8. `expected_grade` is derived from the CR `flag` field — never assumed; **always compared against `observed_grade`**.
9. Baseline comparison is against `system/evals/baseline.md` — never from memory of prior results.
10. **Read-only on production evo-logs** (`agents/*/evo-log.md`). The skill never writes to them.
11. `trial_correct` is computed **by polarity** (§Scoring) — a guardrail task that correctly produces FAIL is a SUCCESS, never a pipeline failure.

---

## Confirmed constants (live-verified 2026-06-21)

```
AGENT NAMES (for as_chat_with_agent):
  "Trend Intelligence" | "Hook Writer" | "Content Repurposer"

TIMEOUTS:
  TI → 180   HW → 120   CR → 120   (seconds; never use defaults)

PRODUCTION EVO-LOG PATHS (READ-ONLY):
  TI → agents/trend-intelligence/evo-log.md
  HW → agents/hook-writer/evo-log.md
  CR → agents/content-repurposer/evo-log.md

LIVE EVO-LOG SCHEMAS (soma-run schema — the one the real files use):
  TI: date | trend_found | confidence | angle_suggested | hook_writer_triggered
  HW: date | trend | platforms | scores | winner_platform | winner_score | flags
  CR: date | trend | platforms_completed | scores | flag | notes
  ⚠️ evo-log-writer.md AND soma-performance-review.md document DIFFERENT HW/CR
     schemas — both are STALE. Trust the schema header inside each live file; it
     matches the soma-run schema above.

CR FLAG VOCABULARY (the only values the live CR log contains):
  none               → clean run                → expected_grade = PASS
  WARN               → unable to confirm pass   → expected_grade = HUMAN_REVIEW
  QUALITY_VIOLATIONS → violation reached output → expected_grade = FAIL
  QUALITY_GATE_FAIL  → CR gate blocked (0/5)    → expected_grade = FAIL
  (HW uses singular "QUALITY_VIOLATION" in its own log — do not key dataset on HW flags.)

CONFIDENCE FORMAT — DUAL (G1 must accept both):
  Legacy : ⭐ / ⭐⭐ / ⭐⭐⭐
  Newer  : "fresh (is_evergreen:false; no ⭐ rating in output)"  ← no star glyph
  G1 confidence_present = (contains "⭐") OR (contains "is_evergreen") OR (contains "fresh")

ABORT SENTINELS (case-insensitive, applied to each agent's full reply):
  - empty OR len < 50 characters
  - starts with "I cannot" / "I don't have" / "I'm unable" / "I'm sorry, I"
  - contains "As an AI, I"

TI → HW HANDOFF BLOCK (must be constructed; never pass raw ti_output to HW):
  <<SOMA_HANDOFF_START>>
  TREND: {ti_trend}
  CONFIDENCE: {ti_confidence}
  ANGLE: {ti_angle}
  PLATFORM_HINT: {platform_hint | "not specified"}
  AUDIENCE_HINT: {audience_hint | "not specified"}
  TIMING: {timing_signal | "not specified"}
  <<SOMA_CONTEXT_START>>
  {ti_output}            ← complete, verbatim TI reply
  <<SOMA_HANDOFF_END>>
  (Extraction rules for the hint fields are identical to soma-run STEP 4g.)

HW → CR HANDOFF: pass {hw_output} verbatim — no structured handoff.

PLATFORM CHAR LIMITS (from HW Change Log 2026-06-15 — HOOK limits, gate-enforced):
  LinkedIn ≤210 (HARD, hw-validator) | X 180 | YouTube 150 | Instagram 200 (stylistic)
  TikTok: no char limit (duration-based ~60s)
  NOTE: hw-validator already enforces these fail-closed, so M2 does NOT re-check them
        (would be redundant — see M2). Kept here for reference only.

PARSER RULES:
  - Read ONLY the "## Entries" section of each log. NEVER parse "## Change Log".
  - Some run-entries leaked into "## Change Log" (e.g. TI/HW 2026-06-19) → strict
    parser intentionally skips them. The 2026-06-19 QUALITY_GATE_FAIL case is instead
    PINNED manually (see Dataset §Pinned cases) using its verbatim logged trend.
```

---

## Graders

> **Classification.** G1–G4 are **structural graders** — they reconstruct the agent's
> self-reported outcome (is the pipeline structurally complete; did a gate fire). M1–M2
> are **quality graders** — the discriminating signal. Graduation and "stable" status
> bind to the quality graders, not to mere gate-passing.

### Grader outcomes (uniform)
```
PASS    = condition met
FAIL    = condition not met OR the agent returned an abort sentinel
ERROR   = grader/judge could not execute (e.g. M1 unparseable after 1 retry). NOT an agent outcome.
TIMEOUT = as_chat_with_agent exceeded the per-agent limit (infra). NOT an agent outcome.
```

### G1 — TI Completeness (structural, code)
```
trend_present      = ti_output has NO abort sentinel AND len(ti_trend) > 5
confidence_present = ti_confidence contains "⭐" OR "is_evergreen" OR "fresh"   ← dual format
angle_present      = len(ti_angle) > 10
G1 = PASS if all three; FAIL if any missing or abort; TIMEOUT per limit
```

### G2 — HW Platform Coverage (structural, code)
```
platforms_found = count of {LinkedIn, X/Twitter, YouTube, Instagram, TikTok} present in hw_output
G2 = PASS if =5; FAIL if <5 or abort; TIMEOUT per limit
```

### G3 — CR Quality Gate (structural, code) — all 4 flag states
```
Detect cr_flag from cr_output (or from extracted CR data):
  "none"               → G3 = PASS
  "WARN"               → G3 = WARN   (borderline → forces H1)
  "QUALITY_VIOLATIONS" → G3 = FAIL
  "QUALITY_GATE_FAIL"  → G3 = FAIL
  abort sentinel       → G3 = FAIL
  no recognizable flag → G3 = ERROR  (parser found none → escalate H1)
```

### G4 — Platform Completion (structural, code)
```
G4 = PASS if platforms_completed = "5/5"
   = FAIL if <5/5 OR contains "(partial:" OR abort
   = TIMEOUT per limit
```

### M1 — Hook-Trend Relevance (quality, model grader)
Covers **all 5 platforms** every trial. Per-platform PASS if score ≥ 4. The 5 scores
collapse to a single M1 verdict by the **4-of-5 rule**:
```
M1 = PASS if ≥ 4 of 5 platforms score ≥ 4
   = FAIL otherwise
All 5 individual scores are still recorded in the report.
```
**Judge determinism:** temperature = 0. On any borderline platform score (=3 or =4),
call that platform twice; if the two scores differ, take the lower and flag for H1.

**Rubric (with anchors — apply per platform; substitute {platform}):**
```
Given a trend topic and a {platform} hook generated by an AI agent, rate the hook's
relevance to the trend on a 1–5 scale:

5: Names the trend entity (product/company/event) OR uses a specific number/date/metric
   from the trend. Format is platform-appropriate.
4: Clearly relevant to the topic but no specific entity. The link is recognizable.
3: Generic tech/AI content applicable to any trend.
2: Does not reflect the angle TI suggested.
1: No recognizable link to the trend.

ANCHORS:
- Trend "Anthropic Claude Sonnet 4", hook "Claude Sonnet 4 just shipped — here's what
  200K context actually changes for builders" → SCORE: 5
- Same trend, hook "AI is moving fast. Here are 5 lessons for founders." → SCORE: 3
- Same trend, hook "Why morning routines make great leaders" → SCORE: 1

Threshold: ≥4 = PASS | ≤3 = FAIL
Reply ONLY:
SCORE: [1-5]
REASONING: [one sentence]
VERDICT: [PASS|FAIL]
```
Unparseable format after 1 retry → M1 = ERROR for that trial → escalate H1.

### M2 — Output Integrity (quality, code grader) — char-check intentionally dropped
```
For the winner_platform hook:
  no_template = does NOT contain "[INSERT" / "{{" / "TODO" / "XXX" / placeholder artifacts
  has_signal  = contains a question, a number, or a CTA-style phrase (soft heuristic)
M2 = PASS if no_template AND has_signal; FAIL otherwise. No ERROR (pure code).
```
> Char-limit checks are **omitted by design**: hw-validator already enforces them
> fail-closed, so by the time M2 sees a hook the limit is guaranteed satisfied —
> re-checking would be redundant (zero discriminating signal). Gate-integrity is a
> separate concern, not folded into the quality grader.

### H1 — Human Flag (human grader)
Activates when: (1) structural vs quality graders conflict; (2) any grader = ERROR;
(3) G3 = WARN; (4) calibration sampling selects this trial (§Calibration). Presented to
the user; logged to `system/evals/calibration-log.md`.

---

## Scoring & metrics (k = 5, polarity-aware)

### Per-trial resolution
```
STEP A — observed_grade:
  any grader = TIMEOUT                         → observed = TIMEOUT  (excluded)
  any grader = ERROR and H1 unresolved         → observed = ERROR    (excluded)
  any G = FAIL (incl. G3 FAIL/QUALITY_GATE_FAIL) → observed = FAIL
  all G = PASS and M1 = PASS and M2 = PASS     → observed = PASS
  conflict (G vs M) or G3 = WARN               → observed = H1 verdict (PASS/FAIL)
  H1 required but unresolved after 2 asks       → observed = H1_PENDING (excluded)
  abort sentinel in any agent → corresponding G = FAIL → observed = FAIL

STEP B — trial_correct (polarity):
  trial_correct = (observed_grade == expected_grade)
    expected PASS         → correct iff observed = PASS
    expected FAIL         → correct iff observed = FAIL    ← agent correctly blocked
    expected HUMAN_REVIEW → correct iff H1 verdict matches the WARN review
```

### Aggregation
```
valid_trials  = k - (TIMEOUT + ERROR + H1_PENDING)        k = 5
correct_count = number of trials with trial_correct = true
consistency   = correct_count / valid_trials

MIN VALIDITY: if valid_trials < 3 → do NOT compute; status = INCONCLUSIVE
              (re-run task, or agent-health-check if cause was TIMEOUT)

Derived (continuity with Anthropic vocabulary; APPROXIMATIONS, not unbiased pass@k):
  correct@k = 1 - (1 - consistency)^k
  correct^k = consistency^k
PRIMARY decision signal = correct_count (X/5).
```

### Interpretation — discrete, by correct_count
| correct_count (valid=5) | Meaning | Action |
|---|---|---|
| 5/5 | Regression-ready | Graduation candidate (if quality gate met) |
| 4/5 | Stable | Continue capability evals |
| 3/5 | Unstable | Instinct analysis |
| ≤ 2/5 | Critical | agent-health-check + instincts-updater |

*(If valid_trials < 5, band scales to valid_trials with a mandatory ⚠️ reduced-n marker.)*

### Quality sub-score (separate from correctness)
```
quality_pass_rate = (M1 PASS + M2 PASS over all valid trials) / (2 * valid_trials)
Graduation requires correct_count = 5/5 AND quality_pass_rate ≥ 0.80.
```

### Aggregate by polarity (mandatory split)
```
capability_tasks (expected PASS): mean_consistency_cap
guardrail_tasks  (expected FAIL/HUMAN_REVIEW): mean_consistency_guard
Report each separately. If guardrail task count is small (n ≤ 2), label its metric
"anecdotal — do not conclude" (current dataset: guardrail n is small).
```

---

## Eval task dataset

### Auto-discovery (strict ## Entries)
```
Read the "## Entries" section of TI, HW, CR logs (NEVER "## Change Log").
Group by date; within a date, match TI↔HW↔CR by trend text (exact, then fuzzy within
the same date only — never across dates). Tie/ambiguity within a date → skip + log
"ambiguous triple skipped @ {date} #{ordinal}".
A task is valid only if all three (TI, HW, CR) are present in their ## Entries.
For each valid triple:
  trend_input   = TI trend_found field, VERBATIM
  expected_grade = map(CR flag)  (see CR FLAG VOCABULARY)
  run_date       = the entry date
```

### Pinned cases (manual, fully grounded — not synthetic)
```
Some real runs are missed by the strict parser because their TI/HW entries sit under
## Change Log. Pin them explicitly with their VERBATIM logged trend:

PIN-1 (QUALITY_GATE_FAIL coverage):
  trend_input   = "Anthropic releases Claude Opus 4 and Claude Sonnet 4, setting new
                   coding and agentic benchmarks"   (verbatim, TI 2026-06-19)
  expected_grade = FAIL    (CR flag QUALITY_GATE_FAIL, 2026-06-19)
  note           = "pinned: exercises G3 QUALITY_GATE_FAIL branch"
```

### Current grounded composition (verified 2026-06-21)
```
Auto-discovered complete triples = 7:
  PASS (4): Claude Sonnet 4 | Opus 4.7 | PwC partnership | AI agent platforms native MCP
  FAIL (2): OpenAI Agents SDK update | Claude Code CLI and Agent SDK  (QUALITY_VIOLATIONS)
  HUMAN_REVIEW (1): Claude Agent SDK expansion  (WARN)
Pinned = 1: PIN-1 (QUALITY_GATE_FAIL)
TOTAL = 8 tasks  (capability 4 / guardrail 4)

MANDATORY report flag:
"⚠️ Dataset = N tasks (recommended minimum 20). Results INDICATIVE, not conclusive.
 Guardrail polarity n small — anecdotal. Labels are single-run snapshots."
```

### Auto-grow + promotion threshold
```
The dataset self-expands: every new soma-run appends a TI+HW+CR triple to the logs,
which auto-discovery picks up on the next eval. Documented promotion rule:
  when auto-discovered complete triples ≥ 20 → drop the "INDICATIVE" flag; results
  may be treated as conclusive. Until then, always flag indicative.
```

---

## Eval storage (Obsidian)

```
system/evals/                         ← system/ exists; evals/ created on first run
  capability/  YYYY-MM-DD-{slug}-{HHMMSS}-cap.md
  regression/  YYYY-MM-DD-{slug}-{HHMMSS}-reg.md
  baseline.md
  calibration-log.md
```
**Slug:** first 30 chars of trend, lowercase, spaces→hyphens, alphanumeric+hyphen only.
**Read before write:** `obsidian_read_note` before any `obsidian_update_note`. Create
`baseline.md` / `calibration-log.md` with `obsidian_create_note` if missing.

**baseline.md row format:**
```
| Eval ID | Date | Type | Polarity | correct_count | quality_rate | Status |
```

---

## Calibration (first 3 eval runs, sampled)

```
H1 does NOT run for every task. Sample per run:
  2 capability + 2 guardrail tasks; 1 random valid trial each → max 4 human judgments/run.
agreement = (sampled trials where H1_verdict == M1_verdict) / sampled_trials   (per-trial)
M1 = "CALIBRATED" when agreement ≥ 0.80 aggregated across all 3 runs (n ≈ 12).
Until then report "M1 IN CALIBRATION (run N/3, agreement X%)".
```

---

## Workflow

### STEP 0 — Task list
```
LOAD → SELECT → TRIAL 1..5 → GRADE → CALIBRATE(if needed) → SCORE → COMPUTE
→ LIFECYCLE → BASELINE → REPORT → SUMMARY
```

### STEP 1 — Eval type
`capability`/`nova funkcionalnost` → CAPABILITY; `regression`/`provjeri stabilnost`
→ REGRESSION; unspecified → ask once.

### STEP 2 — Load dataset
Auto-discover (strict ## Entries) + add pinned cases. If the user supplies a direct
trend input, run it as a single task (expected_grade = PASS unless they state it is a
negative/guardrail test). Flag N < 20 and the polarity split.

### STEP 3 — Select
Capability: subset or all. Regression: ALL tasks.

### STEP 4–8 — Run Trial 1..5 (identical per trial)
```
4a TI: as_chat_with_agent("Trend Intelligence", "Today is {YYYY-MM-DD}. {trend_input}", 180)
       (the "Today is {date}." prefix is mandatory — confirmed TI freshness bug otherwise)
4b     abort → handled as G-grader FAIL (do NOT stop grading); TIMEOUT → trial TIMEOUT
4c     extract {ti_trend,ti_confidence,ti_angle}; build {ti_handoff} (see Confirmed constants)
4d HW: as_chat_with_agent("Hook Writer", {ti_handoff}, 120); abort/TIMEOUT same treatment
4e CR: as_chat_with_agent("Content Repurposer", {hw_output}, 120); abort/TIMEOUT same treatment
```

### STEP 9 — Grade & score
Apply G1→G4, then M1 (5 platforms, 4/5 collapse), then M2. Resolve `observed_grade`
(Scoring STEP A). Trigger H1 on conflict/ERROR/WARN/calibration-sample. Compute
`trial_correct` vs `expected_grade` (Scoring STEP B).

### STEP 10 — Compute
correct_count, consistency, quality_pass_rate, derived metrics, INCONCLUSIVE check.

### STEP 11 — Lifecycle
```
CAPABILITY graduation:
  correct_count = 5/5 AND quality_pass_rate ≥ 0.80 for 3 consecutive capability runs
  → "✅ Task ready to graduate to Regression suite"
REGRESSION (discrete, no 0.10 threshold):
  Open baseline.md, find prior correct_count for the task.
  REGRESSION if correct_count drops ≥ 2 trials OR crosses a band boundary downward.
  → "⚠️ REGRESSION: correct_count {prev} → {curr} for [trend]"
  Also: quality_pass_rate drop ≥ 0.20 → "⚠️ QUALITY REGRESSION".
```

### STEP 12 — Write report + update baseline.md (read before write)

### STEP 13 — Chat summary
```
📊 SOMA EVAL — {CAPABILITY|REGRESSION}
Tasks: N (cap X / guard Y) | Trials/task: 5 | M1: {CALIBRATED|IN CALIBRATION n/3}
correct_count (mean): X.X/5 | consistency: 0.XX | quality_rate: 0.XX
{INCONCLUSIVE tasks: N if >0} {⚠️ REGRESSION / ✅ GRADUATION}
Report: system/evals/{type}/{path}
⚠️ Dataset < 20 — indicative. Guardrail n small — anecdotal.
```

---

## Report format (system/evals/.../...md)

```markdown
# SOMA Eval Report — {type} — YYYY-MM-DD
**Eval ID:** {HHMMSS}  **Type:** CAPABILITY|REGRESSION  **k:** 5
**Dataset:** N (cap X / guard Y)  **M1:** CALIBRATED | IN CALIBRATION (n/3)
**⚠️ Dataset < 20 — indicative. Labels are single-run snapshots.**

## Per-task
### Task: {trend_input}  |  expected: {PASS|FAIL|HUMAN_REVIEW}
| Trial | G1 | G2 | G3 | G4 | M1(LI/X/YT/IG/TT) | M2 | H1 | observed | correct |
| 1 | P | P | P | P | 5/5/4/4/4 (PASS) | P | - | PASS | ✅ |
valid_trials: 5  correct_count: X/5  consistency: 0.XX  quality_rate: 0.XX

## Confusion matrix (aggregate)
|          | obs PASS | obs FAIL | obs H1 |
| exp PASS |    .     |    .     |   .    |
| exp FAIL |    .     |    .     |   .    |
| exp HUMAN|    .     |    .     |   .    |

## Aggregate
| Metric | Value | Interpretation |
| mean correct_count | X.X/5 | [band] |
| mean consistency (cap) | 0.XX | |
| mean consistency (guard) | 0.XX | [anecdotal if n≤2] |
| quality_pass_rate | 0.XX | |
| TIMEOUT/ERROR/H1_PENDING | n/n/n | [⚠️ if >0] |

## Lifecycle
[Graduation: YES/NO + reason] [Regression: YES/NO + correct_count delta]

## Recommendations
[Which grader/polarity failed and what it means] [INCONCLUSIVE → re-run/health-check]
[Dataset < 20 → keep running soma-run to auto-grow toward 20]

*Generated by soma-eval-harness · SOMA v1 · {YYYY-MM-DD HH:MM}*
```

---

## Edge cases

- **< 3 complete triples in vault:** "Not enough for dataset. Enter a trend manually." → single-task.
- **valid_trials < 3:** INCONCLUSIVE → re-run / agent-health-check.
- **All 5 trials TIMEOUT:** valid=0 → "⛔ All timed out. Run agent-health-check."
- **H1 unanswered after 2 asks:** trial = H1_PENDING, excluded, reported.
- **M1 unparseable:** retry 1×; else M1 = ERROR → H1; if H1 unavailable → trial ERROR (excluded).
- **baseline.md missing:** create with current results; mark all "INITIAL BASELINE — no regression detection".
- **Regression and correct_count = 0/5:** flag BEFORE writing: "⛔ CRITICAL: 0/5 for [trend]. Run instincts-updater + agent-health-check."
- **All guardrail tasks observed PASS (agent accepts bad input):** "⚠️ Guardrails not catching bad input — check CR quality gate."
- **Run-entry found under ## Change Log:** strict parser skips it; only pinned cases pull such runs.

---

## Scope boundary

| Scenario | Skill |
|---|---|
| Production run | soma-run |
| Log a finished run | evo-log-writer / winners-log-logger |
| Summarize past runs | soma-performance-review |
| Pre-run system check | agent-health-check |
| **Reliability / quality-gate eval** | **soma-eval-harness** |
| Update instincts | instincts-updater |

---

## Tool reference

| Tool | Used for |
|---|---|
| `as_chat_with_agent` | Run TI / HW / CR (agent_name, message, timeout_seconds) |
| `obsidian_read_note` | Read evo-logs (read-only) + read eval notes before write |
| `obsidian_update_note` | Append/update eval reports & baseline (mode: append/replace) |
| `obsidian_create_note` | Create eval notes if missing |

---

## Integrity check after deploy

Verify these 8 markers in the installed Instructions:
```
"Trend Intelligence" | "Hook Writer" | "Content Repurposer"
<<SOMA_HANDOFF_START>>
len < 50 characters                     (abort sentinel)
Read ONLY the "## Entries" section
"is_evergreen" OR "fresh"               (dual confidence)
≥ 4 of 5 platforms score ≥ 4            (M1 collapse)
trial_correct = (observed_grade == expected_grade)
correct_count = number of trials with trial_correct = true
```
