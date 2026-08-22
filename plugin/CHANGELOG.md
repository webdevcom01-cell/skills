# Changelog

All notable changes to this plugin (the `plugin/` package as a whole) are documented here.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), dates in
YYYY-MM-DD. **This file starts tracking from 2026-08-22 forward — it does not backfill the
plugin's commit history from before that date.**

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
