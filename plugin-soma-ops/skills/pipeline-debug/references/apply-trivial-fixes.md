# Apply Trivial Fixes (STEP 10)

> Loaded from `pipeline-debug` STEP 10. This step MUTATES production via `as_patch_node_field`. Fixes are applied ONLY after explicit user confirmation (10a.5) — read this file in full before proposing or applying any patch.

## STEP 10 — Apply Trivial Fixes (after explicit confirmation)

Eligible fixes from Step 9 are applied ONLY after the user confirms the exact patch (see 10a.5). This step **MUTATES production** via `as_patch_node_field`.

**Trivial = eligible to apply AFTER explicit user confirmation:**
1. RULE C2/C3 (FLOW_BROKEN from D4): ONLY where the suggested fix resolves to a
   concrete `node_id` + `field_name` + `field_value` — see 10b. If it does not,
   the issue is non-trivial and goes to the manual list.
2. RULE C7 (KB_UNWIRED): `as_patch_node_field` with live IDs from D5 + D6

**Non-trivial = NEVER applied by this skill.** These override the C2/C3
eligibility above: if a D4 issue is one of these, it is manual regardless of
severity — the D4 scan covers empty prompts and phantom call_agent nodes, and
both appear here.

- Empty prompt (needs human content)
- Wrong model value (needs target from user)
- KB empty/failed (needs kb-sync — different skill)
- Phantom call_agent (needs deletion decision)
- Ambiguous KB (2+ KBs — same rule as soma-memory-fix)

### 10a — Pre-fix safety checks (per agent to fix)

Before touching any agent:

1. **Active execution guard:** Check `{agent}_has_running`. If true → SKIP this agent.
   Log: "⚠️ {agent} is currently RUNNING — skipping auto-fix to avoid race condition."

2. **Pre-patch re-read:** Call `as_inspect_flow(agent_name: "{agent}")` to confirm
   condition still exists. If condition resolved (another process fixed it) → SKIP.
   Log: "ℹ️ {agent}: condition already resolved. Skipping."

### 10a.5 — Confirmation gate (MANDATORY before any patch)

Before any `as_patch_node_field` call, present every planned patch to the user:
`{agent_name, node_id, field_name, old_value → field_value}` for each eligible fix.
Ask: *"Apply these N flow patches to production? (da / yes)"*.

- **Fail‑closed:** if the user does not explicitly confirm, apply NOTHING — report all eligible fixes as `PROPOSED (awaiting confirmation)` and stop the apply phase.
- One confirmation may cover the whole batch; record it before proceeding.

### 10b — Apply FLOW_BROKEN fix (from D4)

```
as_patch_node_field(
  agent_name: "<from d4_issues>",
  node_id:    "<node.id from an as_inspect_flow call made THIS session>",
  field_name: "<from d4_issues>",
  field_value: "\"<from d4_issues>\""
)
```

**`field_value` must be a JSON literal.** The schema states it "is parsed as JSON"
and gives these forms: `'"my-variable"'` (string), `'0.7'` (number), `'true'`
(boolean), `'{"key":"value"}'` (object). So:
- an id or any string value carries inner quotes — `'"cmxyz..."'`
- a number does NOT — `'15'`, not `'"15"'`
- a string containing newlines, `"` or `\` must be JSON-**escaped**, not merely
  wrapped. This matters for prompt fields: a raw prompt wrapped in quotes is
  invalid JSON.

The schema does not document what happens when `field_value` fails to parse — it
says only that "changes are applied directly to the database". So a malformed
value may be rejected OR stored raw; do not assume either. Because 10d's
post-patch verify compares the field to the value you sent, a raw-stored bad
value can read back as a match. Verify the node's field against the intended
value, not against the string you passed.

**Do not treat `d4_issues[agent].fix` as structured data.** `as_find_broken_flows`
returns "a list of issues per agent with severity and suggested fixes" — the `fix`
field is a suggestion string of unspecified shape, not four named keys. If you
cannot read `node_id` and `field_name` off it unambiguously, do NOT invent them:
obtain `node_id` from an `as_inspect_flow` call in this session, and abort the
patch if `field_name` is still ambiguous. Inventing either one while believing the
"live IDs only" rule was honoured is exactly the failure that rule exists to stop.

### 10c — Apply KB_UNWIRED fix (from D5+D6)

```
as_patch_node_field(
  agent_name: "<agent_name>",
  node_id:    "<node.id from D5 as_inspect_flow>",
  field_name: "knowledgeBaseId",
  field_value: "\"<kb id from D6 as_list_knowledge_bases>\""
)
```

Only if `{agent}_kb_count` == 1. If 0 or 2+ → skip, report as manual.

### 10d — Post-patch verification

After each patch, re-read to confirm:
```
as_inspect_flow(agent_name: "<agent_name>", node_type: "<patched_node_type>")
```

- If field now has expected value → mark as `FIXED ✅`
- If field still empty → mark as `VERIFY_FAILED ❌` — log error, report for manual follow-up
- If field has unexpected value → mark as `VERIFY_MISMATCH ❌` — do NOT overwrite, report

### 10e — Track results
```
{auto_fixes_applied}   = list of FIXED nodes
{auto_fixes_failed}    = list of VERIFY_FAILED / VERIFY_MISMATCH
{auto_fixes_skipped}   = list of skipped (running agent / ambiguous)
```
