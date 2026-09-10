# Recommendation: Do NOT create a new "AgentStack flow debugger" skill

## Task as given
Create a skill that helps debug AgentStack agents when their flow isn't working correctly.

## Overlap check (done before writing anything)

Before scaffolding a new skill, I checked the available-skills catalog, per the
"before creating a new skill, check for existing overlap" convention this
workspace uses (see `skill-creator-pro`, `system-teardown`, and others, which
all explicitly say "do NOT use for X — use soma-agent-debugger instead").

A skill named **`soma-agent-debugger`** is already present, described as:

> Specialized skill for debugging, fixing, and deploying production AgentStack
> agents. 4 modes: Investigate (root cause), Plan Fix, Build Validator, Verify
> Deploy.

The fuller (Serbian-language) version of the same skill in the catalog adds:

> Kapitalizuje learnings iz Hook Writer 9-sprint debug-a... Anti-hallucination
> first: forensic verification PRE svake izmene koda.
> Triggeri: debug agent, fix agent, audit agent, agent ne radi, agent broken,
> production broken, build quality gate, smoke test agent, verify deploy,
> popravi agent, audituj agent, pukla produkcija, hocu validator, validate
> deploy.

### Why this is a direct hit, not a near-miss

1. **Scope match.** "AgentStack agent" + "flow isn't working" is squarely a
   root-cause / debugging problem. That is exactly `soma-agent-debugger`'s
   **Investigate (root cause)** mode — mode 1 of 4.
2. **Domain match.** Both the task and the existing skill are scoped to
   *production AgentStack agents* specifically (not generic app debugging).
3. **Tooling already exists for this exact job.** The AgentStack MCP server
   available in this environment (`mcp__93684bab...`) already ships
   flow-specific diagnostic tools: `as_find_broken_flows`, `as_inspect_flow`,
   `as_get_recent_executions`, `as_get_agent_call_log`, `as_diagnose_models`,
   `as_health_check`, `as_get_heartbeat_status`. A new skill would either
   re-wrap these same tools (duplication) or ignore them (regression).
4. **Ecosystem convention already routes here.** Several other skills in the
   catalog explicitly defer to `soma-agent-debugger` for this exact scenario,
   e.g. `system-teardown`: "Do NOT use for ... fixing or hardening an agent
   you own (use soma-agent-debugger)."
5. **The skill is duplicated/namespaced multiple times already**
   (`soma-agent-debugger`, `soma-skills:soma-agent-debugger`,
   `anthropic-skills:soma-agent-debugger`), which is itself a sign that this
   surface is already crowded — adding a fourth near-identical entry would
   make triggering *worse*, not better (more ambiguous matches competing for
   the same user phrasing).

Creating a new skill here would produce an unhelpful duplicate: two skills
with overlapping triggers competing for the same request, inconsistent
methodology (whichever one didn't inherit the "anti-hallucination /
forensic verification" discipline the existing one has already learned from
real incidents), and double the maintenance burden for zero new capability.

## Decision

**No new skill folder was created.** This file is the deliverable: a
recommendation to use the existing `soma-agent-debugger` skill for this task,
plus one small, concrete gap worth patching in *that* skill rather than
forking a new one.

## What to do instead

- For "AgentStack agent flow isn't working" requests, invoke
  **`soma-agent-debugger`** in **Investigate** mode. That mode is defined as
  root-cause analysis, which is precisely what a broken flow needs.
- If the flow turns out to need a code change, that same skill's **Plan Fix**
  mode produces a structured fix prompt; **Build Validator** and
  **Verify Deploy** cover the regression-gate and post-deploy smoke test that
  a flow fix should go through before being trusted in production.
- If broken-flow debugging turns out to need heavier forensic legwork than a
  skill alone should carry (e.g., long multi-file traces), delegate from
  inside that skill's Investigate mode to a general-purpose research agent —
  don't build a second skill to do it.

## One real (small) gap found — recommend a fold-in patch, not a new skill

The existing skill's trigger list is Serbian-first and English-light:

```
debug agent, fix agent, audit agent, agent ne radi, agent broken,
production broken, build quality gate, smoke test agent, verify deploy,
popravi agent, audituj agent, pukla produkcija, hocu validator, validate deploy
```

None of these triggers literally contain the phrase **"flow isn't working"**
or **"flow is broken"** — the exact wording used in this task and likely to
be used by an English-speaking user. The capability is there (Investigate
mode), but the trigger surface might miss that specific phrasing in a
description-matching system.

**Recommended fold-in (one line, in the existing skill, not a new file):**
add `agent flow broken, flow not working, flow isn't working, broken flow`
to `soma-agent-debugger`'s trigger list. This closes the only gap found,
without creating a competing skill.

## When a new, separate skill *would* be justified (none of these apply here)

- The new work targets a different system than AgentStack/SOMA agents.
- The new work is a fundamentally different activity (e.g., authoring new
  flows, not debugging existing ones) — that's closer to `agent-scaffolder`
  or `safe-agent-builder`, also already in the catalog.
- The existing skill's methodology is actively wrong for this case and can't
  be fixed in place (not observed here — the description and modes line up).

None of these hold, so the answer is "use what's already there," with the
one small trigger-list patch noted above filed as the only actionable change.
