# AgentStack MCP Cookbook
# Source: verified usage patterns from SOMA pipeline sessions (May-Jun 2026)
# Every pattern confirmed to work in production.

## Pattern 1: Inspect flow (always first before any change)

as_inspect_flow agentId=<id>

Returns: nodes array + edges array of current live flow.
Always run before ANY change. Save output to file as backup before modifying.

---

## Pattern 2: as_update_flow — mandatory dry_run sequence

as_update_flow is IRREVERSIBLE (no undo). Always use this sequence:

Step 1 — dry run:
as_update_flow agentId=<id> nodes=<nodes_json> edges=<edges_json> dry_run=true

Verify in response:
- success: true
- nodes.before = expected current count
- nodes.after = expected new count
- edges.before / edges.after match expected structure

Step 2 — ONLY after dry_run confirms structure:
as_update_flow agentId=<id> nodes=<nodes_json> edges=<edges_json> dry_run=false

STOP if dry_run shows unexpected node/edge counts. Do not apply live.

---

## Pattern 3: as_patch_node_field — single field edit

Use instead of as_update_flow when changing ONE field on ONE node:

as_patch_node_field agentId=<id> nodeId=<node-id> field=<field-path> value=<new-value>

Examples:
- Function code:      field="data.code"              value="<new js code>"
- KB ID:              field="data.knowledgeBaseId"    value="<kb-id>"
- Output variable:    field="data.outputVariable"     value="new_var_name"

Safer than as_update_flow (atomic single-field). Run as_inspect_flow after to confirm.

---

## Pattern 4: Eval suite — correct polling flow

Step 1 — trigger run:
as_run_eval eval_id=<suite-id>
Returns: jobId (NOT runId). as_run_eval is async.

Step 2 — wait 30-45 seconds, then poll:
as_list_evals agent_name="<Agent Name>"

Check in response:
- lastRunStatus: "COMPLETED" (not "RUNNING" or "FAILED")
- lastRunScore: 1.0
- caseCount: expected number

Do NOT use as_get_eval_result — it requires run_id which as_run_eval does not return.
If as_run_eval returns 403: ownership issue, see lessons-learned.md L8.
If lastRunStatus stays "RUNNING" > 5 minutes: BullMQ worker may be down.

---

## Pattern 5: as_chat_with_agent — smoke test

as_chat_with_agent agentId=<id> message="<test input>"

Returns: LAST message node output only (not full stream).
For gate-flow agents: expect payload (PASS) or {"status":"BLOCKED",...} (BLOCK).
For chain agents: expect downstream agent's final output.

Note: returns only last message, so it looks clean even if processor emitted malformed JSON.
Evals grade the full stream and are stricter. Do not rely solely on this for validation.

---

## Pattern 6: as_get_recent_executions — verify run completed

as_get_recent_executions agentId=<id> limit=5

Returns: last N executions with status, inputParams, outputResult, duration.
Use after as_chat_with_agent to confirm:
- status: "COMPLETED"
- outputResult contains expected content
- No unexpected errors

---

## Pattern 7: as_list_evals — check eval suite status

as_list_evals agent_name="<Agent Name>"

Returns all eval suites with: id, name, caseCount, lastRunStatus, lastRunScore.
Works without AGENT_STUDIO_API_KEY (DB-direct). Use this to verify everything.

---

## Known gotchas

| Situation                          | What NOT to do                    | What to do instead                  |
|------------------------------------|-----------------------------------|--------------------------------------|
| as_run_eval done, want results     | as_get_eval_result (needs run_id) | as_list_evals > lastRunScore         |
| as_create_eval_case returns 403    | retry or switch to REST           | check agent ownership first          |
| as_update_flow applied wrong       | try to "undo" it                  | no undo — restore from backup JSON   |
| Node seems right but wrong behav.  | trust memory or docs              | as_inspect_flow for live state       |
| eval PASS case false-fails         | add more assertions               | remove json_valid, use not_contains  |
