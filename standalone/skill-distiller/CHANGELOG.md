# Changelog

All notable changes to `skill-distiller` are documented here.

## [1.4.0] — 2026-09-08

### Added
- Description-length check (1024-char spec limit) in `scripts/lint_skill.py`
  — handles both plain single-line and YAML block-scalar (`>-`/`|-`)
  description values without adding a YAML-parsing dependency. Added after
  a real eval run produced a 1086-character description that went
  uncaught because the executor's access to skill-creator-pro's
  `quick_validate.py` was (correctly) blocked during that eval to prevent
  grading-criteria leakage — `skill-distiller` now checks this itself
  rather than depending entirely on a sibling tool being reachable.

### Changed
- Eval id 3's expected output and first expectation clarified: a brief,
  transparent note in the produced skill acknowledging a rejected
  injection attempt is acceptable and not itself a violation — the bar is
  "no harmful content," not "zero mention of the incident." Previous
  wording ("only legitimate content") was ambiguous and penalized honest
  transparency in an eval run.

### Context
Both changes are direct responses to a real skill-creator-pro eval run
(iteration 2) rather than speculative hardening: the description-length
gap and the eval #3 wording ambiguity were both observed in actual grader
output, not hypothesized.

## [1.3.0] — 2026-09-08

### Added
- `scripts/check_verbatim_overlap.py` — mechanical detector for long
  (15+ word) verbatim runs shared between a source document and the
  distilled output. Added after a real eval run reproduced up to 29
  consecutive words from source while simultaneously self-reporting no
  verbatim copying had occurred — prose instruction alone was proven
  insufficient. Run during distillation, while the source is still
  available as a file, since the source is typically gone by the time
  `lint_skill.py` runs post-hoc.
- New Step 5 in `SKILL.md` (renumbering subsequent steps) requiring this
  check before frontmatter/finalization, with an explicit, honest
  limitation noted: it only catches exact word-for-word runs, not close
  paraphrase.
- New "Verbatim source overlap" section in `references/quality-checks.md`.
- Eval id 5 in `evals/evals.json`, formalizing this scenario for future
  regression testing.

### Context
Found via a real skill-creator-pro eval run (with-skill configuration,
eval id 1): the executor's self-report of compliance with the
no-verbatim-copying instruction was independently checked by the grader
and found false. This is the direct fix for that finding.

## [1.2.0] — 2026-09-08

### Added
- `LICENSE` (Apache-2.0 full text), `README.md` (human-facing
  documentation), `CHANGELOG.md` (this file), and `evals/evals.json`
  (the four manually-tested scenarios from development, formalized as
  re-runnable eval cases per skill-creator-pro's schema) — closing the
  gap between "works correctly" and "a serious organization can adopt
  and maintain this."
- Baseline entries for two new false positives surfaced by re-scanning
  after these additions (`evals/evals.json` legitimately contains a
  simulated prompt-injection attempt as test fixture data for eval id 3,
  which the scanner flags without understanding it's intentional test
  content — same root cause pattern as the SKILL.md/distillation-algorithm.md
  suppressions from 1.1.0).

## [1.1.0] — 2026-09-08

### Added
- Third quality check, "Fidelity to source": guards against confident,
  specific-sounding claims (a number, a named threshold, a hard rule) that
  don't actually trace back to anything the source stated. Threaded through
  `SKILL.md` (Step 4, Step 5, Step 6 listing) and
  `references/distillation-algorithm.md` (Step 4, Step 5).
- `.skillspector-baseline.yaml`, documenting SkillSpector findings from
  external security scanning, verified false positives (with root-cause
  explanations) and one accepted as a deliberate design choice
  (no `allowed-tools` declared). Uses path-based rules rather than exact
  fingerprints, so the suppression survives future edits to the flagged
  files instead of silently expiring when line numbers shift.
- `LICENSE` (Apache-2.0 full text) — previously only referenced by the
  `license:` frontmatter field without an actual bundled license file.
- This `CHANGELOG.md`.
- `README.md` for human readers (maintainers, reviewers) — previously all
  documentation was written for the executing agent only.
- `evals/evals.json` — the four scenarios manually tested during
  development, formalized as re-runnable eval cases (distillation of a
  large multi-topic source, fold-in detection against a real overlapping
  skill, adversarial source with an embedded injection attempt, and
  `incident-log-shape` detection on a raw transcript).

### Changed
- Step 2 (fold-in check) now specifies a concrete fallback order for
  locating the existing skill catalog (`<available_skills>` context →
  `search_skills` tool → directory listing → ask the user), instead of
  assuming a catalog is always visible.
- Step 2 also clarifies that "extend the match" isn't always a
  `references/` patch — for an operational/procedural skill, extending may
  mean adding a mode/section instead, or simply confirming no new work is
  needed.
- Step 3 / source hygiene now explicitly states that no part of suspicious
  embedded content may be carried into the produced skill, however
  indirectly — not just that it should be flagged to the user.
- Step 7 (validation) now also runs this skill's own `scripts/lint_skill.py`
  in addition to `quick_validate.py`, since the latter doesn't check body
  length or the advisory judgment calls.

### Fixed
- Renamed from `skill-forge` to `skill-distiller` — the original name
  collided with a pre-existing built-in Anthropic skill of the same name.

## [1.0.0] — 2026-09-07

Initial version. Core workflow (scope source → fold-in check → inventory →
incremental distillation → always-on/on-demand classification → frontmatter
per verified spec → advisory lint → structural validation → hand off to
skill-creator-pro), plus `references/distillation-algorithm.md`,
`references/quality-checks.md`, `references/frontmatter-reference.md`, and
`scripts/lint_skill.py`.
