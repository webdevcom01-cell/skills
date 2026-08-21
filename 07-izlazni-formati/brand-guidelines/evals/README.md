# Evals for brand-guidelines

`brand-guidelines` is Anthropic's official brand styling skill
(`07-izlazni-formati/brand-guidelines/SKILL.md`), 73 lines total. It carries no
`evaluation_status` or prior eval claim in its frontmatter, and no `evals/` directory
existed before this one. These are the skill's first evals: 6 cases, no baseline claim
attached, because no with-skill-vs-without-skill baseline run was performed.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
This is a short, fact-heavy skill — four main colors, three accent colors, two font
families, and one point-size threshold, each stated once as a hex code, name, or rule.
There is no branching decision tree or multi-mode workflow to probe (unlike, say,
`agent-architect`), so instead of one case per "mode," each case targets one distinct
fact-or-rule cluster and tests **precise recall** and **correct application** of it,
not just paraphrase:

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Main Colors — all four hex codes and stated purposes; correct choice of Dark vs. Light for text depending on background | "Main Colors" section |
| 2 | Accent Colors — all three hex codes and roles (primary/secondary/tertiary); the "cycle through orange, blue, and green" rotation rule applied to a concrete set of shapes | "Accent Colors" section + "Shape and Accent Colors" feature section |
| 3 | Typography threshold — Poppins for headings "24pt and larger" / "24pt+", tested at a heading exactly at 24pt (inclusive boundary) and one just under it, plus Lora for body text | "Typography" section + "Smart Font Application" / "Text Styling" feature sections |
| 4 | Fallback behavior — "Automatically falls back to Arial/Georgia if custom fonts unavailable," with the heading→Arial / body→Georgia mapping, when Poppins/Lora aren't installed | "Smart Font Application" + "Technical Details > Font Management" |
| 5 | Color implementation mechanism — "Applied via python-pptx's RGBColor class" and "Uses RGB color values for precise brand matching," tested against an agent building a PPTX artifact | "Technical Details > Color Application" |
| 6 | Misapplication scenario — a user asks for the accent orange across body text; correct behavior keeps accents to "Non-text shapes" per the explicit rule and routes body text through "Smart color selection based on background" instead | "Shape and Accent Colors" + "Text Styling" |

Every prompt is self-contained: no case references "this conversation," a prior turn,
or an unstated file. A solver with only the prompt text and `SKILL.md` open should be
able to answer each one.

### Grounding discipline

This repo's skills were already flagged once, in a prior review, for grounding
hallucination as the #1 defect category — `expected_output` text that asserted
plausible-sounding facts (a hex code, a font name, a threshold) that were not actually
written anywhere in the target `SKILL.md`. Because this skill is almost entirely a list
of exact values (hex codes, point sizes, font names), that risk is higher here than for
a process-heavy skill, so the grounding check was done mechanically rather than by eye:

- Every double-quoted phrase inside every `expected_output` in `evals.json` was
  extracted and diffed against the literal text of `SKILL.md` (with backticks and `**`
  emphasis markers stripped, since those are formatting, not content). All 33 quoted
  spans across the 6 cases matched a literal substring of `SKILL.md` verbatim — see
  the "Grounding check" script output below.
- Every hex code that appears anywhere in `evals.json` (`#141413`, `#faf9f5`,
  `#b0aea5`, `#e8e6dc`, `#d97757`, `#6a9bcc`, `#788c5d`) is one of the seven hex codes
  SKILL.md itself defines — no case invents an eighth color or a shade/tint of a listed
  one.
- The 24pt threshold in case 3 uses only the two ways SKILL.md itself states it —
  "24pt and larger" and "24pt+" — never a different number (e.g. "20pt," "18pt") and
  never a stricter comparison ("over 24pt") that SKILL.md doesn't use.
- No case invents a rule the skill doesn't state. In particular, SKILL.md defines only
  two text-size categories (headings 24pt+, and body text) — there is no third
  "subheading" tier — and case 3's `expected_output` says so explicitly instead of
  inventing one for the 20pt example.

**Grounding check** (run against `evals.json` and the target `SKILL.md`):

```
$ python3 -c "... extract every \"quoted\" span from expected_output, normalize
  backticks/markdown, and confirm it is a literal substring of SKILL.md ..."
ALL QUOTES GROUNDED   (33/33 quoted spans matched verbatim)
```

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, quote it exactly, then write the eval around it — not the other
way around.

## How to run

There is no packaged harness for `evals.json` yet. Run each case by hand:

1. Start a fresh session with `brand-guidelines` loaded and no prior conversation
   state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript (a hex code is
   either stated correctly or it isn't; a rule is either applied or it isn't), not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A response that gets four out
   of five color values right but transposes one hex code, or that applies Poppins to
   a 20pt heading, should be scored as a failure on that specific expectation even if
   the rest of the response reads well — these evals exist to catch exact-recall and
   threshold errors, not to grade prose quality.

## Interpreting results

- **Cases 1, 2, and 5** are pure recall-plus-mechanism checks: exact hex codes, exact
  role labels (primary/secondary/tertiary accent), and the exact python-pptx
  `RGBColor` mechanism. Any wrong hex digit, swapped purpose, or invented
  implementation mechanism is a straightforward factual failure — there's no
  interpretation to argue about.
- **Case 3** is a boundary-condition check. The skill states the same threshold twice
  ("24pt and larger" / "24pt+"), and both phrasings are inclusive of 24pt itself. A
  response that excludes the exactly-24pt heading, or that substitutes a different
  number (e.g. "over 20pt"), has misread an explicit, unambiguous line in `SKILL.md`.
- **Case 4** checks that missing fonts are treated as an explicitly anticipated,
  handled case ("Automatically falls back to Arial/Georgia") rather than an error
  state or an excuse to substitute an unlisted font.
- **Case 6** is the one process/judgment case in the set: it checks whether the skill's
  narrow scoping of accent colors to "Non-text shapes" is respected even when a user's
  literal request pushes against it, and whether body text is routed through "Smart
  color selection based on background" instead of a flat accent fill. A response that
  silently complies with painting body copy orange has missed an explicit scope
  boundary the skill states, not just given a stylistic choice a reviewer might
  disagree with.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six
  fact/rule clusters above, not as proof the skill improves output quality overall.
