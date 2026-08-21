<!-- Part of a derivative work of anthropics/skills@b29e7cf6 (skills/skill-creator), by buky <webdevcom01@gmail.com>, 2026-07-31. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md. -->

# Evals for skill-creator-pro

This skill tells its users to write evals for their skills. Until 2026-07-30 it had
none of its own, and never mentioned either validator (N-20). These are its own.

Neither file is packaged into a `.skill` artifact — `evals/` is excluded at the skill
root by both `scripts/package_skill.py` and `scripts/quick_validate.py`. They live here
for the repository and for anyone running the loop against this skill.

## `evals.json` — model-level suite (5 cases)

Follows the contract in `references/schemas.md`. Every case targets a failure mode
established by the 2026-07-29 audit rather than an invented scenario, per
`platform.claude.com/…/agent-skills/best-practices`: *"This ensures your Skill solves
real problems rather than documenting imagined ones."* The floor is 3 cases (same
source); `enterprise.md` asks for 3–5 representative cases.

## `trigger_queries.json` — description eval set (20 queries)

10 should-trigger, 10 near-miss negatives, per
`agentskills.io/skill-creation/optimizing-descriptions` (~20 queries, 8–10 of each
type, negatives must be near-misses). The negatives come from the trigger-collision
map in §4a of the audit — each one belongs to a specific other skill installed in this
environment, so they test a real boundary rather than an imagined one. Bilingual on
purpose: 20+ installed skills carry Serbian triggers and this one had none (§4a).

### Constraint every query must satisfy (N-47, learned the expensive way)

**Each query must be answerable by a fresh agent with no conversation history and no
assumption about the filesystem.** `run_eval.py` spawns a separate `claude -p` process
per query: there is no prior turn, and the machine is not necessarily yours.

This was measured, not reasoned. On 2026-07-31 two queries from the first version of
this file were run with full transcripts:

- *"napravi mi skill od ovoga sto smo sad radili"* — the agent called **no tool at all**
  and replied that it sees no prior work in the conversation. It cannot trigger, ever.
- *"imam skill za pdf-ove u ~/.claude/skills/pdf-filler…"* — the agent called `Bash`
  five times trying to list a path that did not exist there.

In both cases `run_eval.py` reported `trigger_rate: 0.0` with `inconclusive: false` and
`errors: 0` — full confidence about a question it never actually asked (that is **N-46**,
a separate finding against the tool itself).

Forbidden in a query: reference to the conversation ("what we just did"), to time
("yesterday"), demonstratives with no referent ("this SKILL.md", "this folder"), and
concrete paths (`~/.claude/skills/...`). Preferred: a hypothetical but concrete task —
"a skill that turns meeting notes into a weekly report" — which is specific without
requiring state.

**This applies to negatives too.** A negative that never reaches a skill decision
"passes" for the wrong reason, which is a false green. Ten of the original twenty
queries violated the constraint: seven positives and **three negatives**.

`regression/test_trigger_upiti_su_samodovoljni` enforces the known markers. It is a
heuristic, not proof of self-containment — that only comes from measuring.

Run it with:

```bash
python -m scripts.run_eval --skill-path . --eval-set evals/trigger_queries.json
```

Cost, measured 2026-07-31: **0,108–0,196 $ per call**. The documented default is
20 queries x 3 runs = 60 calls, so roughly **6–12 $** per full pass. Measured in an
environment with 148 slash commands loaded; yours will differ.
