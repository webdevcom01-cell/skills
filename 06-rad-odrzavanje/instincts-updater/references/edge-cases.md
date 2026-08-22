# Edge cases

Loaded from `instincts-updater/SKILL.md` — read when a run hits one of these specific scenarios (all-clean logs, below-threshold agent, dedup dispute, partial approval, unresolved domain tag, missing shared file, TI continuation lines). Verbatim from the skill body, moved here only because the combined SKILL.md was approaching the repo's line-count budget.

---

## Edge cases

**All entries are clean (no flags):**
Report: *"No quality gate failures found in any agent's evo-log. No instinct proposals generated. If you want P-code analysis, I can report on winners-log patterns."*

**Agent below threshold (< 3 entries):**
Log the skip and explain to the user. Score Analyzer will typically hit this early on (1 entry as of 2026-05-16).

**Semantic dedup fires on a proposal the user believes is different:**
Present both the existing instinct and the proposed new one to the user and let them decide. Do not override the dedup automatically — let the human judge.

**User approves a partial list (e.g., "1, 3" out of 5):**
Write only proposals 1 and 3. Mark 2, 4, 5 as "Rejected by user" in the final summary.

**Domain is UNKNOWN and user approves the proposal without selecting a tag:**
Before writing, ask once more:
> *"Proposal #N has Domain: UNKNOWN — please select one before I write it: tone | sourcing | format | orchestration | scoring | input-handling | cross-agent"*
Do not write the instinct until a valid domain tag is received. If the user declines to select, mark the proposal as "Skipped — domain not resolved" in the final summary.

**Global promotion proposed but `shared/global-instincts.md` does not exist:**
Use `obsidian_create_note` with vault path `shared/global-instincts.md`. Initialize with a header:
```
# Global Instincts — SOMA Pipeline
*Cross-agent patterns appearing in ≥3 agents.*

## Quality Gate Failures
```
Then append the instinct entry.

**TI evo-log has continuation lines that contain useful context:**
Include the continuation line content in the `flag_text` of the flagged entry. The full flag message may span the base entry line plus one or more continuation lines.

---
