# Evals for theme-factory

These are the skill's first evals: 6 cases, no baseline claim attached, because no
with-skill-vs-without-skill baseline run was performed to produce one. `theme-factory`'s
own `SKILL.md` frontmatter carries no `evaluation_status` metadata and makes no claim
about existing evals, so unlike some other skills in this repo there is no pre-existing
false claim to flag here — this is simply a from-scratch first pass.

## A note on what could and could not be grounded

`SKILL.md` (07-izlazni-formati/theme-factory) names the 10 available themes and gives
each a one-line description, and it describes the *process* for showing, selecting,
reading, applying, and — when needed — custom-generating a theme. It does **not**
contain the actual per-theme specifications (hex codes, font pairings) — those live in
individual files under the skill's `themes/` directory, which were not available when
this eval set was built. Every case below is therefore grounded only in:

- the 4-step Usage Instructions process (show showcase → ask → wait for confirmation → apply),
- the Application Process's own 4 steps (read the theme file → apply consistently → check
  contrast → maintain identity across all slides),
- the 10 theme names and their one-line descriptions as printed in "Themes Available",
- the "Create your Own Theme" custom-theme path.

No case asserts a specific hex code, specific font name, or any other content that would
only exist inside a `themes/*.md` file. Where a case needs the agent to *use* a theme
file (Case 4), the expectation is that the agent describes reading it — not that a
particular color or font appears in the transcript.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
Each case targets one distinct, explicit rule in `SKILL.md` rather than a generic "does
it work" probe.

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Step 1 — show the showcase as-is; refuse to modify `theme-showcase.pdf` even when asked to crop/brighten a single theme's preview before showing it | Usage Instructions Step 1 |
| 2 | Steps 2-3 — ask which theme, then wait for *explicit* confirmation; naming two liked themes without picking one is not a confirmed selection | Usage Instructions Steps 2-3 |
| 3 | Correct recall of a theme name from the fixed list of 10, matched to its listed one-line description, without inventing a theme or fabricating hex/font specifics | "Themes Available" list (all 10 names + descriptions) |
| 4 | Application Process step 1 — read the actual theme file from `themes/` before applying, rather than improvising colors/fonts from the theme's one-line description | Application Process steps 1-4; "Theme Details" section |
| 5 | Custom theme path — when none of the 10 fit, generate a descriptively-named custom theme and show it for review *before* applying, even if the user asks to skip straight to applying | "Create your Own Theme" section |
| 6 | Consistency requirement — applying a theme to only one slide conflicts with "consistently throughout the deck" / "across all slides" and should be flagged, not silently done | Application Process steps 2 and 4 |

Every prompt is self-contained: no case references "this conversation," a prior turn, or
an unstated filesystem path. A solver with only the prompt text and `SKILL.md` open
should be able to answer each one.

### Grounding discipline

A prior review of this repo flagged grounding hallucination — `expected_output` text
that sounds plausible but is not actually written in the target `SKILL.md` — as the #1
defect category. To avoid repeating that here, every quoted or paraphrased claim in
`expected_output` below was checked against the literal text of `SKILL.md`
(07-izlazni-formati/theme-factory) before being included:

- Anything inside `'single quotes'` in an `expected_output` is a verbatim substring of a
  line in `SKILL.md` (only outer sentence punctuation adjusted for quoting, never the
  wording).
- Anything paraphrased (e.g. "the custom theme path," "the consistency requirement") is
  named after a section or numbered step that literally exists in `SKILL.md` — never
  invented.
- No case states or implies a specific hex code, specific font name, or any other detail
  that would only live in a `themes/*.md` file, since those files were not available to
  ground against. Case 3 stays at the level of theme *names and descriptions* printed in
  `SKILL.md`; Case 4 only requires that the agent describe reading the theme file, not
  that it produce or guess the file's contents.
- Case 2's premise (liking two themes without picking one) is a scenario constructed to
  test the "wait for explicit confirmation" rule — it is clearly a hypothetical prompt,
  not a claim about what `SKILL.md` says.

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, then write the eval around it — not the other way around. If you
later gain access to the `themes/` directory, a natural extension is a case that checks
an applied theme's colors/fonts actually match its theme file — that case cannot be
written responsibly without those files, which is why it is not included here.

## How to run

There is no packaged harness in this skill for `evals.json`. Run each case by hand:

1. Start a fresh session with `theme-factory` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A case that gets the
   substantive theme recommendation right but fails one process-discipline check (e.g.
   it edits `theme-showcase.pdf`, or applies a theme without waiting for explicit
   confirmation, or skips reading the theme file) should be scored as a failure on that
   expectation even if the rest of the response is reasonable — these evals exist
   specifically to catch process-discipline failures the skill's numbered steps call
   out, not to grade writing or design quality.

## Interpreting results

- **Cases 1, 2, and 6** test the skill's explicit sequencing and consistency
  requirements (show unmodified → ask → wait for confirmation → apply consistently
  across all slides). A failure on any expectation here means a step was skipped or
  silently violated, which is the exact failure mode the numbered process exists to
  prevent.
- **Case 3** tests factual recall against a fixed, small, enumerable list (10 theme
  names). A failure here — inventing an 11th theme, or misattributing a description —
  is a straightforward grounding error.
- **Case 4** tests that the skill treats the theme name/description as a pointer to a
  file to be read, not as enough information to freehand colors and fonts.
- **Case 5** tests the custom-theme fallback path specifically for its own
  review-before-apply ordering, distinct from the ordering tested in Case 2.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas
  above, not as proof the skill helps overall.
