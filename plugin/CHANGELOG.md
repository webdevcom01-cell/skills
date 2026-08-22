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
