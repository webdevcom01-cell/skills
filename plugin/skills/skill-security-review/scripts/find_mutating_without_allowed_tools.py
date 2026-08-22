#!/usr/bin/env python3
"""
find_mutating_without_allowed_tools.py — finds skills that reference a state-mutating tool
(MCP write/delete operation, or destructive-sounding language) but declare no `allowed-tools:`
frontmatter field to actually constrain what they can call.

This is the mechanical, generalized version of the finding in
forenzicka-analiza-DODATAK.md §2: nine skills described themselves as mutating/deleting
production data while relying only on prose ("ask the user before...") to prevent an unwanted
action, with no allowed-tools scoping as a mechanical backstop. All nine were fixed directly
(commit "security(skills): dodaj allowed-tools za 9 operativnih skillova"), so a clean run here
now is the regression check that they stay fixed -- and this script's job going forward is to
catch the *next* skill that adds a mutating MCP call without allowed-tools, not just the
original nine by name.

Two independent signals, reported separately since their confidence differs:

1. TOOL-NAME signal (higher confidence): any `mcp__*__as_*` tool name mentioned anywhere in the
   skill's SKILL.md body is classified by its verb prefix as mutating (delete/patch/update/
   create/add/set) or read-only (get/list/search/find/inspect/diagnose/health_check/export) --
   name-based, not a hardcoded per-skill list, so a new as_* tool is classified automatically.
   Flagged if a skill mentions a mutating tool name and has no allowed-tools field.

2. KEYWORD signal (lower confidence, needs a human read): the description contains a strong
   destructive/irreversible keyword (delete, deletes, deletion, quarantine, irreversible,
   "cannot be undone", destructive, briše, brisanje) with no allowed-tools field. This catches
   skills that mutate through something other than a named as_* MCP tool (e.g. Bash, a raw file
   delete) that signal #1 can't see -- reported as a separate, softer bucket, not merged with #1.

Neither signal proves the skill is unsafe, and this script never judges whether a given
allowed-tools scope (once present) is actually *sufficient* or *too broad* for what the skill
describes doing -- that comparison requires reading the skill's actual behavior and reasoning
about it, which is exactly why skill-security-review's SKILL.md asks the invoking agent to do
that reading as a second, semantic step after this script's mechanical first pass.

Exit 0 if nothing is flagged. Exit 1 if either bucket has findings. Report-only.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

PHASE_RE = re.compile(r"^\d\d-")
MCP_TOOL_RE = re.compile(r"\bmcp__[a-zA-Z0-9_-]+__(as_[a-zA-Z0-9_]+)\b")

MUTATING_PREFIXES = ("as_delete_", "as_patch_", "as_update_", "as_create_", "as_add_", "as_set_")
READONLY_PREFIXES = (
    "as_get_", "as_list_", "as_search_", "as_find_", "as_inspect_", "as_diagnose_",
    "as_health_", "as_export_", "as_run_eval",
)

KEYWORD_RE = re.compile(
    r"\b(delete[sd]?|deletion|quarantine[sd]?|irreversib\w*|cannot be undone|destructive|"
    r"bri[sš]e\w*|brisanj\w*)\b",
    re.IGNORECASE,
)


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
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def has_allowed_tools(fm_text: str) -> bool:
    try:
        data = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        # Fall back to a plain text check if the frontmatter doesn't parse cleanly -- better to
        # risk a false "has it" than crash the whole scan on one malformed file.
        return "allowed-tools" in fm_text
    return isinstance(data, dict) and bool(data.get("allowed-tools"))


def classify_tool(name: str):
    if name.startswith(MUTATING_PREFIXES):
        return "mutating"
    if name.startswith(READONLY_PREFIXES):
        return "readonly"
    return "ambiguous"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo_root", nargs="?", default=".", help="Koren repoa (default: trenutni folder)")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()

    tool_findings, keyword_findings, ambiguous_notes = [], [], []

    for skill_dir in discover_skill_dirs(root):
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        fm_text, body = split_frontmatter(text)
        if has_allowed_tools(fm_text):
            continue  # already scoped -- not this script's job to judge if the scope is right

        tool_names = {m.group(1) for m in MCP_TOOL_RE.finditer(text)}
        mutating = sorted(n for n in tool_names if classify_tool(n) == "mutating")
        ambiguous = sorted(n for n in tool_names if classify_tool(n) == "ambiguous")

        if mutating:
            tool_findings.append(f"[MUTATING-TOOL] {skill_dir.name}: pominje {mutating} bez allowed-tools")
        if ambiguous:
            ambiguous_notes.append(f"[AMBIGUOUS-TOOL] {skill_dir.name}: pominje {ambiguous} (nije klasifikovano ni kao mutating ni readonly) bez allowed-tools")

        # Keyword signal on the frontmatter description only (not the whole body) -- the body of
        # a long skill almost always contains words like "delete" somewhere incidentally
        # (e.g. "Do NOT use for deleting X"); the description is what the skill claims about
        # itself, which is what the original finding was actually about.
        desc_match = re.search(r"description:\s*(.*?)(?=\n[a-zA-Z_-]+:|\Z)", fm_text, re.DOTALL)
        description = desc_match.group(1) if desc_match else ""
        if KEYWORD_RE.search(description) and not mutating:
            # Only added if not already caught by the tool-name signal, to avoid double-counting
            # the same skill in both buckets.
            keyword_findings.append(f"[KEYWORD] {skill_dir.name}: opis sadrži destruktivan jezik bez allowed-tools")

    total = len(tool_findings) + len(keyword_findings)
    print("find_mutating_without_allowed_tools — mehanički sken (tool-name + keyword signali)\n")

    if ambiguous_notes:
        print(f"--- Nejasno klasifikovani alati ({len(ambiguous_notes)}) — pogledaj ručno ---")
        for n in ambiguous_notes:
            print(" ", n)
        print()

    if tool_findings:
        print(f"❌ Mutating MCP alat bez allowed-tools ({len(tool_findings)}):")
        for f in tool_findings:
            print(" ", f)
        print()

    if keyword_findings:
        print(f"⚠️  Destruktivan jezik u opisu bez allowed-tools, nije preko as_* alata ({len(keyword_findings)}) — pogledaj ručno:")
        for f in keyword_findings:
            print(" ", f)
        print()

    if total:
        sys.exit(1)
    else:
        print("✅ Nema skillova koji pominju mutating alat ili destruktivan jezik bez allowed-tools.")
        sys.exit(0)


if __name__ == "__main__":
    main()
