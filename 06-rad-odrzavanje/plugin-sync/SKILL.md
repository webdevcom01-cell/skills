---
name: plugin-sync
description: Proverava i sinhronizuje plugin/skills/ sa izvornim faznim folderima (01-08) u ovom repou, i pakuje plugin/ u distributable .plugin fajl za Cowork/Claude Code instalaciju. Koristi ovaj skill kad god korisnik menja neki skill u faznim folderima i treba da ažurira plugin kopiju, kad pita da li je plugin/skills/ usklađen sa izvorom, kad želi da spakuje plugin za instalaciju, ili kaže nešto poput "sinhronizuj plugin", "azuriraj plugin", "spakuj plugin", "napravi .plugin fajl", "da li je plugin u sync-u", "regeneriši plugin/skills", "plugin je zastareo". Takođe koristi PRE svakog "package/upload the plugin" zahteva da bi se izbeglo pakovanje zastarelog plugin/skills/. Ne koristi za kreiranje novog pojedinačnog skilla (koristi skill-creator-pro), niti za git add/commit/push (to korisnik radi sam).
---

# Skill: plugin-sync
*Version: 1.0 — modeled on skill-creator-pro's scripts/package_skill.py, one level up (whole plugin, not one skill)*

---

## Trigger

Use this skill when the user wants to:
- Check whether `plugin/skills/` still matches the source skills in `01-ideja-validacija/`
  through `08-drugi-projekti/`
- Apply that sync after editing a skill in its phase folder
- Package `plugin/` into a `.plugin` file for Cowork or Claude Code installation

Do NOT use this skill for:
- Creating or drafting a brand-new individual skill → use `skill-creator-pro`
- Running `git add`/`git commit`/`git push` → tell the user the exact commands, don't run them
  yourself (this repo's convention: git write operations go through the user's own terminal)

---

## What This Skill Does

`plugin/` is a flattened, installable copy of every skill in the phase folders — Cowork and
Claude Code expect `skills/<name>/SKILL.md` with no phase subfolders in between. Nothing
enforces that the copy stays current; `plugin/README.md` says as much ("kad se neki skill
promeni u izvornom folderu, ovaj folder treba ponovo generisati"), but until this skill existed
that was just a sentence, not a check — the CRLF fix on 2026-08-21 had to be applied to both
copies by hand because nothing would have caught a drifted copy otherwise.

Two scripts, modeled on `skill-creator-pro/scripts/package_skill.py`'s own shape (validate
before you act, exclude-pattern zip, argparse CLI):

1. **`scripts/sync_plugin.py`** — discovers every skill under the phase folders (by scanning
   for `\d\d-` prefixed directories, not a hardcoded list), hashes every file (SHA-256, not
   mtime — mtime survives a copy or clone and proves nothing) in both the source and the
   `plugin/skills/` copy, and reports NEW / UPDATED / ORPHANED / IN SYNC per skill. Default mode
   only reports (exit 1 if anything is out of sync — composes as a pre-flight gate). `--apply`
   performs the sync. `--prune-orphans` (only together with `--apply`) deletes plugin-only
   skills that no longer exist in any phase folder — a separate flag on purpose, same
   fail-closed-on-delete posture `kb-sync` uses for KB sources.

2. **`scripts/package_plugin.py`** — validates `plugin.json` and that every skill under
   `plugin/skills/` has a `SKILL.md`, refuses to package if `sync_plugin.py` reports drift
   (override with `--skip-sync-check`), then zips `plugin/` into `<plugin-name>.plugin`. The
   zip's top-level folder is named after `plugin.json`'s `"name"` field (not the on-disk
   `plugin/` folder name — an installed plugin lives at `<plugin-name>/…`, not `plugin/…`).
   Each skill's own `evals/` folder is dropped from the distributable zip (dev/test scaffolding
   the installed skill doesn't need at runtime) — the working copy in `plugin/skills/` keeps it.

---

## STEP 0 — Task List

Call TaskCreate for each step:
- "Proveri usklađenost plugin/skills/ sa izvorom"
- "Primeni sinhronizaciju (ako ima razlike)"
- "Spakuj plugin/ u .plugin fajl (ako je zatraženo)"
- "Izveštaj šta je promenjeno"

Mark each in_progress before starting, completed when done. Skip a step outright (don't just
mark it done) if the user only asked for one piece — e.g. "da li je plugin u sync-u" only needs
the first step.

---

## STEP 1 — Check

Run from the repo root:
```
python3 06-rad-odrzavanje/plugin-sync/scripts/sync_plugin.py .
```
Exit 0 with "potpuno usklađen" means nothing else to do — say so plainly and stop, don't
manufacture busywork. Exit 1 lists NEW / UPDATED / ORPHANED skills by name; exit 2 means two
phase folders have a skill with the same name — that's a naming conflict for a human to resolve,
not something to auto-fix by picking one arbitrarily.

## STEP 2 — Apply (only if Step 1 found drift and the user wants it fixed)

```
python3 06-rad-odrzavanje/plugin-sync/scripts/sync_plugin.py . --apply
```
Add `--prune-orphans` only when the user has confirmed an orphaned skill should actually be
deleted from `plugin/skills/` — don't default to pruning. An orphan usually means a skill was
renamed or moved, not necessarily deleted; check with the user if it's not obvious which.

Re-running Step 1's check command after `--apply` should report clean. If it doesn't, stop and
report the mismatch rather than guessing why.

## STEP 3 — Package (only if the user asked to package/upload/install the plugin)

```
python3 06-rad-odrzavanje/plugin-sync/scripts/package_plugin.py plugin dist
```
This refuses to run if Step 1 would report drift — run Step 1/2 first rather than reaching for
`--skip-sync-check` as a shortcut. The `.plugin` file lands in `dist/`; hand it back to the user
the way any other deliverable in this session would be delivered (send it, and if a connected
folder exists, write it there too) rather than leaving it only on disk unmentioned.

## STEP 4 — Report

Say what changed in plain terms: which skills were new/updated/pruned, whether a `.plugin` was
produced and where. If `plugin.json`'s version wasn't bumped and real content changed, mention
that as an open call for the user, not a hidden default — this skill deliberately doesn't pick a
version number, only detects drift.

---

## Constraints and Rules

1. **Sync uses content hashes, never mtime or file size.** A git clone or a copy resets
   timestamps; only the actual bytes tell you whether a skill really changed.
2. **Deleting is opt-in, twice.** `--apply` alone never removes anything from `plugin/skills/`;
   `--prune-orphans` is required on top of it, and only for skills genuinely absent from every
   phase folder — never delete based on a guess.
3. **Never invoke `git add`/`git commit`/`git push` from this skill.** This repo's established
   pattern is that Claude proposes the exact command and the user runs it from their own
   terminal — a script or session invoking git writes here has caused stale lock files before.
4. **Packaging without a clean sync is a deliberate override, not a default.** `--skip-sync-check`
   exists for the rare case the user explicitly wants to ship the current state anyway — using it
   automatically defeats the point of this skill.
5. **No hardcoded skill or phase list.** Both scripts discover phase folders (`\d\d-*`) and skill
   names from the filesystem at run time — a renamed phase or a 9th phase folder should not
   require editing this skill.
