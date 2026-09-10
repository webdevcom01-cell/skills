# skill-distiller

A Claude Agent Skill that distills a new, standards-compliant Agent Skill
from a substantial source — existing code, documentation, a book or spec, a
long conversation transcript, or a described multi-step workflow.

This file is for people (reviewers, maintainers, anyone deciding whether to
adopt this) — `SKILL.md` and `references/` are written for the AI agent that
executes the skill, not for a human reading top-to-bottom.

## What it does

Given a source and a request to turn it into a skill, `skill-distiller`
distills — extracts structure, decision rules, and reusable procedures —
rather than summarizing or copying the source. The output is a standard
`SKILL.md` (+ optional `references/`, `scripts/`, `assets/`) that follows the
open [agentskills.io](https://agentskills.io) specification and works
unmodified in Claude, Hermes Agent, and other compatible clients.

## Why it exists

Built after researching how the most disciplined skill-authoring systems in
the ecosystem (primarily Hermes Agent's `/learn` command and its skill
maintenance mechanisms) actually decide what's worth turning into a skill,
how to organize it, and how to catch bad output before it ships — then
generalizing those principles into something that doesn't depend on any
particular runtime. See `references/distillation-algorithm.md` for the full
algorithm and its sourcing.

## Quality and security posture

- **Structural compliance**: validated against the agentskills.io
  specification (`scripts.quick_validate` from the `skill-creator-pro` skill).
- **Advisory quality checks**: `scripts/lint_skill.py` mechanically checks
  for `incident-log-shape` (a rule that only makes sense with its
  originating incident still attached) and `references-sprawl` (too many
  one-off files instead of topic-organized ones) — thresholds ported
  directly from Hermes Agent's own linter, not invented.
- **Behavioral testing**: five scenarios were manually run end-to-end during
  development — a real multi-topic source distillation, a fold-in check
  against a genuinely overlapping existing skill, an adversarial source
  containing an embedded prompt-injection attempt, an `incident-log-shape`
  check against a raw, unstructured transcript, and a verbatim-overlap check
  against a distinctively-phrased source sentence. All five are formalized
  as re-runnable cases in `evals/evals.json`.
- **Verbatim copying defense**: `scripts/check_verbatim_overlap.py`
  mechanically flags any 15+ consecutive words shared between a source and
  the produced output, run during distillation while the source is still
  available. Added after a real eval run showed prose instruction alone
  ("don't copy verbatim") is not reliably followed — the executor
  reproduced 29 consecutive source words while self-reporting compliance.
  Known limit: catches exact matches only, not close paraphrase.
- **External security scan**: scanned with NVIDIA SkillSpector (static
  analysis — no LLM API key was available at scan time, so this reflects
  Stage 1 pattern/AST/YARA checks only, not the optional LLM semantic
  layer). The raw scan initially flagged CRITICAL/DO NOT INSTALL; every
  finding was manually traced to its exact source line before being
  accepted or suppressed. `.skillspector-baseline.yaml` documents each
  suppression with a specific, checkable reason — nothing is suppressed
  without an explanation tied to actual file content. Final score after
  review: 0/100 LOW.

## Known limitations (honest, not exhaustive)

- **No eval/benchmark loop run yet.** `skill-creator-pro`'s with-skill /
  without-skill comparison requires subagent orchestration not available in
  every environment this skill might run in. `evals/evals.json` is written
  and ready to run wherever that capability exists.
- **No adversarial verification of this skill's own claims** (as opposed to
  the research it was built from, which was independently verified). This
  is the natural next step before treating this as fully hardened.
- **Not signed.** There is no cryptographic provenance mechanism — anyone
  with write access to wherever this is stored can modify it undetected.
  Acceptable for personal/single-organization use where the storage location
  itself is trusted; not acceptable as-is for third-party distribution.
- **`incident-log-shape` and `references-sprawl` are pattern-based, not
  semantic.** They catch the specific shapes described in
  `references/quality-checks.md`, not every possible way a distilled skill
  could go wrong.

## Relationship to `skill-creator-pro`

`skill-distiller` produces an initial, standards-compliant draft from a
substantial source. `skill-creator-pro` iterates and eval-tests a skill
interactively. Use `skill-distiller` first when there's real source material;
hand off to `skill-creator-pro` afterward for testing and refinement. Neither
replaces the other.

## Version

Current: 1.4.0. See `CHANGELOG.md` for history.
