# Changelog

All notable changes to this plugin (the `plugin/` package as a whole) are documented here.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), dates in
YYYY-MM-DD. **This file starts tracking from 2026-08-22 forward — it does not backfill the
plugin's commit history from before that date.**

## 2026-09-25 — v0.4.1

### Added
- `skill-lint` / `lint_metadata.py`: hard check on frontmatter field lengths (`description`
  ≤ 1024, `compatibility` ≤ 500). claude.ai rejects a plugin upload that exceeds them; this is
  how soma-ops-skills v0.2.1 failed to install (see that package's CHANGELOG).

## 2026-09-25 — v0.4.0

### Removed
- `brand-guidelines`, `canvas-design`, `internal-comms`, `mcp-builder`, `morning`,
  `slack-gif-creator`, `web-artifacts-builder` — their `SKILL.md` is identical to the copy
  Anthropic already ships on the Claude account, so installing this package put two skills with
  the same name and content side by side. They remain in their phase folders.

### Changed
- `deep-research` renamed `deep-research-sop` (folder, `name:`, eval `skill_name`). Anthropic
  ships a different skill named `deep-research` (a subagent coordinator); this one is the
  single-agent SOP with Tier 1/Tier 2 sources. Invoke it as `/deep-research-sop`.
- `plugin.json` description count corrected (it said 21 while the package held 24; now 17).

### Note
- The installed v0.3.1 predated commit 53251f4 (which added idea-to-project Rule #8) despite
  carrying the same version number. From here on: bump the version whenever content changes.

## 2026-08-22

### Added
- Root `LICENSE` (MIT, same text already used by `geo-prompt-library`) and this `CHANGELOG.md`
  for the plugin as a whole.

### Fixed
- 8 skills (`algorithmic-art`, `mcp-builder`, `brand-guidelines`, `canvas-design`,
  `internal-comms`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`) had an
  Apache 2.0 `LICENSE.txt` with an unfilled `Copyright [yyyy] [name of copyright owner]`
  placeholder — filled in with the actual copyright holder.

### Changed
- Extracted `references/` for 11 skills that were at or approaching the repo's 500-line /
  ~5000-estimated-token `SKILL.md` size limit: `prospect-discovery`, `soma-performance-review`,
  `agent-health-check`, `pipeline-input-validator`, `soma-agent-debugger`, `instincts-updater`,
  `kb-sync`, `soma-memory-fix`, `winners-log-logger`, `algorithmic-art`, `doc-coauthoring`. No
  behavior change — extracted content is verbatim, only relocated. `skill-creator-pro` was left
  as-is (tracks an upstream Anthropic fork; restructuring it risks future sync conflicts).
- Removed `market-research-navigator` and `system-teardown` from the distributable plugin —
  their `LICENSE.txt` is "all rights reserved" without redistribution permission. They remain in
  their phase folders for personal use, license unchanged.
- `catalog_sync_check.py` now only counts a phase-folder skill against the README catalog if
  it's also mirrored into `plugin/skills/` — supports a skill intentionally existing in a phase
  folder only.
- Added `allowed-tools` frontmatter to 12 mutating/destructive skills that previously relied on
  prose alone ("ask the user before...") to gate the action.
- `geo-prompt-library`: `CHANGELOG.md`/`version` alignment; `plugin.json` version bumped to
  `0.2.0`.

## 2026-08-22 (later same day) — package split

### Changed
- Split this package (#16 in the improvement plan). 27 skills specific to Agent
  Studio/AgentStack/SOMA content pipeline and the consulting layer built on it moved to a new
  sibling package, `plugin-soma-ops/` — copied fresh from their phase-folder source, not moved
  from here (this package's copies were removed). List: `agent-architect`,
  `agent-delivery-pack`, `agent-dependency-mapper`, `agent-health-check`, `agent-scaffolder`,
  `automation-triage`, `enterprise-agent-readiness`, `evo-log-writer`, `instincts-updater`,
  `kb-sync`, `memory-integrity-gate`, `pipeline-debug`, `pipeline-input-validator`,
  `prospect-discovery`, `rls-rollout`, `safe-agent-builder`, `soma-agent-cleanup`,
  `soma-agent-debugger`, `soma-distribution`, `soma-eval-harness`, `soma-memory-fix`,
  `soma-model-preflight`, `soma-performance-review`, `soma-run`, `soma-score-analyzer`,
  `team-enablement-program`, `winners-log-logger`.
- `plugin-sync` and `tender-projekat` removed from this package entirely (not moved to
  `plugin-soma-ops/` either) — `plugin-sync` is a meta-tool for maintaining this repo itself,
  `tender-projekat` is hardcoded to a single client engagement. Both remain in their phase
  folders for personal use.
- Package total: 50 → 21 skills. `plugin.json` version bumped to `0.3.0`, description updated to
  reflect the narrower scope.
- `catalog_sync_check.py` generalized to accept `--package-dir`, so the same script checks either
  package's README catalog against its own `skills/` mirror.

## 2026-09-18

### Changed
- `idea-to-project` (T-52): added a STEP 5 (DEPLOY) row and Constraints Rule #7 for real
  infrastructure deployment (a hosting platform, e.g. Railway) — found missing during the first
  live DEPLOY-phase run for a code project ("Polovni brodovi" pilot); the skill previously had no
  route to real hosting at all, so it was done entirely ad-hoc. Applied identically to the source
  copy (`08-drugi-projekti/idea-to-project/`) and the `plugin/skills/` mirror.
- `idea-to-project` (second pass, same day): added Constraints Rule #8, formalizing the public
  `/health`-style-route requirement that was applied ad hoc exactly once during the first full
  idea-to-project→sdd-workflow→agentic-loop-engineer chain run on a real deployed product (QR Kod
  Menadžer) — see `claude/OCENA-sistema-posle-runde-10-11-i-preporuka.md` recommendation #2.
  Applied identically to both copies, same as above.
- `plugin.json` version bumped to `0.3.1`.
