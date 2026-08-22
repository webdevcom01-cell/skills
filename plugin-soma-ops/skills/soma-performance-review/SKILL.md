---
name: soma-performance-review
description: "Generates a SOMA pipeline performance report by reading all 4 agent logs from the Obsidian vault (TI evo-log, HW evo-log, CR evo-log, winners-log) and producing a structured markdown report with per-agent metrics, pipeline health score, and if-then recommendations. Use when the user says \"uradi performance review\", \"performance check\", \"kako radi SOMA\", \"pregled performansi\", \"review agent logs\", \"SOMA statistike\", \"SOMA health\", \"koliko hookova je prošlo\", \"how is the pipeline doing\", \"pipeline review\", \"agent performance\", \"šta je SOMA uradila ovog meseca\", \"izveštaj o agentima\", \"agent stats\", \"koji agent loše radi\", \"SOMA performance\", \"koliko runa je urađeno\", \"SOMA report\", \"pipeline status\", \"check logs\", or any request to evaluate, audit, or summarize SOMA agent performance over a time period. Do NOT use for logging a single run (use evo-log-writer), logging a winner hook (use winners-log-logger), or updating agent instincts (use instincts-updater)."
allowed-tools:
  - mcp__obsidian__obsidian_create_note
  - mcp__obsidian__obsidian_list_folders
  - mcp__obsidian__obsidian_read_note
---

# SOMA Performance Review

Read all 4 SOMA log files from the vault, parse every entry, compute metrics, calculate the SOMA Health Score, apply up to 10 deterministic if-then recommendation rules, and write a structured report note. Zero hallucination — every number must come from parsed entries, every recommendation from the if-then table.

## Core idea

The SOMA pipeline runs continuously: Trend Intelligence → Hook Writer → Content Repurposer. Without periodic performance reviews, quality degradation goes undetected ("half-life" problem). This skill provides a complete, deterministic audit: raw counts, rates, distributions, and explicit recommendations — all grounded in actual log data, nothing invented.

---

## Vault paths (read-only)

| Agent | Vault path |
|---|---|
| Trend Intelligence evo-log | `agents/trend-intelligence/evo-log.md` |
| Hook Writer evo-log | `agents/hook-writer/evo-log.md` |
| Content Repurposer evo-log | `agents/content-repurposer/evo-log.md` |
| Winners log | `agents/hook-writer/winners-log.md` |

**Critical**: winners-log section is `## Winners` (not `## Entries`). TI, HW, and CR evo-logs all use `## Entries`.

---

## Report output path (Step 2 decision logic)

1. Call `obsidian_list_folders`. If `system/performance-reviews` exists → output path: `system/performance-reviews/YYYY-MM-DD`
2. Otherwise → output path: `system/soma-performance-YYYY-MM-DD`
3. If a note already exists at the chosen path → append `-2` suffix (e.g., `system/performance-reviews/2026-05-15-2`)

---

## Log entry formats and field counts

### Trend Intelligence evo-log — 5 fields
```
date | trend | confidence | angle | angle_suggested
```
Example: `2026-05-15 | Claude Agent SDK launch | ⭐⭐⭐ | Multi-agent pipelines collapse to 3 nodes | yes`

Fields:
- `date` — YYYY-MM-DD
- `trend` — free text
- `confidence` — one to three ⭐ characters
- `angle` — free text (the suggested angle)
- `angle_suggested` — `yes` / `no` / `partial` / `-`

### Hook Writer evo-log — 6 fields
```
date | trend | platform | hook | winner_score | repurposer_hook
```
Example: `2026-05-15 | Claude Agent SDK | linkedin | Hook text here | 18/20 | yes`

Fields:
- `date` — YYYY-MM-DD
- `trend` — free text
- `platform` — one of: linkedin, x, youtube, instagram, tiktok
- `hook` — full hook text
- `winner_score` — `N/20` (integer N 1–20) or `-`
- `repurposer_hook` — `yes` / `no` / `-`

### Content Repurposer evo-log — 7 fields
```
date | trend | platforms_completed | linkedin_word_count | tiktok_duration | flag | notes
```
Example: `2026-05-15 | Claude Agent SDK | 5/5 | 312 | 45s | OK | Strong performance`

Fields:
- `date` — YYYY-MM-DD
- `trend` — free text
- `platforms_completed` — `N/5` or `(partial: X)` format
- `linkedin_word_count` — integer or `-`
- `tiktok_duration` — integer (seconds), string like `45s`, or `-`
- `flag` — `OK` / `PARTIAL_OUTPUT` / `HUMAN_REVIEW_NEEDED` / `-`
- `notes` — free text or `-`

### Winners log — 6 fields (section: `## Winners`)
```
date | trend | platform | hook_text | score | pattern
```
Example: `2026-05-15 | Claude Agent SDK | linkedin | Hook text | 18/20 | P1 (Hard Stat)`

Fields:
- `date` — YYYY-MM-DD
- `trend` — free text
- `platform` — canonical platform name
- `hook_text` — full hook text
- `score` — `N/20`
- `pattern` — pattern label or `-`

---

## Parsing rules

### General
1. Find the `## Entries` section in evo-logs; find the `## Winners` section in winners-log.
2. Each data line is a pipe-separated row. Split on `|`, strip whitespace from each field.
3. Skip: blank lines, lines starting with `*` (placeholder/italic), lines starting with `#`, header lines (contain field names like "date | trend").
4. A line is a valid entry if: it contains the expected number of `|` separators (field_count - 1) AND field[0] matches `YYYY-MM-DD` format.
5. If a line has wrong field count → skip silently (do not halt).

### Dash (`-`) handling — CRITICAL
- A `-` in any numeric field (winner_score, linkedin_word_count, tiktok_duration, score) means **no data**.
- **Exclude dash values from all aggregations** (averages, min, max, counts of numeric values).
- Report excluded count separately if > 0: `(N entries excluded — no data)`.
- Do NOT count `-` as zero.

### Specific field parsing
- **confidence**: count `⭐` characters in field[2]. One `⭐` = 1, two `⭐⭐` = 2, three `⭐⭐⭐` = 3.
- **winner_score**: `"18/20".split("/")[0]` → integer 18. Validate range 1–20.
- **platforms_completed**: `"5/5"` → completed=5, total=5. `"(partial: 3)"` → completed=2.5, total=5.
- **tiktok_duration**: strip trailing `s` if present, then parse as integer seconds.
- **angle_suggested**: case-insensitive. `"yes"` → handoff, `"no"` or `"partial"` or `-` → no handoff.
- **repurposer_hook**: `"yes"` → CR triggered, `"no"` or `-` → not triggered.
- **flag**: case-insensitive match to OK / PARTIAL_OUTPUT / HUMAN_REVIEW_NEEDED / `-`.

### Time filtering
- If user specifies a date range (e.g., "this month", "last 7 days", "May 2026") → apply to field[0] (date).
- If no date range specified → use ALL entries (no filter).
- After filtering, note the effective date range in the report header: `Period: YYYY-MM-DD to YYYY-MM-DD (N total entries across all logs)`.

---

## Metrics computed

### Trend Intelligence
- `ti_runs` — total valid TI entries in period
- `ti_halt_rate` — entries where `angle_suggested = "no"` ÷ `ti_runs` × 100%
- `ti_confidence_dist` — count of ⭐, ⭐⭐, ⭐⭐⭐ entries
- `ti_last3_angles` — last 3 `angle` field values, verbatim (no paraphrase)

### Hook Writer
- `hw_runs` — total valid HW entries in period
- `hw_scores` — list of integer scores from winner_score (dash-excluded)
- `hw_score_avg` — mean of `hw_scores`, 1 decimal place
- `hw_score_min`, `hw_score_max` — min/max of `hw_scores`
- `hw_winner_count` — count of entries where `winner_score ≥ 17`
- `hw_winner_rate` — `hw_winner_count ÷ hw_runs × 100%`
- `hw_platform_dist` — count per platform (linkedin, x, youtube, instagram, tiktok)
- `hw_repurposer_triggered` — count of entries where `repurposer_hook = "yes"`

### Content Repurposer
- `cr_runs` — total valid CR entries in period
- `cr_flag_dist` — count per flag value (OK, PARTIAL_OUTPUT, HUMAN_REVIEW_NEEDED, -)
- `cr_linkedin_avg` — mean of `linkedin_word_count` (dash-excluded), rounded to integer
- `cr_tiktok_avg` — mean of `tiktok_duration` in seconds (dash-excluded), rounded to integer
- `cr_completion_rate` — sum of `completed` ÷ sum of `total` × 100% across all `platforms_completed` values

### Winners
- `w_total` — total entries in `## Winners` section
- `w_in_period` — winners with date in the review period
- `w_platform_dist` — count per platform
- `w_pattern_dist` — count per pattern label (dash-excluded)
- `w_score_range` — min and max score from `score` field

### Pipeline
- `pipe_ti_to_hw_rate` — `hw_runs ÷ ti_runs × 100%` (how often TI runs lead to HW runs)
- `pipe_hw_to_cr_rate` — `cr_runs ÷ hw_runs × 100%`
- `pipe_end_to_end` — `cr_runs ÷ ti_runs × 100%`

---

## SOMA Health Score

Evaluate three conditions independently, then assign the worst-case color:

| Condition | Check |
|---|---|
| TI halt rate | > 30% → 🔴 ; 15–30% → 🟡 ; < 15% → 🟢 |
| HW winner rate | 0% with ≥ 5 runs → 🔴 ; > 0% but < 20% → 🟡 ; ≥ 20% → 🟢 |
| CR flag rate (non-OK) | ≥ 50% → 🔴 ; 20–49% → 🟡 ; < 20% → 🟢 |

**Final score**: take the worst (most severe) color across all three conditions.

- 🟢 **HEALTHY** — all systems operating within normal parameters
- 🟡 **WATCH** — one or more metrics trending toward threshold; monitor closely
- 🔴 **ACTION NEEDED** — critical threshold breached; immediate review recommended

If total entries across all logs < 3 → report: `⚪ INSUFFICIENT DATA — fewer than 3 total entries. Run more pipeline cycles before reviewing.` Do not compute health score.

---

## 10 Deterministic recommendation rules

**Read `references/recommendation-rules.md` at STEP 11** for the full R1-R10 if-then table (condition + exact recommendation text for each), plus the R8/R5/R10 implementation notes. Apply ALL rules that match. Do NOT generate recommendations outside this table. If no rule matches → write: `No recommendations — all metrics within normal parameters.`

## Workflow — 13 steps

### Step 1 — Scope and date range
Ask (or infer from context): what period to review? Options:
- "all time" (default if not specified)
- "this month" → current calendar month
- "last N days" → today minus N
- Custom date range: "from YYYY-MM-DD to YYYY-MM-DD"

If user did not specify → use all time and note this in the report.

### Step 2 — Check output path (FIRST action before reading logs)
Call `obsidian_list_folders`.
- If `system/performance-reviews` in results → planned output: `system/performance-reviews/YYYY-MM-DD`
- Otherwise → planned output: `system/soma-performance-YYYY-MM-DD`
- Note planned path. Do NOT create anything yet.

### Step 3 — Read all 4 log files (sequential)
Call `obsidian_read_note` four times, in order:
1. `agents/trend-intelligence/evo-log.md`
2. `agents/hook-writer/evo-log.md`
3. `agents/content-repurposer/evo-log.md`
4. `agents/hook-writer/winners-log.md`

For each file:
- If file not found → record: `[agent] evo-log: NOT FOUND`. Continue with remaining files.
- If file found but section (`## Entries` or `## Winners`) contains only placeholder → record: `[agent]: 0 entries`.
- Store raw content for parsing.

### Step 3b — Read instincts files (conditional — staleness detection)

Execute this step only if the effective review period (from Step 1) is ≥ 30 days. If period < 30 days → skip entirely, record: `Step 3b skipped — review period < 30 days`. R10 will not fire.

If executing, call `obsidian_read_note` four times, in order:
1. `agents/trend-intelligence/instincts.md`
2. `agents/hook-writer/instincts.md`
3. `agents/content-repurposer/instincts.md`
4. `agents/score-analyzer/instincts.md`

For each file:
- If file not found → record: `[agent] instincts.md: NOT FOUND`. Continue.
- If file found → parse all HTML comments matching this exact format:
  `<!-- added: YYYY-MM-DD | confidence: X.X | last_seen: YYYY-MM-DD | domain: tag -->`

For each matched comment, extract the instinct snippet:
- Find the `**situation:**` line immediately before or after the comment block
- Take text between `**situation:**` and the next `**mistake:**` line
- Strip markdown bold markers (`**`)
- Truncate to 80 characters. Append `…` if truncated.
- If no `**situation:**` line found near the comment → use snippet: `[situation not found]`

Collect per instinct:
```
{
  agent,        ← which instincts.md file (TI / HW / CR / SA)
  snippet,      ← situation text, max 80 chars
  confidence,   ← numeric X.X value from comment
  last_seen,    ← YYYY-MM-DD verbatim from comment
  domain        ← tag verbatim from comment
}
```

Instincts without `last_seen` in their HTML comment → silently skip. Do not estimate `last_seen` from any other source.

Store result as `instinct_records[]`. If all 4 files are NOT FOUND or have 0 parseable comments → record: `Step 3b: 0 instinct records found`. R10 will not fire.

### Step 4 — Minimum data check
Count total parsed entries across all files after Step 3.
- If total < 3 → write: `⚪ INSUFFICIENT DATA — only [N] total entries found. Run more pipeline cycles before a meaningful review.` Stop here. Do NOT write a report note.
- If total ≥ 3 → continue.

### Step 5 — Parse all entries
For each file, parse valid entries per the parsing rules above.
- Apply date filter (Step 1 scope) to each entry.
- For TI: extract `date, trend, confidence, angle, angle_suggested`
- For HW: extract `date, trend, platform, hook, winner_score, repurposer_hook`
- For CR: extract `date, trend, platforms_completed, linkedin_word_count, tiktok_duration, flag, notes`
- For Winners: extract `date, trend, platform, hook_text, score, pattern`

Track: entries parsed, entries skipped (wrong field count), entries date-filtered.

### Step 6 — Apply time filter
After parsing, filter to the period from Step 1. Record effective period: actual `min(date)` to `max(date)` across all entries.

### Step 7 — Compute per-agent metrics
Calculate all metrics as defined in the Metrics section.
- Respect dash exclusion rule everywhere numeric aggregation is done.
- For `ti_last3_angles`: sort by date descending, take first 3 `angle` values verbatim.
- For `cr_completion_rate`: handle `(partial: X)` as 2.5/5.

### Step 8 — Compute pipeline metrics
Calculate `pipe_ti_to_hw_rate`, `pipe_hw_to_cr_rate`, `pipe_end_to_end`.
- If denominator is 0 → report `N/A (no [agent] runs in period)`.

### Step 9 — SOMA Health Score
Apply the three-condition health score table. Record which conditions triggered which color. Show reasoning in report.

### Step 10 — Cross-log check (R5)
For each HW entry with `winner_score ≥ 17`:
- Normalize: `hook.strip().lower()`
- Search winners-log entries: `hook_text.strip().lower()`
- If no match found AND date is within review period → add to R5 list.

### Step 11 — Generate recommendations
Apply all applicable if-then rules (R1–R10). R10 fires only if `instinct_records[]` from Step 3b is non-empty AND ≥1 record has `last_seen` older than 30 days from end of review period AND `confidence < 0.7`. Collect all applicable rules. If none match → use the "no recommendations" fallback text.

### Step 12 — Build and write report

#### Report structure (exact)

**Read `references/report-template.md`** for the exact markdown structure to fill in and write — every section, in order, with placeholder syntax.

#### Write the note
Call `obsidian_create_note` at the planned path (Step 2) with the full report body.
- If note creation fails → retry once. If still fails → report error to user with exact path and content excerpt.

#### Post-write verification (mandatory)
Immediately call `obsidian_read_note` on the written path. Verify:
1. ✓ First line matches `# SOMA Performance Review`
2. ✓ Health score section is present
3. ✓ Recommendations section is present
4. ✓ `*Generated by soma-performance-review skill` footer is present
5. ✓ If R10 fired: `## Instinct Health` section is present in the written note

If any check fails → report exact discrepancy. Do NOT claim success.

---

## Summary output to user (after successful write)

Print in chat:
```
[health_emoji] SOMA Health: [HEALTHY / WATCH / ACTION NEEDED]

Quick stats:
- TI: [N] runs, [N]% halt rate
- HW: [N] runs, [N]% winner rate, avg score [X]/20
- CR: [N] runs, [N]% non-OK flag rate
- Winners: [N] total

[N] recommendation(s) generated.
[N] stale instinct(s) flagged for review.   ← include only if R10 fired

Full report: [vault path]
```

---

## Anti-hallucination rules (9)

1. **Metrics from parsed entries only** — never estimate, interpolate, or assume. If a value is absent, report `-` or `N/A`.
2. **Dash = no data, not zero** — `-` in numeric fields must be excluded from aggregations. Reporting `-` as 0 is a hallucination.
3. **Recommendations only from if-then table** — do not generate free-form recommendations. If a situation does not match any of the 10 rules → no recommendation for that situation.
4. **Below-minimum data → stop, no report** — do not generate a report with < 3 total entries. Report insufficient data and stop.
5. **`angle_suggested` verbatim** — last 3 TI angles must be copied character-for-character from field[3]. No paraphrase, no summarization.
6. **Cross-log check is a suggestion, not an error** — R5 mismatch does not mean the winners-log is corrupted. It is a suggestion to log missing winners.
7. **`bytes_written` (or successful obsidian_create_note response) before claiming report is saved** — do not say "report saved" without tool confirmation.
8. **`last_seen` and `confidence` values in Step 3b must be read verbatim from HTML comments in instincts.md files.** Do not estimate instinct staleness from evo-log dates, memory, or context. If the comment does not exist or is malformed, skip that instinct silently.
9. **R10 must never fire based on instincts without `last_seen` metadata.** Instincts written before Faza 1 upgrade have no `last_seen` field. These are silently excluded from staleness detection — do not infer or estimate a `last_seen` date for them under any circumstances.

---

## Edge cases

**All logs are empty (placeholder only):**
Step 4 triggers → `⚪ INSUFFICIENT DATA`. Do not continue.

**One log file missing:**
Continue with remaining files. Note in report header: `⚠️ [agent] evo-log not found — [agent] metrics unavailable.`

**Date range produces 0 entries (all filtered out):**
Report: `No entries found for the specified period ([start] to [end]). Widen the date range or use "all time".` Do not generate health score.

**CR `platforms_completed` has unexpected format:**
If value does not match `N/5` or `(partial: X)` → treat as `-` (no data). Do not halt.

**HW score is decimal (e.g., 17.5):**
Per SOMA scoring rules, decimals are invalid. Skip the entry for score aggregation, note: `[N] entries had invalid score format (decimal) — excluded.`

**Same-date report already exists:**
Append `-2` suffix (Step 2 logic). If `-2` also exists → use `-3`, etc.

**ti_runs = 0 but hw_runs > 0:**
Pipeline rates: `pipe_ti_to_hw_rate = N/A (no TI runs)`. This is a data integrity note, not an error.

**R9 check with < 7 days of data:**
If the review period is shorter than 7 days, apply R9 to the full available period. Note: `(R9 applied to full period — fewer than 7 days of data available)`.

**Step 3b finds instincts files but no parseable HTML comments (all instincts pre-date Faza 1):**
Record: `Step 3b: 0 instinct records with last_seen metadata`. R10 will not fire. Continue normally. Do not flag this as an error — it simply means instincts-updater has not yet written any post-Faza-1 instincts.

**Step 3b: instinct snippet cannot be extracted (no `situation:` line near comment):**
Use snippet: `[situation not found]`. Do not halt. Include in R10 output if instinct otherwise qualifies (last_seen > 30 days AND confidence < 0.7).