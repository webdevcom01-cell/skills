# Skill Benchmark: skill-distiller

**Model**: claude-sonnet-5
**Date**: 2026-09-08T14:07:08Z
**Evals**: 1, 2, 3, 4
**Runs**: 4 per configuration (1 per eval x 4 evals)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 96% ± 7% (n=4) | 71% ± 22% (n=4) | +0.26 |
| Time | 353.0s ± 260.8s (n=4) | 225.5s ± 98.2s (n=4) | +127.4s |
| Tokens | 139,901 ± 27,640 (n=4) | 110,766 ± 9,497 (n=4) | +29,134 |

## Data quality note

Token stats above were patched in manually after the initial aggregate run — `aggregate_benchmark.py` only falls back to reading `timing.json`'s `total_tokens` when `grading.json`'s own `timing.total_duration_seconds` is exactly `0.0`. Every grader here correctly populated a non-zero timing per `agents/grader.md`, so that fallback never triggered and tokens were silently dropped. This looks like a real upstream gap in the script, not a data-collection failure — the real token counts were captured live from each subagent's completion notification and are accurate.
