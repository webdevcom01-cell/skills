# Health report format (exact)

Loaded from `agent-health-check/SKILL.md` — read at STEP 6 when generating the report. Verbatim from the skill body, moved here only because the combined SKILL.md was approaching the repo's line-count budget (300-499 zone with no hierarchy).

---

## STEP 6 — Generate Report

Format the report exactly as follows:

```
🏥 AGENT STUDIO HEALTH REPORT
══════════════════════════════════════════
Generated : <timestamp>
Scope     : <production scope list>
Agents scanned (D0) : <as_find_broken_flows().scanned>
Agents deep-checked : <N production agents>
══════════════════════════════════════════

OVERALL HEALTH: <score>/100 <status emoji + label>

══════════════════════════════════════════
❌ CRITICAL — <N issues>
══════════════════════════════════════════
[list each CRITICAL issue]

For each issue:
  [Dimension tag] Agent name
  Issue description
  Fix: <exact command or "Manual: description of required action">

══════════════════════════════════════════
⚠️ WARNING — <N issues>
══════════════════════════════════════════
[list each WARNING issue]

For each issue:
  [Dimension tag] Agent name
  Issue description
  Fix: <exact command or suggested action>

══════════════════════════════════════════
✅ OK — <N checks passed>
══════════════════════════════════════════
[list passing checks briefly]

══════════════════════════════════════════
PRIORITIZED ACTION LIST
══════════════════════════════════════════
1. [CRITICAL] <most urgent fix>
2. [CRITICAL] <second most urgent>
...
N. [WARNING]  <lowest priority>
══════════════════════════════════════════
```

### Fix command format (exact — do not vary)

For Memory Wiring fix where KB exists:
```
as_patch_node_field
  agent_id:    <id>
  node_id:     <node_id>
  field_name:  knowledgeBaseId
  field_value: "<kb_id>"
```

For model fix:
```
as_patch_node_field
  agent_id:   <id>
  node_id:    <node_id>
  field_name: model
  field_value: "gpt-4.1-mini"
```

For outputVariable fix (from D0):
```
as_patch_node_field
  agent_id:   <id>
  node_id:    <node_id>
  field_name: outputVariable
  field_value: "<suggest a name based on node purpose, e.g. 'format_result'>"
```

---
