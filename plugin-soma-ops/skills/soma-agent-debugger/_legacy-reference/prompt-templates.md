# Battle-tested Claude Code Prompt Templates
# Source: soma-agent-debugger SKILL.md Mode 2 (confirmed read 2026-06-14) + session fix prompts

## Standard Fix Prompt Template

Use this structure for ANY code or flow fix delegated to Claude Code.
Every section is mandatory. Missing a STOP point = risk of silent destructive action.

```markdown
# Fix Prompt: <Title>
# Agent: <which AgentStack agent>
# Fix type: <prompt | flow | vault | code | multi-layer>
# Date: <YYYY-MM-DD>

## Hard Rules
1. Anti-hallucination first: verify current state before changing anything
2. NE pretpostavljaj — uvek verifikuj pre menjanja (cite each MCP/file output)
3. STOP points are mandatory — do not skip them, even if the next step seems obvious
4. dry_run: true on as_update_flow before any live apply
5. Backup as_inspect_flow output to file before any flow change

---

## KORAK 0: Pre-flight verification

Verify that the current state matches what this prompt assumes:
[List specific MCP calls to run and what their output should show]
Example:
- as_inspect_flow(<agentId>) → confirm node "<node-id>" exists with type "function"
- Read src/lib/... → confirm function at line X matches what we expect

### STOP: If pre-flight shows different state than expected, halt and report.

---

## KORAK 1: <First change>

[Step-by-step, one action at a time]
[Include exact values, not "appropriate values"]

Verify after:
[What to check — specific MCP call or Read command]

---

## KORAK 2: <Second change>

[...]

### STOP: <Decision point requiring human input>
Example: "The DB shows 3 eval cases. Should we delete existing cases before adding new ones? Halt for confirmation."

---

## KORAK 3: Final verification

[Checklist of what must be true for this fix to be complete]
- [ ] <specific verifiable condition>
- [ ] <specific verifiable condition>
- [ ] Smoke test: as_chat_with_agent input="<test input>" → expect "<expected output pattern>"
- [ ] as_list_evals confirms eval suite score (if applicable)

## Final acceptance criteria
[Binary PASS/FAIL list — every item must be PASS before declaring done]
```

---

## Fix Type Guide

**Prompt fix** (fastest, no deploy):
- Tool: `as_update_agent_prompt` or `as_patch_node_field` (for node data.content)
- Instant: no Railway deploy needed
- Risk: low. Rollback: `as_update_agent_prompt` with previous content
- When: system prompt change, node prompt change

**Flow fix** (fast, no deploy):
- Tool: `as_update_flow` (structural) or `as_patch_node_field` (single field)
- Instant: no Railway deploy needed
- Risk: medium. `as_update_flow` is IRREVERSIBLE — always backup + dry_run
- When: add/remove/rewire nodes, change node type, change outputVariable

**Vault fix** (no impact on runtime):
- Tool: Write/Edit on vault markdown files
- No deploy needed
- Risk: low. Only affects documentation.
- When: update DESIGN_SPEC, instincts, evo-log

**Code fix** (slowest, requires deploy):
- Tool: Edit TypeScript files → PR → Railway deploy
- Requires: PR review + merge + Railway redeploy
- Risk: high. Rollback: git revert + redeploy
- When: src/lib/runtime changes, new node handler types, platform-level changes

**Multi-layer fix** (most complex):
- Combination of above
- MUST coordinate order: prompt/flow changes first (instant) → code changes (deploy) → vault (after confirm)
- Risk: regression window between layers. Document sequence explicitly.
