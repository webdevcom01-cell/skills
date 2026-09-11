---
name: sdd-workflow
description: "Implements a complete Spec-Driven Development (SDD) workflow for code changes: Constitution, Specify, Clarify, Plan, Tasks, Implement, independent Converge/Verify — human approval between phases, verification done separately from implementation. Use for any new feature, module, or non-trivial code change needing discipline over ad-hoc prompting. Triggers: spec driven development, SDD, napravi spec za X, hocu SDD tok, specify plan tasks, constitution za projekat, planiraj pre nego sto pises kod, EARS notacija. Scales rigor to change size — trivial fixes get a lightweight task, features get the full flow, regulated work (fiscalization, payments, compliance) gets the full flow plus mandatory EARS. Do NOT use for whole-product ideation from a raw idea (use idea-to-project, which can call this skill for BUILD), for scaffolding AgentStack agents (use agent-scaffolder), or for a human-facing RFC/decision doc with no code gate (use doc-coauthoring)."
---

# Skill: sdd-workflow
*Version: 1.6 — updated 2026-09-07 (Converge worktree-isolation guidance, Plan-phase
environment-capability check with explicit missing-test-infrastructure flagging for Regulated
rigor, a proposed environment-NOT-YET handoff.md, a Step 0 self-check note, and an explicit
UC-1/2/3 out-loud decision requirement, from real-repo validation on `zalihe-app` and
`agent-studio`).*

## Trigger

Use this skill when someone wants a code change built with a written, approved specification
driving it — not just a prompt and whatever comes back. Typical openers:
- "hoću SDD tok za ovu fičeru"
- "napravi spec pre nego što počneš da kodiraš"
- "dodaj [fičeru] u postojeći projekat, ali uradi to kako treba"
- "constitution za ovaj repo"

Do NOT use this skill for:
- Whole-product ideation starting from a raw idea, or a non-code deliverable (dashboard,
  document, deck) — use `idea-to-project`; it can call into this skill for the BUILD step
  when the deliverable is specifically a code change in an existing or new repo.
- Scaffolding a new AgentStack agent — `agent-scaffolder` already implements an equivalent,
  more specialized flow for that exact architecture.
- Writing a human-facing RFC/decision doc with no code to implement — use `doc-coauthoring`.
- A one-line fix with no real ambiguity — just do it, then still run CONVERGE (Step 7) so it
  doesn't silently skip verification.

## What This Skill Does

Six phases, each producing a visible file or an explicit approval, so a feature can't quietly
slide from "sounds good" straight into unreviewed code:

```
CONSTITUTION → SPECIFY → CLARIFY → PLAN → TASKS → IMPLEMENT → CONVERGE
   (once)       (what)    (gaps)   (how)  (steps)   (code)     (proof)
```

The rule that makes this different from ad-hoc prompting: **every phase produces a file, and
no phase starts until the previous one is explicitly approved by the person.** If the agent
silently jumps from "sounds good" to writing code, or verifies its own work in the same
reasoning pass that wrote it, this skill hasn't been followed — no matter how good the
result looks.

---

## STEP 0 — Task List

Call `TaskCreate` for each phase before starting (skip phases Step 1 rules out):
- "Odredi nivo rigoroznosti"
- "Constitution (ili potvrdi da već postoji)"
- "Specify + Clarify"
- "Plan"
- "Tasks"
- "Implement"
- "Converge / Verify"

Mark each `in_progress` before starting, `completed` when done.

**This step is easy to silently skip while still following every other step correctly** — a
real earlier run of this skill wrote a complete, well-formed spec/plan/tasks/verify sequence
with no `TaskCreate` call anywhere in it, and the miss was only found later by grepping the
session transcript for tool calls, not by re-reading the produced files (which looked identical
either way). If there's any doubt whether Step 0 actually happened for the current run — not
whether it was intended to, whether it actually did — check with `TaskList` rather than assuming
from memory of having meant to call it.

## STEP 1 — Decide the rigor level

Read `references/rigor-scaling.md` for the full decision table. In short:
- **Trivial** (1–2 files, no new dependency, no new user-visible behavior) → skip straight to
  a one-line task in Step 6, implement, then still run Step 7 Converge.
- **Feature-sized** (new module, new endpoint, touches multiple files or subsystems) → run the
  full flow below.
- **Regulated/safety-critical** (payments, fiscalization/ESIR, tender compliance, anything
  touching real money, personal data, or a legal obligation) → full flow, and EARS notation
  becomes mandatory in Specify (see `references/specify-and-clarify.md`).

State which level was picked and why, in one sentence, before proceeding — this is the
person's chance to override before any file gets written.

## STEP 2 — CONSTITUTION (once per project, rarely revisited)

Read `references/constitution.md`. In short: this skill does **not** create a separate
`constitution.md`. It reads and extends the project's existing `CLAUDE.md` (creating a minimal
one if none exists), because a second source of truth for the same rules is how constitution
and code drift apart in practice. Keep it short — this phase adds to `CLAUDE.md`, it doesn't
rewrite it.

- **Greenfield** (new project/repo): ask for stack, non-negotiables, and any compliance
  constraints; write them into `CLAUDE.md`.
- **Brownfield** (existing code, which is the common case here): read the existing structure
  and conventions first, propose additions to `CLAUDE.md` from what's actually there, and ask
  the person to confirm or correct — don't just ask questions cold.

Skip this step entirely if `CLAUDE.md` already documents the relevant conventions — re-reading
it is enough.

## STEP 3 — SPECIFY + CLARIFY

Read `references/specify-and-clarify.md` for the template, the EARS module, and the UC-1/UC-2/UC-3
concrete-example pattern. Write `specs/<feature-slug>/spec.md`. This is the "what and why," with
no implementation detail — acceptance criteria must be concrete enough to check later, not "looks
good."

**State out loud, in one sentence, whether UC-1/UC-2/UC-3 applies to this spec's real-logic
requirements — yes or no, not silence.** Two separate real runs of this skill skipped the pattern
entirely for requirements that clearly had real logic (a variance calculation, a status-gating
rule) with zero discussion either time — the miss never showed up as a defect (Plan's own review
caught the resulting bugs anyway), but that's not something to rely on happening again. This
mirrors the existing "state the rigor level out loud" rule in `rigor-scaling.md`: a recommendation
that's easy to silently skip needs to become an explicit decision instead, not a stronger
requirement — "no, this requirement is simple enough to skip it" is a completely fine answer, as
long as it's said, not defaulted into.

Before moving on, ask clarifying questions about anything the spec leaves ambiguous. This is the
single highest-leverage step for preventing drift later — underspecification here is the most
common reason an agent goes off the rails during implementation. Get explicit approval on
`spec.md` before Step 4.

## STEP 4 — PLAN

**Before writing anything, do a quick environment-capability check** — a few direct probes, not
a research project: can this environment actually reach whatever the feature will need (a
database connection/credentials, a package registry, a deploy target)? Does the repo already
have a migration/schema tool configured, and does it have a prior baseline (existing migrations)
or none? Is there a test runner installed? State findings in one or two sentences before
proceeding — don't let Plan assume access or tooling that Implement will discover is missing.
This exists because assuming DB access or a migration baseline that turns out not to be there is
exactly the kind of thing that should shape the plan (e.g. "commit the schema change, but the
actual migration is a manual step, flagged as a risk") rather than surface for the first time
mid-Implement, when changing course costs more.

**If rigor is Regulated and the repo has no test framework at all** (no runner installed, no
`test` script), name this explicitly as a risk in `plan.md`'s Risks section, not just in the
capability-check sentence — real business logic (a calculation, a status/gating rule) shipping
with zero automated regression protection is a materially different risk at Regulated rigor than
at Feature-sized, since a wrong answer there has real-world consequences. This is a flag, not a
fix: naming the gap is in scope for this skill, bootstrapping a test framework for the target
repo is a product decision for that repo and stays out of Plan's scope.

Read `references/plan.md`. Write `specs/<feature-slug>/plan.md`: architecture, data model,
interfaces, affected files, and the risks worth flagging before code exists. This is the "how" —
if `spec.md` mentions a technology choice or a file path, that's a sign it belongs here instead.
Get approval before Step 5.

## STEP 5 — TASKS

Read `references/tasks.md`. Write `specs/<feature-slug>/tasks.md`: an ordered, atomic checklist
where each task traces back to a specific requirement or acceptance criterion from `spec.md`.
A task that can't name which requirement it satisfies is probably scope creep — flag it rather
than quietly including it.

## STEP 6 — IMPLEMENT

Work through `tasks.md` one task at a time, checking each box as it's done. For anything beyond
a couple of tasks, check in with the person after a meaningful chunk rather than after every
single box — momentum matters, but silent scope changes don't get to happen here either: if
reality forces a change to the plan or tasks, update those files and say so, the same rule
`idea-to-project` already follows for its own spec.

## STEP 7 — CONVERGE / VERIFY

Read `references/converge-and-verify.md`. This is the step most SDD tooling skips entirely —
verification done by someone other than the implementer, because an agent checking its own
work shares all its own blind spots. Write `specs/<feature-slug>/verify.md`:

- **If subagents are available** (Claude Code with the Task tool): spawn an independent verifier
  with only `spec.md`, `plan.md`, `tasks.md`, and the actual diff — not the conversation that
  produced them — and have it check the implementation against the spec's acceptance criteria.
- **If no subagents are available**: do the same check yourself, but deliberately — re-read
  `spec.md`'s acceptance criteria fresh, one at a time, against the actual code, rather than
  trusting that "the build finished" means "the spec is satisfied."

**Isolate the verifier's filesystem when implementer and verifier would otherwise share one
live working directory** (a device-bridge shell to a real machine, a single-checkout sandbox) —
a subagent given only spec/plan/tasks/diff is still not independent if it can see the
implementer's scratch files, uncommitted future edits, or other leftover state in that same
directory. Concretely: commit the implementation locally first (even if pushing comes later),
then `git worktree add <verifier-path> <commit>` and point the verifier there instead of the
main working tree — its view is then exactly what's in that commit, nothing more. Symlink (don't
copy) `node_modules` into the worktree if present, since it's untracked, expensive to reinstall,
and not itself part of what's being verified. Remove the worktree (`git worktree remove`) once
verify.md is written. Skip this when the repo isn't git-tracked, or when implementer and
verifier already run in genuinely separate environments (e.g. distinct sandboxes) — no need to
layer worktree isolation on top of isolation that already exists.

**When a NOT YET verdict is caused by an environment/tooling gap rather than a code defect**
(missing credentials, no network from this environment, a tool or runtime that isn't
installed/reachable) — write `specs/<feature-slug>/handoff.md` alongside `verify.md`: one line
per blocker naming exactly what a human needs to do to unblock it (the specific credential,
command, or access to grant), not a restatement of the code problem. This is distinct from a
code-defect NOT YET, which goes through the normal remediate-and-re-Converge loop instead —
`handoff.md` exists for the case where no amount of further reasoning in this session closes the
gap. **[PROPOSAL — not yet exercised through a real NOT YET-by-environment case]**: this
technique is a reasonable-looking idea, not yet validated by an actual run where it mattered —
treat it as a starting point to try, the same caveat `converge-and-verify.md` already carries for
its own untested techniques.

Do not report the feature complete until `verify.md` shows every acceptance criterion checked
against the real result.

---

## Constraints and Rules

1. **The spec file is mandatory, even for features that feel obvious.** Skipping it because
   the shape "seems clear" is exactly how specs stop driving code and become decoration.
2. **No phase auto-chains without explicit approval.** An agent that runs Specify→Plan→Tasks→
   Implement in one uninterrupted pass has not used this skill, regardless of file names.
3. **Verification is not self-verification.** Converge must not be done by the same reasoning
   pass that wrote the implementation — use a subagent when available, a deliberately fresh
   re-read when not.
4. **No invented data, APIs, or dependencies.** If Plan assumes something that turns out not to
   exist, stop and update Plan — don't paper over it in Implement.
5. **Constitution lives in `CLAUDE.md`, never a duplicate file.** Two sources of truth for the
   same rules is how they drift apart.
6. **Rigor scales down, not away.** Even a trivial change still gets a Converge pass (Step 7) —
   the thing that's allowed to shrink is Specify/Plan/Tasks, never verification.