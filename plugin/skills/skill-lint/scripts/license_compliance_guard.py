#!/usr/bin/env python3
"""
license_compliance_guard.py — flags any skill LICENSE that's incompatible with sharing the
plugin as a distributable .plugin package.

plugin/README.md states the distribution model plainly: the plugin is meant to be uploaded and
installed by other Cowork/Claude Code users. A LICENSE.txt whose text explicitly forbids that
(Anthropic's own "Services only" example-skill license is the known case: "may not... Extract
these materials from the Services... Distribute, sublicense, or transfer these materials to any
third party") cannot legally sit inside that distributable package.

Method: any LICENSE file matching a known-permissive identifier (Apache, MIT, BSD, ISC, ...) is
treated as compliant without further inspection. Everything else is scanned for a restrictive
combination of phrases (not just the exact Anthropic wording, so a differently-worded future
restrictive license still gets caught) and flagged for a human to actually read and decide on --
this script never *concludes* a license is fine on the restrictive path, only that it needs eyes.

A skill with no LICENSE file at all is not flagged: silence isn't a restrictive license, it's
the absence of an explicit one (covered by whatever top-level LICENSE the repo itself carries,
which is a separate, repo-level question this script doesn't adjudicate).

Exit 0 if nothing restrictive is found. Exit 1 if any LICENSE needs review. Report-only.
"""

import argparse
import re
import sys
from pathlib import Path

PHASE_RE = re.compile(r"^\d\d-")
LICENSE_NAMES = {"LICENSE.txt", "LICENSE", "LICENSE.md"}

# Identifiers of well-known permissive licenses -- if any of these appear near the top of the
# file, treat it as compliant without running the restrictive-phrase heuristic below. Checked
# as case-insensitive substrings.
PERMISSIVE_IDENTIFIERS = [
    "apache license",
    "mit license",
    "bsd license",
    "bsd 2-clause",
    "bsd 3-clause",
    "isc license",
    "mozilla public license",
    "the unlicense",
    "creative commons",
]

# Phrases that, in combination, indicate a restrictive "not for redistribution" license --
# modeled on the exact Anthropic docx/pdf/pptx/xlsx wording found in the forensic analysis, but
# written as independent signals (not one exact-match string) so a differently-worded future
# restrictive license still trips this.
RESTRICTIVE_SIGNALS = [
    re.compile(r"\ball rights reserved\b", re.IGNORECASE),
    re.compile(r"\bmay not\b.{0,80}\b(distribute|sublicense|transfer)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\boutside the services\b", re.IGNORECASE),
    re.compile(r"\bthird part(y|ies)\b", re.IGNORECASE),
    re.compile(r"\bretain copies\b", re.IGNORECASE),
]
# How many distinct signals must hit before we flag it -- one alone (e.g. just "third party" in
# an otherwise-permissive license's boilerplate) is too weak on its own.
RESTRICTIVE_THRESHOLD = 2


def discover_phase_dirs(root: Path):
    return sorted(p for p in root.iterdir() if p.is_dir() and PHASE_RE.match(p.name))


def find_license_files(root: Path):
    files = []
    for phase_dir in discover_phase_dirs(root):
        for skill_dir in sorted(phase_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            for name in LICENSE_NAMES:
                candidate = skill_dir / name
                if candidate.is_file():
                    files.append((skill_dir.name, candidate))
    return files


def classify(text: str):
    lowered = text.lower()
    for ident in PERMISSIVE_IDENTIFIERS:
        if ident in lowered:
            return "permissive", ident

    hits = [sig.pattern for sig in RESTRICTIVE_SIGNALS if sig.search(text)]
    if len(hits) >= RESTRICTIVE_THRESHOLD:
        return "restrictive", hits
    return "unknown", hits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo_root", nargs="?", default=".", help="Koren repoa (default: trenutni folder)")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()

    license_files = find_license_files(root)
    restrictive, unknown, permissive = [], [], []

    for skill_name, path in license_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        verdict, detail = classify(text)
        if verdict == "restrictive":
            restrictive.append((skill_name, path, detail))
        elif verdict == "unknown":
            unknown.append((skill_name, path, detail))
        else:
            permissive.append((skill_name, path, detail))

    print(f"license-compliance-guard — {len(license_files)} LICENSE fajlova pregledano\n")

    if permissive:
        print(f"✅ Permisivna ({len(permissive)}): " + ", ".join(s for s, _, _ in permissive))
        print()

    if unknown:
        print(f"--- Nepoznato ({len(unknown)}) — nije prepoznat kao permisivan, ali ni ispod praga za restriktivan; pogledaj ručno ---")
        for skill_name, path, hits in unknown:
            print(f"  {skill_name} ({path}) — signali: {hits or 'nijedan'}")
        print()

    if restrictive:
        print(f"❌ {len(restrictive)} LICENSE fajl(ova) izgleda restriktivno (nespojivo sa deljivim .plugin paketom):")
        for skill_name, path, hits in restrictive:
            print(f"  [LICENSE] {skill_name} ({path}) — signali: {hits}")
        sys.exit(1)
    else:
        print("✅ Nema restriktivnih licenci.")
        sys.exit(0)


if __name__ == "__main__":
    main()
