# Changelog

All notable changes to the `soma-ops-skills` plugin package are documented here.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), dates in
YYYY-MM-DD.

## 2026-09-25 — v0.2.2

### Fixed
- v0.2.1 was rejected at upload on claude.ai: "field 'compatibility' in SKILL.md must be at most
  500 characters" for `agent-delivery-pack` (518) and `enterprise-agent-readiness` (550).
  Both shortened (now 422 and 447) with the same tool lists kept; only explanatory wording
  trimmed. `skill-lint` now checks this limit.

## 2026-09-25 — v0.2.1

### Fixed
- `soma-agent-debugger` was missing `_legacy-reference/` (added to the phase folder in c0ce4e7,
  never mirrored here). This package now has a drift check: `sync_plugin.py --package
  plugin-soma-ops` (and `--package all` in the pre-commit hook).

## 2026-08-22 (later same day) — vault-schema-reference added

### Added
- `vault-schema-reference` (#15 in the improvement plan) — documentation-only skill covering the SOMA/Agent Studio Obsidian vault's folder structure, note types, and known schemas, assembled from what the other soma-ops skills already stated about the vault (not a fresh live audit). Two items are explicitly marked unconfirmed pending verification: whether `system/soma-rules.md` and `system/config.md` actually exist. Package total: 27 -> 28, `plugin.json` version bumped to `0.2.0`.

## 2026-08-22

### Added
- Package created (#16 in the improvement plan) — split out of the original single `plugin/`
  package. Contains the 27 skills specific to Agent Studio/AgentStack/SOMA content pipeline and
  the consulting layer built on top of it (`prospect-discovery`, `team-enablement-program`,
  `agent-delivery-pack`), copied fresh from their phase-folder source.
- Root `LICENSE` (MIT, same text as the `plugin/` package) and this `CHANGELOG.md`.
- `README.md` with the Agent Studio/Obsidian MCP dependency notes (moved here from `plugin/`,
  since all 9 skills that carried those `allowed-tools` restrictions live in this package now)
  and the phase catalog for all 27 skills.

### Changed
- `rls-rollout` moved here from `plugin/` (it's Agent Studio infrastructure-specific, not a
  general-purpose skill) — its `disable-model-invocation: true` note moved with it.
