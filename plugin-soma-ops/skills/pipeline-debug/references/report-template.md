# Debug Report Template (STEP 11)

> Loaded from `pipeline-debug` STEP 11. Use this template to generate the final debug report.

## STEP 11 — Generate Debug Report

```
🔍 SOMA PIPELINE DEBUG REPORT
══════════════════════════════════════════════════════════════
Generated  : {timestamp}
Scope      : {debug_scope}
Symptom    : {symptom_type}
Depth      : {STANDARD | DEEP}
Time ref   : {time_reference or "last 10 executions per agent"}
══════════════════════════════════════════════════════════════

INFRASTRUCTURE: {✅ REACHABLE | 🔴 DOWN}

EXECUTION STATUS SUMMARY:
  TI  → {last_status} | {execution_count} executions | {consecutive_failed} consecutive failed
  HW  → {last_status} | {execution_count} executions | {consecutive_failed} consecutive failed
  CR  → {last_status} | {execution_count} executions | {consecutive_failed} consecutive failed
  SA  → {last_status} | {execution_count} executions

══════════════════════════════════════════════════════════════
OVERALL: {🔴 CRITICAL | 🟠 MAJOR | 🟡 WARN | ✅ CLEAN} — {N total issues}
══════════════════════════════════════════════════════════════

🔴 CRITICAL ({N})
──────────────────────────────────────────
[For each CRITICAL finding:]
  [Rule: {RULE_ID}] [{Category}] Agent: {agent}
  Issue    : {description}
  Evidence : {specific data from MCP response}
  Fix      : {the exact patch that was confirmed, or "Manual: instruction"}
  Auto-fix : {✅ Applied | ❌ Failed | ⏭️ Skipped | — N/A}

🟠 MAJOR ({N})
──────────────────────────────────────────
[Same format]

🟡 WARN ({N})
──────────────────────────────────────────
[Same format]

══════════════════════════════════════════════════════════════
ROOT CAUSE HYPOTHESIS
══════════════════════════════════════════════════════════════
Primary   : {highest-severity category} — {agent}
Cascade   : {CASCADING note if M2 fired}
Evidence  : {key data point from MCP that confirms root cause}
Fix order : {numbered list of fixes in priority order}

══════════════════════════════════════════════════════════════
AUTO-FIX LOG
══════════════════════════════════════════════════════════════
Applied   ({N}): {list of FIXED nodes}
Failed    ({N}): {list of VERIFY_FAILED nodes}
Skipped   ({N}): {reasons}

══════════════════════════════════════════════════════════════
NEXT STEPS
══════════════════════════════════════════════════════════════
{Numbered action list — manual fixes, plus any confirmed fixes already applied}

1. [CRITICAL] ...
2. [MAJOR] ...
...
══════════════════════════════════════════════════════════════
```

**If CLEAN (no issues found):**
```
✅ No issues detected across all {N} dimensions checked.
{If symptom reported}: Escalating to DEEP diagnostic...
```

**If auto-fixes were applied:**
```
⚡ {N} trivial fix(es) applied after confirmation. Recommend re-running soma-run to verify pipeline health.
```

**If DEEP mode ran:**
```
📋 DEEP mode: reviewed call log previews (300-char limit) for output content.
   Useful for: detecting empty outputs, abort sentinels.
   Not useful for: quality analysis, score patterns (use D7 evo-log for those).
```

