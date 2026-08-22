# Deterministic recommendation rules (R1-R10)

Loaded from `soma-performance-review/SKILL.md` — read at STEP 11 (Generate recommendations) when applying the if-then table. Verbatim from the skill body, moved here only because the combined SKILL.md exceeded the repo's token budget.

---

## 10 Deterministic recommendation rules

Apply ALL rules that match. Do NOT generate recommendations outside this table. If no rule matches → write: `No recommendations — all metrics within normal parameters.`

| # | Condition | Recommendation text |
|---|---|---|
| R1 | `ti_halt_rate > 30%` | `⚠️ TI halt rate is [N]% — above 30% threshold. Review VAGUE_INPUT criteria in Trend Intelligence instincts. Consider loosening the halt condition or providing richer input context.` |
| R2 | `ti_halt_rate = 0% AND ti_runs ≥ 3` | `✅ TI halt rate is 0% — Trend Intelligence is accepting all inputs cleanly.` |
| R3 | `hw_winner_rate = 0% AND hw_runs ≥ 5` | `🚨 Hook Writer has produced 0 winners in [N] runs. Critical quality issue — review HW scoring calibration and per-platform hook intelligence in instincts.` |
| R4 | `hw_winner_rate ≥ 40%` | `✅ Hook Writer winner rate is [N]% — strong hook quality. Pipeline performing above expectations.` |
| R5 | cross-log check: HW entry has `winner_score ≥ 17` AND no matching entry found in winners-log by same date AND same hook text (case-insensitive trim) | `📋 Found [N] HW run(s) with winner_score ≥ 17 not logged in winners-log. Use winners-log-logger to log them: [list date + trend + score].` |
| R6 | `cr_flag_dist["PARTIAL_OUTPUT"] ≥ 50% of cr_runs` | `⚠️ Content Repurposer is producing PARTIAL_OUTPUT in [N]% of runs. Review format templates in CR instincts — one or more platform formats may be under-specified.` |
| R7 | `cr_flag_dist["HUMAN_REVIEW_NEEDED"] ≥ 2` | `⚠️ HUMAN_REVIEW_NEEDED flagged [N] times by Content Repurposer. Review CR instincts for quality detection thresholds — may be set too strict or too loose.` |
| R8 | `(ti_runs + hw_runs + cr_runs) ≥ 10 AND (no instinct updates detected in period — inferred from: all logs show entries but no reference to instinct changes in notes fields)` | `💡 10+ pipeline runs completed with no detected instinct updates. Consider running instincts-updater to consolidate learnings from this period.` |
| R9 | TI entries in last 7 days: zero entries with `confidence = ⭐⭐⭐` | `⚠️ No high-confidence (⭐⭐⭐) TI signals in the last 7 days. Review source priority order in Trend Intelligence instincts — primary sources may be underperforming.` |
| R10 | Step 3b was executed AND ≥1 instinct has `last_seen` older than 30 days from end of review period AND `confidence < 0.7` | `⚠️ [N] instinct(s) not seen in logs for ≥30 days with confidence < 0.7. Candidates for review: [list: agent — situation snippet (last_seen: YYYY-MM-DD, confidence: X.X, domain: tag)]. Consider running instincts-updater to verify they are still relevant.` |

**R8 note**: "no instinct updates detected" is inferred heuristically — if `notes` fields in CR log contain no mention of "instinct" or "learned" → assume no updates. This is a suggestion, not an error.

**R5 implementation**: after parsing both HW evo-log and winners-log, for each HW entry where `winner_score ≥ 17`, check if a winners-log entry exists with matching hook text (`.strip().lower()`). Collect all mismatches. If count > 0 → apply R5.

**R10 note**: Only fires if Step 3b was executed (review period ≥ 30 days AND instincts files were readable). Staleness is measured from the end of the review period, not from today. Only instincts with `last_seen` metadata (written after Faza 1 upgrade) are checked — older instincts without this field are silently skipped. R10 does not fire if `instinct_records[]` is empty.

---
