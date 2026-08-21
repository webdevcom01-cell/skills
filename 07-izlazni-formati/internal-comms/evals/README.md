# Evals for internal-comms

`internal-comms` is an unusually short skill (32 lines of `SKILL.md`, no scripts, no
other reference docs at the top level). It is a routing table: it names seven
communication types Claude might be asked to write, and for three of them points to a
specific guideline file under `examples/` — `examples/3p-updates.md`,
`examples/company-newsletter.md`, and `examples/faq-answers.md` — with a fourth file,
`examples/general-comms.md`, acting as an explicit catch-all ("For anything else that
doesn't explicitly match one of the above").

**Important limitation on this eval set:** only `SKILL.md` itself was available while
writing these evals. The four files under `examples/` were not provided and were never
read — this eval set knows only that they exist, their filenames, and the one-line
description of each given in `SKILL.md`'s step 2. No case here asserts, quotes, or
tests anything about what is actually written *inside* `examples/3p-updates.md`,
`examples/company-newsletter.md`, `examples/faq-answers.md`, or
`examples/general-comms.md`. All six cases test the **routing and process logic**
`SKILL.md` itself specifies — which file gets loaded for which request, and whether the
three-step process ("Identify the communication type" → "Load the appropriate
guideline file" → "Follow the specific instructions in that file") is actually
followed — not the guidance those files contain once loaded. If the `examples/` files
become available later, a second, content-focused eval set should be built against them
separately; extending the cases below is the wrong place for that.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
Each case targets one distinct piece of the routing table in `SKILL.md`'s "How to use
this skill" section.

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Correct routing for a 3P (Progress/Plans/Problems) team update → `examples/3p-updates.md` | "When to use this skill" bullet "3P updates (Progress, Plans, Problems)"; step 2 line "`examples/3p-updates.md` - For Progress/Plans/Problems team updates" |
| 2 | Correct routing for a company-wide newsletter → `examples/company-newsletter.md` | "When to use this skill" bullet "Company newsletters"; step 2 line "`examples/company-newsletter.md` - For company-wide newsletters" |
| 3 | Correct routing for an FAQ-answering request → `examples/faq-answers.md` | "When to use this skill" bullet "FAQ responses"; step 2 line "`examples/faq-answers.md` - For answering frequently asked questions" |
| 4 | A named use case with no dedicated file (incident report) correctly falls through to the catch-all `examples/general-comms.md`, rather than triggering a clarification request | "When to use this skill" bullet "Incident reports"; step 2 catch-all line "`examples/general-comms.md` - For anything else that doesn't explicitly match one of the above" |
| 5 | A genuinely ambiguous request (no stated type at all) triggers a clarifying question instead of a silent default or a guess | Closing line: "If the communication type doesn't match any existing guideline, ask for clarification or more context about the desired format." |
| 6 | The 3-step process itself, tested generically: even under explicit user pressure to skip research, the agent must still identify the type, load the matching `examples/` file, and follow it — not improvise formatting from general knowledge | "How to use this skill" steps 1–3 in full |

Every prompt is self-contained: no case references "this conversation," a prior turn, or
an unstated filesystem path. A solver with only the prompt text and `SKILL.md` open
should be able to answer each one.

### Why cases 4 and 5 are both needed, and why they're different

`SKILL.md` names seven use cases (3P updates, company newsletters, FAQ responses,
status reports, leadership updates, project updates, incident reports) but only
describes three files by name in step 2, plus the fourth, `examples/general-comms.md`,
explicitly scoped as "anything else that doesn't explicitly match one of the above."
That means a request for a status report, leadership update, project update, or
incident report is *not* an unmatched case in the sense the closing line ("ask for
clarification") addresses — it has a clearly identifiable type (step 1 succeeds), and a
guideline file whose stated scope covers it (`general-comms.md`). Case 4 tests that the
agent recognizes this and routes there directly instead of pausing to ask what kind of
communication the user wants.

Case 5 tests the different, narrower situation the closing line actually describes: a
request where step 1 itself cannot be completed because the user hasn't said what type
of communication they need at all. Only there does "ask for clarification or more
context about the desired format" apply. Conflating these two would have been an easy
way to reintroduce grounding hallucination — asserting "ask for clarification" applies
to *any* request outside the three named files, when `SKILL.md`'s own step 2 already
supplies a fourth file that covers exactly that gap.

### Grounding discipline

This skill's SKILL.md was flagged in an earlier review pass as belonging to a batch
where grounding hallucination — an eval's `expected_output` asserting something that
sounded plausible but was never actually written in the target `SKILL.md` — was the
number one defect category. Because this particular `SKILL.md` is so short and so much
of it is a routing table, the temptation to fill in "obviously true" details about
tone, formatting conventions, or what a 3P update / newsletter / FAQ "usually" contains
is real — and every one of those details would be an invention, since none of that is
in `SKILL.md` and the `examples/` files were not read. To guard against that:

- Every double-quoted phrase in an `expected_output` below is a verbatim substring of a
  line in `SKILL.md` (markdown emphasis markers and backticks stripped for the
  comparison, since those are formatting, not content) — checked programmatically
  against the actual file content, not from memory.
- The two exceptions are direct quotes of the case's own prompt text (case 5's "not
  sure exactly what format or type of update it should be yet" and case 6's "skip the
  research"), used to point back at what the user said — these are explicitly not
  presented as claims about `SKILL.md`.
- No case describes, paraphrases, or guesses at formatting/tone/structure rules that
  would live inside `examples/3p-updates.md`, `examples/company-newsletter.md`,
  `examples/faq-answers.md`, or `examples/general-comms.md`. Wherever a case needs to
  say something about "what the drafted output should look like," it says only that the
  output should reflect having consulted the relevant file — never what that file
  supposedly says.
- No case invents a "hard rule," "core principle," or numbered sub-step that isn't in
  the 3-line numbered list under "How to use this skill." This skill has no equivalent
  of a hard-rules/soft-rules section, write-boundaries section, or severity scale — it
  is genuinely just: identify → load → follow, with one fallback line for when
  identification fails.

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, then write the eval around it — and if a case would require
knowing what's inside an `examples/` file, either get that file first or don't write
the case.

## How to run

There is no packaged harness for `evals.json` yet. Run each case by hand:

1. Start a fresh session with `internal-comms` loaded and no prior conversation state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A case that picks the right
   `examples/` file but never says it actually consulted it (i.e. it just recognized the
   category and drafted from general knowledge) should be scored as a failure on that
   expectation, even if the drafted communication reads fine — these evals exist to
   catch routing/process shortcuts, not to grade writing quality.

## Interpreting results

- **Cases 1, 2, and 3** are the core routing tests: one type, one correct file, three
  files it must *not* be. A failure here means the skill is misreading its own routing
  table for the three most explicitly-specified categories.
- **Case 4** tests the catch-all logic specifically — that a named-but-file-less use
  case still resolves to `general-comms.md` rather than stalling on a clarification
  request it doesn't need. A failure here (routing to the wrong file, or asking a
  question the user already answered) suggests the model is treating "no dedicated
  file" as equivalent to "unidentifiable type."
- **Case 5** is the one case where clarification is correct. A failure here — silently
  guessing a type, or defaulting to `general-comms.md` for a request that gave no
  content to work with — is arguably worse than a wrong-file routing error, since it
  produces a confidently-drafted communication about nothing the user asked for.
- **Case 6** is a process-discipline check that cuts across all the others: it directly
  tests whether "load the appropriate guideline file" is a real step the model performs
  or a step it silently skips once it recognizes the category. Because the prompt
  explicitly pressures the model to skip it, this case is the closest thing this short
  skill has to a "hard rule" test — steps 2 and 3 are stated as required, not optional,
  and this case is the one built to catch a model that quietly treats them as optional
  under time pressure.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the routing
  table and the three-step process, not as proof the skill improves output quality —
  that would need paired with/without runs, which have not been done here, and would
  also need the `examples/` files to be readable so the *content* of what gets loaded
  could be evaluated too.
