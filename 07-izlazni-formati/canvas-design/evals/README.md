# Evals for canvas-design

`canvas-design` (`07-izlazni-formati/canvas-design`, an official Anthropic skill, entirely
in English) had no `evals/` directory before this. These are its first evals: 6 cases, no
baseline claim attached, because no with-skill-vs-without-skill run was performed to
produce one.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
Each case targets one distinct, high-signal part of `SKILL.md` rather than a generic
"does it work" probe:

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | The mandatory two-step process (philosophy `.md` first, then visual expression) even when the user demands the final image immediately | "Complete this in two steps" + "Output only .md files, .pdf files, and .png files." |
| 2 | The FINAL STEP scripted refinement instruction — refine/subtract existing elements, never add new graphics | FINAL STEP section: the scripted "already said" line, "avoid adding more graphics," and the "STOP and instead ask" instruction |
| 3 | Minimal-text / no-overlap / containment requirements under pressure from a long literal text request | CANVAS CREATION: "nothing falls off the page and nothing overlaps... contained within the canvas boundaries with proper margins... non-negotiable" + "MINIMAL TEXT" principle |
| 4 | The sophistication-regardless-of-topic rule, tested against a request for something inherently playful/cartoony | CANVAS CREATION: "even if the user requests something for a movie/game/book, the approach should still be sophisticated... not something that's cartoony or amateur" |
| 5 | The subtle-conceptual-reference discipline, tested against a user naming an explicit literal subject | DEDUCING THE SUBTLE REFERENCE section: "not always literal, always sophisticated" + "only those who know will catch it" |
| 6 | The multi-page option — single page by default, thematically-related-but-distinct pages only when asked | CANVAS CREATION: "unless asked for more pages" + MULTI-PAGE OPTION section |

Every prompt is self-contained: no case references "the previous step," "the file you
made earlier" as an artifact only visible to the model, or an unstated filesystem path.
Case 2 is the one exception worth calling out explicitly: it does not assume the model
remembers a prior turn — it restates the already-created poster's description and the
scripted trigger line directly inside the single prompt, so the case is answerable from
the prompt text and `SKILL.md` alone, with no hidden conversation history required.

### Grounding discipline

This repo's skills were already flagged once, in a prior review, for grounding
hallucination as the #1 defect category — `expected_output` text asserting things that
sounded plausible but were not actually written anywhere in the target `SKILL.md`. To
avoid repeating that here:

- Every double-quoted span inside `expected_output` is a verbatim substring of a line in
  `SKILL.md` (markdown emphasis markers `**`/`*` stripped for the comparison, since those
  are formatting, not content; whitespace collapsed).
- Every single-quoted span inside `expectations` that refers to `SKILL.md` text is
  likewise verbatim (same normalization). Two exceptions are intentional, not grounding
  gaps: case 4's expectation about the user's own request ("make it fun and cartoony
  like the show") quotes the *prompt*, not `SKILL.md`, and is phrased without quote
  marks around it for that reason; and the apostrophe in "the agent's proposed changes"
  (case 2) is plain possessive text, not a citation.
- This was checked mechanically: a script extracted every `"..."` span from
  `expected_output` and every `'...'` span from `expectations`, normalized both the
  extracted spans and the full `SKILL.md` text the same way, and confirmed each span is
  a literal substring. 45 real citation spans were checked this way; all 45 pass. (A
  46th regex match was a false positive from an apostrophe, not an actual quote — see
  above.)
- No case invents a rule, a section name, or a percentage/number that isn't printed in
  `SKILL.md`. Section names used (CANVAS CREATION, FINAL STEP, MULTI-PAGE OPTION,
  DEDUCING THE SUBTLE REFERENCE, ESSENTIAL PRINCIPLES) are the skill's own `##`/`###`
  headers, copied as written.
- One quote is reproduced with its source typo intact rather than silently corrected:
  the FINAL STEP line reads "a masterpiece if craftsmanship" in `SKILL.md` (almost
  certainly a typo for "of craftsmanship"). Case 2's prompt and `expected_output` both
  quote it exactly as written, because the eval is testing whether the model recognizes
  *this specific scripted line* as the refinement trigger — silently fixing the typo
  would make the eval prompt no longer match what `SKILL.md` says the user "ALREADY
  said."

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, then write the eval around it — not the other way around.

## How to run

There is no packaged harness for `evals.json` yet. Until one exists, run each case by
hand:

1. Start a fresh session with `canvas-design` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript and any files
   produced, not a subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A case that produces a
   visually strong poster but skips a required step (e.g. it goes straight to the .png
   with no philosophy .md, or it adds a new shape during the FINAL STEP refinement pass)
   should be scored as a failure on that expectation even if the artwork itself looks
   good — these evals exist specifically to catch process and discipline failures that
   a purely visual judgment would miss.

## Interpreting results

- **Cases 1, 2, and 3** test structural/process requirements the skill states as
  effectively mandatory ("Complete this in two steps," the FINAL STEP's "STOP" 
  instruction, the "non-negotiable" containment rule). A failure on any expectation in
  these cases means the skill skipped a step it explicitly requires, not a matter of
  taste.
- **Cases 4 and 5** test whether sophistication and subtlety survive contact with a user
  request that pulls the other way (a cartoony ask, a literal-imagery ask). These are
  the cases most likely to fail under normal model drift toward "just do what the user
  literally asked for," which is exactly why `SKILL.md` calls them out ("Never lose
  sight of the idea that this should be art" / "not always literal, always
  sophisticated").
- **Case 6** tests both directions of one rule at once: that the default stays a single
  page absent a request, and that an explicit multi-page request is honored correctly
  (shared philosophy, distinct pages, loosely narrative) rather than either over- or
  under-applying the MULTI-PAGE OPTION section.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas
  above, not as proof the skill helps overall.
