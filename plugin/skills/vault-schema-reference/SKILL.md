---
name: vault-schema-reference
description: Reference for the structure of the SOMA/Agent Studio Obsidian vault used by the soma-ops skills — folders, note types, and their known schemas. Use when writing to or reading from the vault in a task that doesn't already document the schema itself, when a vault path assumption needs checking before hardcoding it into a new skill, when debugging a "note not found" error, or when creating a new agent's vault files by hand instead of through agent-scaffolder. Do NOT use as a substitute for reading the actual current file with obsidian_read_note or obsidian_list_notes/obsidian_list_folders — this documents the known/intended schema, not a live snapshot.
compatibility: No MCP dependency to read this reference itself. Skills that act on the vault still need Obsidian MCP (and Agent Studio MCP where relevant) — this document only describes what those calls should expect to find; it does not call them.
version: 1.3.0
---

# Vault Schema Reference

This is a documentation-only skill — it has no steps to execute. It exists so other skills that
read or write the SOMA/Agent Studio Obsidian vault can cite a single source of truth for paths and
file schemas instead of each re-deriving or silently assuming them.

**Provenance:** this schema was assembled on 2026-08-22 by cross-referencing what the vault-touching
skills already stated about the vault in their own SKILL.md bodies (several of those statements
carry their own live-audit dates, e.g. "confirmed 2026-05-16" in `kb-sync`) — it is not itself a
fresh live audit of the vault. The two `system/` items that were originally left unconfirmed were
checked directly against the live vault the same day (`obsidian_list_folders`, `obsidian_search_notes`)
— see "`system/`" below for the result.

If you change the vault's actual structure (add a folder, change a file's schema, resolve one of
the open items below), update this file in the same session — it only stays useful if it tracks
reality.

## Vault root

```
agents/{slug}/        one folder per SOMA agent
Insights/              agent-architect's write destination (audits, proposed agents, analyses)
shared/                cross-agent resources
system/                repo-wide config/rules — see "system/" below
```

## `agents/{slug}/`

Confirmed slugs (the 4 SOMA pipeline agents): `trend-intelligence`, `hook-writer`,
`content-repurposer`, `score-analyzer`.

| File | Schema | Who reads/writes it |
|---|---|---|
| `evo-log.md` | `# {agent} — Evolution Log`, then `## Log Format` (pipe-delimited: `date \| key \| confidence \| summary \| downstream_triggered`), then `## Entries`. Entries can span multiple lines — a continuation line is anything not starting with `YYYY-MM-DD \|`. | Written by `evo-log-writer` and `soma-run`; read by `instincts-updater`, `soma-performance-review`, `pipeline-debug`, `soma-agent-debugger`. |
| `instincts.md` | Free-form rules, not a fixed structure — **body skeleton still differs per agent by design** (see "instincts.md metadata skeleton" below), but as of 2026-08-22 all four share the same metadata skeleton: `version:` in frontmatter + a trailing `## Changelog` table. Human-approval gated: only `instincts-updater` writes here, and only after the user approves each proposed instinct. | Written by `instincts-updater` (with human approval); read by most soma-ops skills for context; scaffolded with a domain-specific starter block by `agent-scaffolder`. |
| `agent-card.md` | Fixed sections: Identity, Knowledge Base, Pipeline, Input, Output, "How to Wire Another Agent to This One". | Written once by `agent-scaffolder` (STEP 6) when the agent is created; not actively maintained elsewhere as of this writing. |
| `winners-log.md` | Only exists for `hook-writer` today. 4 fixed sections (header, Log Format, Winners, Reference); every write rebuilds the full body verbatim to avoid structural drift. Threshold: score >= 17/20. | Written by `winners-log-logger`; read by `hook-writer` runs for calibration. |
| `DESIGN_SPEC.md` | 11 fixed sections in order: Purpose, Pipeline Position, Use Cases, Tools, Constraints, I/O Contract, Quality Gate, Evo-log Schema, Open Questions, Implementation Plan, Versioning. | Drafted by `agent-architect` Mode 4 into `Insights/proposed-agents/` first (see below) — promotion into `agents/{slug}/DESIGN_SPEC.md` is a human decision, not automatic. Read (read-only) by `agent-architect` Mode 2 once present. |

## `Insights/`

Write destination for `agent-architect` only; no other soma-ops skill writes here as of this
writing.

| Path | Contents |
|---|---|
| `Insights/audits/<agent-name>-<YYYY-MM-DD>.md` | Agent audit reports from `agent-architect` Mode 2. |
| `Insights/proposed-agents/<name>-design-spec.draft.md` | Draft `DESIGN_SPEC.md` from `agent-architect` Mode 4, `.draft.md` suffix until a human promotes it into `agents/{slug}/`. |
| `Insights/analyses/` | Referenced as a write boundary in `agent-architect`; no skill currently documents what it writes there or in what format. Treat as reserved, not yet in active use. |

## `shared/`

| Path | Contents |
|---|---|
| `shared/global-instincts.md` | Cross-agent instinct, proposed by `instincts-updater` only when the same root cause recurs in >= 3 agents with >= 2 occurrences each — additive to per-agent `instincts.md`, never a replacement for it. |
| `shared/` (folder itself) | Exists; may currently hold no other files (per `instincts-updater`'s own note). |

## `system/`

Confirmed 2026-08-22 by a live `obsidian_list_folders`/`obsidian_search_notes` check — the folder
is **not** empty; it holds 13 notes, including both files below.

| Path | Referenced by | Status |
|---|---|---|
| `system/soma-rules.md` | `agent-architect` (cites it as the source of SOMA core principles and trade-offs) | **Confirmed.** Exists, last modified 2026-05-29. Also cited by name (as an existing file, not a plan) in over ten other vault notes — audits, `Insights/proposed-agents/*.draft.md` design specs, `Insights/code-as-agent-harness/*`, and `README.md`. |
| `system/config.md` | `pipeline-input-validator` (reads a `Primary niche:` field, with an explicit fallback to `"AI/tech"` and a warning message if the file or field is missing) | **Confirmed.** Exists, last modified 2026-06-14. |

`instincts-updater`'s "`system/` is currently empty" note was stale as of this check — treat that
line in `instincts-updater` as out of date rather than re-propagating it. The live folder also
contains `system/vault-standard.md` (a vault-organization standard, last modified 2026-05-30) plus
assorted incident/handoff notes (`HANDOFF-*`, `open-problems-ledger-*`, `rollback-*`,
`*-retry-storm-*`) and a `system/podsjetnici/` subfolder of personal reminders — none of those are
currently documented elsewhere in this reference; add them here if a future skill starts depending
on one.

## `instincts.md` metadata skeleton — converged 2026-08-22

All 4 agents now carry the same metadata skeleton, confirmed by a live read of each note:

| Agent | `version:` in frontmatter | `## Changelog` table |
|---|---|---|
| Trend Intelligence | Yes (`1.0`) | Yes |
| Hook Writer | Yes (`1.0`) | Yes |
| Content Repurposer | Yes (`1.0`) | Yes |
| Score Analyzer | Yes (`1.0`, pre-existing — this was the reference format the others converged to) | Yes (pre-existing) |

This was a deliberately narrow convergence — **only** the frontmatter `version:` field and a
trailing `## Changelog` table (`| Date | Change | Trigger |`) were added to the three agents that
lacked them. `1.0` marks "first explicit version of the already-existing state", same convention
`prospect-discovery`'s `CHANGELOG.md` used in the skills repo itself — it does not imply the content
is new or that anything before this date is undocumented; known prior additions (e.g. Trend
Intelligence's 2026-06-15 anti-hallucination rules, Hook Writer's 2026-06-28 quarantine entry,
Content Repurposer's 2026-05-15 Run 3 findings) are logged as dated pre-`1.0` rows.

**Explicitly NOT converged** — still genuinely different per agent, by design, not by omission:

- **Body skeleton.** Score Analyzer's `## Scoring Calibration` / `## Confidence Rating Guide` /
  `## Common Edge Cases` structure was not imposed on the other three, and their
  `## Learned Patterns` structure was not imposed on Score Analyzer — these describe genuinely
  different things per agent type (a scoring agent vs. content-generation agents), and forcing one
  skeleton onto the other would misrepresent the content, not just reformat it.
- **`## Quality Gate Failures` section.** Hook Writer and Content Repurposer have one (with real
  learned entries); Trend Intelligence and Score Analyzer do not. Left as-is rather than adding
  empty placeholder sections — a skill proposing a new QGF entry for TI/Score Analyzer should add
  the section fresh at that point, in Content Repurposer's format (`### <emoji> Run N — date —
  title` then `What happened` / `Root cause` / `Fix`), which is the house style going forward if
  this is revisited.
- **Header "Last updated" line** — fixed in a follow-up pass the same day (was stale on all three,
  e.g. Trend Intelligence's predated its own `created:` date). Now matches frontmatter `modified:`.
  Still a manually-maintained line, not auto-synced to `modified:` — a future edit to any of these
  files should update both, or a skill touching `instincts.md` should stop relying on this line and
  read frontmatter `modified:` / the Changelog's last row instead.

A skill writing to `instincts.md` should still match the target agent's existing body structure
rather than imposing a different one — only the metadata skeleton above is now guaranteed uniform.

## Explicitly out of scope

`format-templates.md` (referenced by `soma-distribution` and `soma-score-analyzer`) is **not** a
vault file — it lives in the Content Repurposer's Agent Studio Knowledge Base, loaded via
`as_search_knowledge_base`. It's noted here only so it isn't mistakenly assumed to be a vault path.

## How other skills should use this

Cite the relevant section instead of re-deriving or hardcoding a vault path from scratch. If a
skill's own body already documents the exact path/schema it needs (most do), it doesn't need to
reference this file at runtime — this exists for the cases that fall outside what any single skill
already owns: a new skill being written, a path that isn't covered above, or a "file not found"
error during debugging where the assumed schema itself might be the bug.
