# Scaffold Report, Error Handling, Rollback, Quality Bar

> Loaded from `agent-scaffolder` STEP 9 plus the three reference tables that follow it in the original skill. Use the STEP 9 template to generate the final report; consult the other three tables as needed (recovering from a failure, or self-checking against the 14-point quality bar before reporting complete).

## STEP 9 — Scaffold Report

```
✅ SCAFFOLD COMPLETE: {agent_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGENTSTACK
  Agent ID  : {agentId}
  Model     : {model_id}
  Flow      : {node_count} nodes, {edge_count} edges
  KB ID     : {kb_id}
  KB status : ready (3 documents: DESIGN_SPEC, instincts, evo-log)
  Smoke test: ✅ PASSED  (or ⚠️ SKIPPED if user overrode)

VAULT  [agents/{agent_slug}/]
  DESIGN_SPEC.md   ✅
  agent-card.md    ✅  ← Use this to wire other agents to/from {agent_name}
  instincts.md     ✅  ← Domain starter content loaded
  evo-log.md       ✅

PIPELINE
  Receives from : {upstream OR "User trigger"}
  Sends to      : {downstream OR "Final output"}
  {If TODO agent ID:}
  ⚠️  Downstream agent ID not resolved — wire it when {downstream_name} is created:
      as_patch_node_field(agent_name="{agent_name}", node_id="call_agent-{agent_slug}-handoff", field_name="agentId", field_value='"{id}"')

VARIABLE BINDING (A2A integrity)
  extractor outputVariable : structured_output
  call_agent inputVariable : structured_output
  Status : ✅ MATCH

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
  1. Run a real trigger via AgentStack UI
  2. After first run → evo-log-writer skill to log result
  3. After 3+ runs → instincts.md grows with real patterns
  4. When evo-log exceeds 20 entries, increase topK from 5 → 15:
     as_patch_node_field(agent_name="{agent_name}", node_id="kb_search-{agent_slug}-memory", field_name="topK", field_value='15')
  5. Use kb-sync skill to keep KB documents updated after instincts.md changes
```

---


## Error Handling Reference

| Error | Step | Action |
|-------|------|--------|
| Name not found in trigger | 1 | Ask user in plain text before AskUserQuestion |
| Downstream agent not in list | 1B | Set `TODO:{name}`, document in report |
| `as_create_agent` name conflict | 4 | Ask user: overwrite flow OR rename |
| `as_get_agent` shows wrong model | 4 | `as_update_agent_model` to fix |
| `as_update_flow` fails | 5 | Inspect current flow, rebuild and retry |
| Dry run shows unexpected node/edge count | 5d | Stop — do NOT apply. Rebuild 5a-5c and dry-run again |
| Flow verify fails (missing node/edge) | 5e | Stop, report exact mismatch, do not continue |
| `as_list_knowledge_bases` returns empty | 7b | KB not created — re-prompt manual UI step |
| Embedding status `"failed"` | 7f | Delete failed doc, re-add with `as_add_kb_text` |
| Smoke test fails | 8 | Report cause, fix, re-run test before reporting complete |
| Vault create fails (note exists) | 6 | Use `obsidian_update_note` instead — never silently overwrite |

---


## Rollback Guide

| Scaffold failed at... | What exists | Recovery |
|----------------------|-------------|---------|
| Before STEP 4 | Nothing in AgentStack | Retry from STEP 1 |
| STEP 4 succeeded, STEP 5 failed | Agent with empty flow | Use stored `agentId`, retry STEP 5 only |
| STEP 5 succeeded, STEP 6 failed | Agent + flow, no vault | Retry STEP 6 only |
| STEP 6 succeeded, STEP 7 failed | Agent + flow + vault, no KB | Retry STEP 7 only (KB docs are additive) |
| STEP 8 smoke test failed | Everything built, agent not working | Debug per STEP 8e failure table |

---


## Quality Bar (v2 — 14 checks)

**AgentStack:**
- [ ] `as_list_agents` shows agent with correct name
- [ ] `as_get_agent` shows correct model (not gpt-4.1-mini default)
- [ ] `as_inspect_flow` returns correct node count with correct IDs
- [ ] `kb_search` node has real KB ID (not "PENDING_KB_CREATION")
- [ ] If call_agent: `inputVariable` = `extractor outputVariable` = `"structured_output"`
- [ ] KB `embeddingStatus: "ready"` with exactly 3 documents

**Vault:**
- [ ] `agents/{slug}/DESIGN_SPEC.md` exists with all sections filled
- [ ] `agents/{slug}/agent-card.md` exists with real `agentId` + `kb_id`
- [ ] `agents/{slug}/instincts.md` exists with domain starter content (not just placeholders)
- [ ] `agents/{slug}/evo-log.md` exists

**Smoke Test:**
- [ ] `as_chat_with_agent` with UC-1 input returns non-empty response
- [ ] All output keys from Output Contract present in response
- [ ] `CONFIDENCE:` and `DATE:` present
- [ ] No FORMAT_ERROR or QUALITY_GATE_FAIL on valid input
