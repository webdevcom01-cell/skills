#!/usr/bin/env python3
"""Verify that SKILL.md's thin orchestrator and references/workflow.md's full
phase text agree on phase count, order, and names.

Why this exists: the phase list now lives in two files (SKILL.md keeps a
9-line orchestrator, references/workflow.md keeps the full mechanics -- see
CHANGELOG.md, round 7 "extract phase mechanics"). This project has already
miscounted things twice before the split even happened ("7 faza" reported
for 8 items; "17+5=22" reported for 23 fixtures), and a sweep done while
writing this script found NINE stale "(Faza N)" cross-references already
live across SKILL.md, references/*.md, and scripts/*.py -- all off by one
phase number, all silent until read closely. Splitting the phase list
across two files is a third opportunity for exactly that drift, and this
time it would be silent by construction: nothing else forces the two files
to agree. This script is that enforcement, run alongside verify_fixtures.py.

Not a general "(Faza N)" reference linter -- that would need to know, for
each prose mention, which phase it SHOULD point to, which is not mechanically
checkable. This only checks the two canonical phase lists against each other.

Run: python -B fixtures/verify_workflow_sync.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "SKILL.md"
WORKFLOW_MD = ROOT / "references" / "workflow.md"

ORCHESTRATOR_HEADING = re.compile(r"^## Workflow", re.MULTILINE)
NEXT_HEADING = re.compile(r"^## ", re.MULTILINE)
ORCHESTRATOR_ITEM = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*\s*$", re.MULTILINE)
WORKFLOW_HEADER = re.compile(r"^##\s+Faza\s+(\d+)\s+—\s+(.+?)\s*$", re.MULTILINE)


def _orchestrator_phases(text):
    start = ORCHESTRATOR_HEADING.search(text)
    if not start:
        return None, "SKILL.md nema '## Workflow' sekciju"
    rest = text[start.end():]
    end = NEXT_HEADING.search(rest)
    section = rest[:end.start()] if end else rest
    phases = [(int(n), name) for n, name in ORCHESTRATOR_ITEM.findall(section)]
    return phases, None


def _workflow_phases(text):
    phases = [(int(n), name) for n, name in WORKFLOW_HEADER.findall(text)]
    return phases, None


def check():
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    workflow_text = WORKFLOW_MD.read_text(encoding="utf-8")

    orchestrator, err = _orchestrator_phases(skill_text)
    if err:
        print(f"FAIL -- {err}")
        return False
    workflow, err = _workflow_phases(workflow_text)
    if err:
        print(f"FAIL -- {err}")
        return False

    ok = True
    if len(orchestrator) != len(workflow):
        print(
            f"FAIL -- broj faza se ne poklapa: SKILL.md orkestrator={len(orchestrator)}, "
            f"workflow.md={len(workflow)}"
        )
        ok = False

    for i, ((sk_n, sk_name), (wf_n, wf_name)) in enumerate(zip(orchestrator, workflow), start=1):
        if sk_n != i or wf_n != i:
            print(f"FAIL -- pozicija {i}: SKILL.md broji {sk_n}, workflow.md broji {wf_n} (očekivano oba {i})")
            ok = False
        if sk_name != wf_name:
            print(f"FAIL -- Faza {i}: SKILL.md='{sk_name}' != workflow.md='{wf_name}'")
            ok = False

    if ok:
        print(f"OK -- {len(orchestrator)} faza, imena i redosled se poklapaju u oba fajla.")
    return ok


def main():
    sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()
