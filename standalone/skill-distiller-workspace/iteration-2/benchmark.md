# Skill Benchmark: skill-distiller

**Model**: claude-sonnet-5
**Date**: 2026-09-08T21:11:01Z
**Evals**: 1, 2, 3, 4, 5
**Runs**: 5 per configuration (1 per eval x 5 evals)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 86% ± 15% (n=5) | 59% ± 33% (n=5) | +0.27 |
| Time | 351.6s ± 217.5s (n=5) | 225.6s ± 88.1s (n=5) | +126.1s |
| Tokens | 139,522 ± 24,513 (n=5) | 112,169 ± 10,733 (n=5) | +27,354 |

## Data quality note

Same aggregate_benchmark.py gap as iteration-1 (script only reads timing.json's total_tokens when grading.json's own timing is exactly 0.0, which never happens here since graders correctly populate it). Tokens patched in manually from timing.json captured live from each subagent's completion notification.
