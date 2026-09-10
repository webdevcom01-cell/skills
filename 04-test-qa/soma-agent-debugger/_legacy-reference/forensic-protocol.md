# Forensic Protocol — Pre-flight Checklist
# Source: soma-agent-debugger SKILL.md Mode 1 (confirmed read 2026-06-14)
# This is the structured version of the Mode 1 investigation process.

## Pre-flight: Ask 4 Questions Before Any Investigation

Before running any MCP calls or looking at code, ask:

1. **Which agent?** — ID or name (ID preferred: prevents confusion if name changes)
2. **Expected vs actual?** — Exact description of what should happen vs what does happen
3. **When did it appear?** — After which commit, deploy, or prompt change? (narrows git range)
4. **Reproducible test case?** — A specific input that reliably triggers the bug

If any of these is missing, STOP and ask. Investigating without a reproducible case wastes time.

---

## Phase 1: Live State Verification (always first)

**Never skip this phase.** Audit documents and vault files may be stale.

```bash
# 1. Current live system prompt
as_get_agent(<agentId>)
# → note: model, prompt sections, any embedded rules

# 2. Current flow structure
as_inspect_flow(<agentId>)
# → note: node types, node order, edge connections, outputVariable values, function node code

# 3. Recent git history
git log --oneline -10
# → look for commits in timeframe when issue appeared

# 4. Detailed diff for suspicious files
git log -p src/lib/runtime/handlers/<relevant-file>.ts
# → actual code changes, not just commit messages

# 5. Bash inspect current code
Read src/lib/runtime/handlers/<handler-file>.ts
# → confirm what's actually running, not what docs say

# 6. Recent executions
as_get_recent_executions agentId=<id> limit=5
# → check status, inputParams, outputResult of recent runs
```

**STOP:** If live state doesn't match what you expected based on docs/audit, the docs are wrong. Work from live state only.

---

## Phase 2: Root Cause Analysis

After live state is confirmed:

1. **4-step execution sequence** — trace what happens at each node in order:
   - What enters the node (variable name + content)
   - What the node does (code/prompt/condition logic)
   - What exits the node (output variable + content)
   - Where the output goes next (edge target)

2. **Cite file:line for every claim** — if you say "the validator checks X", cite which node, which line of code

3. **Distinguish root cause types:**
   - Race condition vs literal duplicate (timing vs logic)
   - Design issue vs code bug (architecture vs implementation)
   - Prompt issue vs flow issue (ai_response vs function/condition node)

4. **List hypotheses ruled out** — explicitly document what you checked and eliminated

---

## Investigation Report Template

```markdown
## Investigation Report — <YYYY-MM-DD>

### Symptom
<exact reproducible description — input + expected + actual>

### Live State (verified via MCP)
- Agent ID: <id>
- Model: <model string>
- Current flow nodes (in order): <list with types>
- Current edges: <list>
- Recent commits (last 5): <hash + message>

### Root Cause
<4-step execution trace with file:line citations>

### Evidence
1. <verifiable fact + source (MCP output / file:line / git hash)>
2. <verifiable fact + source>
...

### Hypotheses Ruled Out
- NOT <hypothesis A>: <reason + evidence>
- NOT <hypothesis B>: <reason + evidence>

### Next Action
[Mode 2: Plan Fix | Sprint planning | Architectural decision needed]
```

**STOP after delivering report.** Do not proceed to fix without explicit user confirmation of root cause.

---

## Anti-Hallucination Checklist (run before submitting report)

- [ ] Every claim in "Live State" came from an MCP call in THIS session, not memory
- [ ] Every file:line citation was confirmed by Read in THIS session
- [ ] Every git hash was confirmed by git log in THIS session
- [ ] "Hypotheses Ruled Out" lists at least one eliminated path
- [ ] Report doesn't say anything happened "probably" or "likely" without evidence
