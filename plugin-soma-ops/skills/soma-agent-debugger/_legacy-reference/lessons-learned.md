# Lessons Learned — soma-agent-debugger
# Source: Hook Writer 9-sprint debug cycle (May–Jun 2026) + cr-x-repair (Jun 2026)
# Every lesson has a verified source. Do not add to this list without a cited source.

## L1: asText() before ANY substring check
**Source:** safe-agent-builder/references/flow-templates.md (confirmed read 2026-06-14)
**What happened:** web_search output arrives in `variables` as an array/object, NOT a string.
`String(someArray)` → `"[object Object]"` — URLs and fields vanish.
A grounding check that should PASS will silently false-block 100% of inputs.
**Rule:** Always coerce before substring/indexOf operations:
```js
function asText(x) {
  if (typeof x === "string") return x;
  try { return JSON.stringify(x); } catch(e) { return String(x); }
}
```
**Applies to:** search_results, sub-agent outputs, KB context, any mapped input you didn't produce as a string yourself.

---

## L2: Diverse input types — never test with happy path only
**Source:** soma-agent-debugger SKILL.md Mode 3 "Critical lessons" (confirmed read 2026-06-14)
**What happened:** A validator built and tested on one trend type (announcement) blocked valid technical + evergreen trends.
**Rule:** Test with minimum 3 input types: announcement + technical + evergreen.
One happy path = false confidence. Test each violation type with a separate case.

---

## L3: 4-layer deploy coordination
**Source:** cr-x-repair implementation (2026-06-14), FIX-LOG P2-11
**What happened:** 3-layer (prompt, code, vault) was documented but missed eval suite verification. Post-deploy regression only caught via manual eval run.
**Rule:** Deploy order must be:
1. Prompt update (MCP, instant)
2. Code change (PR + Railway/platform deploy)
3. Vault docs update
4. Eval suite verification (`as_run_eval` → `as_list_evals` confirm lastRunScore)
Missing any layer creates a regression window.

---

## L4: Live state IS source of truth — forensic before fix
**Source:** soma-agent-debugger SKILL.md Hard Rule #3 (confirmed read 2026-06-14)
**What happened:** Multiple times an audit finding pointed to a bug that had already been fixed in live, or described a different version of the code than what was running.
**Rule:** Before any fix, call `as_get_agent(<id>)` + `as_inspect_flow(<id>)` to read current live state. Vault docs and past audits are secondary. If they conflict with live state, live state wins.

---

## L5: Verbatim match requires normalization
**Source:** safe-agent-builder/references/flow-templates.md lines 146-149 (confirmed read 2026-06-14)
**What happened:** A hook-verbatim gate blocked valid output because the model used a curly quote (”) instead of a straight quote ("). Byte-identical comparison fails on whitespace, punctuation, and smart-quote reformatting.
**Rule:** Never compare byte-identically. Normalize both sides before substring match:
```js
function norm(s) {
  return String(s).toLowerCase()
    .replace(/\s+/g, " ")
    .replace(/[^a-z0-9 ]/g, "")
    .trim();
}
// norm(expected) vs norm(actual) — catches real rewrites, forgives formatting
```

---

## L6: Hardcoded linked fields in prompt templates break logical coupling
**Source:** safe-agent-builder/references/flow-templates.md lines 254-257 (confirmed read 2026-06-14)
**What happened:** A hardcoded `"is_evergreen": false` in a prompt example made the agent emit it even when confidence was "1 star" (which implies is_evergreen: true). The model copied the literal value.
**Rule:** If two output fields are logically coupled, use a descriptive placeholder in the example, not a hardcoded value. Add a FINAL CHECK line restating the link. Enforce the link in the validator too.

---

## L7: json_valid eval assertion false-fails on gate-flow agents
**Source:** safe-agent-builder/references/evals.md lines 76-82 (confirmed read 2026-06-14)
**What happened:** A `json_valid` assertion was added to the PASS case of an eval suite. It failed even though the agent was producing correct output, because the eval grades the WHOLE assistant message stream (including the ai_response processor's raw output with ```json fences), not just the final message node.
**Rule:** On gate-flow agents, use only `contains` / `not_contains` with stable string markers (e.g., `"BLOCKED"`). Never use `json_valid`, `exact_match`, or `starts_with` on gate-flow eval cases.
Note: `as_chat_with_agent` returns only the LAST message so it looks clean there — evals are stricter.

---

## L8: as_create_eval_case returns 403 = ownership issue, not API key
**Source:** FIX-LOG.md P1-12 (confirmed grep 2026-06-14)
**What happened:** `as_create_eval_case` returned HTTP 403 for a newly-created agent. Initial diagnosis was wrong API key. Real cause: agent was not owned by the authenticated user.
**Fix:** `UPDATE "Agent" SET "userId" = '<correct-user-id>' WHERE id = '<agentId>'`
**Rule:** If `as_create_eval_case` or `as_run_eval` returns 403, check agent ownership first. Switching to the REST API fallback (as documented in evals.md) will also fail if ownership is wrong.

---

## L9: vm.Script hermetic testing before deploy for function nodes
**Source:** cr-x-repair.test.ts (created 2026-06-14), cr-x-repair implementation
**What happened:** Function node code (cr-x-repair) was developed and iterated without deploy. vm.Script sandbox was used to run the exact code from the DB node in an isolated context, catching logic errors before touching production.
**Rule:** For any non-trivial function node, create a hermetic test harness before deploy:
```js
const vm = require("vm");
const REPAIR_CODE = `<exact function node body from DB>`;
const script = new vm.Script(`(function(variables) { ${REPAIR_CODE} })(variables)`);
const ctx = vm.createContext({ variables: { /* test input */ } });
const result = script.runInContext(ctx);
```
Test with diverse inputs (happy path + edge cases + deliberate bad input).
11/11 unit tests passing = safe to deploy. 1 test = false confidence.
