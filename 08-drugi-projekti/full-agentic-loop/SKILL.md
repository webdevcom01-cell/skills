---
name: full-agentic-loop
description: "Runs the complete idea-to-live-deploy pipeline for a code project by chaining idea-to-project → sdd-workflow → agentic-loop-engineer, including the manual bridge between them that none of the three handles alone. Use when asked to run the full/complete/unshortened agentic loop chain, or Serbian: pokreni pun lanac, ceo sistem, idea do live deploy-a, agentic loop pilot."
---

# Skill: full-agentic-loop

*Distilled from the first real end-to-end run of this chain (QR Kod Menadžer pilot, 18. sept
2026, `claude/PILOT-runda10-...md` and `claude/PILOT-runda11-...md` in the "loops" project) —
not theory, this is what actually happened and what actually broke.*

## Why this skill exists

Three skills already do real work on their own — `idea-to-project` (idea→spec→build→test→deploy),
`sdd-workflow` (spec-driven code changes), `agentic-loop-engineer` (worktree-isolated,
guardrail-enforced implementation loops). `idea-to-project` already auto-routes code/feature
BUILD work to `sdd-workflow`. **But `sdd-workflow` does NOT itself call `agentic-loop-engineer`
for its IMPLEMENT step — that bridge has to be decided and driven by hand, every time**, and the
task-format translation between them (`tasks.md` → `task_spec.md`) is not automatic either. This
skill is that missing bridge, plus every concrete gotcha found the first time it was actually
driven end-to-end on a real, live-deployed product.

## When to use / not use

Use for: a code idea that should end up **actually live** (a real deployed service, not a chat
artifact) and where the person wants the full discipline — written spec, independent
verification, worktree-isolated implementation — not just "write the code."

Do NOT use for: a non-code deliverable (plain `idea-to-project` handles that alone); a small
change to an already-deployed project that stays within `sdd-workflow`'s own "Trivial" bar (just
use `sdd-workflow` directly, skip `agentic-loop-engineer` — worktree/Maker-Checker overhead
isn't worth it for a 1-2 file change, same reasoning `sdd-workflow` itself uses); a project with
no real deploy target at all (persist as an Artifact instead, per `idea-to-project`'s own DEPLOY
step).

## STEP 0 — Confirm exact skill names before anything else

Call whatever skill-listing mechanism is available and confirm `idea-to-project`, `sdd-workflow`,
and `agentic-loop-engineer` are present under their exact `plugin:skill` names before invoking
any of them. (Found necessary the first time: names can differ by a prefix depending on how they
were installed — confirm first, don't assume.)

## STEP 1 — idea-to-project: IDEA → SPEC

Invoke `idea-to-project` normally through its own STEP 0-2 (task list, idea clarification
questions if ambiguous, real `SPEC.md` file written before anything else). Let it run its own
STEP 3 BUILD-table routing — when Section 5 of its spec names a code/feature/module deliverable
at or above `sdd-workflow`'s Trivial bar, it will itself say to reach for `sdd-workflow`. That's
the cue to move to Step 2 below, not a separate decision you make.

## STEP 2 — sdd-workflow: Constitution → Specify/Clarify → Plan → Tasks

Invoke `sdd-workflow` for the code-level spec/plan/tasks work, through its own phases, with
human approval between phases as it normally requires. State the rigor level out loud (its own
Step 1 rule). Its Plan-phase environment-capability check matters here more than usual, because
Step 3 below is about to actually spawn worktrees that depend on those tools working.

**Bridge decision point (this is the part sdd-workflow doesn't make for you):** once `tasks.md`
exists, decide whether IMPLEMENT should go through `agentic-loop-engineer`'s worktree/Maker-Checker
machinery or just be done directly:
- Use `agentic-loop-engineer` when tasks.md has multiple groupable, independently-checkable units
  of work (the QR pilot grouped 12 tasks into 3 spawns) — the isolation and independent Checker
  are worth the overhead.
- Skip it (implement directly, still run sdd-workflow's own CONVERGE step) for a handful of tasks
  too small/interdependent to usefully split — same Trivial-bar logic sdd-workflow already uses
  for whether to run the full flow at all.

## STEP 3 — agentic-loop-engineer: Implement (only if Step 2 chose this path)

Follow `agentic-loop-engineer`'s own Pre-Flight Checklist and "Verifikacija guardrails-a" step
first — don't skip the guardrail-hook verification even for "just a test."

**Translate `tasks.md` groups into `task_spec.md` files yourself** — one per spawn, each naming
its concrete acceptance criteria traced back to the sdd-workflow `tasks.md` items it covers. This
translation is manual; nothing does it automatically. Then run each spawn through
`spawn-worktree-agent.sh`, its own independent Checker via `prepare-checker-bundle.sh` (fresh
subagent, bundle-isolated — never the Maker's own context), and `circuit_breaker.py` between
iterations, exactly as `agentic-loop-engineer`'s own SKILL.md describes.

## STEP 4 — CONVERGE: independent, not self-verification — non-negotiable

This is the single most important rule in this whole bridge, because it's the one place the
first real run actually got wrong (T12 in the QR pilot was self-verified, an explicit, named
deviation from `sdd-workflow`'s own rule #3 "Verification is not self-verification"). The
second attempt (T13) got it right and is the pattern to repeat:

1. Commit the implementation locally.
2. `git worktree add <isolated-path> <commit-sha>` — physically isolated, not just "a different
   context window."
3. Spawn a fresh `Agent` subagent with **only** the commit hash and that isolated worktree path
   — no exposure to your reasoning, the conversation, or prior narrative. Instruct it to run its
   own real server/tests/HTTP calls and check the spec's acceptance criteria itself, skeptically.
4. Fold its findings into `verify.md`. Remove the worktree when done.

Do not report a feature/task done based on your own smoke-test alone, even if you ran it for
real — real-but-self-verified is still not independent (that distinction is exactly what went
wrong the first time).

## STEP 5 — DEPLOY (idea-to-project's Constraints Rule #7, with the gaps this run found closed)

- Repo must reach a real git host (GitHub) before a hosting platform (Railway etc.) can deploy
  from it. If the repo currently only exists in a worktree/cloud sandbox, transfer it with
  `agentic-loop-engineer`'s `scripts/portable-repo-transfer.sh` (git bundle) — never tar/cp a
  worktree directory (its `.git` is a path-pointer, not portable).
  - **Known gotcha #1:** `git bundle verify` (used internally by both `export` and `import`)
    requires the CURRENT DIRECTORY to already be inside some git repo — run the script from
    inside the source repo (for export) or from inside an existing repo (for import's verify
    step), not from a plain folder. Seen live 3 times across two pilot rounds.
  - **Known gotcha #2:** the script's `import` subcommand only supports a fresh `git clone` into
    a NEW (non-existent) target directory — it has no incremental-sync mode. For transferring new
    commits into a target repo that already exists (e.g. a second round of changes after the
    first deploy), do this manually instead: `git bundle verify <bundle>` (from inside the
    existing repo), `git fetch <bundle-file> <branch>:refs/tmp-incoming`, then
    `git merge --ff-only refs/tmp-incoming`, then `git update-ref -d refs/tmp-incoming` to clean
    up. This still uses the git-bundle mechanism (satisfies the "never tar/cp" rule) even though
    the script itself doesn't offer this mode yet.
- The actual `git push` to the real remote, and any real login/account creation (GitHub, hosting
  platform), stays the human's job, done in their own real terminal/browser — never a
  device-bridge shell (which is a separate, credential-less environment even when it looks like
  "the user's machine") and never by embedding credentials into a URL (this is correctly blocked
  by safety tooling — don't try to route around it, ask the human to do that one step).
- **Before considering DEPLOY done, make sure at least one route is genuinely public and
  unauthenticated** (e.g. `/health` returning a bare status/count, nothing sensitive) — found
  necessary because every auth-gated route requires a human in the loop for live verification,
  every single time, which doesn't scale past the first deploy. If the project's spec doesn't
  already have one, add it as a small spec amendment (REQ/AC pair) before or right after first
  deploy, through `sdd-workflow`'s own amendment pattern (see "Trivial bar" reasoning in Step 2),
  with its own independent Converge pass (Step 4).
- After deploy, verify live — real HTTP calls (WebFetch/browser) against the real production URL,
  cross-checked against an independent signal where possible (e.g. the hosting platform's own
  deployment metadata showing the exact commit hash that's live, not just "the push succeeded").

## STEP 6 — Close the loop

Write a forensic pilot report to wherever this project's durable docs live, following whatever
naming convention already exists there (e.g. `claude/PILOT-runda<N>-<slug>.md` in the "loops"
project) — phase-by-phase account, every real bug found and fixed, an honest self-evaluation
(did CONVERGE actually stay independent this time, per Step 4?), and any new gotchas found that
aren't already listed in Step 5 above (update this skill file itself if a new one is found —
don't let the same gotcha get rediscovered a third time). If the person wants stronger assurance
on the claims produced, offer (don't force) an `adversarial-verify` pass at `standard` or `deep`
depth — `quick`/single-refuter runs are triage signals, not confidence.

## Honest limits

This bridge is proven on exactly one real project so far (a small greenfield CRUD-shaped
service). It has not been exercised on: a brownfield codebase, a project needing real multi-user
auth, a database migration, or genuine parallel (simultaneous) worktrees. Treat those as open
risk, not "probably fine by analogy" — the first run of each of those dimensions should be
watched at least as closely as this first run was.