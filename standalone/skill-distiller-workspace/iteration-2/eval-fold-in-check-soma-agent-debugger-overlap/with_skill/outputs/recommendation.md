# Recommendation: no new skill created

**Request:** create a skill that helps debug AgentStack agents when their flow isn't working correctly.

**Decision:** did not create a new skill. Following the `skill-distiller` workflow
(Step 2 of `SKILL.md`, "Check for fold-in before creating anything new" — same
check as Step 1 of `references/distillation-algorithm.md`), an existing skill
already covers this ground.

## Fold-in check performed

Per Step 2, checked option (a) first: the `<available_skills>` catalog already
visible in context. That catalog lists:

> **soma-agent-debugger** — "Specialized skill for debugging, fixing, and
> deploying production AgentStack agents. 4 modes: Investigate (root cause),
> Plan Fix, Build Validator, Verify Deploy"

No further search was needed — this is a direct hit, not a partial or
tangential one.

## Why this counts as a match, not just an adjacent topic

The requested capability — "debug AgentStack agents when their flow isn't
working correctly" — is a root-cause-diagnosis task on a broken agent flow.
That is exactly what `soma-agent-debugger`'s **Investigate (root cause)**
mode is described as doing, on the same target system (AgentStack agents).
The existing skill's scope is a strict superset of the request: beyond
diagnosis, it also plans the fix, builds a validator, and verifies the
deploy. There's no part of the requested skill that falls outside what
`soma-agent-debugger` already claims to do.

## Why this isn't a `references/` patch

`distillation-algorithm.md` Step 1 says a fold-in match should be extended
rather than duplicated. `SKILL.md` Step 2 adds the nuance that "extend the
match" isn't always a `references/` patch: that's the right move for a
knowledge-base-shaped skill, but for an **operational/procedural skill built
around fixed modes** — which is exactly how `soma-agent-debugger` is
described (4 named modes) — the right move is either adding a new mode/
section to its own `SKILL.md`, or, if the existing modes already cover the
need, simply telling the user no new work is needed.

## A constraint on how far this check could go

`SKILL.md` Step 2 also says: "Read the matched skill's actual shape before
deciding which kind of extension applies." That step was not performed here
by design — this task's instructions explicitly directed treating the given
one-line description as ground truth and *not* going looking for the real
`soma-agent-debugger` skill files on this machine. So this recommendation is
based on the description alone, not on an inspection of its actual
`SKILL.md` body or modes.

Given that constraint, the conclusion that best fits the evidence available
is: **no new skill, and most likely no edit to the existing skill either** —
its stated Investigate mode already is a debug-the-broken-flow tool for
AgentStack agents. If there turns out to be a real gap (e.g. a lighter-weight
check than the full Investigate → Plan Fix → Build Validator → Verify Deploy
pipeline, or a flow-debugging angle the Investigate mode's actual body
doesn't in fact cover), the next step should be: open the real
`soma-agent-debugger` `SKILL.md`, confirm what its Investigate mode actually
does, and if a gap is confirmed, add a mode/section to that skill directly
rather than standing up a separate one — not to build a new skill from
scratch.

## What would change this recommendation

- If the user says the need is actually for a different system than
  AgentStack (a different agent framework, or debugging something upstream/
  downstream of the agent itself, e.g. the orchestration layer that calls
  it), the overlap would be weaker and a new skill could be justified.
- If reading the real `soma-agent-debugger` `SKILL.md` shows its Investigate
  mode is narrower than its description implies (e.g. it only checks one
  specific class of failure), a targeted addition to that skill — not a new
  one — would be the fix.
