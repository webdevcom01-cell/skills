# Evals for docx

This is the first eval set for the `docx` skill (`07-izlazni-formati/docx/SKILL.md`).
No prior `evals.json`/`README.md` existed for this skill, and `SKILL.md`'s frontmatter
carries no `evaluation_status` claim to reconcile — these 6 cases are a clean first
pass, not a correction of an existing number.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
`SKILL.md` is short (91 lines) but dense: a 3-row task-routing table up top, a list of
~11 docx-js "gotchas," a mandatory verification step, a multi-part tracked-changes
workflow, and an untrusted-external-file discipline. Each case targets one coherent
slice of that content rather than a generic "does it produce a docx" probe.

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Task routing — editing an existing .docx must use unzip → edit `word/document.xml` → zip, not a docx-js script, because docx-js "cannot open existing files" | Task-routing table ("Edit" row) + "Editing existing documents" section |
| 2 | Page-size and orientation gotchas together — US Letter DXA dimensions (`12240 × 15840`) passed *unswapped*, with `orientation: PageOrientation.LANDSCAPE` doing the swap internally | "Creating with docx-js — gotchas": page size and landscape bullets |
| 3 | Table/list/shading gotchas combined — dual `columnWidths`+cell `width` in `WidthType.DXA` summing correctly, `ShadingType.CLEAR` (never `SOLID`), and `LevelFormat.BULLET` numbering instead of a literal `•` | "Creating with docx-js — gotchas": table widths, table shading, and lists bullets |
| 4 | Tracked-changes/redlining discipline — `--author` validation, `<w:ins>`/`<w:del>` with required `w:id`/`w:author`/`w:date`, `<w:delText>` vs `<w:t>`, and the deleted-paragraph-mark + per-run-`<w:del>` requirement for deleting a whole paragraph | "Tracked changes" section |
| 5 | Mandatory post-creation verification — a docx-js script exiting cleanly is not "done"; render to PDF, rasterize with `pdftoppm`, and actually read the page images, including the zero-padded filename behavior | "Verify the output" section |
| 6 | Untrusted external file discipline — stripping symlinks from a client-sourced .docx and running `merge_runs.py` before any find-and-replace, since Word fragments visible text across many `<w:r>` runs | "Editing existing documents" section: symlink-strip comment, `merge_runs.py` paragraph |

Every prompt is self-contained: each states the concrete file, task, and (where
relevant) the redlining author name up front, so a solver with only the prompt text
and `SKILL.md` open can answer it without any other context.

### Grounding discipline

The task brief flagged grounding hallucination as the #1 defect category found in a
prior review of this repo's skills, and called for extra precision here specifically
because `docx`'s gotchas are made of exact, unforgiving names — `ShadingType.CLEAR`,
`LevelFormat.BULLET`, `<w:delText>`, `PageOrientation.LANDSCAPE`, `--author`, exact DXA
numbers. To meet that bar, every quoted or closely-paraphrased claim in each
`expected_output` was checked as a literal substring of `SKILL.md` (with `**bold**` and
`` `backticks` `` stripped, since those are formatting, not content) before being
included, and re-verified programmatically after the file was written — all 26 quoted
spans across the six `expected_output` fields were confirmed present in `SKILL.md`
verbatim. Concretely:

- Anything inside `"double quotes"` in an `expected_output` is a verbatim substring of
  a `SKILL.md` line (formatting-stripped).
- Numbers (`12240`, `15840`, `2000`/`3000`/`5000` summing to `10000`, DXA, `1440 = 1″`)
  are copied from `SKILL.md` or are arithmetic on the eval's own stated inputs (e.g. the
  three column widths chosen for case 3 sum to the table width by construction) — never
  invented values dressed up as skill content.
- Function/script/class/flag names are copied character-for-character from `SKILL.md`:
  `merge_runs.py`, `accept_changes.py`, `validate.py`, `--auto-repair`, `--original`,
  `soffice.py`, `pdftoppm`, `WidthType.DXA`, `WidthType.PERCENTAGE`.
- No case invents a rule, script, or constant not present in this `SKILL.md` — e.g. no
  case references `comment.py`'s six comment files (case 5's routing) or
  `accept_changes.py`'s empty-spacer-paragraph edge case, since neither was pulled into
  this first set of 6.

## How to run

There is no packaged eval harness in this skill yet. Until one exists, run each case by
hand:

1. Start a fresh session with `docx` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A response can get the
   substantive artifact right (a table that looks correct, a redline that looks right)
   while still failing a specific expectation — e.g. it shades the header row with
   `ShadingType.SOLID`, or it validates tracked changes without the `--author` flag —
   and that should be scored as a failure on that expectation even if the rest of the
   response is strong.

## Interpreting results

- **Cases 1, 2, 3** test the "gotchas" lists — precise settings that silently produce a
  broken or wrong-looking document (wrong page shape, black table shading, a literal
  bullet character, a table that doesn't render in Google Docs) without throwing any
  error. A failure here means the generated document is subtly wrong, not that the
  script crashed.
- **Case 4** tests a multi-step correctness chain (`<w:ins>`/`<w:del>` attributes,
  `<w:delText>` vs `<w:t>`, paragraph-mark-plus-per-run deletion, `<w:del/>` element
  order) where any single missed step produces a change that renders correctly in the
  accepted view but is not actually tracked, or is tracked in a way that violates the
  XSD schema — exactly the class of invisible defect `--author` validation exists to
  catch.
- **Case 5** tests whether the skill's explicit, unconditional verification step
  survives a "the script ran with no errors, so I'm done" framing. A failure here means
  the skill's guidance gets skipped under time pressure or a false sense of completion,
  not that the skill's content was misunderstood.
- **Case 6** tests whether untrusted-input handling (symlink stripping) and text-search
  correctness (`merge_runs.py`) are applied *before* editing when a file's provenance
  (an external client) is stated in the prompt, rather than only when the skill is
  asked about them directly.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas
  above, not as proof the skill helps overall.
