# Evals for doc-coauthoring

This is the skill's first eval set: 6 cases, no baseline claim attached, because no
with-skill-vs-without-skill baseline run has been performed. `doc-coauthoring` is an
official Anthropic skill, written entirely in English, so this eval set is written in
English too rather than following the mixed-language convention used elsewhere in this
repo.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
Each case targets one distinct, high-signal part of the skill's 3-stage workflow
(Context Gathering → Refinement & Structure → Reader Testing) rather than a generic
"does it work" probe.

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Trigger recognition ("design doc") and the mandatory up-front offer of the 3-stage workflow, with all three stages named and explained before assuming a mode | "When to Offer This Workflow" — Trigger conditions + Initial offer |
| 2 | Stage 1's specific, non-generic exit condition — contrasting a still-basic clarifying question against an edge-case/trade-off question | Stage 1, "Exit condition" |
| 3 | Stage 2 Step 3 (Curation) — parsing freeform, non-numbered user feedback instead of demanding the "Keep/Remove/Combine" numbered format | Stage 2, Step 3: Curation |
| 4 | The "3 consecutive iterations, no substantial changes" quality-check trigger during Iterative Refinement | Stage 2, Step 6 → "Quality Checking" |
| 5 | Reader Testing in a sub-agent-available environment — running the test autonomously (predict questions, invoke sub-agent with doc + question only, summarize right/wrong) rather than sending the user to test manually | Stage 3, "Testing Approach" (sub-agent branch) + shared "Exit Condition" |
| 6 | Editing discipline — surgical `str_replace` edits instead of reprinting the whole doc, and never creating an artifact just to list brainstorm options | Stage 2, Step 6 + "Artifact Management" |

Every prompt is self-contained: no case references "this conversation," a prior turn,
or an unstated filesystem path. A solver with only the prompt text and `SKILL.md` open
should be able to answer each one.

### Grounding discipline

Grounding hallucination was flagged as the #1 defect category in a prior review of this
repo's eval sets — cases whose `expected_output` asserted things that sounded plausible
but weren't actually written anywhere in the target `SKILL.md`. To avoid repeating that
here, every quoted claim in `expected_output` below was checked against the literal text
of `SKILL.md` (07-izlazni-formati/doc-coauthoring) with a `grep -F` verbatim-substring
check before being included:

- Anything inside `'single quotes'` in an `expected_output` is a verbatim substring of a
  line in `SKILL.md` (bold-markdown asterisks stripped for the comparison, since those
  wrap only part of some sentences — e.g. `**If user gives freeform feedback**` — and are
  formatting, not content; no other punctuation was altered except where noted below).
- Two quotes were corrected during verification: `SKILL.md`'s bullet list under
  "Artifact Management" (`Provide artifact link after every change` and
  `Never use artifacts for brainstorming lists - that's just conversation`) has **no
  trailing period** on either line — an initially-drafted period was removed from both
  quotes in case 6 to keep them exact substrings.
- Anything paraphrased (e.g. "the Stage 1 exit condition," "the Quality Checking step")
  is named after a section or step that literally exists in `SKILL.md` — never invented.
- No case invents a rule, a numeric threshold, or a tool name not printed in the file
  (e.g. `str_replace` and `create_file` are both used exactly as named in the skill).

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, then write the eval around it — not the other way around.

## How to run

There is no packaged harness for `evals.json` yet. Run each case by hand:

1. Start a fresh session with `doc-coauthoring` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A response that gets the
   substantive writing advice right but skips a process step (e.g. it starts drafting
   without offering the workflow, or it reprints the whole doc instead of using
   `str_replace`) should be scored as a failure on that expectation even if the rest of
   the response reads well — these evals exist specifically to catch process-discipline
   failures, not to grade prose quality.

## Interpreting results

- **Cases 1, 3, and 6** test whether the skill's specific, worked-example instructions
  are followed under pressure to shortcut them — offering the workflow before assuming a
  mode, parsing freeform feedback instead of demanding a rigid format, and editing
  surgically instead of reprinting. A failure here means the skill produced
  plausible-looking output by skipping a step `SKILL.md` spells out explicitly.
- **Cases 2 and 4** test the skill's two concrete, checkable thresholds — the Stage 1
  exit condition (edge-case/trade-off questions vs. basics) and the 3-consecutive-
  iteration quality check. Both are specific enough that a generic "keep asking
  questions" or "keep iterating" response would fail them.
- **Case 5** tests the environment-dependent branch in Stage 3 (sub-agent path vs.
  manual path) and the shared exit condition. A failure here — sending the user to
  manually test in an environment where sub-agents are explicitly available — means the
  skill picked the wrong branch of its own documented decision point.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas
  above, not as proof the skill helps overall — that would require a paired with/without
  run, which has not been done for this skill.
