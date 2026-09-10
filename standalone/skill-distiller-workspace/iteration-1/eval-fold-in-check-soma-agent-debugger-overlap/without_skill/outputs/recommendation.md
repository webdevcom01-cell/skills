# Recommendation: Do NOT create a new skill

## Request
"Create a skill that helps debug AgentStack agents when their flow isn't working correctly."

## Finding
An available skill already covers this exact job:

> **soma-agent-debugger** — "Specialized skill for debugging, fixing, and deploying
> production AgentStack agents. 4 modes: Investigate (root cause), Plan Fix, Build
> Validator, Verify Deploy"

This is a near-total overlap, not a partial one:

| Requested capability | Covered by soma-agent-debugger? |
|---|---|
| Target system: AgentStack agents | Yes — exact match |
| Trigger: "flow isn't working correctly" | Yes — this is a root-cause diagnosis of a broken agent, which is precisely the **Investigate** mode's job |
| Debugging in general | Yes — it's the skill's primary stated purpose |
| Anything beyond debugging (fix, validate, deploy) | Also covered — soma-agent-debugger's scope is a **superset** of what was asked for |

A new skill scoped to "debug agent flows" would not add any capability that doesn't
already exist. It would only duplicate a trigger surface ("agent broken", "flow not
working", "debug agent") that soma-agent-debugger already owns.

## Why not build it anyway

1. **Trigger collision.** Two skills matching the same request class ("my AgentStack
   agent's flow is broken") makes skill selection ambiguous — which one fires depends
   on wording, ordering, or luck. That's worse for the user than having one skill.
2. **Fragmented learnings.** soma-agent-debugger's description states it "capitalizes
   learnings iz Hook Writer 9-sprint debug-a" (i.e., it was distilled from real
   production incident history). A parallel skill starts from zero and can't inherit
   that accumulated knowledge; fixes discovered later would have to be duplicated
   across two files to stay in sync, and they won't be.
3. **No unmet need identified.** Nothing in the request ("flow isn't working
   correctly") falls outside soma-agent-debugger's stated Investigate mode. If there
   were a genuine gap (e.g., a distinct debugging surface it doesn't touch), a new
   skill would be justified — but that gap wasn't found.
4. **Tooling already assumes this path exists.** The environment exposes AgentStack
   MCP tools such as `as_inspect_flow`, `as_find_broken_flows`, `as_update_flow`, and
   `as_patch_node_field` — i.e., flow-level inspection and repair is already a
   first-class, wired-up capability, most plausibly consumed by
   soma-agent-debugger's Investigate/Plan Fix modes rather than needing a fresh skill
   to reach it.

## Adjacent skills worth a quick check before assuming a gap
While soma-agent-debugger is the clear primary match, two other listed skills sit near
this space and should be ruled out (not built around) before concluding there's
nothing to add:
- **agent-health-check** — may already provide a lighter-weight status/health signal
  that's distinct from full root-cause investigation.
- **pipeline-debug** — may cover SOMA pipeline-level failures as opposed to
  single-agent flow failures; worth confirming the boundary between "pipeline" and
  "agent flow" is where the user expects it.

Neither of these changes the conclusion for the specific request as stated ("debug
AgentStack agents when their flow isn't working") — that language maps directly onto
soma-agent-debugger's Investigate mode.

## What to do instead

1. **Use soma-agent-debugger, Investigate mode**, the next time a flow issue comes up.
   No new artifact is needed.
2. **If Investigate mode turns out to be insufficient** for flow-specific debugging in
   practice (e.g., it doesn't currently call `as_inspect_flow` /
   `as_find_broken_flows`, or lacks a fast triage path for flow issues specifically),
   the right fix is a **targeted enhancement to soma-agent-debugger** — e.g., add or
   tighten a "flow trace" step inside Investigate mode — not a standalone competing
   skill. That keeps one canonical place for AgentStack agent debugging and lets
   future fixes accumulate in one file instead of being split across two.
3. **If you genuinely want a second, independent skill anyway** (e.g., for a different
   audience, a different invocation surface, or a deliberately narrower/faster tool),
   say so explicitly and name what it should do that soma-agent-debugger does not —
   that's the trigger for building something new, not the original request as stated.

## Bottom line
No new skill folder was created. The requested capability already exists under
`soma-agent-debugger` (also present as `soma-skills:soma-agent-debugger` and
`anthropic-skills:soma-agent-debugger` in the catalog). Building a duplicate would
fragment triggers and split future learnings across two files for zero net-new
capability.
