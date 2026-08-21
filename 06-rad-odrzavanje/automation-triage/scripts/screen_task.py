#!/usr/bin/env python3
"""Pass one — the sieve. Four fields per task, a minute each.

The sieve may only DROP or ADVANCE. It may never reach a verdict.

That restriction is the whole design. A cheap pass that can say REFUSE is a
cheap pass that produces expensive conclusions from four fields, and a client
who is told "do not automate this" deserves the ten fields behind it.

What is dropped is still written down. A task that vanishes without a record
comes back at the next meeting, and nobody remembers why it went.

Exit: 0 ADVANCE, 1 DROP, 2 unusable input.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "adp-triage-screen-1"
BANDS = ("daily", "weekly", "monthly", "rarely")
WILDCARD = re.compile(r"[*?]")
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*$")

# Roughly how a band reads in occurrences per month. Used for ordering the
# shortlist only — never for a verdict, and never passed downstream.
BAND_ORDER = {"daily": 3, "weekly": 2, "monthly": 1, "rarely": 0}


def die(message):
    sys.stderr.write(message.rstrip() + "\n")
    raise SystemExit(2)


def main():
    p = argparse.ArgumentParser(description="Screen one task before scoring it.")
    p.add_argument("--task-id", required=True)
    p.add_argument("--task", required=True, help="the team's own words, passed through unchanged")
    p.add_argument("--who", required=True, help="role, never a person's name")
    p.add_argument("--how-many", type=int, default=1)
    p.add_argument("--frequency-band", required=True, choices=list(BANDS))
    p.add_argument("--who-notices", required=True,
                   help="who would notice it was wrong, and when")
    p.add_argument("--out-dir", default="triage")
    a = p.parse_args()

    if not TASK_ID.fullmatch(a.task_id or ""):
        die("--task-id must be letters, digits, hyphens and underscores only")
    if WILDCARD.search(a.task):
        die("a task name may not contain * or ? — those become wildcards in the "
            "baseline workbook and silently absorb other rows")
    if not a.task.strip():
        die("--task is empty")
    if a.how_many < 1:
        die("--how-many must be at least 1")
    if not a.who_notices.strip():
        die("--who-notices is the cheapest signal there is; do not leave it blank")

    if a.frequency_band == "rarely":
        outcome, why = "DROP", "too infrequent for anything to repay itself"
    else:
        outcome, why = "ADVANCE", "repeated often enough to be worth ten fields"

    record = {
        "schema": SCHEMA,
        "task_id": a.task_id,
        "task": a.task,
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "who": a.who,
        "how_many": a.how_many,
        "frequency_band": a.frequency_band,
        "band_order": BAND_ORDER[a.frequency_band],
        "who_notices": a.who_notices,
        "outcome": outcome,
        "reason": why,
        "note": "a screen decides what is worth scoring; it never decides what to do",
    }

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"screen-{a.task_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"{a.task_id}: {outcome} — {why}")
    print(f"  written: {path}")
    return 0 if outcome == "ADVANCE" else 1


if __name__ == "__main__":
    sys.exit(main())
