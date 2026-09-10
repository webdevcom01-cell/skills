# Converge / Verify

Write `specs/<feature-slug>/verify.md`. This is the step most ad-hoc AI coding skips
entirely, and the one most spec-driven tooling stops short of too — most tools verify that
code was *generated*, not that it *satisfies the spec*. The point of this phase is
independent verification: checking the work from outside the reasoning pass that produced it,
because an agent grading its own implementation shares all of that implementation's blind
spots by construction.

## With subagents available

Different environments name this differently — the Task tool in Claude Code, the Agent
tool in Cowork, or an equivalent in other runtimes. Before assuming it's absent, actually
check what's available to you right now (e.g. list your tools) rather than pattern-matching
on a specific name from this doc — the capability is what matters, not the label.

Note: a subagent you spawn this way typically does *not* itself have access to a further
subagent-launching tool (this is a common platform-level ceiling, not a skill defect) — so
if you are already running as a subagent when you reach this step, the "Without subagents"
path below is likely your real situation even if the top-level session has the capability.

Spawn a verifier with a narrow, deliberately limited context:
- `spec.md`, `plan.md`, `tasks.md`, and the actual diff or changed files.
- **Not** the conversation that produced them — a verifier that inherited the same framing
  the implementer used is prone to inheriting the same mistakes.

Give it one job: for each acceptance criterion in `spec.md`, determine whether the actual
code satisfies it, and report which do, which don't, and which couldn't be determined from
the diff alone. Ask it to flag anything in the diff that isn't traceable to a task in
`tasks.md` — that's often where undiscussed scope crept in.

## Without subagents

Do the same check yourself, but deliberately, not as a continuation of the implementation
work:
1. Set aside the mental model of "how I built this" and re-read `spec.md`'s acceptance
   criteria as if seeing them for the first time.
2. For each one, look at the actual resulting code or behavior — don't reason from memory of
   what you intended to write.
3. Note anything that can't be confirmed this way rather than assuming it's fine because the
   build succeeded.
4. **[PROPOSAL — untested in practice]** Concretely: write down, per acceptance criterion,
   one thing that would have to be true in the code for it to pass — then go find that exact
   thing (a line, a test, a log) rather than asking "does this seem right." A checklist you
   fill from evidence is harder to rubber-stamp than a mental walkthrough. This technique has
   not itself been validated against a real failure case — treat it as a starting point to
   try, not a proven fix for the fallback's weaker independence.

This is weaker than an isolated subagent (same session, same blind spots), but it's still
meaningfully different from "it compiled, ship it" — the human review step and an honest
pass through this checklist compensate for what independence would otherwise catch.

## verify.md template

```markdown
# Verify: <Feature Name>

## Verification method used
- [ ] Independent subagent (narrow context: spec/plan/tasks/diff only, no conversation history)
- [ ] Same-session deliberate re-read (no subagent capability available)
State which, and why — this materially affects how much confidence the verdict below
deserves. If a subagent was used, note whether it plausibly had access to anything beyond
what it was given (e.g. full filesystem access in the same sandbox) — that's a real
limitation to flag, not an implementation detail to omit.

## Acceptance criteria check
- [x] AC-1 — <criterion> — confirmed: <how>
- [x] AC-2 — <criterion> — confirmed: <how>
- [ ] AC-3 — <criterion> — NOT satisfied: <what's missing>

## Traceability check
- Every task in tasks.md maps to a requirement: yes / no (list any that don't)
- Any code in the diff not traceable to a task: none / list them

## Drift notes
Anything discovered during Implement that changed Plan or Tasks after the fact, and whether
those files were updated to match reality.

## Verdict
PASS — all acceptance criteria confirmed, no unexplained diff.
or
NOT YET — list what's outstanding before this can be called done.
```

## Do not report complete on a partial verify

If any acceptance criterion is unconfirmed or failing, the feature is not done, regardless of
how much of `tasks.md` is checked off. Report the gap plainly rather than rounding up — a
task list that's 100% checked but a `verify.md` that's NOT YET is the state SDD exists to
make visible instead of hidden.

## After NOT YET: remediate and re-Converge

**[PROPOSAL — theoretical, not validated through a full cycle]** A `NOT YET` verdict isn't
the end of the phase — it's a punch list. Once addressed:
1. Fix only what verify.md flagged — resist the urge to also "improve" unrelated things,
   which would itself need its own traceability check.
2. Re-run Converge on the changed surface, not the whole feature from scratch — but do
   re-check any acceptance criterion the fix could plausibly have affected, not just the one
   it targeted.
3. Update `verify.md` in place (don't leave the stale NOT YET as the only record) with what
   changed and the new verdict.
If the same acceptance criterion fails NOT YET twice, treat that as a signal the underlying
plan or task breakdown may be wrong, not just the implementation — consider whether this
needs to go back to Plan rather than another Implement pass.
