#!/usr/bin/env python3
"""
sync_plugin.py — Keep plugin/skills/ a byte-for-byte mirror of the phase folders.

The plugin/ folder is a flattened copy of every skill in 01-*/ through 08-*/
(phase subfolders stripped, because Cowork/Claude Code expect skills/<name>/SKILL.md
with no extra nesting). plugin/README.md says as much: "kad se neki skill promeni u
izvornom folderu, ovaj folder treba ponovo generisati." Nothing enforces that today —
there is no build step, so the two copies drift the moment someone edits a skill in
01-08/ and forgets the mirror in plugin/skills/. That already happened once (the CRLF
fix on 2026-08-21 touched both copies by hand because nothing would have caught it if
we hadn't).

This script is the enforcement: it diffs every skill in the phase folders against its
plugin/skills/ copy by content hash (not mtime — mtime survives a git clone or a copy
with the wrong value and proves nothing), and reports NEW / UPDATED / ORPHANED /
IN SYNC per skill. Default mode only reports and exits 1 if anything is out of sync,
so it composes as a pre-flight check (CI, a pre-commit hook, or just "is it safe to
package?"). --apply performs the sync. Deleting an orphaned plugin-only skill (one
that no longer exists in any phase folder) is a separate, explicit --prune-orphans
flag on top of --apply — the same fail-closed-on-delete posture kb-sync uses for KB
sources, because a plugin skill silently disappearing on every future install is a
worse failure mode than one silently going stale.
"""

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

# Files/dirs that don't count as skill content in either copy.
EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git"}
EXCLUDE_FILES = {".DS_Store"}
EXCLUDE_SUFFIXES = {".pyc"}

# Phase folders are discovered, not hardcoded, so a renamed or added phase
# doesn't silently fall outside the sync — matches the naming convention
# already in use (two digits, a hyphen, then the phase slug).
import re
PHASE_DIR_RE = re.compile(r"^\d{2}-")


def _included_files(root: Path) -> dict[str, str]:
    """Return {relative_posix_path: sha256} for every real file under root."""
    out = {}
    if not root.is_dir():
        return out
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDE_FILES or path.suffix in EXCLUDE_SUFFIXES:
            continue
        out[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def discover_source_skills(repo_root: Path) -> dict[str, Path]:
    """Map skill name -> its source directory across every phase folder.

    Raises ValueError if the same skill name appears under two different
    phases — that's ambiguous for a flat plugin layout and needs a human,
    not a script, to resolve.
    """
    skills: dict[str, Path] = {}
    dupes: dict[str, list[Path]] = {}
    for phase_dir in sorted(p for p in repo_root.iterdir() if p.is_dir() and PHASE_DIR_RE.match(p.name)):
        for skill_dir in sorted(p for p in phase_dir.iterdir() if p.is_dir() and not p.name.startswith(".")):
            name = skill_dir.name
            if name in skills:
                dupes.setdefault(name, [skills[name]]).append(skill_dir)
            else:
                skills[name] = skill_dir
    if dupes:
        lines = [f"  {name}: {', '.join(str(p) for p in paths)}" for name, paths in dupes.items()]
        raise ValueError(
            "Same skill name appears under more than one phase folder — can't "
            "flatten unambiguously:\n" + "\n".join(lines)
        )
    return skills


def diff_skill(source_dir: Path, plugin_dir: Path) -> dict:
    """Compare one skill's source and plugin copy. Returns a diff summary dict."""
    src_files = _included_files(source_dir)
    plg_files = _included_files(plugin_dir)
    added = sorted(set(src_files) - set(plg_files))       # in source, missing from plugin
    removed = sorted(set(plg_files) - set(src_files))      # in plugin, missing from source
    changed = sorted(p for p in set(src_files) & set(plg_files) if src_files[p] != plg_files[p])
    return {"added": added, "removed": removed, "changed": changed}


def sync(repo_root: Path, apply: bool, prune_orphans: bool) -> int:
    repo_root = repo_root.resolve()
    plugin_skills_dir = repo_root / "plugin" / "skills"

    try:
        source_skills = discover_source_skills(repo_root)
    except ValueError as e:
        print(f"❌ {e}")
        return 2

    plugin_skill_names = {
        p.name for p in plugin_skills_dir.iterdir() if p.is_dir()
    } if plugin_skills_dir.is_dir() else set()

    new_skills = sorted(set(source_skills) - plugin_skill_names)
    orphaned_skills = sorted(plugin_skill_names - set(source_skills))
    shared_skills = sorted(set(source_skills) & plugin_skill_names)

    updated_skills = []
    in_sync_skills = []
    per_skill_diff = {}
    for name in shared_skills:
        d = diff_skill(source_skills[name], plugin_skills_dir / name)
        if d["added"] or d["removed"] or d["changed"]:
            updated_skills.append(name)
            per_skill_diff[name] = d
        else:
            in_sync_skills.append(name)

    drift = bool(new_skills or orphaned_skills or updated_skills)

    print(f"Izvor: {len(source_skills)} skillova u fazama, plugin/skills/: {len(plugin_skill_names)} skillova\n")

    if new_skills:
        print(f"🆕 NOVO ({len(new_skills)}) — postoji u izvoru, nedostaje u pluginu:")
        for name in new_skills:
            print(f"   {name}")
        print()

    if updated_skills:
        print(f"✏️  IZMENJENO ({len(updated_skills)}) — sadržaj se razlikuje:")
        for name in updated_skills:
            d = per_skill_diff[name]
            bits = []
            if d["added"]:
                bits.append(f"+{len(d['added'])} novih fajlova")
            if d["removed"]:
                bits.append(f"-{len(d['removed'])} fajlova viška u pluginu")
            if d["changed"]:
                bits.append(f"{len(d['changed'])} izmenjenih")
            print(f"   {name} ({', '.join(bits)})")
        print()

    if orphaned_skills:
        print(f"👻 NAPUŠTENO ({len(orphaned_skills)}) — postoji u pluginu, više ne postoji ni u jednoj fazi:")
        for name in orphaned_skills:
            print(f"   {name}")
        print()

    print(f"✅ Usklađeno: {len(in_sync_skills)} / {len(shared_skills)} deljenih skillova")

    if not drift:
        print("\n✅ plugin/skills/ je potpuno usklađen sa izvorom. Ništa za sinhronizaciju.")
        return 0

    if not apply:
        print("\nPokreni sa --apply da primeniš sinhronizaciju (kopira NOVO i IZMENJENO;")
        print("za brisanje NAPUŠTENIH dodaj i --prune-orphans).")
        return 1

    # --- apply ---
    print("\n--- Primena ---")
    for name in new_skills + updated_skills:
        dest = plugin_skills_dir / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source_skills[name], dest,
                         ignore=shutil.ignore_patterns(*EXCLUDE_FILES, "__pycache__", ".git"))
        print(f"   synced: {name}")

    if orphaned_skills:
        if prune_orphans:
            for name in orphaned_skills:
                shutil.rmtree(plugin_skills_dir / name)
                print(f"   removed orphan: {name}")
        else:
            print(f"   ⚠️  {len(orphaned_skills)} napušten(ih) skill(ova) OSTAJE u pluginu "
                  f"(dodaj --prune-orphans da ih ukloniš): {', '.join(orphaned_skills)}")

    # Re-verify.
    recheck_new = sorted(set(source_skills) - {p.name for p in plugin_skills_dir.iterdir() if p.is_dir()})
    still_drift = False
    for name in shared_skills:
        if name in orphaned_skills:
            continue
        d = diff_skill(source_skills[name], plugin_skills_dir / name)
        if d["added"] or d["removed"] or d["changed"]:
            still_drift = True
    if recheck_new or still_drift:
        print("\n❌ Sinhronizacija primenjena, ali razlika i dalje postoji — proveri ručno.")
        return 1

    print("\n✅ Sinhronizovano. plugin/skills/ sada odgovara izvoru"
          + (" (napušteni skillovi nisu uklonjeni — koristi --prune-orphans)." if orphaned_skills and not prune_orphans else "."))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Proveri (i po želji primeni) sinhronizaciju plugin/skills/ sa izvornim fazama.")
    parser.add_argument("repo_root", nargs="?", default=".",
                         help="Koren repozitorijuma (podrazumevano trenutni direktorijum)")
    parser.add_argument("--apply", action="store_true",
                         help="Primeni sinhronizaciju (kopira NOVO/IZMENJENO iz izvora u plugin/skills/)")
    parser.add_argument("--prune-orphans", action="store_true",
                         help="Uz --apply, ukloni i skillove iz plugin/skills/ koji više ne postoje ni u jednoj fazi")
    args = parser.parse_args()

    sys.exit(sync(Path(args.repo_root), apply=args.apply, prune_orphans=args.prune_orphans))


if __name__ == "__main__":
    main()
