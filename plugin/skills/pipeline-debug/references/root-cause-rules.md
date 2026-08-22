# Root Cause Rules — IF-THEN Table (STEP 9)

> Loaded from `pipeline-debug` STEP 9. Root cause classification uses ONLY this table — never free-form LLM reasoning. Read this file in full before evaluating rules.

## STEP 9 — Root Cause Mapping (IF-THEN Table)

**CRITICAL: All root cause classification uses ONLY this table. No free-form LLM reasoning.**

Evaluate all rules. Multiple rules can fire simultaneously. Process in priority order.

### 9a — CRITICAL severity rules

```
RULE C1 — INFRA_DOWN
  IF d0_status == "DOWN"
  → Category: INFRA_DOWN | Severity: CRITICAL
  → Stop all other rules. Report infra issue only.

RULE C2 — FLOW_BROKEN (from D4)
  IF {agent}_appears_in d4_issues with severity != "WARN"
  → Category: FLOW_BROKEN | Severity: CRITICAL | Agent: {agent}
  → Evidence: d4_issues[agent].issue
  → Fix source: the suggested-fix text for this issue — treat as a hint, not as
    four named keys; see 10b before building a patch from it
  → Apply after user confirmation (trivial-eligible) — see Step 10

RULE C3 — FLOW_BROKEN (from D4, WARN severity)
  IF {agent}_appears_in d4_issues with severity == "WARN"
  → Category: FLOW_BROKEN | Severity: MAJOR | Agent: {agent}
  → Evidence: d4_issues[agent].issue
  → Fix source: the suggested-fix text for this issue — see 10b
  → Apply after user confirmation (trivial-eligible) — see Step 10

RULE C4 — KB_DEAD
  IF {agent}_kb_embedding_status == "empty"
  AND {agent}_kb_search_nodes is non-empty (agent queries KB)
  → Category: KB_DEAD | Severity: CRITICAL | Agent: {agent}
  → Evidence: "KB empty AND kb_search node exists — agent runs without memory"
  → Fix: "Run kb-sync skill to seed KB"
  → Auto-apply: NO (kb-sync is a separate skill)

RULE C5 — KB_MISSING
  IF {agent}_kb_count == 0
  AND {agent}_kb_search_nodes is non-empty
  → Category: KB_MISSING | Severity: CRITICAL | Agent: {agent}
  → Evidence: "No KB exists AND kb_search node wired — agent queries non-existent KB"
  → Fix: "Create KB via agent-scaffolder, then run kb-sync"
  → Auto-apply: NO

RULE C6 — KB_FAILED
  IF {agent}_kb_embedding_status == "failed"
  → Category: KB_FAILED | Severity: CRITICAL | Agent: {agent}
  → Evidence: "KB embedding permanently failed — agent memory is broken"
  → Fix: "Delete and recreate KB, then reseed with kb-sync"
  → Auto-apply: NO

RULE C7 — KB_UNWIRED
  IF D5 reveals {agent}_kb_search_node with knowledgeBaseId null or empty
  AND {agent}_kb_count == 1 (exactly one KB exists)
  → Category: KB_UNWIRED | Severity: CRITICAL | Agent: {agent}
  → Evidence: "kb_search node exists but knowledgeBaseId is unset"
  → Fix: as_patch_node_field (node_id from D5, kb_id from D6)
  → Apply after user confirmation (trivial-eligible)

RULE C8 — AGENT_FAILED (consecutive)
  IF {agent}_consecutive_failed >= 3
  → Category: AGENT_FAILED | Severity: CRITICAL | Agent: {agent}
  → Evidence: "{N} consecutive FAILED executions"
  → Fix: "Check flow config (D5) and KB status (D6) for this agent"
  → Auto-apply: NO
```

### 9b — MAJOR severity rules

```
RULE M1 — TIMEOUT
  IF {agent}_has_running == true AND any RUNNING execution duration > 5 min
  → Category: TIMEOUT | Severity: MAJOR | Agent: {agent}
  → Evidence: "Agent has RUNNING execution exceeding 5 minutes"
  → Fix: "Increase timeout on call_agent node; check if web search is hanging"
  → Auto-apply: NO

RULE M2 — CASCADING
  Cascade detection (requires at least 2 agents checked):
  IF ti_last_status == "FAILED"
  AND (hw_execution_count == 0 OR hw_last_timestamp < ti_last_timestamp)
  → Category: CASCADING | Severity: MAJOR
  → Evidence: "TI failed; HW has no subsequent executions → pipeline blocked at TI"
  → Primary: TI fix (from C2/C3/C8/M1 rules above)
  → Note: "Fix TI first — HW and CR failures are downstream consequences"

  IF ti_last_status == "COMPLETED"
  AND hw_last_status == "FAILED"
  AND (cr_execution_count == 0 OR cr_last_timestamp < hw_last_timestamp)
  → Category: CASCADING | Severity: MAJOR
  → Evidence: "TI OK; HW failed; CR has no subsequent executions → pipeline blocked at HW"
  → Primary: HW fix

RULE M3 — AGENT_FAILED (single)
  IF {agent}_consecutive_failed == 1 OR == 2
  → Category: AGENT_FAILED | Severity: MAJOR | Agent: {agent}
  → Evidence: "{N} recent FAILED executions"
  → Fix: "Review D5 flow config; may be transient — retry pipeline"
  → Auto-apply: NO
```

### 9c — WARNING severity rules

```
RULE W1 — KB_UNSEEDED
  IF {agent}_kb_embedding_status == "empty"
  AND {agent}_kb_search_nodes is empty (agent does NOT query KB)
  → Category: KB_UNSEEDED | Severity: WARN | Agent: {agent}
  → Evidence: "KB exists but empty; no kb_search node — not operationally blocking"
  → Fix: "Seed KB via kb-sync when ready to enable memory"
  → Auto-apply: NO

RULE W2 — KB_PROCESSING
  IF {agent}_kb_embedding_status == "processing"
  → Category: KB_PROCESSING | Severity: WARN | Agent: {agent}
  → Evidence: "KB embedding in progress — temporary state"
  → Fix: "Wait 60s and re-run pipeline-debug"
  → Auto-apply: NO

RULE W3 — KB_DEGRADED
  IF {agent}_kb_embedding_status == "partial_failure"
  → Category: KB_DEGRADED | Severity: WARN | Agent: {agent}
  → Evidence: "Some KB documents failed embedding — memory partially degraded"
  → Fix: "Run kb-sync to re-upload failed documents"
  → Auto-apply: NO

RULE W4 — QUALITY_DEGRADATION (HW)
  IF hw_quality_degradation == true (from D7)
  → Category: QUALITY_DEGRADATION | Severity: WARN | Agent: HW
  → Evidence: "{hw_unscored_count} consecutive UNSCORED entries in HW evo-log"
  → Fix: "Check HW prompt (D5) for score output format; check KB for instincts freshness"
  → Auto-apply: NO

RULE W5 — QUALITY_DEGRADATION (CR)
  IF cr_quality_violations == true (from D7)
  → Category: QUALITY_DEGRADATION | Severity: WARN | Agent: CR
  → Evidence: "Repeated QUALITY_VIOLATIONS in CR evo-log"
  → Fix: "Check CR instincts.md via kb-sync; update banned phrase list"
  → Auto-apply: NO

RULE W6 — NEVER_RAN
  IF {agent}_execution_count == 0 (NEVER_RAN)
  AND {agent} is in debug_scope
  → Category: NEVER_RAN | Severity: WARN | Agent: {agent}
  → Evidence: "No execution records found — agent may never have been triggered"
  → Fix: "Run soma-run to trigger the pipeline"
  → Auto-apply: NO

RULE W7 — DRIFT_PATTERN (TI)
  IF ti_drift_pattern == true (from D7)
  → Category: DRIFT_PATTERN | Severity: WARN | Agent: TI
  → Evidence: "TI consistently redirecting from provided inputs to different trends"
  → Fix: "Review TI prompt and instincts — consider whether drift is intentional"
  → Auto-apply: NO

RULE W8 — REPAIR_NOT_PERSISTED
  IF hw_last_status == "COMPLETED" (hw-validator passed — gate returned "PASS")
  AND cr_quality_violations == true (CR blocked on banned phrases in D7)
  AND D5 reveals hw-validator node whose code contains SUBS map or BN_REP repair phase
  AND call_agent-cr inputMapping uses {{hw_payload}} (the processor outputVariable)
  AND no write-back function node exists between hw-validator and hw-gate
  → Category: REPAIR_NOT_PERSISTED | Severity: WARN | Agent: HW→CR cascade
  → Evidence: "hw-validator repairs payload in-memory but returns 'PASS' only — call_agent-cr sends {{hw_payload}} (original, unrepaired) to CR"
  → Fix: "Add hw-payload-writeback function node (outputVariable: 'hw_payload') between hw-validator and hw-gate. Re-wire: hw-validator → hw-payload-writeback → hw-gate. Gate and call_agent-cr unchanged."
  → Auto-apply: NO (requires as_update_flow with new node + edge rewiring — not a patch_node_field fix)
```

### 9d — CLEAN result
```
IF no rules fired above:
  → {root_cause} = CLEAN
  → Report: "No issues detected across all checked dimensions."
  → If symptom_type != UNKNOWN: escalate to DEEP (Step 8 trigger)
```
