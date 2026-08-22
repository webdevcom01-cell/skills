# Reference Tables

> Loaded from `pipeline-debug`. Diagnostic dimension summary, MCP call-count estimate, tool reference, and constraints summary — consult as needed, not required for every run.

## Diagnostic Dimension Summary

| Dim | Tool | What it finds | SOMA-specific note |
|---|---|---|---|
| D0 | `as_health_check` | DB connectivity | Returns basic counts only |
| D1 | `as_get_recent_executions` × 4 | Execution history per agent | PRIMARY tool for SOMA (external orchestration) |
| D1b | `as_list_agent_calls` | A2A internal calls | Supplementary — usually empty for SOMA |
| D4 | `as_find_broken_flows` | 4 static flow patterns | Does NOT check KB wiring |
| D5 | `as_inspect_flow` | Full config: prompts, model, KB wiring | KB wiring check done here |
| D6 | `as_list_knowledge_bases` | KB embedding status | Cross-referenced with D5 |
| D7 | `obsidian_read_note` × 3 | Evo-log quality patterns | Conditional on symptom type |

**MCP call count (corrected):**
```
STANDARD (no quality trigger):
  D0(1) + D1(4) + D1b(1) + D4(1) + D5(0–4) + D6(0–3) = 7–13 calls, ~90s

STANDARD (quality trigger, D7 added):
  +3 obsidian reads = 10–16 calls, ~2min

DEEP:
  All above + as_get_agent_call_log × 3 + full D5 × 4 = max 22 calls, ~4min
```

---

## Tool Reference

| Tool | Parameters used | Notes |
|---|---|---|
| `as_health_check` | none | Returns basic counts only |
| `as_get_recent_executions` | `agent_name`, `limit`, optional `status` | PRIMARY execution check |
| `as_list_agent_calls` | `since_hours`, `limit` | A2A only — supplementary |
| `as_get_agent_call_log` | `agent_name`, `limit`, optional `status` | A2A only, no time filter |
| `as_find_broken_flows` | none (optional `public_only`) | 4 patterns, all agents |
| `as_inspect_flow` | `agent_name`, optional `node_type` | Full flow config |
| `as_list_knowledge_bases` | `agent_name` | KB status per agent |
| `as_patch_node_field` | `agent_name`, `node_id`, `field_name`, `field_value` (JSON literal — see 10b) | Apply only after 10a.5 confirmation |
| `obsidian_read_note` | `path` | Evo-log analysis |

**Excluded tools and reasons:**
- `as_get_heartbeat_status`: requires exact `agent_id` — needs extra as_list_agents call for minimal value
- `as_get_kb_embedding_status`: redundant — `as_list_knowledge_bases` already returns full status breakdown
- `as_diagnose_models`: covered by agent-health-check scope, not needed reactively

---

## Constraints Summary

| Constraint | Rule |
|---|---|
| Root cause | ONLY from IF-THEN table in Step 9 — never LLM inference |
| Fix IDs | ONLY from live MCP calls in current session — never from memory |
| Apply after confirmation | ONLY trivial fixes (C2/C3 from D4, C7 with 1 KB) — never without 10a.5 |
| Auto-apply guard | Check RUNNING status + pre-patch re-read before every patch |
| Post-patch verify | Always re-read to confirm patch took effect |
| A2A tools | D1b only — never as primary SOMA diagnostic |
| D7 trigger | Quality keywords in input → Standard; otherwise → Deep only |
| CONFIG_DRIFT | Not a category — cannot detect without config baseline |
| Score Analyzer | D1 check only — no evo-log, no auto-fix, secondary scope |
| 300-char limit | Call log output preview detects empty/sentinel outputs only |
| Time filter | as_get_recent_executions has no time filter — always last N records |

