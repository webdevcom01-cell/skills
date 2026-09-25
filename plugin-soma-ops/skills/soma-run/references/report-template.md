# Final Summary Report Template (STEP 9)

> Loaded from `soma-run` STEP 9. Use this template to generate the final run report after all steps complete.

## STEP 9 — REPORT: Final Summary

After all steps complete, output the final report. With `pipeline_scope == "TI"` (the default),
HW and CR still execute server-side inside TI — report them as `↪️ RAN SERVER-SIDE`, never as
`SKIPPED`, and their evo-logs as `not written (scope=TI)`:

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
  HW         → {✅ COMPLETED | ⛔ FAILED | ↪️ RAN SERVER-SIDE (inside TI, output not captured) | ⏭️ SKIPPED}
  CR         → {✅ COMPLETED | ⛔ FAILED | ↪️ RAN SERVER-SIDE (inside HW, output not captured) | ⏭️ SKIPPED}

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
  HW evo-log  → {✅ written | ⛔ failed | ⏭️ not written (scope=TI) | ⏭️ skipped}
  CR evo-log  → {✅ written | ⛔ failed | ⏭️ not written (scope=TI) | ⏭️ skipped}
  Winners-log → {✅ N entries written | ⏭️ no hooks ≥17 | ⏭️ not written (no HW scores: SA not in chain) | ⏭️ skipped}
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

