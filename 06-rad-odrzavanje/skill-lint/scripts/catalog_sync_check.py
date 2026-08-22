#!/usr/bin/env python3
"""
catalog_sync_check.py — checks that a distributable package's README.md phase catalog and
"Ukupno: N skillova." count match the real contents of that package's skills/ folder,
cross-referenced against the phase folders (01-* .. 08-*) only to know which phase each one
belongs to.

This is the automated version of the manual check that found finding #3 in the original
forensic analysis: plugin-sync existed on disk but was missing from the README's phase catalog
and from its total count. Reusable any time a skill is added, removed, or moved between phases.

A skill can legitimately exist in a phase folder but be absent from a given package's skills/ —
e.g. a skill kept for personal use whose LICENSE.txt doesn't permit redistribution
(market-research-navigator, system-teardown), a repo-maintenance-only meta-tool (plugin-sync), a
single-client-hardcoded skill (tender-projekat), or a skill that belongs to the OTHER package
(as of 22.08.2026 the repo ships two packages: plugin/ — general-purpose toolkit — and
plugin-soma-ops/ — Agent Studio/AgentStack/SOMA-pipeline-specific). Such a skill is correctly
absent from a given package's README catalog, so ground truth for "what should be listed" is
that package's own skills/ mirror, not the phase folder alone — a phase-folder skill only counts
for a package if it is also mirrored into that package's skills/.

Method: parses each "### NN — Title" section in <package>/README.md and the backtick-quoted skill
names on the line(s) immediately below it, up to the next blank line or heading. Compares that
name set, per phase, against the real subfolders of NN-*/ that contain a SKILL.md AND are also
present under <package>/skills/. Also parses the "**Ukupno: N skillova.**" line and compares N
against the real total across all phases.

Usage: catalog_sync_check.py [repo_root] [--package-dir plugin|plugin-soma-ops]
Default --package-dir is "plugin" (backward compatible with the single-package era). Run it once
per package to check the whole repo.

Exit 0 if the catalog and count are exactly in sync. Exit 1 on any drift. Report-only.
"""

import argparse
import re
import sys
from pathlib import Path

PHASE_DIR_RE = re.compile(r"^(\d\d)-")
README_HEADING_RE = re.compile(r"^###\s+(\d\d)\s*—\s*(.+?)\s*$", re.MULTILINE)
README_TOTAL_RE = re.compile(r"Ukupno:\s*(\d+)\s*skillova", re.IGNORECASE)
BACKTICK_NAME_RE = re.compile(r"`([a-zA-Z0-9._-]+)`")


def discover_phase_dirs(root: Path):
    dirs = {}
    for p in root.iterdir():
        if p.is_dir():
            m = PHASE_DIR_RE.match(p.name)
            if m:
                dirs[m.group(1)] = p
    return dirs


def actual_skills_by_phase(root: Path, package_dir: str):
    pkg_skills_dir = root / package_dir / "skills"
    result = {}
    for num, phase_dir in discover_phase_dirs(root).items():
        names = set()
        for child in phase_dir.iterdir():
            if child.is_dir() and (child / "SKILL.md").is_file():
                # Only count it if it's also mirrored into this package's skills/ — a skill can
                # legitimately live in the phase folder only, or be mirrored into the OTHER
                # package instead, without being catalog drift for THIS package.
                if (pkg_skills_dir / child.name).is_dir():
                    names.add(child.name)
        result[num] = names
    return result


def parse_readme_catalog(readme_text: str):
    """Return {phase_num: set(skill_names)} by reading each '### NN — Title' section and the
    backtick-quoted names on the non-blank lines directly under it."""
    headings = list(README_HEADING_RE.finditer(readme_text))
    catalog = {}
    for i, m in enumerate(headings):
        phase_num = m.group(1)
        section_start = m.end()
        section_end = headings[i + 1].start() if i + 1 < len(headings) else len(readme_text)
        section_text = readme_text[section_start:section_end]
        # Only the first non-blank paragraph under the heading is the skill list -- stop at the
        # first blank line so prose further down in the section isn't scanned for stray backticks.
        first_para = section_text.split("\n\n", 1)[0]
        names = set(BACKTICK_NAME_RE.findall(first_para))
        catalog[phase_num] = names
    return catalog


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo_root", nargs="?", default=".", help="Koren repoa (default: trenutni folder)")
    ap.add_argument("--package-dir", default="plugin", help="Koji distributable paket da proveri (default: plugin)")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()
    package_dir = args.package_dir

    readme_path = root / package_dir / "README.md"
    if not readme_path.is_file():
        print(f"❌ {readme_path} ne postoji.")
        sys.exit(2)
    readme_text = readme_path.read_text(encoding="utf-8", errors="replace")

    readme_catalog = parse_readme_catalog(readme_text)
    actual = actual_skills_by_phase(root, package_dir)

    findings = []
    all_phases = sorted(set(readme_catalog) | set(actual))

    for phase in all_phases:
        readme_names = readme_catalog.get(phase, set())
        actual_names = actual.get(phase, set())
        missing_from_readme = actual_names - readme_names
        stale_in_readme = readme_names - actual_names
        for name in sorted(missing_from_readme):
            findings.append(f"[CATALOG:{package_dir}] '{name}' postoji na disku u fazi {phase} ali nije u README katalogu te faze")
        for name in sorted(stale_in_readme):
            findings.append(f"[CATALOG:{package_dir}] '{name}' je u README katalogu faze {phase} ali ne postoji na disku")

    # cross-phase: a skill listed under the wrong phase entirely
    all_readme_names = {n: p for p, names in readme_catalog.items() for n in names}
    all_actual_names = {n: p for p, names in actual.items() for n in names}
    for name, actual_phase in all_actual_names.items():
        readme_phase = all_readme_names.get(name)
        if readme_phase is not None and readme_phase != actual_phase:
            findings.append(f"[CATALOG:{package_dir}] '{name}' je na disku u fazi {actual_phase} ali u README-u pod fazom {readme_phase}")

    total_actual = sum(len(v) for v in actual.values())
    m = README_TOTAL_RE.search(readme_text)
    if not m:
        findings.append(f"[CATALOG:{package_dir}] Nije pronađena 'Ukupno: N skillova.' linija u README-u")
    else:
        total_readme = int(m.group(1))
        if total_readme != total_actual:
            findings.append(f"[CATALOG:{package_dir}] README kaže 'Ukupno: {total_readme}', stvarno stanje na disku je {total_actual}")

    print(f"catalog-sync-check [{package_dir}] — {total_actual} skillova na disku, {len(all_phases)} faza\n")

    if findings:
        print(f"❌ {len(findings)} nalaza:")
        for f in findings:
            print(" ", f)
        sys.exit(1)
    else:
        print(f"✅ [{package_dir}] README fazni katalog i 'Ukupno: {total_actual} skillova.' tačno odgovaraju disku.")
        sys.exit(0)


if __name__ == "__main__":
    main()
