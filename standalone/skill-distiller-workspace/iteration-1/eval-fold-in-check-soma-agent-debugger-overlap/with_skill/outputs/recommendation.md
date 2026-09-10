# No new skill created — use `soma-agent-debugger`

## Request

"Create a skill that helps debug AgentStack agents when their flow isn't
working correctly."

## Fold-in check (skill-distiller, Step 2 of the workflow / Step 1 of the
distillation algorithm)

Before creating anything, the available-skills catalog was checked for
something that already covers this ground. It does:

> **soma-agent-debugger** — "Specialized skill for debugging, fixing, and
> deploying production AgentStack agents. 4 modes: Investigate (root cause),
> Plan Fix, Build Validator, Verify Deploy."

## Why this is a fold-in, not a new skill

- **Same target system.** Both the request and the existing skill are about
  AgentStack agents specifically, not agents in general.
- **Same failure class.** "Flow isn't working correctly" is exactly what
  root-cause debugging of a broken agent means — there's no daylight between
  the request and the existing skill's own stated purpose.
- **Direct mode match.** soma-agent-debugger's first mode, *Investigate (root
  cause)*, is described as covering root-cause investigation of a broken
  agent. That is precisely the request. This isn't adjacent or partial
  overlap that might justify a companion skill — the request is a subset of
  a capability that already exists, described almost verbatim.

## Shape check before deciding how to fold in

skill-distiller's fold-in rule warns against defaulting to "extend the match
== add a `references/` file" — that pattern only fits a knowledge-base-shaped
skill. soma-agent-debugger's own description shows it is **not** that shape:
it's an operational/procedural skill organized around four fixed modes
(Investigate → Plan Fix → Build Validator → Verify Deploy), closer to a
pipeline than a topic library. For a skill like this, extension — if
warranted — means adding a new mode or section to its `SKILL.md` body, not
dropping a reference file into it.

That said, extension isn't warranted here either. The request doesn't ask
for any capability outside the four existing modes — it asks for exactly
what Investigate (root cause) already does. There is no gap to fill with a
fifth mode.

## Decision

No new skill folder was created, and no change to soma-agent-debugger is
proposed. The existing skill already covers this need in full.

## What to do instead

Invoke **soma-agent-debugger**, using its **Investigate (root cause)** mode,
against the AgentStack agent whose flow is misbehaving. If investigation
turns up a fix, the same skill's **Plan Fix**, **Build Validator**, and
**Verify Deploy** modes carry the fix through to a validated production
deploy — the full path from "flow is broken" to "fix is verified in
production" is already one skill.

## When a new skill (or a new mode on this one) would actually be justified

Only if a future request needs something none of the four modes cover —
for example, something outside root-cause investigation, fix planning,
validation, or deploy verification (e.g., ongoing agent performance
monitoring after a clean deploy). Even then, per the shape check above, the
right move would most likely be proposing a fifth mode on
soma-agent-debugger's own `SKILL.md`, not standing up a separate skill —
unless that new concern is broad enough to be its own topic (in which case
it should be raised with the user rather than assumed).
