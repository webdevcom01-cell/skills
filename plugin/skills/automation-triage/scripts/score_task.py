#!/usr/bin/env python3
"""Score one candidate task and compute its verdict.

Why this is a script and not a prompt instruction
-------------------------------------------------
A consultant is paid more for BUILD than for TRAIN, and supplies every input.
So the verdict must not be an opinion. It is computed here, from stated fields
and stated commercial parameters, and the record says which rule fired.

Three things this refuses to do, each because a sibling skill was bitten by it:

  * It will not accept a task name carrying * or ?. Those become wildcards in
    team-enablement-program's baseline workbook and silently absorb other rows.
  * It will not score verifiability 2 or 3 without a written check rule.
    safe-agent-builder: "if a rule matters, it must be checkable in code."
  * It will not report a verdict that a 2x error in the client's own estimate
    would overturn. team-enablement-program: "sponsors are routinely wrong
    about where their team's hours actually go."

Exit: 0 BUILD or TRAIN, 1 WATCH or REFUSE, 2 unusable input.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "adp-triage-1"
NOT_MEASURED = "NOT MEASURED"

# The rule language is the one record_evidence.py already accepts, so a rule
# written on the discovery call survives into the acceptance test unchanged.
RULE_KINDS = ("contains", "not_contains", "regex", "json_has_key", "json_key_in")
NESTED_QUANTIFIER = re.compile(r"\([^)]*[+*][^)]*\)\s*[+*]")
WILDCARD = re.compile(r"[*?]")
CASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*$")


def die(message):
    sys.stderr.write(message.rstrip() + "\n")
    raise SystemExit(2)


def validate_rule(rule):
    """A check rule must be writable, and must not be a rule that can hang."""
    if ":" not in rule:
        die(f"--check-rule must be kind:value, got {rule!r}; kinds: {', '.join(RULE_KINDS)}")
    kind, value = rule.split(":", 1)
    kind = kind.strip().lower()
    if kind not in RULE_KINDS:
        die(f"unknown rule kind {kind!r}; kinds: {', '.join(RULE_KINDS)}")
    if not value.strip():
        die(f"rule {rule!r} has no value")
    if kind == "json_key_in" and "=" not in value:
        die("json_key_in needs key=a,b,c")
    if kind == "regex":
        if NESTED_QUANTIFIER.search(value):
            die("regex rule nests one quantifier inside another; write it as contains: instead")
        try:
            re.compile(value)
        except re.error as e:
            die(f"regex rule does not compile: {e}")
    return rule


# --------------------------------------------------------------------- payback

def payback(volume_hours, p):
    """Months to recover the build, or None when nothing is saved.

    saved_fraction is an assumption, never a measurement, and every number
    derived from it carries that word into the record.
    """
    saved = volume_hours * p["saved_fraction"]
    value_per_month = saved * p["hour_value"]
    if value_per_month <= 0:
        return None
    cost = p["build_cost"] + p["maintain_year"] * p["payback_months"] / 12.0
    return cost / value_per_month


# --------------------------------------------------------------------- verdict

def decide(f, volume_hours, p):
    """Return (verdict, rule_number, reason). First rule that matches wins."""
    if f["data_access"] == 0:
        return "REFUSE", 1, "the inputs do not exist"
    if f["must_be_human"]:
        return "REFUSE", 2, "a contract or regulation requires a person"
    if f["error_cost"] == "high" and f["verifiability"] == 0:
        return "REFUSE", 3, "an expensive mistake with no possible check"
    if f["missing"]:
        return "WATCH", 4, f"nothing to score it with: {', '.join(f['missing'])} is {NOT_MEASURED}"
    if f["verifiability"] == 0:
        return "TRAIN", 5, "a person is the only check there is"
    if f["stability"] == "drifting":
        return "TRAIN", 6, "the procedure is still changing"
    pb = payback(volume_hours, p)
    if (f["verifiability"] >= 2 and f["data_access"] >= 2
            and pb is not None and pb <= p["payback_months"]):
        return "BUILD", 7, f"pays for itself in {pb:.1f} months against a {p['payback_months']:g}-month window"
    if volume_hours >= p["train_floor_hours"]:
        return "TRAIN", 8, "repeated often enough to be worth a written skill"
    return "WATCH", 9, "too small to repay anything today"


def supervision(error_cost):
    return {"high": "a person signs off every output",
            "medium": "a person signs off a sample",
            "low": "unattended running is acceptable"}[error_cost]


def warnings_for(f, volume_hours, verdict, p):
    out = []
    if f["friction"] is not None and f["friction"] <= 2 and verdict == "BUILD":
        out.append("nobody complains about this one; expect resistance to adopting it")
    if f["how_many"] >= 3:
        out.append(f"{f['how_many']} people do this; adoption is the risk, not the technology")
    if f["already_automated"] == "partial":
        out.append("the volume is the manual remainder, not the whole task")
    if f["seasonal"]:
        out.append("a monthly average misleads for a task that clusters in one period")
    if f["chain_with"]:
        out.append(f"scored as one piece of work together with {f['chain_with']}")
    if f["friction"] is None:
        out.append("friction was not supplied by the person doing the task, so ranking is partial")
    return out


def main():
    p = argparse.ArgumentParser(description="Score one candidate task.")
    p.add_argument("--task-id", required=True, help="internal key, e.g. T-01")
    p.add_argument("--task", required=True, help="the team's own words, passed through unchanged")
    p.add_argument("--who", required=True, help="role, never a person's name")
    p.add_argument("--how-many", type=int, default=1)
    p.add_argument("--per-month", help="client estimate, or NOT MEASURED")
    p.add_argument("--minutes-each", help="client estimate, or NOT MEASURED")
    p.add_argument("--output", required=True)
    p.add_argument("--when-wrong", required=True)
    p.add_argument("--verifiability", type=int, required=True, choices=[0, 1, 2, 3])
    p.add_argument("--check-rule", help="required at verifiability 2 or 3")
    p.add_argument("--data-access", type=int, required=True, choices=[0, 1, 2, 3])
    p.add_argument("--error-cost", required=True, choices=["low", "medium", "high"])
    p.add_argument("--stability", required=True, choices=["stable", "drifting"])
    p.add_argument("--friction", help="1-5, from the person doing the task, or NOT MEASURED")
    p.add_argument("--already-automated", default="none", choices=["none", "partial", "full"])
    p.add_argument("--seasonal", action="store_true")
    p.add_argument("--must-be-human", action="store_true")
    p.add_argument("--chain-with")
    p.add_argument("--build-cost", type=float, required=True)
    p.add_argument("--hour-value", type=float, required=True)
    p.add_argument("--maintain-year", type=float)
    p.add_argument("--payback-months", type=float, default=6.0)
    p.add_argument("--saved-fraction", type=float, default=0.5)
    p.add_argument("--train-floor-hours", type=float, default=2.0)
    p.add_argument("--out-dir", default="triage")
    a = p.parse_args()

    if not CASE_ID.fullmatch(a.task_id or ""):
        die("--task-id must be letters, digits, hyphens and underscores only")
    if WILDCARD.search(a.task):
        die("a task name may not contain * or ? — those become wildcards in the "
            "baseline workbook and silently absorb other rows")
    if not a.task.strip():
        die("--task is empty")
    if a.how_many < 1:
        die("--how-many must be at least 1")
    if a.verifiability >= 2 and not a.check_rule:
        die(f"verifiability {a.verifiability} needs --check-rule; if you cannot write the rule, "
            "the score is not 2 or 3")
    if a.check_rule:
        validate_rule(a.check_rule)
    for name, value in (("--build-cost", a.build_cost), ("--hour-value", a.hour_value),
                        ("--payback-months", a.payback_months), ("--saved-fraction", a.saved_fraction)):
        if value <= 0:
            die(f"{name} must be greater than zero")
    if a.saved_fraction > 1:
        die("--saved-fraction is a share of the task, so it cannot exceed 1")

    def number(raw, name):
        if raw is None or str(raw).strip().upper() == NOT_MEASURED:
            return None
        try:
            v = float(str(raw).replace(",", "."))
        except ValueError:
            die(f"{name} must be a number or {NOT_MEASURED}, got {raw!r}")
        if v <= 0:
            die(f"{name} must be greater than zero")
        return v

    per_month = number(a.per_month, "--per-month")
    minutes = number(a.minutes_each, "--minutes-each")
    friction = number(a.friction, "--friction")
    if friction is not None and not 1 <= friction <= 5:
        die("--friction is a 1-5 scale")

    missing = [n for n, v in (("--per-month", per_month), ("--minutes-each", minutes)) if v is None]
    volume_hours = 0.0 if missing else per_month * minutes * a.how_many / 60.0

    params = {"build_cost": a.build_cost, "hour_value": a.hour_value,
              "maintain_year": a.maintain_year if a.maintain_year is not None else 0.2 * a.build_cost,
              "payback_months": a.payback_months, "saved_fraction": a.saved_fraction,
              "train_floor_hours": a.train_floor_hours}

    fields = {"data_access": a.data_access, "must_be_human": a.must_be_human,
              "error_cost": a.error_cost, "verifiability": a.verifiability,
              "stability": a.stability, "missing": missing, "friction": friction,
              "how_many": a.how_many, "already_automated": a.already_automated,
              "seasonal": a.seasonal, "chain_with": a.chain_with}

    verdict, rule, reason = decide(fields, volume_hours, params)

    # A verdict a 2x error in the client's own estimate would overturn is not a
    # verdict. It is a guess wearing one.
    fragile, fragile_note = False, None
    if not missing:
        for factor in (0.5, 2.0):
            other, _, _ = decide(fields, volume_hours * factor, params)
            if other != verdict:
                fragile = True
                fragile_note = (f"at {factor:g}x the estimated volume the verdict would be {other}; "
                                "the estimate has not been measured")
                break
    if fragile:
        verdict, rule, reason = "WATCH", rule, "rests on an unmeasured estimate — " + fragile_note

    pb = None if missing else payback(volume_hours, params)
    record = {
        "schema": SCHEMA,
        "task_id": a.task_id,
        "task": a.task,
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "supplied_by": {
            "task": "the team, verbatim",
            "per_month": "the team — estimate, not measured" if per_month else NOT_MEASURED,
            "minutes_each": "the team — estimate, not measured" if minutes else NOT_MEASURED,
            "friction": "the person doing the task" if friction else NOT_MEASURED,
            "verifiability": "the consultant, with a written rule" if a.check_rule else "the consultant",
            "data_access": "the consultant",
        },
        "fields": {
            "who": a.who, "how_many": a.how_many,
            "per_month": per_month, "minutes_each": minutes,
            "output": a.output, "when_wrong": a.when_wrong,
            "verifiability": a.verifiability, "check_rule": a.check_rule,
            "data_access": a.data_access, "error_cost": a.error_cost,
            "stability": a.stability, "friction": friction,
            "already_automated": a.already_automated, "seasonal": a.seasonal,
            "must_be_human": a.must_be_human, "chain_with": a.chain_with,
        },
        "derived": {
            "volume_hours_per_month": None if missing else round(volume_hours, 2),
            "payback_months": None if pb is None else round(pb, 2),
            "basis": "client estimate multiplied by an assumed saved fraction; neither is a measurement",
        },
        "parameters": params,
        "verdict": verdict,
        "rule": rule,
        "reason": reason,
        "fragile": fragile,
        "fragile_note": fragile_note,
        "supervision": supervision(a.error_cost) if verdict == "BUILD" else None,
        "warnings": warnings_for(fields, volume_hours, verdict, params),
    }

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{a.task_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")

    print(f"{a.task_id}: {verdict} (rule {rule}) — {reason}")
    if record["supervision"]:
        print(f"  supervision: {record['supervision']}")
    for w in record["warnings"]:
        print(f"  warning: {w}")
    print(f"  written: {path}")
    return 0 if verdict in ("BUILD", "TRAIN") else 1


if __name__ == "__main__":
    sys.exit(main())
