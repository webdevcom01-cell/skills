# Evals for slack-gif-creator

This is the skill's first eval set. `slack-gif-creator/SKILL.md` carries no
`evaluation_status` or prior evals claim, so unlike some other skills in this repo there
is no pre-existing baseline number to correct here — these 6 cases are simply the first
ones that exist, with no with-skill vs. without-skill baseline attached (none was run).

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
Each case targets one distinct, checkable rule from `SKILL.md` rather than a generic
"does it make a GIF" probe.

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Dimension and duration requirements differ by GIF type: 128x128 + <3s for emoji GIFs vs. 480x480 for message GIFs, with no stated duration cap for the latter | "Slack Requirements" — Dimensions and Parameters lists |
| 2 | Drawing a "star emoji GIF" with PIL primitives (`draw.polygon` / `draw_star`) instead of an emoji font or an assumed pre-packaged graphic | "Don't use: Emoji fonts..." + "It does NOT provide" list + "Drawing from Scratch" / Frame Helpers |
| 3 | Correcting a naive `width=1` outline per the explicit line-thickness rule | "Making Graphics Look Good" — "Use thicker lines" |
| 4 | Recognizing upload ambiguity ("make this into a GIF") instead of silently assuming "use directly" or "use as inspiration" | "Working with User-Uploaded Images" + "Note on user uploads" |
| 5 | Optimization is conditional on being asked, not a default; contrasts an un-optimized build with a follow-up shrink request that applies named techniques | "Optimization Strategies" — the "Only when asked..." rule and its 5 named methods |
| 6 | Bounce animation implemented with the exact named easing functions (`ease_in` fall, `bounce_out` landing) and per-frame gravity, not invented/generic easing | "Animation Concepts" — Bounce + "Easing Functions" available list |

Every prompt is self-contained: each states everything a solver needs (including, for
case 5, both turns of the exchange inline) without depending on prior conversation
state, so a solver with only the prompt text and `SKILL.md` open can answer it.

### Grounding discipline

This repo's skills were previously flagged for grounding hallucination — evals whose
`expected_output` asserted things that sounded plausible but were not actually written
in the target `SKILL.md` — as the #1 defect category found in a prior review. To avoid
repeating that here, every quoted or paraphrased claim in `expected_output` below was
checked against the literal text of `SKILL.md`
(`07-izlazni-formati/slack-gif-creator/SKILL.md`) before being included:

- Anything inside `"double quotes"` in an `expected_output` is a verbatim substring of a
  line in `SKILL.md` (markdown emphasis markers and backticks stripped for the
  comparison — e.g. `**Don't use:**` and `` `width=2` `` compare as `Don't use:` and
  `width=2`, since those are formatting, not content). This was verified
  programmatically against the source file, not just by eye.
- Case 1's claim that message GIFs have *no* stated duration cap is an absence claim,
  not a positive quote: `SKILL.md`'s "Parameters:" list under "Slack Requirements"
  contains exactly one `Duration:` line, and it is textually scoped to "for emoji
  GIFs" — no second Duration line or equivalent exists anywhere else in the file for
  message GIFs. The eval expectations ask the solver to *not* invent one, not to
  produce a quote for something that isn't there.
- Nothing paraphrased invents a rule, a numeric value, or a function name that isn't
  literally present — e.g. the easing names in case 6 (`ease_in`, `bounce_out`) are
  copied from the "Available:" list in the "Easing Functions" section, not assumed from
  general animation knowledge.

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, then write the eval around it — not the other way around.

## How to run

There is no packaged harness in this skill for `evals.json` yet. Until one exists, run
each case by hand:

1. Start a fresh session with `slack-gif-creator` loaded and no prior conversation
   state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript or generated
   code, not a subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A case that produces a
   good-looking GIF but fails one discipline check (e.g. it uses `width=1` outlines
   anyway, or it proactively shrinks colors nobody asked to shrink) should be scored as
   a failure on that expectation even if the visual result is fine — these evals exist
   to catch the specific rule violations `SKILL.md` calls out, not to grade aesthetics.

## Interpreting results

- **Cases 2, 3, and 6** test concrete implementation rules (no emoji fonts / no assumed
  pre-packaged graphics, minimum line width, exact named easing functions for bounce).
  A failure here means the generated code or asset violates something `SKILL.md` states
  outright, not a matter of taste.
- **Cases 1 and 5** test scope discipline — using the right dimensions/duration for the
  right GIF type, and only optimizing when asked. A failure here means the skill
  over-applies a rule (e.g. capping a message GIF's duration when none is specified, or
  optimizing a GIF nobody asked to shrink) or under-applies it (missing the emoji
  duration cap, or not optimizing with named techniques once asked).
- **Case 4** tests whether the skill surfaces an explicit ambiguity it is told to check
  for, rather than silently resolving it. A failure here (proceeding straight to a
  finished GIF without asking) means the skill produced a plausible-looking result while
  skipping a judgment call `SKILL.md` explicitly calls out.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas
  above, not as proof the skill helps overall.
