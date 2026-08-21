# Evals for xlsx

`xlsx` is an official Anthropic skill (07-izlazni-formati/xlsx/SKILL.md, ~99 lines) covering
spreadsheet creation, editing, and analysis with `openpyxl`, `pandas`, and `markitdown`, plus a
mandatory LibreOffice-based recalculation step (`scripts/recalc.py`). These are the skill's first
evals: 6 cases, no baseline claim attached, because no with-skill-vs-without-skill run was
performed to produce one.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`. Each
case targets one distinct, high-signal rule from `SKILL.md` — chosen because the source text
states it as an absolute ("never," "only," "no formulas left") rather than a soft preference, and
because each has a documented failure trap where a naive agent looks correct while being silently
wrong.

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | The mandatory recalc requirement and the exit-code trap: `recalc.py` exits 0 for both `success` and `errors_found` — only a missing `status` key (replaced by an `error` key) means nothing ran, and that's the sole non-zero case | "Recalculate" section + "Requirements for every output" |
| 2 | The forbidden-functions list (`XLOOKUP`, `XMATCH`, `SORT`, `FILTER`, `UNIQUE`, `SEQUENCE`) and the silent-truncation trap where `recalc.py` reports `total_errors: 0` on a spilled formula that only wrote its top-left cell | "Choosing formulas that survive verification" |
| 3 | The `_xlfn.` prefix required for exactly the six named post-2007 functions (`TEXTJOIN`, `CONCAT`, `IFS`, `SWITCH`, `MAXIFS`, `MINIFS`), contrasted with Excel-2007-era functions (`SUMIFS`, `INDEX`, `MATCH`, `IFERROR`, `SUMPRODUCT`) that need no prefix | "Choosing formulas that survive verification" |
| 4 | Formulas-not-hardcoded-values, plus the destructive `data_only=True` trap: saving a workbook loaded that way permanently replaces every formula with its cached literal | "Requirements for every output" + "openpyxl gotchas" |
| 5 | Financial-model color-coding (blue hardcoded inputs, green cross-sheet links, red cross-file links) and the percentage-as-fraction storage gotcha (`0.15` → `15.0%`, `15` → `1500.0%`) | "Financial models" |
| 6 | The file-conventions-override rule: an existing file's own input-cell marker (here, orange fill) overrides the skill's own default (yellow fill) | "Requirements for every output" |

Every prompt is self-contained: no case references "this conversation," a prior turn, or an
unstated filesystem path. A solver with only the prompt text and `SKILL.md` open should be able
to answer each one.

### Grounding discipline

The brief for this eval set flagged grounding hallucination as the #1 defect category found in a
prior review of this repo's evals, so every quoted or paraphrased claim in `expected_output` and
`expectations` was checked mechanically against the literal text of `SKILL.md`
(07-izlazni-formati/xlsx) before being included:

- Anything inside `"double quotes"` in an `expected_output` is a verbatim substring of a line in
  `SKILL.md`, once markdown emphasis markers (`**bold**`, `*italic*`) and backticks are stripped
  — those are formatting, not content, the same convention used to verify quotes in this
  suite's template (`agent-architect`'s eval set).
- Every quote was checked with a script that strips that markdown formatting from both the quote
  and the full `SKILL.md` text and confirms the quote is a substring of the result — not eyeballed.
  An early pass caught and fixed several near-misses this way: two RGB-convention quotes in case 5
  and one file-convention quote in case 6 had picked up a sentence-ending period or comma that
  wasn't actually in the source (`SKILL.md` uses `·` middot separators between list items there,
  not periods), and a "needs no prefix" paraphrase in case 3's expectations didn't match the
  source's actual verb agreement ("need no prefix"). All were corrected to match the literal text.
- Function names, the `_xlfn.` prefix, and every RGB triple (`0,0,255`, `0,128,0`, `255,0,0`,
  `255,255,0`) are copied exactly as printed in `SKILL.md`, never approximated or re-derived from
  general Excel/openpyxl knowledge.
- No case invents a rule, script name, flag, or numeric threshold that isn't printed in the file.
  Where `expected_output` explains *why* a rule exists (e.g. why `data_only=True` returns cached
  values), that explanation is itself a quoted or closely paraphrased `SKILL.md` sentence, not
  independent reasoning about how `openpyxl` works in general.

## How to run

There is no packaged harness in this skill for `evals.json` yet. Until one exists, run each case
by hand:

1. Start a fresh session with `xlsx` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list — each is
   meant to be answerable pass/fail by re-reading the transcript, not a subjective quality
   judgment.
4. Record pass/fail per expectation, not just per case. A case that gets the substantive answer
   right but fails one discipline check (e.g. it writes `TEXTJOIN` without the `_xlfn.` prefix, or
   it silently saves over a `data_only=True` workbook) should be scored as a failure on that
   expectation even if the rest of the response is strong — these evals exist specifically to
   catch the traps `SKILL.md` calls out, not to grade writing quality or spreadsheet polish.

## Interpreting results

- **Cases 1, 2, 3, and 4** test hard, absolute rules ("never," "only," destructive-if-you-save)
  that `SKILL.md` states without exception. A failure on any expectation in these cases is a
  blocker-level regression: it means the delivered spreadsheet would contain a formula error, a
  silently truncated lookup, a `#NAME?` cell, or permanently destroyed formulas.
- **Cases 5 and 6** test convention-application discipline — applying the right color/format
  convention, and correctly recognizing when a file's own existing convention overrides the
  skill's stated default. A failure here means the deliverable is functionally correct but
  violates the skill's own stated presentation contract, or (case 6) actively fights an existing
  file's established formatting instead of matching it.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas above,
  not as proof the skill helps overall — that would require a paired with/without run, which has
  not been done for this skill.
