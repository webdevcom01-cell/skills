# Evals for pptx

This is the skill's first eval set: 6 cases, no baseline claim attached, because no
with-skill-vs-without-skill baseline run was performed to produce one.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
`pptx` (`07-izlazni-formati/pptx/SKILL.md`) is dense with file-corrupting footguns —
specific option names and constants that, gotten wrong, produce a `.pptx` PowerPoint
refuses to open or silently discards a chart from. This set targets six of the
highest-severity, most concretely checkable rules rather than a generic "can it build
a deck" probe:

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Hex-color format (`"FF0000"`, never `#`, never 8 digits) and shadow-offset sign (`angle: 270` + positive `offset` for an upward cast, never negative) | "Creating with pptxgenjs — gotchas" bullets 2 and 4 |
| 2 | Combo-chart secondary-axis trap — `valAxes`/`catAxes` both required, two entries each, when a series uses `secondaryValAxis`/`secondaryCatAxis` | "Creating with pptxgenjs — gotchas," the `secondaryValAxis`/`secondaryCatAxis` bullet |
| 3 | Stacked bar/column `dataLabelPosition` allowlist (`ctr`, `inEnd`, `inBase`) vs. the file-corrupting `outEnd` | "Creating with pptxgenjs — gotchas," the stacked-chart `dataLabelPosition` bullet |
| 4 | `pres.layout` must be set before adding slides; default canvas is `LAYOUT_16x9` (10" × 5.625"), not 13.3" wide; off-canvas coordinates are written, not clamped, and the shape just doesn't appear | "Creating with pptxgenjs — gotchas," first bullet |
| 5 | Design "Avoid" list — accent stripes on a card edge are explicitly named AI-slop and must be replaced with a tint, shadow, or icon | "Avoid (Common Mistakes)," the accent-lines and decorative-color-bars/accent-stripes bullets |
| 6 | Mandatory QA order (Content QA → File QA → Visual QA) for a template-derived deck: `--original` is required on `validate.py`, and a QA-unreliable font (Georgia) means the visual preview's apparent text-fit can't be trusted | "QA (Required)" section — Content QA, File QA, Visual QA — plus the Typography section's QA-unreliable-fonts list |

Every prompt is self-contained: no case references "this conversation," a prior turn,
or an unstated file that wasn't described inline. A solver with only the prompt text
and `SKILL.md` open should be able to answer each one.

### Grounding discipline

A prior review of skills in this repo flagged grounding hallucination as the #1 defect
category in eval sets — `expected_output` text that sounded plausible but wasn't
actually written anywhere in the target `SKILL.md`. To avoid that here:

- Every claim in `expected_output` traces to a specific, quotable line in `pptx`'s
  `SKILL.md`. Option names (`color`, `angle`, `offset`, `valAxes`, `catAxes`,
  `secondaryValAxis`, `secondaryCatAxis`, `dataLabelPosition`, `outEnd`, `pres.layout`,
  `LAYOUT_16x9`, `LAYOUT_WIDE`, `--original`) and constants (`"FF0000"`, `270`, `10" ×
  5.625"`, `13.3" × 7.5"`) are copied verbatim from the source, not reconstructed from
  memory of how `pptxgenjs` "usually" works.
- Every quoted sentence inside `expected_output` was checked against the literal text
  of `SKILL.md` before being included (markdown bold/backtick/italic markers stripped
  for the comparison, since those are formatting, not content) — see the verification
  method below.
- No case invents a rule that sounds reasonable but isn't in the file (e.g. no case
  claims a specific EMU conversion factor, a specific `validate.py` exit code, or a
  numeric contrast ratio — none of those are stated in `SKILL.md`).
- Case 6 deliberately combines three separate SKILL.md requirements (template grep,
  `--original`, QA-unreliable-font caveat) into one scenario because they only bite
  together on a realistic task — "finish a deck built from a template, using a font
  outside the safe list" — not because the case is padding out weaker single-rule
  cases with unrelated claims.

**Verification method used while building this set:** every quoted string in
`expected_output` was checked with a script that strips `**`/`` ` ``/`*` markdown
markers from both the quote and `SKILL.md` and asserts the quote is a literal substring
of the stripped source. All quotes passed. (One quote — "Without them pptxgenjs writes
axis ids it never declares..." — initially flagged as a near-miss because the source
italicizes "ids" with single asterisks (`axis *ids*`), which the first pass of the
strip regex didn't catch; re-checking confirmed the underlying text matches exactly.)

## How to run

There is no packaged harness in this skill for `evals.json` yet. Until one exists, run
each case by hand:

1. Start a fresh session with `pptx` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A response that gets the
   general shape right but slips on one option name or constant (e.g. uses `"#FF0000"`
   instead of `"FF0000"`, or forgets `--original` on a template-derived deck) should be
   scored as a failure on that expectation even if everything else is right — for a
   file-format skill like this, a single wrong constant is the difference between a
   deck that opens and one that doesn't.

## Interpreting results

- **Cases 1, 2, and 3** test hard file-corruption constraints inside `addShape`/
  `addChart` calls — wrong hex format, a negative shadow offset, a missing axis array,
  or `outEnd` on a stacked chart each independently corrupt the output file per
  `SKILL.md`. A failure on any expectation in these cases means the generated `.pptx`
  would likely fail to open or silently lose a chart — a blocker, not a nitpick.
- **Case 4** tests a silent-failure mode rather than a corruption — the shape is
  written but invisible, with no error PowerPoint or `validate.py` would necessarily
  surface as loudly as a corrupt chart. This makes it easy to miss in review, which is
  exactly why `SKILL.md` calls it out as the first gotcha in the list.
- **Case 5** tests design-taste judgment against an explicit rule (not general
  aesthetics) — the skill names accent stripes as a specific, recognizable
  AI-generated-slide signal and names three approved substitutes. A response that
  either keeps the stripe or invents a fourth alternative not in the text fails this
  case.
- **Case 6** tests process discipline across all three QA passes on a single realistic
  scenario. A response that runs `validate.py` without `--original` on a
  template-derived deck, or that treats a Georgia-titled slide's clean visual QA render
  as proof of fit, has skipped a step `SKILL.md` requires — exactly the failure mode
  that makes a "looks done" deck actually broken or overflowing once opened in real
  PowerPoint.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six
  areas above, not as proof the skill helps overall.
