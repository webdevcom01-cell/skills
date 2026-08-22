#!/usr/bin/env python3
"""
package_plugin.py — Zip plugin/ into a distributable .plugin file for Cowork/Claude Code.

Modeled on skill-creator-pro's scripts/package_skill.py (same exclude-pattern
approach, same zipfile walk, same "validate before you zip" order) but one level
up: it packages the whole plugin/ folder (every skill under plugin/skills/, plus
.claude-plugin/plugin.json) instead of a single skill folder.

One deliberate difference from package_skill.py: the zip's top-level folder is
named after plugin.json's "name" field, not the on-disk folder name ("plugin").
That matches how an installed plugin actually lays out on disk (<plugin-name>/
.claude-plugin/..., <plugin-name>/skills/<skill>/...) — zipping the literal
"plugin/" folder name would ship a package that unpacks into a folder just called
"plugin", which is wrong for anyone with more than one plugin installed.

Run sync_plugin.py first (or --check-sync here) — packaging a plugin/skills/
that's already drifted from the source phase folders ships stale skills.
"""

import argparse
import fnmatch
import json
import subprocess
import sys
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git"}
EXCLUDE_GLOBS = {"*.pyc"}
EXCLUDE_FILES = {".DS_Store"}
# Per-skill dirs dropped only from the distributable zip (dev/test scaffolding
# the installed skill doesn't need at runtime) — plugin/skills/ on disk keeps them.
PER_SKILL_EXCLUDE_DIRS = {"evals"}


def should_exclude(rel_path: Path) -> bool:
    """rel_path is relative to plugin_dir, e.g. skills/<name>/evals/case-1.json."""
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    # parts: ("skills", "<skill-name>", "evals", ...) -> exclude at this depth only.
    if len(parts) > 2 and parts[0] == "skills" and parts[2] in PER_SKILL_EXCLUDE_DIRS:
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_GLOBS)


def validate_plugin(plugin_dir: Path) -> tuple[bool, str]:
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        return False, f"Nema .claude-plugin/plugin.json u {plugin_dir}"
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return False, f"plugin.json nije validan JSON: {e}"
    for key in ("name", "version"):
        if not manifest.get(key):
            return False, f"plugin.json nema polje '{key}'"

    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        return False, f"Nema skills/ foldera u {plugin_dir}"

    skill_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir())
    if not skill_dirs:
        return False, "skills/ folder je prazan — nema šta da se pakuje"

    missing_skill_md = [p.name for p in skill_dirs if not (p / "SKILL.md").exists()]
    if missing_skill_md:
        return False, f"{len(missing_skill_md)} skill(ova) nema SKILL.md: {', '.join(missing_skill_md)}"

    return True, f"{len(skill_dirs)} skillova, manifest OK ({manifest['name']} v{manifest['version']})"


def check_sync(plugin_dir: Path) -> bool:
    """Run sync_plugin.py in check mode against the repo this plugin/ lives in.

    Returns True if in sync (or the check couldn't run — e.g. sync_plugin.py isn't
    on this machine yet), False only on a confirmed, reported drift.
    """
    sync_script = plugin_dir.parent / "06-rad-odrzavanje" / "plugin-sync" / "scripts" / "sync_plugin.py"
    if not sync_script.exists():
        print("ℹ️  sync_plugin.py nije nađen — preskačem proveru usklađenosti.")
        return True
    result = subprocess.run(
        [sys.executable, str(sync_script), str(plugin_dir.parent)],
        capture_output=True, text=True,
    )
    print(result.stdout)
    return result.returncode == 0


def package_plugin(plugin_dir: str, output_dir: str | None = None, skip_sync_check: bool = False) -> Path | None:
    plugin_dir = Path(plugin_dir).resolve()

    if not plugin_dir.is_dir():
        print(f"❌ Error: folder nije nađen: {plugin_dir}")
        return None

    print("🔍 Validacija plugina...")
    valid, message = validate_plugin(plugin_dir)
    if not valid:
        print(f"❌ Validacija nije prošla: {message}")
        return None
    print(f"✅ {message}\n")

    if not skip_sync_check:
        print("🔍 Provera usklađenosti sa izvornim fazama...")
        if not check_sync(plugin_dir):
            print("❌ plugin/skills/ nije usklađen sa izvorom — pokreni sync_plugin.py --apply prvo,")
            print("   ili prosledi --skip-sync-check da ipak spakuješ trenutno stanje.")
            return None
        print("✅ Usklađeno.\n")

    manifest = json.loads((plugin_dir / ".claude-plugin" / "plugin.json").read_text())
    plugin_name = manifest["name"]

    output_path = Path(output_dir).resolve() if output_dir else Path.cwd()
    output_path.mkdir(parents=True, exist_ok=True)
    plugin_filename = output_path / f"{plugin_name}.plugin"

    try:
        with zipfile.ZipFile(plugin_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in sorted(plugin_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                rel = file_path.relative_to(plugin_dir)
                if should_exclude(rel):
                    print(f"  Skipped: {rel}")
                    continue
                arcname = Path(plugin_name) / rel
                zipf.write(file_path, arcname)
        print(f"\n✅ Spakovano u: {plugin_filename}")
        return plugin_filename
    except Exception as e:
        print(f"❌ Greška pri pravljenju .plugin fajla: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Zip plugin/ folder u distributable .plugin fajl.")
    parser.add_argument("plugin_dir", nargs="?", default="plugin",
                         help="Putanja do plugin/ foldera (podrazumevano ./plugin)")
    parser.add_argument("output_dir", nargs="?", default=None,
                         help="Izlazni direktorijum (podrazumevano trenutni)")
    parser.add_argument("--skip-sync-check", action="store_true",
                         help="Spakuj i ako plugin/skills/ nije usklađen sa izvornim fazama")
    args = parser.parse_args()

    result = package_plugin(args.plugin_dir, args.output_dir, args.skip_sync_check)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
