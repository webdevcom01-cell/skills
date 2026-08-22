# Tool reference and examples

Loaded from `soma-memory-fix/SKILL.md` — read for the MCP tool signature summary, or for calibration on invocation phrasing, the ambiguous-KB case, and a full successful 1-agent run trace. Verbatim from the skill body, moved here only because the combined SKILL.md was approaching the repo's line-count budget.

---

## Tool Reference

| Tool | Used for |
|---|---|
| `as_inspect_flow(agent_name, node_type: "kb_search")` | Read kb_search nodes + their current knowledgeBaseId |
| `as_list_knowledge_bases(agent_name)` | List KBs for an agent — get KB ID for matching |
| `as_patch_node_field(agent_name, node_id, field_name, field_value)` | Apply the fix |
| `as_get_recent_executions(agent_name)` | Incident guard — check if agent is mid-execution |

---

## Examples

### Invocation examples

```
"run soma-memory-fix"
"popravi kb_search wiring"
"fix agent memory"
"which agents don't have KB wired?"
"soma memory fix — dry run first"
"soma memory fix — just fix it"
"fix only SOMA agents"
"fix only Trend Intelligence"
```

### Example of ambiguous KB case

```
⚠️ BLOCKED — AMBIGUOUS
Agent: "Trend Intelligence"
Node:  node_abc123 (kb_search)
Found 2 KBs:
  1. "SOMA Trend Intelligence KB" (ID: kb_111)
  2. "TI Archive KB" (ID: kb_222)

→ Cannot auto-select. Tell me which KB ID to use:
  "use kb_111 for Trend Intelligence" or "use kb_222 for Trend Intelligence"
```

### Example of a successful 1-agent run

```
User: "fix only Score Analyzer"

[Phase 1] Inspecting Score Analyzer...
  → 1 kb_search node found, knowledgeBaseId: null → UNWIRED

[Phase 2] Looking up KBs for Score Analyzer...
  → 1 KB found: "Score Analyzer KB" (ID: kb_xyz789) → MATCH

[Plan]
  1. Score Analyzer / node_kb_001 → KB "Score Analyzer KB" (ID: kb_xyz789)

Type "confirm" to apply.

User: confirm

[5a] Checking executions... no active runs ✅
[5b] Re-reading node... still unwired ✅
[5c] Patching...
[5d] Verifying... knowledgeBaseId = kb_xyz789 ✅

✅ FIXED: Score Analyzer / node_kb_001 → KB "Score Analyzer KB" wired.
```
