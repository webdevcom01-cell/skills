#!/usr/bin/env python3
"""Verify fixtures/*.json against fixtures/expectations.json -- the source of
truth for what each fixture should do. NOT the filename prefix: p03_branded_over
.json is a deliberate exception (a 'p'-prefixed fixture that must FAIL), and a
filename-based check reads it as a bug and invites someone to "fix" a fixture
that is working exactly as designed.

Run:
  python -B fixtures/verify_fixtures.py             # check all fixtures against expectations.json
  python -B fixtures/verify_fixtures.py --capture    # print current gate output as an expectations.json draft

--capture output is a starting point, not something to paste in blind: review
the "note" field for each entry (capture always writes "TODO") and confirm any
changed failing_rules/derived_rules are the change you intended before
overwriting expectations.json.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent
GATE_SCRIPT = FIXTURES_DIR.parent / "scripts" / "validate_library.py"
EXPECTATIONS_PATH = FIXTURES_DIR / "expectations.json"

# Files in fixtures/ that are not gate input: dev tooling and the
# network-requiring verify_grounding.py demo (see its own "_note" field).
NOT_A_GATE_FIXTURE = {"expectations.json", "grounding_live_dentio.json"}


def run_gate(path):
    result = subprocess.run(
        [sys.executable, "-B", str(GATE_SCRIPT), str(path)], capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, result.stderr or result.stdout


def capture():
    out = {}
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        if path.name in NOT_A_GATE_FIXTURE:
            continue
        report, error = run_gate(path)
        if report is None:
            print(f"# {path.name}: gate produced no JSON -- {error}", file=sys.stderr)
            continue
        failing = sorted(c["rule"] for c in report["checks"] if not c["passed"])
        derived = sorted(c["rule"] for c in report["checks"] if not c["passed"] and c.get("derived"))
        out[path.name] = {
            "expect": "pass" if report["passed"] else "fail",
            "failing_rules": failing,
            "derived_rules": derived,
            "note": "TODO",
        }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def check():
    raw = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))
    expectations = {k: v for k, v in raw.items() if not k.startswith("_")}

    on_disk = {p.name for p in FIXTURES_DIR.glob("*.json") if p.name not in NOT_A_GATE_FIXTURE}
    missing = on_disk - set(expectations)
    stale = set(expectations) - on_disk
    if missing:
        print(f"WARN: fixture(s) with no expectations.json entry (not checked): {sorted(missing)}")
    if stale:
        print(f"WARN: expectations.json entry with no matching fixture file: {sorted(stale)}")

    all_ok = True
    for name in sorted(expectations):
        path = FIXTURES_DIR / name
        if not path.exists():
            continue
        expected = expectations[name]
        report, error = run_gate(path)
        if report is None:
            print(f"{name:38s} *** FAIL -- gate produced no JSON ({error}) ***")
            all_ok = False
            continue

        actual_pass = report["passed"]
        expected_pass = expected["expect"] == "pass"
        actual_failing = sorted(c["rule"] for c in report["checks"] if not c["passed"])
        actual_derived = sorted(c["rule"] for c in report["checks"] if not c["passed"] and c.get("derived"))
        expected_failing = sorted(expected.get("failing_rules", []))
        expected_derived = sorted(expected.get("derived_rules", []))

        ok = (
            actual_pass == expected_pass
            and actual_failing == expected_failing
            and actual_derived == expected_derived
        )
        print(f"{name:38s} {'OK' if ok else '*** MISMATCH ***'}")
        if not ok:
            all_ok = False
            print(f"    expected: pass={expected_pass} failing={expected_failing} derived={expected_derived}")
            print(f"    actual:   pass={actual_pass} failing={actual_failing} derived={actual_derived}")

    print()
    if not all_ok:
        print("FAILED -- one or more fixtures do not match fixtures/expectations.json.")
        sys.exit(1)
    print(f"All {len(expectations)} fixtures match fixtures/expectations.json.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--capture", action="store_true", help="Print current gate output as an expectations.json draft.")
    args = parser.parse_args()
    capture() if args.capture else check()


if __name__ == "__main__":
    main()
