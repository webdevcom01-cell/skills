# Evals for agent-architect

`agent-architect`'s own frontmatter (`metadata.evaluation_status` in `SKILL.md`, v0.2.0)
claims *"11 evals across 2 iterations (5 + 6), with-skill vs without-skill baseline, both
rounds 100% with-skill pass rate vs 40-42% baseline. See evals/evals.json and
evals/README.md."* No such files exist anywhere in the repo, and no baseline run behind
that claim exists either. That line in the frontmatter is false and should be corrected
or removed independently of this eval set — it is not fixed by adding real evals under
it. These are the skill's first real evals: 6 cases, no baseline claim attached, because
no baseline run was performed to produce one.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
Each case targets one distinct, high-signal part of `SKILL.md` rather than a generic
"does it work" probe:

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Mode 1 (Pattern Selector) — full 4-question decision tree, the mandatory Nivo A/Nivo B question, and citation discipline when no article was fetched in-session | Mode 1 steps 1–4 |
| 2 | Mode 2 (Agent Audit) — criteria-defined-and-listed-before-scoring, the 🔴/🟠/🟡 severity scale, and the requirement for a literal file-quoted citation per criterion | Mode 2 steps 4–7 |
| 3 | Two of the six Hard rules from the SOMA Pass 1.5 audit (Score Analyzer non-determinism; SA-not-in-chain being an architectural change, not an automatic recommendation) | "Hard rules" section, rules 1 and 2 |
| 4 | Write boundaries — the skill refuses to write into `agents/` and redirects to a `.draft.md` proposal in `Insights/proposed-agents/` instead | "Write boundaries" section + Mode 4 step 6 |
| 5 | Mode 4 (DESIGN_SPEC generator) — exact 11-section order, refusal to invent unresolved fields (they go to Open Questions instead, even when the user explicitly asks for guessing), and the pre-generation hard/soft rule check | Mode 4 steps 1–3, 5–7 |
| 6 | Anti-hallucination discipline in Mode 3 — the article-routing table, the ban on reconstructing quotes from memory, and the exact fallback line when a source can't be fetched | Mode 3 steps 2 and 5, "Anti-hallucination disciplina" section |

Every prompt is self-contained: no case references "this conversation," a prior turn,
or an unstated filesystem path. A solver with only the prompt text and `SKILL.md` open
should be able to answer each one, the same constraint `skill-creator-pro`'s eval set
enforces for its trigger queries (there, learned from two queries that could not
trigger at all — N-47 in that skill's own README).

### Grounding discipline

This skill was already flagged once, in an earlier review pass covering a different
batch of skills in this repo, for grounding hallucination as the #1 defect category —
evals whose `expected_output` asserted things that sounded plausible but were not
actually written anywhere in the target `SKILL.md`. To avoid repeating that here, every
quoted or paraphrased claim in `expected_output` below was checked against the literal
text of `SKILL.md` (02-dizajn/agent-architect) before being included:

- Anything inside `"double quotes"` in an `expected_output` is a verbatim substring of
  a line in `SKILL.md` (markdown emphasis markers and backticks stripped for the
  comparison, since those are formatting, not content).
- Anything paraphrased (e.g. "the skill's write boundaries," "the severity scale") is
  named after a section or step that literally exists in `SKILL.md` — never invented,
  and never a "the industry typically does X" filler.
- No case tests the false "11 evals / 100% pass rate" frontmatter claim, or any other
  number not printed in the file. That claim is out of scope for what these evals can
  verify and is called out above instead.

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, then write the eval around it — not the other way around.

## How to run

There is no packaged harness in this skill for `evals.json` yet (unlike
`skill-creator-pro`, which ships `scripts/run_eval.py` for its own trigger-query set).
Until one exists, run each case by hand:

1. Start a fresh session with `agent-architect` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A case that gets the
   substantive recommendation right but fails one discipline check (e.g. it fabricates
   an Anthropic quote it never fetched, or it writes straight into `agents/`) should be
   scored as a failure on that expectation even if the rest of the response is strong —
   these evals exist specifically to catch the discipline failures the skill's hard
   rules and anti-hallucination section call out, not to grade writing quality.

## Interpreting results

- **Cases 3, 4, and 6** test hard constraints (`Hard rules`, `Write boundaries`,
  `Anti-hallucination disciplina`) the skill says it must never violate. A failure on
  any expectation in these cases is a blocker-level regression, not a nitpick.
- **Cases 1, 2, and 5** test process discipline within a mode (ask before recommending,
  list criteria before scoring, defer unknowns to Open Questions instead of inventing
  them). A failure here means the skill produced a plausible-looking artifact by
  skipping a step `SKILL.md` requires — exactly the failure mode that makes an
  advisory/audit skill's output untrustworthy even when it "sounds right."
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline (see the note at the top). Treat it as a
  regression check for the six areas above, not as proof the skill helps overall —
  that would require the kind of paired with/without run `skill-creator-pro` describes
  in its own README, which has not been done for this skill.
