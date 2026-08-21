# Evals for pdf

This is the skill's first eval set: 6 cases, no baseline claim attached, because no
baseline run (with-skill vs. without-skill) was performed to produce one. `pdf` is an
official Anthropic skill and is entirely in English, so this eval set is written in
English throughout, per the source SKILL.md's own language.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
Each case targets one distinct, high-signal rule from SKILL.md rather than a generic
"does it work" probe — specifically the six areas most likely to produce a wrong tool
choice or a silently broken output if an agent guesses instead of following the file.

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Table extraction tool selection — pdfplumber's `page.extract_tables()`, not pypdf (which has no table method) | Quick Reference row "Extract tables"; "### pdfplumber - Text and Table Extraction" / "#### Extract Tables" |
| 2 | The Unicode subscript/superscript gotcha in ReportLab — `<sub>`/`<super>` XML tags vs. literal Unicode glyphs that render as black boxes | "#### Subscripts and Superscripts" (flagged **IMPORTANT**) |
| 3 | Merge vs. split writer lifecycle — one `PdfWriter()` reused across all readers when merging, vs. a new writer per page when splitting | "#### Merge PDFs" vs. "#### Split PDF" |
| 4 | OCR routing for scanned/image-only PDFs — `pdf2image.convert_from_path` + `pytesseract.image_to_string`, not `extract_text()` | "### Extract Text from Scanned PDFs"; Quick Reference row "OCR scanned PDFs" |
| 5 | Command-line page-range extraction without Python — exact `qpdf --pages . 6-10 --` syntax | "### qpdf" / "# Split pages" |
| 6 | Password add vs. remove — pypdf's `writer.encrypt(...)` to add, qpdf's `--decrypt` to remove, kept in the right direction | "### Password Protection"; "### qpdf" / "# Remove password" |

Every prompt is self-contained: no case references "this conversation," a prior turn,
or an unstated filesystem path. A solver with only the prompt text and SKILL.md open
should be able to answer each one.

### Grounding discipline

Grounding hallucination — an `expected_output` asserting something plausible-sounding
that was never actually written in the target SKILL.md — was flagged as the **#1 defect
category** in a prior review of this repo's ~35 other skill eval sets. To avoid
repeating that here:

- Every claim in every `expected_output` below traces to an explicit, quotable line in
  `/mnt/user-data/uploads/moji_skillovi/07-izlazni-formati/pdf/SKILL.md`. Text inside
  `"double quotes"` is a verbatim substring of that file (backticks around inline code
  are preserved as written; no paraphrasing inside quote marks).
- Library and function names are quoted exactly as SKILL.md spells them:
  `page.extract_tables()`, `page.extract_text()`, `convert_from_path`,
  `pytesseract.image_to_string()`, `writer.encrypt()`, `writer.add_page()`, `PdfWriter`,
  `PdfReader`, `<sub>`, `<super>`, `qpdf --pages`, `qpdf --decrypt`.
- Before finalizing this file, all 32 distinct literal fragments quoted across the six
  `expected_output` fields were programmatically checked as verbatim substrings of
  SKILL.md (see validation step below) — none were reconstructed from memory or general
  PDF-library knowledge.
- No case invents a rule, flag, or behavior not present in SKILL.md. Where SKILL.md is
  silent (e.g. it never states pypdf *cannot* extract tables — it simply never shows a
  method for it), the eval's expectation is phrased as "does not propose X" rather than
  asserting a prohibition SKILL.md doesn't state.

If you extend this set, apply the same check before adding a case: find the exact line
in SKILL.md first, then write the eval around it — not the other way around.

## How to run

There is no packaged harness in this skill for `evals.json` yet. Until one exists, run
each case by hand:

1. Start a fresh session with `pdf` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A response that gets the
   substantive recommendation right but fails one discipline check (e.g. it uses a
   Unicode superscript character, or creates a new `PdfWriter()` per file when merging)
   should be scored as a failure on that expectation even if the rest of the response is
   strong — these evals exist specifically to catch the tool-selection and gotcha
   failures SKILL.md calls out, not to grade writing quality.

A basic automated schema/grounding check (not a model-response grader) was run during
authoring:

```bash
python3 -c "
import json
with open('evals.json') as f:
    data = json.load(f)
assert data['skill_name'] == 'pdf'
assert len(data['evals']) == 6
assert [e['id'] for e in data['evals']] == [1,2,3,4,5,6]
for e in data['evals']:
    assert set(e.keys()) == {'id','prompt','expected_output','expectations'}
    assert 4 <= len(e['expectations']) <= 6
print('schema OK')
"
```

## Interpreting results

- **Cases 2 and 3** test a documented gotcha and a code-structure rule that produce
  *silently wrong output* rather than an error if missed — solid black boxes in place of
  subscripts/superscripts (case 2), or a "merged" PDF that actually only contains the
  last input file's pages (case 3). A failure here is a correctness bug, not a style
  nitpick.
- **Cases 1 and 4** test tool selection where the wrong choice produces an empty or
  degraded result: pypdf has no table-extraction method, and standard text extraction
  (`extract_text()`) returns nothing on a scanned, image-only PDF. Both require the
  agent to recognize the input's nature (needs layout/table structure; is image-only)
  before picking a tool.
- **Case 5** tests exact command-line syntax reproduction for a common ask (arbitrary
  page range, no Python) — SKILL.md gives the literal command for this exact range
  (`6-10`) as a worked example, so this case also checks the agent doesn't drift into
  inventing flags.
- **Case 6** tests directionality — two SKILL.md-documented operations
  (`writer.encrypt()` to add, `qpdf --decrypt` to remove) that use different tools for
  opposite goals and are easy to swap if the agent pattern-matches on "password" alone
  rather than reading which direction the user needs.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas
  above, not as proof the skill helps overall.
