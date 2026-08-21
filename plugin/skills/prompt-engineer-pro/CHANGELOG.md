# Changelog — prompt-engineer-pro

## v2.0.0 (2026-08-14)

Rewritten against the Claude 5 context-engineering standard (Thariq / Anthropic,
July 2026: ~80% of the Claude Code system prompt removed with no regression).

The governing change: **v1 taught rules, v2 teaches criteria.** A rule that is right
most of the time was replaced by a criterion that is right all of the time.

### SKILL.md — 974 → 231 lines (−68% tokens: 7,944 → 2,534)

**Removed**

| What | Why |
|---|---|
| Mode-detection ASCII tree | Claude infers the mode from the request. The tree only forced it to route through a diagram first. |
| Technique selector ASCII ("simple task → zero-shot") | Restated general knowledge the model has. |
| Craft→Evaluate→Optimize flow diagram | Decorative; the phases survive as prose. |
| 70-line AcmeCorp worked system prompt | Exactly the "examples → interface design" shift. Constrained the solution space and cost ~900 tokens. |
| Mode 4: chat quick-wins ("be specific, not abstract") | Textbook general knowledge. |
| Anti-patterns list ("NIKAD ne raditi") | Absolute-rule shape; several entries now contradict current guidance. |
| Quick Reference Card | Pure repetition of the body, plus stale pricing. |
| S-Tier Skill checklist + SKILL.md sizing rules | Prescribed the bloat this version deletes ("version history, core philosophy, mode detection…"), and duplicated `skill-creator-pro`. |
| Mode 3 (skill meta-prompting) in full | Duplication across layers. Now a one-line pointer to `skill-creator-pro`. |
| Hardcoded model IDs and per-token pricing | `claude-sonnet-4-5-20250514`, "Opus 4 ~$15/M". Stale figures are worse than none — they mislead confidently. Replaced with a pointer to docs.claude.com. |
| Troubleshooting fixes: "repeat rules at the end", "add more examples" | Directly contradicted by the repetition and over-exampling findings. Table rewritten to diagnose by cause, with an explicit "don't do this" column. |
| Integration table, Notes platitudes | Failed the one test. |

**Kept and elevated**

- Security section — the deliberate exception. Hard constraints stay hard for
  compliance and untrusted input.
- Tool-description guidance (when NOT to use, enums) — promoted from a subsection
  to the section that replaces worked examples.
- Evaluation discipline and the deterministic scripts.
- Reference-loading table — this was already progressive disclosure.

**Added**

- The one test, as the skill's organising principle.
- **Model-tier gate.** The 80% guidance is a frontier-model finding. On Haiku or
  older Sonnet, examples and repeated rules still do real work. Deleting guardrails
  there is a regression, not a cleanup.
- `description` now has a "Do NOT use for" clause, ending the collision with
  `skill-creator-pro`, `agent-scaffolder` and `geo-prompt-library`.

### scripts/evaluate_prompt.py — inverted

The v1 evaluator scored prompts by 2025 rules. Left unpatched it would have
outvoted the new prose, because a numeric score beats an argument.

**Checks removed or inverted**

- `"No examples found"` (warning) and `"Only 1 example found"` → **inverted**.
  Examples no longer earn points; >3 is now flagged as over-constraining.
- `"No role/identity definition found"` → **inverted** into persona-theater detection.
- `"No XML structure detected"` → **removed**. Markdown headers are equally valid;
  XML is now required only where it delimits untrusted input.
- `"Uses XML tags"` as a scored strength → **removed**.
- `"No error handling instructions"` → **removed** (verification inflation).
- `"Too many negative rules"` → **reframed** as absolute-rule density, with the
  rule→criterion suggestion.

**Checks added**

- `bloat:persona` — invented biography and flattery.
- `bloat:verification` — "verify your work", "double-check". Causes *over*-verification
  on Opus 5.
- `bloat:emphasis` — ALL-CAPS and shouted-token density.
- `bloat:threshold` — size-based routing ("more than 5 files"), with the
  domain-count replacement.
- `bloat:vague` — "think very carefully", "try your best".
- Contradiction detection promoted `warning` → `critical`.
- `--model-tier {frontier,small}` — relaxes the example and verification checks on
  small models.

**Bugs fixed**

- **False-negative in injection detection.** The v1 pattern required the full word
  `NIKADA` and so missed `nikad`, the far more common Serbian spelling — silently
  reporting hardened prompts as unprotected. Broadened, and "treat as data"
  phrasing added in both languages.
- **False-positive storm in the security check.** v1 raised *critical* on every
  prompt over 300 tokens, whether or not it ingested untrusted input, which trains
  people to ignore critical findings. Now gated on actual interpolation or
  user-input markers.
- **Mention vs. use.** Bloat scanning now strips fenced blocks and quoted spans, so
  a document that *quotes* an anti-pattern is not reported as committing it. The
  limitation is documented in the function: a regex cannot solve this in general.

### scripts/compare_prompts.py — created

Referenced three times in v1's SKILL.md but **the file did not exist**. Any run of
the documented workflow failed.

Now a real deterministic before/after comparator. No API calls. Asymmetric on
purpose: losing tokens is the goal, so it is never a regression; gaining a security
issue or a contradiction is, regardless of tokens saved. Exits 1 on `REGRESSION`
so it can gate CI.

Verdicts: `CLEAN REDUCTION` · `REVIEW` (something valuable disappeared) ·
`REGRESSION` (do not ship) · `GREW` · `NO CHANGE`.

### Verification

```
compare_prompts.py SKILL.old.md SKILL.md
  Tokens  7944 → 2534   (−68.1%)
  Score     76 → 100    (+24)    B → A+
  Verdict: REVIEW — 2 lost strengths, both intentional
           (stale prompt-caching and prefill code snippets removed)
```

The two "lost" items are the stale API snippets, deleted on purpose. No security
control lost, no contradiction introduced.

Also verified: `--model-tier small` relaxes correctly, `generate_test_cases.py`
unaffected, JSON output schema intact, exit codes 1/0 correct on synthetic
regression and clean-reduction fixtures.

### Known limitations

- The bloat scanner is regex-based and cannot separate mention from use beyond
  fences and quotes. Read a flagged line before deleting it.
- A static audit cannot tell you the prompt still does its job. Run your own test
  cases against both versions.
- Reference files under `references/` were **not** rewritten in this pass. Several
  still carry v1 framing and stale model IDs. They are loaded on demand, so the
  blast radius is smaller — but they are the next thing to cut.
- `references/skill-meta-prompting.md` was deleted: Mode 3 moved to
  `skill-creator-pro`, leaving the file unreferenced. All remaining reference
  paths in SKILL.md were checked and resolve.

## v1.0.0 (2025-02)

Initial version. Four modes, Craft→Evaluate→Optimize workflow, Claude-specific
techniques, multi-agent patterns, evaluation framework, cost optimisation.
