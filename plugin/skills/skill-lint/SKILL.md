---
name: skill-lint
description: >
  Proverava mehaničku higijenu repoa skillova pre paketovanja ili merge-a: SKILL.md preko
  500 linija/5000 tokena bez references/scripts foldera, version: neusklađen sa CHANGELOG.md,
  pip importi bez requirements.txt, LICENSE.txt nespojiv sa deljenjem plugina (npr. Anthropic
  "Services only"), i README fazni katalog/"Ukupno: N" van sinhronizacije sa stvarnim folderima.
  Koristi kad korisnik kaže "lint skillove", "proveri higijenu repoa", "skill lint", "proveri
  licence", "proveri README katalog", "provera pre paketovanja", ili traži bilo koju od ovih
  provera — i uvek PRE package_plugin.py poziva kao gate. Ne koristi za sinhronizaciju
  plugin/skills/ (koristi plugin-sync), niti za allowed-tools/kredencijal proveru koja zahteva
  čitanje i rasuđivanje o sadržaju (koristi skill-security-review).
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TodoWrite
---

# Skill: skill-lint

*Version: 1.0 — nastao iz plan-unapredjenja-skills-repo.md, Faza C, kao spoj tri mehaničke
provere (skill-lint, license-compliance-guard, skill-catalog-sync) koje forenzička analiza i
njen dodatak predlažu kao zaseban prioritet. Namerno spojene u jedan skill jer nijedna od tri ne
zahteva rasuđivanje o sadržaju — sve tri su regex/AST/brojanje-linija provere nad fajl-sistemom.
Poređenje: skill-security-review ostaje poseban skill jer TA provera zahteva čitanje SKILL.md
teksta i procenu da li opisano ponašanje opravdava dati allowed-tools obim — to nije mehaničko.*

---

## Trigger

Use this skill when the user wants to:
- Check whether any `SKILL.md` violates the repo's own 500-line/5000-token size standard
- Check whether a skill's `version:` frontmatter matches its `CHANGELOG.md`
- Check whether a bundled script imports a pip package with no matching `requirements.txt`
- Check whether any `LICENSE.txt` in the repo is incompatible with sharing the plugin
- Check whether `plugin/README.md`'s phase catalog and "Ukupno: N" count match the real folders
- Run any pre-packaging hygiene gate before `plugin-sync`'s `package_plugin.py`

Do NOT use this skill for:
- Syncing `plugin/skills/` with the source phase folders → use `plugin-sync`
- Packaging `plugin/` into a `.plugin` file → use `plugin-sync`
- Judging whether `allowed-tools` scope matches a skill's actual described behavior, or scanning
  for hardcoded credentials → use `skill-security-review` (requires reading and reasoning about
  content, not just mechanical checks)
- Running `git add`/`git commit`/`git push` → tell the user the exact commands, don't run them
  yourself (this repo's convention: git write operations go through the user's own terminal)

---

## What This Skill Does

Three independent, mechanical scripts — each one answers exactly one question, each one exits
non-zero when it finds something, so any of the three composes as a CI/pre-commit gate on its
own:

1. **`scripts/lint_metadata.py`** — for every skill folder under `01-*` through `08-*`:
   - **Size**: counts the SKILL.md *body* (everything after the closing `---` of the YAML
     frontmatter — the part that's actually loaded into context when the skill triggers) in
     lines, and estimates tokens as `len(body) / 4` (same chars/4 heuristic the forensic
     analysis used, for comparability). Hard violation: body ≥ 500 lines **or** ≥ 5000 estimated
     tokens (the guide states these are conjunctive — either one alone is already over).
     Soft warning: 300–499 lines with no `references/` or `scripts/` folder present — the guide
     calls this "approaching the limit" and recommends adding a hierarchy layer before it becomes
     a hard violation.
   - **Version vs CHANGELOG**: if a skill has both a `version:` frontmatter field and a
     `CHANGELOG.md`, parses the changelog's topmost `## [X.Y.Z]`-style heading and compares
     against the frontmatter value. Mismatch is a violation. A skill missing one of the two is
     reported informationally, not as a violation (having neither, or having only version, is
     valid — the check only fires when both exist and disagree).
   - **Pip deps vs requirements.txt**: AST-parses every `.py` file under the skill folder for
     top-level `import X` / `from X import Y` statements, filters out anything in
     `sys.stdlib_module_names` (no hardcoded stdlib list — always current for the Python running
     the check), and flags any remaining third-party import that isn't listed in a
     `requirements.txt` anywhere under the skill folder.

2. **`scripts/license_compliance_guard.py`** — finds every `LICENSE.txt` / `LICENSE` file under
   the phase folders AND both distributable packages (`plugin/` and `plugin-soma-ops/` — their
   own root `LICENSE` plus every `skills/*/LICENSE*` actually shipped inside each), and flags any
   whose text matches known redistribution-restrictive language (e.g. Anthropic's "Services only"
   / "may not extract... outside the Services" / "may not distribute, sublicense, or transfer"
   pattern) as incompatible with the packages' stated distribution model (a shareable `.plugin`
   file). Scanning the packages directly — not just the phase folders they're synced from — is
   what actually protects what ships; a skill added straight into `plugin/skills/` or
   `plugin-soma-ops/skills/`, bypassing the phase folder, would otherwise slip through unchecked.
   A skill with no `LICENSE.txt` at all is not flagged — silence isn't a restrictive license, it's
   just the absence of an explicit one.

3. **`scripts/catalog_sync_check.py`** — parses `plugin/README.md`'s phase-by-phase skill catalog
   (the `### 0N — ...` sections) and its `**Ukupno: N skillova.**` line, and compares both against
   the real contents of `01-*` through `08-*` (every folder containing a `SKILL.md`, keyed by its
   actual phase folder). Reports any skill that exists on disk but isn't listed under the right
   phase in the README, any skill listed in the README that no longer exists on disk, and any
   mismatch between the stated total and the real count.

None of the three write anything by default — pure reporting, exit 0 clean / exit 1 findings.
None of the three have a `--fix` mode on purpose: catalog and license findings usually need a
human decision (which license? which phase?), not an automatic edit.

---

## STEP 0 — Task List

Call TaskCreate for each check the user actually wants run — don't create tasks for checks
they didn't ask about (e.g. "proveri licence" only needs the license task):
- "Pokreni lint_metadata.py (veličina/verzija/deps)"
- "Pokreni license_compliance_guard.py"
- "Pokreni catalog_sync_check.py"
- "Izveštaj nalaze"

Mark each in_progress before starting, completed when done.

The three scripts live in `scripts/` next to this SKILL.md — resolve that path relative to
*this file's own location*, not to a hardcoded repo path: if you're reading this from
`06-rad-odrzavanje/skill-lint/SKILL.md`, the scripts are at
`06-rad-odrzavanje/skill-lint/scripts/`; if you're reading this from an installed
`plugin/skills/skill-lint/SKILL.md`, they're at `plugin/skills/skill-lint/scripts/` instead. The
repo-root argument (`.` below) always points at the actual repo root regardless of which copy of
this skill is running — for `license_compliance_guard.py` and `catalog_sync_check.py`
specifically, that must be a checkout that contains the phase folders (`01-*`–`08-*`) or the
`plugin`/`plugin-soma-ops` package dirs, not just this skill's own folder in isolation.

## STEP 1 — Size / version / deps

```
python3 <this-skill's-scripts-dir>/lint_metadata.py <repo_root>
```

## STEP 2 — License compliance

```
python3 <this-skill's-scripts-dir>/license_compliance_guard.py <repo_root>
```

## STEP 3 — Catalog sync

```
python3 <this-skill's-scripts-dir>/catalog_sync_check.py <repo_root>
```

## STEP 4 — Report

Summarize per script: clean, or exactly what it found (skill name, line/token count vs limit,
version mismatch, missing requirements.txt package, restrictive license file, or catalog
drift) — in plain terms, not just pasting raw script output. If the user only ran one of the
three, don't imply the other two were also checked.

---

## Constraints and Rules

1. **No hardcoded skill/phase list.** All three scripts discover phase folders (`\d\d-*`) and
   skill names from the filesystem at run time, same convention as `plugin-sync`.
2. **No hardcoded stdlib list.** `lint_metadata.py` uses `sys.stdlib_module_names` at run time —
   never maintain a manual list that will drift from the Python version actually in use.
3. **Report-only, no auto-fix.** None of the three scripts modify files. Findings are for a human
   (or a follow-up skill invocation) to act on.
4. **Never invoke `git add`/`git commit`/`git push` from this skill** — same convention as
   `plugin-sync`: propose the exact command, the user runs it from their own terminal.
5. **Body line count, not file line count.** The 500-line standard is about what loads into
   context when the skill triggers — the YAML frontmatter block is excluded from the count on
   purpose, matching how `skill-creator-pro/references/skill-writing-guide.md` defines it.
