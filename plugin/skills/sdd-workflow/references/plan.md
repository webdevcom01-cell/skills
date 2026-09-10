# Plan

Write `specs/<feature-slug>/plan.md`. This is the "how" — the first place technology choices,
file paths, and architecture decisions are allowed to appear. If Specify named a specific
library or file, that was actually Plan content that leaked upstream; move it here.

## plan.md template

```markdown
# Plan: <Feature Name>

## Architecture
How this fits into the existing system. A short diagram-in-words or an actual diagram if
the shape is non-obvious. Name the existing patterns being followed (per CLAUDE.md) or
explicitly flag a deviation and why it's justified.

## Data model
New or changed data structures, schema changes, migrations needed.

## Interfaces
New or changed APIs, function signatures, or contracts between components. Be concrete
enough that Tasks can be written directly from this section.

## Affected files
The actual files that will be created or touched. This is what makes Tasks (Step 5)
possible to write without re-deriving the plan.

## Risks and open questions
What could go wrong, what's still uncertain, what assumption this plan is making that
should be flagged now rather than discovered mid-Implement.

## Alternatives considered (optional)
Only include this if a real fork was decided between — don't manufacture alternatives to
look thorough.
```

## What belongs here vs. in Specify

A useful test: if the sentence would still make sense to a non-technical stakeholder who
just wants to know the feature works, it's Specify. If it requires knowing this codebase's
internals to evaluate, it's Plan. Keeping this boundary clean is what lets Specify survive a
technology change (e.g. swapping the database) without needing a rewrite.

## Get approval before Tasks

Plan is where an architecture mistake is cheapest to catch — before any file exists. Don't
let this phase get rubber-stamped just because Specify already went through review; a
technically-sound spec can still have a bad plan underneath it.
