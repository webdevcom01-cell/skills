# Evals for algorithmic-art

This is the first eval set for `algorithmic-art` (`07-izlazni-formati/algorithmic-art`).
No prior `evals.json`/`evals/README.md` existed for this skill and no baseline
with-skill-vs-without-skill run has been performed, so no pass-rate claim is attached
here or in the skill's frontmatter. These are 6 cases, first pass, nothing more.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
Each case targets one distinct, high-signal part of `SKILL.md` rather than a generic
"does it make something pretty" probe:

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Two-phase structure and STEP 0 — philosophy-first, then read `templates/viewer.html` before any HTML, even when the user asks to skip straight to code | "This happens in two steps" intro, "⚠️ STEP 0: READ THE TEMPLATE FIRST ⚠️" |
| 2 | FIXED vs VARIABLE template sections — refusing to touch the seed-navigation controls or switch to a dark theme, while allowing algorithm/parameter customization | "CRITICAL: WHAT'S FIXED VS VARIABLE" section, STEP 0's Avoid/Follow lists |
| 3 | Seeded randomness / reproducibility — `randomSeed(seed)` + `noiseSeed(seed)` and why seed navigation depends on it | "Seeded Randomness (Art Blocks Pattern)" code block, "Reproducibility" bullet, "Seed Navigation" requirement |
| 4 | Conceptual-seed subtlety vs. an explicit, literal, labeled user request ("giant spiral labeled Fibonacci") | "DEDUCING THE CONCEPTUAL SEED" section |
| 5 | Craftsmanship-phrase repetition and the mandatory 4-6 paragraph philosophy length, tested against an under-length draft | "Articulate the philosophy (4-6 paragraphs...)", "Emphasize craftsmanship REPEATEDLY" |
| 6 | Output-format completeness — one self-contained HTML artifact, no separate `.js`/`.css` files | "OUTPUT FORMAT" section, "Single Artifact Structure", `templates/generator_template.js` resource note |

Every prompt is self-contained: no case references "the artifact you made earlier,"
a prior turn, or any file the user hasn't been given. A solver with only the prompt
text and `SKILL.md` open should be able to answer each one without outside context.

### Grounding discipline

A prior review of this repo identified grounding hallucination — an `expected_output`
asserting something that sounds plausible but is not actually written in the target
`SKILL.md` — as the #1 defect category across skills. To avoid repeating that here,
every quoted or paraphrased claim in `expected_output` below was checked against the
literal text of `SKILL.md` (`07-izlazni-formati/algorithmic-art`) before being included:

- Anything inside `"double quotes"` in an `expected_output` is a verbatim substring of
  a line (or contiguous lines) in `SKILL.md`, confirmed with an automated
  whitespace-normalized containment check against the source file — not retyped from
  memory. Markdown emphasis markers (`**`) and the section's own bullet/numbering are
  preserved exactly as they appear in the source.
- Anything paraphrased (e.g. "FIXED vs VARIABLE," "the conceptual-seed subtlety
  principle") is named after a section or requirement that literally exists in
  `SKILL.md` — never invented, and never a "best practice" imported from outside the
  skill text.
- Case 4 deliberately sits at a point of tension in the skill (an explicit, literal
  user instruction vs. the skill's stated preference for subtle, non-announced
  references). The `expected_output` does not resolve this by inventing a rule that
  isn't there ("labels are forbidden" appears nowhere in `SKILL.md`); instead it
  requires the agent to surface the tension explicitly, which is the one thing the
  quoted text actually supports.
- No case tests anything about `templates/viewer.html`'s or
  `templates/generator_template.js`'s actual file contents, since those files were not
  supplied alongside `SKILL.md` for this eval-writing pass — only what `SKILL.md`
  itself says about how to use them.

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, then write the eval around it — not the other way around.

## How to run

There is no packaged harness for this skill yet. Until one exists, run each case by
hand:

1. Start a fresh session with `algorithmic-art` loaded and no prior conversation state
   (a fresh chat with the skill's `SKILL.md` — and ideally `templates/viewer.html` —
   available, since several cases specifically probe whether the agent reads/respects
   that template).
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is written to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A response that produces
   visually striking art but skips STEP 0, silently reskins the FIXED seed controls,
   or forgets `noiseSeed()` should be scored as a failure on that expectation even
   though the output "looks like" algorithmic art — these evals exist to catch process
   and discipline failures the skill's explicit rules call out, not to grade
   aesthetics.

## Interpreting results

- **Cases 2, 3, and 6** test requirements SKILL.md marks as fixed/critical constraints
  ("FIXED (always include exactly as shown)," "ALWAYS use a seed," "This is a single
  artifact... Everything inline"). A failure on any expectation in these cases means
  the output would actually misbehave — a broken seed-navigation feature, a UI that
  violates the template contract, or an artifact that doesn't run standalone — not a
  matter of taste.
- **Cases 1 and 5** test whether the two-phase process and its stated quality bars
  (paragraph count, craftsmanship-phrase repetition, reading the template first) are
  followed even under user pressure to shortcut them. A failure here means the skill's
  explicit process was skipped to satisfy a surface-level request for speed.
- **Case 4** tests judgment under a stated tension rather than a clean rule violation —
  whether the agent notices and names the conflict between "without announcing itself"
  and an explicit "unmistakable... label" request, instead of silently picking one side
  and pretending there was no conflict. This is the most interpretation-dependent case
  in the set; graders should treat "acknowledges the tension" as the pass bar, not
  "refuses the literal label" (SKILL.md does not say labels are forbidden).
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas
  above, not as proof the skill improves output quality overall — that would require a
  paired with/without run that has not been done for this skill.
