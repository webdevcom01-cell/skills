# Tasks

Write `specs/<feature-slug>/tasks.md`. This breaks Plan into an ordered, atomic checklist
that Implement (Step 6) executes one item at a time.

## tasks.md template

```markdown
# Tasks: <Feature Name>

- [ ] T1 — <atomic, concrete action> (satisfies: REQ-2)
- [ ] T2 — <atomic, concrete action> (satisfies: REQ-1, REQ-3)
- [ ] T3 — <atomic, concrete action> (satisfies: REQ-4)
...
```

## What makes a task atomic

A task is sized right when it can be checked off as a single, reviewable unit — one function,
one endpoint, one migration, one component — not "implement the backend" and not
"add a comment to line 42." If a task description needs "and" to describe what it does, it's
probably two tasks.

## The traceability rule

Every task names which requirement or acceptance criterion (from `spec.md`) it satisfies. A
task that can't name one is a strong signal of scope creep sneaking in during Implement
rather than having been decided during Specify — flag it to the person rather than quietly
including it. This traceability is also what makes Converge (Step 7) possible to do
mechanically: walk the requirements, confirm each has a task, confirm each task's code
actually satisfies it.

## Evidence on checkboxes

When checking off a task, add a short evidence note, not just the checkbox — what you
actually looked at to confirm it's done (a test that passed, a grep result, a manual trace).
An unqualified `[x]` is a claim; the evidence is what makes the claim checkable later,
including by a Converge-phase verifier who wasn't there when the work was done.

## Ordering

Order tasks so that each one leaves the system in a working (even if incomplete) state where
practical — this makes it possible to check in partway through Implement without having
broken the build in the interim. Dependencies between tasks should be explicit in the order,
not left to be discovered mid-implementation.
