# Evals for web-artifacts-builder

These are the skill's first evals — no prior `evals.json`/`README.md` existed for
`web-artifacts-builder`, and no baseline (with-skill vs. without-skill) run has been
performed, so no pass-rate claim is attached here or added to `SKILL.md`.

## `evals.json` — model-level suite (6 cases)

Follows the schema `{skill_name, evals: [{id, prompt, expected_output, expectations}]}`.
`web-artifacts-builder` is short (~73 lines) and entirely procedural, so each case
targets one distinct, load-bearing rule rather than a generic "does it work" probe:

| ID | Focus | Grounded in |
|----|-------|-------------|
| 1 | Scope — when the skill applies vs. when it doesn't (simple single-file artifact vs. an artifact needing routing/state/shadcn-ui) | Frontmatter `description`: "Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts." |
| 2 | The exact 5-step process in order — catching a plan that skips `init-artifact.sh` and skips bundling before "displaying" the artifact | The 5 numbered steps; Step 2 ("editing the generated code"); Step 3/4 wording on bundling and sharing `bundle.html` |
| 3 | The explicit "AI slop" avoid-list — purple gradients, Inter font, uniform rounded corners, excessive centered layouts | "Design & Style Guidelines" — the `VERY IMPORTANT` line |
| 4 | Bundling's explicit requirement — a missing root `index.html` blocks `bundle-artifact.sh` | Step 3, "**Requirements**: Your project must have an `index.html` in the root directory." |
| 5 | Testing is optional and should not be run upfront by default | Step 5 note + "In general, avoid testing the artifact upfront..." |
| 6 | Precise recall of the stack and what `init-artifact.sh` configures | "**Stack**:" line + the Step 1 bullet list (Tailwind 3.4.1, path aliases, 40+ shadcn/ui components, Radix UI deps, `.parcelrc`, Node 18+ handling) |

Every prompt is self-contained: no case references "this conversation," a prior turn,
or an unstated file the solver doesn't already have (project state needed for a case —
e.g. "I already ran `init-artifact.sh`" or "my `index.html` is missing" — is stated
plainly in the prompt itself). A solver with only the prompt text and `SKILL.md` open
should be able to answer each one.

### Grounding discipline

The task brief for this eval set explicitly named grounding hallucination as the #1
defect category found in a prior review of this repo's skills. To avoid repeating that
here, every quoted or paraphrased claim in `expected_output` was checked against the
literal text of `SKILL.md`
(`07-izlazni-formati/web-artifacts-builder/SKILL.md`) before being included, and
re-verified with a script that searches the raw file for each quoted string after
stripping markdown formatting (backticks/emphasis) — see the verification pass run
before this file was finalized. Two disciplines were applied:

- Anything inside `"double quotes"` in an `expected_output` is a verbatim (or
  emphasis-stripped) substring of a line in `SKILL.md` — never a paraphrase dressed up
  as a quote.
- Anything paraphrased (e.g. "the 5-step process," "the AI slop guideline") is named
  after a section or line that literally exists in `SKILL.md` — never invented, and
  never filled in with plausible-sounding frontend-development conventions the skill
  itself doesn't state. In particular:
  - No case invents a *replacement* for what the "AI slop" guideline tells you to
    avoid — `SKILL.md` only lists what to avoid (purple gradients, Inter font, uniform
    rounded corners, excessive centered layouts), not what to use instead, so Case 3's
    `expectations` explicitly forbid the agent from attributing an invented alternative
    to the skill.
  - No case claims `scripts/bundle-artifact.sh` auto-generates a missing `index.html` —
    `SKILL.md`'s "What the script does" list (install deps, create `.parcelrc`, build
    with Parcel, inline assets) says nothing of the sort, so Case 4 treats the missing
    file purely as a stated blocker, not as something the tooling silently fixes.
  - No case claims Playwright/Puppeteer testing is forbidden outright — `SKILL.md`
    names them as acceptable tools for the *optional* step, so Case 5 tests only the
    *timing* rule (not upfront, only after presenting or if requested/issues arise),
    not a blanket ban.
  - Case 6 pins down every specific fact from the Step 1 bullet list (Tailwind version
    number, exact component count, `.parcelrc`, Node 18+ handling) and explicitly
    checks the agent does *not* introduce unlisted tools (Next.js, Webpack,
    styled-components) that a generic "modern React setup" answer might hallucinate.

If you extend this set, apply the same check before adding a case: find the exact line
in `SKILL.md` first, then write the eval around it — not the other way around.

## How to run

There is no packaged harness for `evals.json` in this skill. Run each case by hand:

1. Start a fresh session with `web-artifacts-builder` loaded and no prior conversation
   state.
2. Paste the `prompt` for one case verbatim.
3. Compare the actual response against every item in that case's `expectations` list —
   each is meant to be answerable pass/fail by re-reading the transcript, not a
   subjective quality judgment.
4. Record pass/fail per expectation, not just per case. A response that reaches the
   right end result but skips a stated step (e.g. it writes files before running
   `init-artifact.sh`, or it tests with Playwright before showing the artifact) should
   be scored as a failure on that expectation even if the final artifact looks fine —
   these evals exist to catch process and discipline failures that a purely
   outcome-based check would miss.

## Interpreting results

- **Cases 2 and 4** test the mechanical workflow contract (the 5 numbered steps, and
  the bundler's explicit `index.html` requirement). A failure here means the agent
  would produce a broken or invalid hand-off — not a style nitpick.
- **Case 1** tests routing discipline: using this skill (and its init/bundle scripts)
  for a trivial artifact wastes the user's time and contradicts the skill's own scoping
  language; not using it for a genuinely complex artifact means missing routing/state/
  shadcn-ui support the user actually needs.
- **Case 3** tests adherence to a guideline the skill itself marks `VERY IMPORTANT`, so
  a failure here is not a matter of taste — it is ignoring an explicitly emphasized
  instruction.
- **Case 5** tests a specific ordering/latency discipline the skill calls out by name
  ("avoid testing the artifact upfront"); a failure here produces the exact
  time-to-first-artifact regression the skill is warning against.
- **Case 6** tests factual recall precision rather than behavior — a model that answers
  vaguely or invents unlisted tooling here is likely to give the user wrong
  expectations about what still needs manual setup.
- This is a first pass at 6 cases, not a statistically powered suite, and it carries no
  with-skill-vs-without-skill baseline. Treat it as a regression check for the six areas
  above, not as proof the skill helps overall.
