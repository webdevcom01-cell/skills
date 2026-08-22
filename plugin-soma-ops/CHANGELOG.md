# Changelog

All notable changes to the `soma-ops-skills` plugin package are documented here.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), dates in
YYYY-MM-DD.

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
