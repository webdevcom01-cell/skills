#!/usr/bin/env python3
"""Regression self-test for check_sources.py, with mutation coverage.

Every case corresponds to a defect that once shipped. Two adversarial reviews and four
real research runs produced this list.

The mutation pass exists because an earlier version of this suite was green after the
entire ASSERTION branch was deleted from the checker: it had no case for two of the five
risk categories, so it certified a checker that had stopped checking. A test suite that
survives its subject being gutted is not a test suite.

    python3 scripts/selftest.py            # cases only
    python3 scripts/selftest.py --mutate   # also verify the suite detects weakenings
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "check_sources.py")

SOURCES = """
## Sources
- [own site] https://acme.example.com/about — fetched 2026-07-30
- [registry] https://registry.example/co/1 — fetched 2026-07-30
- [filing] https://acme.example.com/f.pdf — fetched 2026-07-30
- [tbd] https://acme.example.com/pending — placeholder deliberately listed
"""

results = []


def record(name, ok, detail=""):
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


def check(body, tmp, script=None, strict=True):
    path = os.path.join(tmp, f"t{len(os.listdir(tmp))}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# D\n" + body + SOURCES)
    cmd = [sys.executable, script or CHECK, path] + (["--strict"] if strict else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout, r.returncode


# Cases: (name, body, must_be_flagged, expected_marker_or_None)
FLAG_CASES = [
    ("short field line with a number", "- Employees: 400\n", "NUMBER"),
    ("currency before the digits", "- Revenue: $4.2m in 2024\n", "NUMBER"),
    ("magnitude suffix without a unit", "They moved 12k MT last year.\n", "NUMBER"),
    ("unit before the figure", "Headcount is 400 across the group.\n", "NUMBER"),
    ("figure inside a table row", "| Throughput | 50,000 MT, up 30% |\n", "NUMBER"),
    ("registration number as a bare field", "- RC 1234567\n", "NUMBER"),
    ("vague attribution is not a source",
     "According to industry sources, it handles over 50,000 MT annually.\n", "NUMBER"),
    ("hedged claim still needs a label",
     "The company states it handles 90,000 MT of oils annually.\n", "NUMBER"),
    ("note in brackets is not a citation",
     "Turnover reached 12 million USD in 2024 [figure to be checked].\n", None),
    # This one isolates NOT_A_LABEL: the placeholder is listed in Sources, so the
    # undefined-label check cannot rescue the case and only NOT_A_LABEL can catch it.
    ("a placeholder listed in Sources is still not a citation",
     "Turnover reached 12 million USD in 2024. [tbd]\n", "note, not a source"),
    ("gap marker does not exempt a figure beside it",
     "Turnover was 12 million USD and headcount 400, though depots are TO CONFIRM.\n", "MIXED"),
    ("'unknown' does not exempt a figure",
     "Headcount is 400, though the split between offices is unknown.\n", "NUMBER"),
    ("'whether' does not exempt a figure",
     "Turnover was USD 4.2m in 2024, though whether that is group is unclear.\n", "NUMBER"),
    ("a question mark does not exempt a figure",
     "Revenue was USD 4.2m in 2024 — group or entity?\n", "NUMBER"),
    ("two disagreeing figures in section 9 are still claims",
     "The site claims 400 staff while the filing gives 260 — which basis is unclear.\n", "NUMBER"),
    ("undefined label is reported",
     "Turnover reached USD 4.2m in 2024. [some other source]\n", "pointing nowhere"),
    ("qualified Sources heading still validates labels",
     "Turnover reached USD 4.2m. [nope]\n", "pointing nowhere"),
    ("uncited assertion with no figure",
     "Acme is headquartered in Lagos and operates six blending plants there.\n", "ASSERTION"),
    ("uncited historical date",
     "The predecessor partnership began trading in 1974, well before the current entity.\n",
     "DATE"),
    ("uncited count in an uncommon unit", "Coverage spans 14 countries.\n", "NUMBER"),
    ("uncited tonnage", "They moved 12,000 tonnes last year.\n", "NUMBER"),
    ("a figure inside a methodology note is still a claim",
     "The aggregator research returned 4 shipments over the window.\n", "NUMBER"),
    ("Serbian assertion with a figure",
     "Preduzeće posluje od 2011. godine i zapošljava 120 radnika.\n", "NUMBER"),
    ("'Sources of supply' does not silence the file",
     "## Sources of supply\nThe refinery processes 90,000 MT and employs 250 people.\n",
     "NUMBER"),
]

PASS_CASES = [
    ("open question in section 9",
     "Was the 1986 founding date inherited from a predecessor entity?\n"),
    ("statement of ignorance in section 8",
     "The size of the documentation team is not known.\n"
     "Which system is the system of record is not established.\n"),
    ("bare URL counts as a citation",
     "They import and blend edible oils. https://acme.example.com/about\n"),
    ("two citation labels after the full stop",
     "Incorporated 12 March 2019, status active. [registry] [filing]\n"),
    ("cited field line", "- Employees: 400 [own site]\n"),
    ("cited table row and its header",
     "| Metric | Value | Source |\n|---|---|---|\n| Throughput | 50,000 MT | [own site] |\n"),
    ("gap marker alone with no figure", "Second office in Accra — UNVERIFIED.\n"),
    ("Serbian gap marker", "- Broj zaposlenih: NIJE UTVRĐENO\n"),
    ("hedge plus label",
     "The company states it handles 90,000 MT annually. [own site]\n"),
    ("editorial insertion inside a quotation",
     'In their words: "we import [and blend] edible oils" [own site]\n'),
    ("abbreviation with internal periods",
     "Gloss: d.o.o. is the Serbian private limited company, A.S. the Turkish [own site]\n"),
    ("hard-wrapped claim with the label on the next line",
     "The company operates six blending plants across the region\n"
     "and employs 400 people. [own site]\n"),
    ("methodology note about the research is not a claim",
     "The registry search could not be reached, so the entity fields are indirect.\n"),
    ("mandated file header block",
     "**INTERNAL — NOT FOR THE PROSPECT.**\nResearch date: 2026-07-30. Delete by 2026-10-28.\n"),
]

# Mutations: a plausible weakening, and the case that must start failing because of it.
MUTATIONS = [
    ("delete the ASSERTION branch",
     ('    if ASSERTIVE.search(text) and words >= 6:\n        return "ASSERTION"',
      '    if False:\n        return "ASSERTION"')),
    ("delete the DATE branch",
     ('    if YEAR.search(text) and words >= 8:\n        return "DATE"',
      '    if False:\n        return "DATE"')),
    ("shrink the unit list to % and MT",
     ('UNIT = (r"(?:%|per\\s?cent', 'UNIT = (r"(?:%|MT)#(?:per\\s?cent')),
    ("make NOT_A_LABEL never match",
     ('NOT_A_LABEL = re.compile(r"\\b(tbd|to be checked|to check|check before|verify|todo|to do|"\n'
      '                         r"placeholder|xxx|\\?\\?)\\b|^\\s*\\?+\\s*$", re.I)',
      'NOT_A_LABEL = re.compile(r"(?!x)x")')),
    ("make METHOD_PROSE swallow everything",
     ('METHOD_PROSE = re.compile(\n    r"\\b(?:dossier', 'METHOD_PROSE = re.compile(\n    r"(?:.|\\n)|\\b(?:dossier')),
    ("restore the whole-unit exemption order",
     ('    if has_figure(text):\n        return "MIXED" if GAP_MARKER.search(text) else "NUMBER"\n'
      '    if GAP_MARKER.search(text):\n        return None\n'
      '    if text.rstrip().endswith("?") or OPEN_QUESTION.search(text) or IGNORANCE.search(text):\n'
      '        return None',
      '    if text.rstrip().endswith("?") or OPEN_QUESTION.search(text) or IGNORANCE.search(text):\n'
      '        return None\n'
      '    if GAP_MARKER.search(text):\n        return None\n'
      '    if has_figure(text):\n        return "NUMBER"')),
]


def run_cases(tmp, script=None):
    """Return the list of case names that behaved wrongly."""
    failures = []
    for name, body, marker in FLAG_CASES:
        out, _ = check(body, tmp, script)
        ok = "Clean:" not in out and (marker is None or marker in out)
        if not ok:
            failures.append(name)
    for name, body in PASS_CASES:
        out, code = check(body, tmp, script)
        if "Clean:" not in out or code != 0:
            failures.append(name)
    return failures




def check_frontmatter():
    """Refuse to pass if SKILL.md would be rejected on save.

    The platform caps `description` at 1024. It is not documented whether that
    counts characters or bytes, and these descriptions carry diacritics, so both
    are held under 1000. A skill that will not save is a skill that does not
    exist, and nothing else in this suite would have noticed.
    """
    import re as _re
    import pathlib as _pl
    md = (_pl.Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
    parts = md.split("---")
    problems = []
    if len(parts) < 3:
        problems.append("SKILL.md has no --- frontmatter block")
    else:
        fm = parts[1]
        if not _re.search(r"^name:\s*\S", fm, _re.M):
            problems.append("no name field")
        m = _re.search(r"^description:\s*(.*?)(?=^\w+:|\Z)", fm, _re.S | _re.M)
        if not m:
            problems.append("no description field")
        else:
            d = m.group(1).strip()
            if d.startswith(">"):
                d = " ".join(l.strip() for l in d.splitlines()[1:] if l.strip())
            if len(d) > 1000:
                problems.append(f"description is {len(d)} characters; the platform refuses over 1024")
            if len(d.encode("utf-8")) > 1000:
                problems.append(f"description is {len(d.encode('utf-8'))} bytes; diacritics cost extra")
    print("== frontmatter ==")
    for p in problems:
        print(f"  FAIL {p}")
    if problems:
        raise SystemExit(1)

def main():
    check_frontmatter()
    mutate = "--mutate" in sys.argv
    tmp = tempfile.mkdtemp(prefix="pd-selftest-")
    print(f"Workspace: {tmp}\n")

    print("Must be flagged")
    for name, body, marker in FLAG_CASES:
        out, _ = check(body, tmp)
        ok = "Clean:" not in out
        detail = ""
        if ok and marker and marker not in out:
            ok, detail = False, f"flagged, but not as {marker}"
        record(name, ok, detail or ("clean — claim slipped through" if not ok else ""))

    print("\nMust pass — constructs the format requires")
    for name, body in PASS_CASES:
        out, code = check(body, tmp)
        ok = "Clean:" in out and code == 0
        bad = [l.strip() for l in out.splitlines() if l.strip().startswith("line ")]
        record(name, ok, "; ".join(bad[:2]) if not ok else "")

    print("\nExit codes and gating")
    out, code = check("Nothing here.\n".replace(SOURCES, ""), tmp)
    out2, code2 = subprocess.run(
        [sys.executable, CHECK, os.path.join(tmp, "no-sources.md"), "--strict"],
        capture_output=True, text=True).stdout, None
    with open(os.path.join(tmp, "ns.md"), "w", encoding="utf-8") as fh:
        fh.write("# D\nAcme is a trading company based in Lagos with six depots.\n")
    r = subprocess.run([sys.executable, CHECK, os.path.join(tmp, "ns.md"), "--strict"],
                       capture_output=True, text=True)
    record("missing Sources block fails under --strict",
           r.returncode == 1 and "no Sources block" in r.stdout, f"exit={r.returncode}")
    r = subprocess.run([sys.executable, CHECK, os.path.join(tmp, "nope.md")],
                       capture_output=True, text=True)
    record("unreadable file exits 2", r.returncode == 2, f"exit={r.returncode}")
    with open(os.path.join(tmp, "bin.md"), "wb") as fh:
        fh.write(b"# D\n\xe9\xe9 400 people\n")
    r = subprocess.run([sys.executable, CHECK, os.path.join(tmp, "bin.md"), "--strict"],
                       capture_output=True, text=True)
    record("non-UTF-8 file exits 2, not 1", r.returncode == 2, f"exit={r.returncode}")
    out, code = check("- Employees: 400\n", tmp, strict=False)
    record("findings without --strict exit 0", code == 0, f"exit={code}")

    if mutate:
        print("\nMutation coverage — each weakening must break at least one case")
        source = open(CHECK, encoding="utf-8").read()
        for name, (old, new) in MUTATIONS:
            if old not in source:
                record(f"mutation: {name}", False, "mutation no longer applies — update it")
                continue
            mdir = tempfile.mkdtemp(prefix="pd-mut-")
            mpath = os.path.join(mdir, "check_sources.py")
            with open(mpath, "w", encoding="utf-8") as fh:
                fh.write(source.replace(old, new, 1))
            mtmp = tempfile.mkdtemp(prefix="pd-mutcase-")
            broke = run_cases(mtmp, script=mpath)
            record(f"mutation: {name}", bool(broke),
                   f"caught by {len(broke)} case(s)" if broke
                   else "SUITE DID NOT NOTICE — add a case for this branch")
            shutil.rmtree(mdir, ignore_errors=True)
            shutil.rmtree(mtmp, ignore_errors=True)
    else:
        print("\n(run with --mutate to verify the suite actually protects the checker)")

    failed = [n for n, ok in results if not ok]
    print(f"\n{'=' * 68}")
    print(f"{len(results) - len(failed)} passed, {len(failed)} failed")
    for n in failed:
        print(f"  FAILED: {n}")
    print("=" * 68)
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
