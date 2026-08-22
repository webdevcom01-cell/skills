#!/usr/bin/env python3
"""
catalog_sync_check.py — checks that plugin/README.md's phase catalog and "Ukupno: N skillova."
count match the real contents of the phase folders (01-* .. 08-*).

This is the automated version of the manual check that found finding #3 in the original
forensic analysis: plugin-sync existed on disk but was missing from the README's phase catalog
and from its total count. Reusable any time a skill is added, removed, or moved between phases.

Method: parses each "### NN — Title" section in plugin/README.md and the backtick-quoted skill
names on the line(s) immediately below it, up to the next blank line or heading. Compares that
name set, per phase, against the real subfolders of NN-*/ that contain a SKILL.md. Also parses
the "**Ukupno: N skillova.**" line and compares N against the real total across all phases.

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


def actual_skills_by_phase(root: Path):
    result = {}
    for num, phase_dir in discover_phase_dirs(root).items():
        names = set()
        for child in phase_dir.iterdir():
            if child.is_dir() and (child / "SKILL.md").is_file():
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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo_root", nargs="?", default=".", help="Koren repoa (default: trenutni folder)")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()

    readme_path = root / "plugin" / "README.md"
    if not readme_path.is_file():
        print(f"❌ {readme_path} ne postoji.")
        sys.exit(2)
    readme_text = readme_path.read_text(encoding="utf-8", errors="replace")

    readme_catalog = parse_readme_catalog(readme_text)
    actual = actual_skills_by_phase(root)

    findings = []
    all_phases = sorted(set(readme_catalog) | set(actual))

    for phase in all_phases:
        readme_names = readme_catalog.get(phase, set())
        actual_names = actual.get(phase, set())
        missing_from_readme = actual_names - readme_names
        stale_in_readme = readme_names - actual_names
        for name in sorted(missing_from_readme):
            findings.append(f"[CATALOG] '{name}' postoji na disku u fazi {phase} ali nije u README katalogu te faze")
        for name in sorted(stale_in_readme):
            findings.append(f"[CATALOG] '{name}' je u README katalogu faze {phase} ali ne postoji na disku")

    # cross-phase: a skill listed under the wrong phase entirely
    all_readme_names = {n: p for p, names in readme_catalog.items() for n in names}
    all_actual_names = {n: p for p, names in actual.items() for n in names}
    for name, actual_phase in all_actual_names.items():
        readme_phase = all_readme_names.get(name)
        if readme_phase is not None and readme_phase != actual_phase:
            findings.append(f"[CATALOG] '{name}' je na disku u fazi {actual_phase} ali u README-u pod fazom {readme_phase}")

    total_actual = sum(len(v) for v in actual.values())
    m = README_TOTAL_RE.search(readme_text)
    if not m:
        findings.append("[CATALOG] Nije pronađena 'Ukupno: N skillova.' linija u README-u")
    else:
        total_readme = int(m.group(1))
        if total_readme != total_actual:
            findings.append(f"[CATALOG] README kaže 'Ukupno: {total_readme}', stvarno stanje na disku je {total_actual}")

    print(f"catalog-sync-check — {total_actual} skillova na disku, {len(all_phases)} faza\n")

    if findings:
        print(f"❌ {len(findings)} nalaza:")
        for f in findings:
            print(" ", f)
        sys.exit(1)
    else:
        print(f"✅ README fazni katalog i 'Ukupno: {total_actual} skillova.' tačno odgovaraju disku.")
        sys.exit(0)


if __name__ == "__main__":
    main()
