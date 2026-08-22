#!/usr/bin/env python3
"""
lint_metadata.py — mechanical SKILL.md hygiene: size, version/CHANGELOG match, pip deps.

Three independent checks, run over every skill folder under the phase folders (01-* .. 08-*):

1. Size: SKILL.md *body* (everything after the closing frontmatter '---') must stay under
   500 lines AND under ~5000 estimated tokens (len(body)/4 — the same chars/4 heuristic the
   original forensic analysis used, for comparable numbers). This mirrors the repo's own written
   standard in skill-creator-pro/references/skill-writing-guide.md. 300-499 lines with no
   references/ or scripts/ folder is a soft warning ("approaching the limit, add hierarchy"),
   not a hard violation.

2. Version vs CHANGELOG: when a skill has both a `version:` frontmatter field and a
   CHANGELOG.md, the changelog's topmost version heading must match the frontmatter value.

3. Pip deps vs requirements.txt: every third-party import (AST-parsed, not text search) in a
   skill's bundled .py files must be covered by a requirements.txt somewhere under that skill's
   folder. Stdlib modules are excluded via sys.stdlib_module_names (no hardcoded list — always
   matches the Python actually running this check).

Exit 0 if nothing hard is found (soft warnings/info still print). Exit 1 if any hard violation
or mismatch is found. Report-only — never modifies files.
"""

import argparse
import ast
import re
import sys
from pathlib import Path

import yaml

PHASE_RE = re.compile(r"^\d\d-")
LINE_LIMIT = 500
TOKEN_LIMIT = 5000
SOFT_ZONE_START = 300

STDLIB = set(getattr(sys, "stdlib_module_names", ()))
# A handful of extra names that are effectively stdlib-adjacent / always available and would
# otherwise be false positives; kept tiny and explicit rather than growing into a hidden list.
STDLIB |= {"__future__", "_typeshed"}

# import-name -> PyPI distribution-name, for the well-known cases where they differ (a
# requirements.txt lists the PyPI name, but the import uses a different name). Kept small and
# explicit; anything not in this map is assumed identical, which is true for most packages.
IMPORT_TO_DIST = {
    "PIL": "pillow",
    "yaml": "pyyaml",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "sklearn": "scikit-learn",
    "attr": "attrs",
    "attrs": "attrs",
    "google": "google-api-python-client",
}


def discover_phase_dirs(root: Path):
    return sorted(p for p in root.iterdir() if p.is_dir() and PHASE_RE.match(p.name))


def discover_skill_dirs(root: Path):
    skills = []
    for phase_dir in discover_phase_dirs(root):
        for child in sorted(phase_dir.iterdir()):
            if child.is_dir() and (child / "SKILL.md").is_file():
                skills.append(child)
    return skills


def split_frontmatter(text: str):
    """Return (frontmatter_text, body_text). Body excludes the closing '---' line itself."""
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    # parts[0] is '' (before the opening ---), parts[1] is frontmatter, parts[2] is body
    return parts[1], parts[2].lstrip("\n")


def check_size(skill_dir: Path, body: str, findings: list, warnings: list):
    lines = body.count("\n") + (1 if body and not body.endswith("\n") else 0)
    tokens_est = round(len(body) / 4)
    has_hierarchy = (skill_dir / "references").is_dir() or (skill_dir / "scripts").is_dir()

    if lines >= LINE_LIMIT or tokens_est >= TOKEN_LIMIT:
        findings.append(
            f"[SIZE] {skill_dir.name}: body {lines} linija (limit {LINE_LIMIT}), "
            f"~{tokens_est} procenjenih tokena (limit {TOKEN_LIMIT})"
            + ("" if has_hierarchy else " — nema references/ ni scripts/")
        )
    elif lines >= SOFT_ZONE_START and not has_hierarchy:
        warnings.append(
            f"[SIZE-WARN] {skill_dir.name}: body {lines} linija (zona {SOFT_ZONE_START}-{LINE_LIMIT-1}), "
            f"nema references/ ni scripts/ — vodič preporučuje hijerarhiju pre nego što se dostigne limit"
        )


def get_frontmatter_version(fm_text: str):
    """version: lives at the top level in most skills, but nested under metadata: in a few
    (e.g. geo-prompt-library) -- check both. Uses real YAML parsing, not regex, since the
    frontmatter structure varies enough between skills that a line-anchored regex misses the
    nested case entirely."""
    try:
        data = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    if "version" in data:
        return str(data["version"]).strip()
    metadata = data.get("metadata")
    if isinstance(metadata, dict) and "version" in metadata:
        return str(metadata["version"]).strip()
    return None


def check_version_changelog(skill_dir: Path, fm_text: str, findings: list, info: list):
    version = get_frontmatter_version(fm_text)
    changelog = skill_dir / "CHANGELOG.md"
    if version is None or not changelog.is_file():
        return  # only fires when both exist
    changelog_text = changelog.read_text(encoding="utf-8", errors="replace")
    # Heading formats seen in this repo: "## [1.0.0] ...", "## v2.0.0 ...", "## 0.2.5 ...".
    # "## Version History" (no digits) falls through to the info note below on purpose --
    # there's nothing machine-parseable to compare there.
    m = re.search(r"^##\s*\[?v?(\d+\.\d+(?:\.\d+)?)\]?", changelog_text, re.MULTILINE | re.IGNORECASE)
    if not m:
        info.append(f"[VERSION-INFO] {skill_dir.name}: CHANGELOG.md postoji ali nema prepoznatljiv broj verzije na vrhu")
        return
    top_version = m.group(1).strip()
    if top_version != version:
        findings.append(
            f"[VERSION] {skill_dir.name}: frontmatter version='{version}' != CHANGELOG.md vrh '{top_version}'"
        )


def collect_pip_imports(py_file: Path):
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"), filename=str(py_file))
    except SyntaxError:
        return set(), [f"[PARSE-WARN] {py_file}: SyntaxError pri AST parsiranju, preskačem"]
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # relative import, not a pip package
            if node.module:
                mods.add(node.module.split(".")[0])
    return mods, []


def local_module_names(skill_dir: Path):
    """Top-level names that resolve to a sibling file/package inside this skill folder —
    these are local imports (e.g. `import evaluate_prompt` for a sibling
    scripts/evaluate_prompt.py, or `import scripts` for a scripts/__init__.py package), never
    a pip dependency, even though AST can't tell the difference from a real package import."""
    names = set()
    for py_file in skill_dir.rglob("*.py"):
        names.add(py_file.stem)  # evaluate_prompt.py -> "evaluate_prompt"
    for init_file in skill_dir.rglob("__init__.py"):
        names.add(init_file.parent.name)  # scripts/__init__.py -> "scripts"
    return names


def check_pip_deps(skill_dir: Path, findings: list, parse_warnings: list):
    py_files = list(skill_dir.rglob("*.py"))
    if not py_files:
        return
    all_mods = set()
    for f in py_files:
        mods, warns = collect_pip_imports(f)
        all_mods |= mods
        parse_warnings.extend(warns)

    local = local_module_names(skill_dir)
    third_party = {m for m in all_mods if m not in STDLIB and m not in local}
    if not third_party:
        return

    req_files = list(skill_dir.rglob("requirements.txt"))
    declared = set()
    for rf in req_files:
        for line in rf.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # strip version specifiers / extras: "jsonschema>=4.0" -> "jsonschema"
            name = re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].strip()
            if name:
                declared.add(name.lower())

    def is_declared(mod: str) -> bool:
        dist_name = IMPORT_TO_DIST.get(mod, mod).lower()
        return mod.lower() in declared or dist_name in declared

    missing = sorted(m for m in third_party if not is_declared(m))
    if missing:
        findings.append(
            f"[DEPS] {skill_dir.name}: importuje {missing} bez odgovarajućeg requirements.txt zapisa"
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo_root", nargs="?", default=".", help="Koren repoa (default: trenutni folder)")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()

    skill_dirs = discover_skill_dirs(root)
    findings, warnings, info, parse_warnings = [], [], [], []

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        fm_text, body = split_frontmatter(text)

        check_size(skill_dir, body, findings, warnings)
        check_version_changelog(skill_dir, fm_text, findings, info)
        check_pip_deps(skill_dir, findings, parse_warnings)

    print(f"skill-lint / lint_metadata.py — {len(skill_dirs)} skillova provereno\n")

    if parse_warnings:
        print("--- Upozorenja pri parsiranju ---")
        for w in parse_warnings:
            print(" ", w)
        print()

    if info:
        print("--- Informativno (nije greška) ---")
        for i in info:
            print(" ", i)
        print()

    if warnings:
        print(f"--- Meka upozorenja ({len(warnings)}) — u zoni 300-499 linija bez hijerarhije ---")
        for w in warnings:
            print(" ", w)
        print()

    if findings:
        print(f"❌ {len(findings)} tvrdih nalaza:")
        for f in findings:
            print(" ", f)
        sys.exit(1)
    else:
        print("✅ Nema tvrdih nalaza (veličina/verzija/deps u redu).")
        sys.exit(0)


if __name__ == "__main__":
    main()
