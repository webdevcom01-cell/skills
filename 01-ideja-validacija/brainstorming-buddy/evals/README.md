# Evals for brainstorming-buddy

Phase 5 of the eval-coverage effort (following the pattern used for the 28 skills across
the 4 prior phases, including `skill-creator-pro`). This skill previously had no evals.

## `evals.json` — model-level suite (6 cases)

Every case targets a rule, table row, or threshold actually written in `SKILL.md` —
none are invented. Each prompt is a self-contained hypothetical: no reference to "this
conversation," no timestamps, no disk paths, nothing that assumes state a fresh agent
wouldn't have. A fresh agent with only `SKILL.md` and the prompt should be able to act
on every case.

| # | Targets | Rule cited |
|---|---------|------------|
| 1 | When NOT to Use This Skill | "User has clear plan" row → *Skip to DESIGN or help execute* |
| 2 | Mode Selection + Core Principles | "New project / 'think through'" → Full Mode; "One question at a time — Never overwhelm"; EXPLORE opening "(pick ONE)" |
| 3 | Resume Mode | "continue X" / "where were we" trigger, and the risk of fabricating a "Last time we..." recap when no real checkpoint exists |
| 4 | Session Signals (phase transition) | EXPAND → EVALUATE requires "3+ concrete options" |
| 5 | Recovery Strategies | The frustrated-user line ("I sense we're spinning...") vs. the distinct "Stuck in EXPLORE" (magic wand) and "Going in circles" responses |
| 6 | DESIGN phase structure | "Present in 200-300 word chunks. After each: 'Does this make sense?'" |

Several cases (1, 4, 6) deliberately put an explicit user request ("just get me started,"
"evaluate these two now," "give it to me all at once") in tension with a structural rule
in the skill. These are the cases most likely to catch an agent that optimizes for
literal compliance with the user's last sentence over the skill's process — which is
exactly the failure mode worth catching here, since the skill is a *process* skill, not
a content-generation one.

Case 3 is also a hallucination check: Resume Mode's own template ("Last time we
[summary]... we reached [phase] and decided [key decisions]") is easy to satisfy by
inventing plausible-sounding content when no real prior session exists. The expectations
require the agent to admit it found no checkpoint rather than fabricate one.

### Self-containment constraint

Same constraint as the rest of this library's eval sets: **each prompt must be
answerable by a fresh agent with no conversation history and no assumption about the
filesystem.** None of these 6 prompts reference prior turns, dates, or paths — each
describes a complete, standalone scenario (a specific project, a specific pair of
options already stated in the prompt itself, etc.) so the eval doesn't depend on state
that doesn't exist when a grader spawns a clean process against it.

## Running

This library's harness convention (see `skill-creator-pro/evals/README.md` for the
fuller description) is:

```bash
python -m scripts.run_eval --skill-path . --eval-set evals/evals.json
```

adjusted to wherever `run_eval.py` / the eval harness lives in this repo checkout. Each
case should be graded independently against its `expectations` list — treat every bullet
as a pass/fail check, not a holistic impression. `expected_output` is the target
behavior description; `expectations` are what a grader (human or model) checks against
the actual transcript.

## Interpreting results

- A case fails if **any** of its expectations fail — they're independent, checkable
  claims, not a vibe score.
- Cases 1, 4, and 6 are the highest-value regression signal: they test whether the skill
  holds its process under direct pressure from the user's own words. A skill update that
  makes the agent more "helpful" in the literal sense (comply immediately, skip the
  chunking, skip flagging the option count) can regress these silently — run them after
  any edit to the Mode Selection, Session Signals, or DESIGN sections.
- Case 3 is the one most likely to reveal an agent papering over missing state with
  invented detail. A pass requires an honest "I don't have that" — not a smooth-sounding
  fake recap.
