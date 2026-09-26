# Changelog

All notable changes to the `soma-ops-skills` plugin package are documented here.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), dates in
YYYY-MM-DD.

## 2026-09-26 — v0.2.4

### Fixed
- Removed the unsupported `do_not_use_when` frontmatter field from the last 7 skills that had it:
  `pipeline-debug` 1.2.2, `soma-eval-harness` 1.3.2, `soma-memory-fix` 1.1.2,
  `soma-model-preflight` 0.1.2, `soma-distribution` 0.1.2, `soma-agent-cleanup` 0.1.2,
  `soma-score-analyzer` 0.1.2. Claude Code ignores the field, so its boundaries never reached
  the model. The first three had no "Do NOT use" text in the description; it is added there now.
  The other four already carried the same boundaries in the description. Skill steps unchanged.
- `soma-memory-fix` eval 6 checked for the removed field; it now checks the boundary stated in
  the description.

## 2026-09-25 — v0.2.3

### Fixed
- `soma-run` 1.3.2:
  - Report template: with the default scope (TI only), HW and CR run server-side inside the
    TI chain; the report now says `RAN SERVER-SIDE (output not captured)` instead of implying
    they were skipped, and marks HW/CR evo-logs and winners-log as not written with the reason.
  - Reference table: TI timeout documented as 300 s in the schema, with the note that the MCP
    client aborts at 60 s anyway (fire-and-poll, never resend).
  - Description and compatibility no longer claim HW/CR evo-logs and winners-log are always
    written; they are written only in the gated external-relay scope.
  - Removed the `do_not_use_when` frontmatter field (not a supported field, silently ignored);
    its routing hints are now in the description.

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
