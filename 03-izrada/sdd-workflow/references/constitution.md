# Constitution

The constitution is the set of non-negotiable principles for a project: stack, security
rules, architectural conventions, things that must never be reintroduced. It exists so that
every later phase (Specify, Plan, Tasks) inherits the same ground rules instead of each
feature quietly re-deciding them.

## Why this lives in CLAUDE.md, not a separate file

Some SDD tooling writes a dedicated `constitution.md`. In practice this creates two places
that claim to describe the same rules, and they drift — someone updates one and not the
other, and six months later nobody knows which is current. `CLAUDE.md` already exists for
exactly this purpose (durable instructions an agent needs to work safely in the repo), so
this phase extends it instead of duplicating it.

Keep additions short. `CLAUDE.md` works best under roughly 200 lines — specific and concise
beats exhaustive. If a rule would only ever matter for one narrow subsystem, it likely
belongs in a scoped rules file near that code, not in the root `CLAUDE.md`.

## Greenfield (new project or repo)

Ask directly:
1. Stack and language choices already decided (or open for this project)?
2. Any non-negotiables — testing requirements, security rules, a pattern that must be
   followed (e.g. "every endpoint needs an auth check", "no direct DB access outside the
   repository layer")?
3. Any compliance or regulatory constraints that apply project-wide (data residency,
   audit trail requirements, fiscal/tax rules)?

Write the answers into `CLAUDE.md` as a short, scannable list — not prose paragraphs.

## Brownfield (existing code — the common case)

Don't ask cold. Read first, then confirm:
1. Look at the existing structure, dependency manifest, and a representative file or two to
   infer stack and conventions already in use.
2. Check whether `CLAUDE.md` already exists and what it currently says.
3. Propose additions based on what the code actually does (e.g. "this repo consistently uses
   the repository pattern for DB access — should that be a stated rule?") rather than asking
   generic questions the person has to answer from scratch.
4. Get explicit confirmation or correction before writing.

## Brownfield, but no repo access in this session

Sometimes the change is against an existing codebase, but this session has no way to read
it — no connected folder, no repo access, a hypothetical or exploratory run. Don't silently
treat this like Greenfield (asking generic questions as if nothing exists) or like ordinary
Brownfield (implying you inspected code you haven't seen). Instead:

1. Say plainly that you have no repo access this session, and that anything you write is a
   stated assumption, not a confirmed fact about the actual codebase.
2. Ask the person directly for the few conventions that would otherwise come from reading
   code (stack, the pattern non-negotiables, anything a wrong guess here would be expensive
   to unwind later).
3. Mark every remaining assumption explicitly in `CLAUDE.md` (e.g. `[ASSUMPTION —
   unverified, confirm against real code before Implement]`) rather than stating it as
   settled. Carry these flagged assumptions forward into `plan.md` as risks — don't let them
   quietly disappear once Constitution is "done."
4. If the assumption is decision-relevant (the choice of approach in Plan actually depends
   on which way it goes), treat it as a blocking open question, not a footnote — propose the
   alternatives explicitly rather than picking one silently.

## When to skip this phase

If `CLAUDE.md` already documents the conventions relevant to the change at hand, re-reading
it satisfies this phase — there's no need to re-run the interview every time. Only revisit
Constitution when the change genuinely introduces a new non-negotiable (a new required
pattern, a new compliance constraint) rather than working within existing ones.
