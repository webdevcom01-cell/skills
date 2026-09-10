#!/usr/bin/env python3
"""Self-test for screen_task.py, score_task.py and check_triage.py.

Three layers, because the first two have fooled this house before:

  1. verdicts the scorer must reach, and inputs it must refuse
  2. documents the gate must flag, and documents it must let through
  3. mutations — the checker and the scorer are deliberately weakened and the
     suite must notice

Layer 3 exists because a suite that stays green after a branch is deleted is
not a suite. Run:  python3 selftest.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCREEN = HERE / "screen_task.py"
SCORE = HERE / "score_task.py"
CHECK = HERE / "check_triage.py"

MONEY = ["--build-cost", "4000", "--hour-value", "25"]


def score(out_dir, **kw):
    args = [sys.executable, str(SCORE), "--out-dir", str(out_dir)] + MONEY
    for k, v in kw.items():
        flag = "--" + k.replace("_", "-")
        if v is True:
            args.append(flag)
        elif v is not None and v is not False:
            args += [flag, str(v)]
    return subprocess.run(args, capture_output=True, text=True)


BASE = dict(task_id="T-01", task="ocenjivanje inbound lead-ova", who="sales",
            output="structured", when_wrong="pogrešan prioritet, primeti se za nedelju",
            verifiability=3, check_rule="json_has_key:score", data_access=3,
            error_cost="low", stability="stable", friction=4)


def run_check(text, records=None, names=(), strict=False, filename="pack.md"):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / filename).write_text(text, encoding="utf-8")
        rd = td / "triage"
        rd.mkdir()
        for key, rec in (records or {}).items():
            (rd / f"{key}.json").write_text(json.dumps(rec), encoding="utf-8")
        cmd = [sys.executable, str(CHECK), str(td / filename), "--records", str(rd)]
        if names:
            cmd += ["--names", *names]
        if strict:
            cmd.append("--strict")
        return subprocess.run(cmd, capture_output=True, text=True)


def rec(tid="T-01", verdict="BUILD", **kw):
    r = {"schema": "adp-triage-1", "task_id": tid, "task": "x", "verdict": verdict,
         "rule": 7, "fragile": False}
    r.update(kw)
    return r




def check_frontmatter():
    """Refuse to pass if SKILL.md would be rejected on save.

    The platform caps `description` at 1024. It is not documented whether that
    counts characters or bytes, and these descriptions carry diacritics, so both
    are held under 1000. A skill that will not save is a skill that does not
    exist, and nothing else in this suite would have noticed.
    """
    import re as _re
    md = (HERE.parent / "SKILL.md").read_text(encoding="utf-8")
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
    passed = failed = 0
    fails = []

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            fails.append(f"{name}: {detail}")


    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        print("== scorer: verdicts ==")

        # 120 x 6 min = 12 h/month. 12 x 0.5 x 25 = 150/month against 4000 + 400 = 4400.
        # 29 months, well past a 6-month window, so this is not a BUILD.
        r = score(td, per_month=120, minutes_each=6, **BASE)
        got = json.loads((td / "T-01.json").read_text())
        check("modest volume is not a build", got["verdict"] != "BUILD",
              f'{got["verdict"]} at {got["derived"]["payback_months"]} months')

        # Enough volume that the payback clears the window on both halves of the
        # sensitivity check.
        r = score(td, per_month=4000, minutes_each=10, **BASE)
        got = json.loads((td / "T-01.json").read_text())
        check("large volume builds", got["verdict"] == "BUILD", f'{got["verdict"]} {got["reason"]}')
        check("build carries supervision", got["supervision"], "")
        check("build is not fragile", not got["fragile"], str(got.get("fragile_note")))

        # A verdict that a 2x error would overturn is downgraded.
        r = score(td, per_month=350, minutes_each=10, **BASE)
        got = json.loads((td / "T-01.json").read_text())
        check("fragile verdict downgraded", got["verdict"] == "WATCH" and got["fragile"],
              f'{got["verdict"]} fragile={got["fragile"]}')

        for name, kw, want in (
            ("no data", dict(data_access=0), "REFUSE"),
            ("must be human", dict(must_be_human=True), "REFUSE"),
            ("expensive and uncheckable", dict(error_cost="high", verifiability=0,
                                               check_rule=None), "REFUSE"),
            ("uncheckable trains", dict(verifiability=0, check_rule=None), "TRAIN"),
            ("drifting trains", dict(stability="drifting"), "TRAIN"),
        ):
            kwargs = dict(BASE, per_month=4000, minutes_each=10)
            kwargs.update(kw)
            if kwargs.get("check_rule") is None:
                kwargs.pop("check_rule", None)
            score(td, **kwargs)
            got = json.loads((td / "T-01.json").read_text())
            check(f"verdict/{name}", got["verdict"] == want, f'{got["verdict"]} — {got["reason"]}')

        score(td, **dict(BASE, per_month="NOT MEASURED", minutes_each=6))
        got = json.loads((td / "T-01.json").read_text())
        check("missing estimate watches", got["verdict"] == "WATCH" and got["rule"] == 4,
              f'{got["verdict"]} rule {got["rule"]}')

        print("== scorer: refusals ==")

        for name, kw, msg in (
            ("wildcard in name", dict(task="unos *svih* podataka"), "wildcard"),
            ("verifiability without rule", dict(verifiability=2, check_rule=None), "check-rule"),
            ("nested quantifier", dict(check_rule="regex:(a+)+"), "quantifier"),
            ("unknown rule kind", dict(check_rule="nonsense:x"), "rule kind"),
            ("path traversal", dict(task_id="../../pwned"), "task-id"),
            ("saved fraction above one", dict(saved_fraction=1.5), "saved-fraction"),
        ):
            kwargs = dict(BASE, per_month=100, minutes_each=6)
            kwargs.update(kw)
            if kwargs.get("check_rule") is None:
                kwargs.pop("check_rule", None)
            out = score(td, **kwargs)
            check(f"refuse/{name}", out.returncode == 2 and "Traceback" not in out.stderr,
                  f"exit {out.returncode}, err={out.stderr.strip()[:120]}")

        print("== screen ==")

        for band, want in (("rarely", "DROP"), ("weekly", "ADVANCE"), ("daily", "ADVANCE")):
            subprocess.run([sys.executable, str(SCREEN), "--task-id", f"S-{band}",
                            "--task", "unos podataka", "--who", "ops",
                            "--frequency-band", band, "--who-notices", "niko do kraja meseca",
                            "--out-dir", str(td)], capture_output=True, text=True)
            got = json.loads((td / f"screen-S-{band}.json").read_text())
            check(f"screen/{band}", got["outcome"] == want, got["outcome"])
            check(f"screen/{band} never verdicts", "verdict" not in got, str(got.keys()))

        out = subprocess.run([sys.executable, str(SCREEN), "--task-id", "S-1",
                              "--task", "unos *svih* podataka", "--who", "ops",
                              "--frequency-band", "weekly", "--who-notices", "x",
                              "--out-dir", str(td)], capture_output=True, text=True)
        check("screen refuses wildcard", out.returncode == 2, f"exit {out.returncode}")

    print("== gate: must flag ==")

    R = {"T-01": rec("T-01", "BUILD"), "T-02": rec("T-02", "REFUSE")}

    MUST_FLAG = [
        ("guarantee", "The agent guarantees a correct score for every lead.", "FORBIDDEN"),
        ("compliance", "This arrangement is compliant with GDPR.", "FORBIDDEN"),
        ("promised outcome", "This will save the team a day a week.", "FORBIDDEN"),
        ("fully automated", "Lead scoring becomes fully automated.", "FORBIDDEN"),
        ("research", "Research shows most AI projects fail.", "FORBIDDEN"),
        ("untagged number", "The task consumes 30 hours a month.", "UNSOURCED_NUMBER"),
        ("estimate as fact", "It saves 30 hours a month [T-01].", "ESTIMATE_AS_FACT"),
        ("verdict mismatch", "Rule 7 gives lead scoring BUILD [T-02].", "VERDICT_MISMATCH"),
        ("dangling", "Rule 7 says BUILD [T-99].", "DANGLING"),
        ("invisible", "The agent guar​antees a score [T-01].", "FORBIDDEN"),
        ("heading forbidden", "## Fully automated lead scoring\n\nOwner: ops.\n", "FORBIDDEN"),
    ]
    for name, line, kind in MUST_FLAG:
        r = run_check(line, R)
        check(f"flag/{name}", r.returncode == 1 and kind in r.stdout,
              f"exit {r.returncode}, expected {kind}, out={r.stdout.strip()[:140]}")

    r = run_check("Rule 7 gives lead scoring BUILD [T-01].", {"T-01": rec(fragile=True)})
    check("fragile unmarked", "FRAGILE_UNMARKED" in r.stdout, r.stdout[:200])

    r = run_check("Nothing here cites anything.", {"T-02": rec("T-02", "REFUSE")})
    check("buried refusal", "BURIED_REFUSAL" in r.stdout, r.stdout[:200])

    r = run_check("Marko does this twice a week [T-01], and rule 7 says BUILD.", R, names=["Marko"])
    check("named person", "NAMED_PERSON" in r.stdout, r.stdout[:200])

    r = run_check("We recommend you do not automate this one.", R,
                  filename="acme-not-worth-automating.md")
    check("advice in the refusal document", "ADVICE_NOT_OBSERVATION" in r.stdout, r.stdout[:200])

    r = run_check("Rule 7 gives it BUILD [T-01].\n```\nunterminated\n", R)
    check("unclosed fence", "UNCLOSED_FENCE" in r.stdout, r.stdout[:200])

    rd = {"a.json": rec("T-01", "BUILD"), "z.json": rec("T-01", "REFUSE")}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "d.md").write_text("Owner: ops.", encoding="utf-8")
        tri = td / "triage"; tri.mkdir()
        for fn, body in rd.items():
            (tri / fn).write_text(json.dumps(body), encoding="utf-8")
        out = subprocess.run([sys.executable, str(CHECK), str(td / "d.md"), "--records", str(tri)],
                             capture_output=True, text=True)
    check("duplicate task id", "DUPLICATE" in out.stdout, out.stdout[:200])

    print("== gate: must pass ==")

    # A REFUSE record that nothing cites is itself a finding, so the clean-document
    # fixtures carry only the record they cite.
    R_PASS = {"T-01": rec("T-01", "BUILD")}

    MUST_PASS = [
        ("tagged verdict with rule", "Rule 7 gives lead scoring BUILD [T-01]."),
        ("gap marked", "Hours for this task are NOT MEASURED."),
        ("negation", "This does not save anyone any time and makes no promise about results."),
        ("observation in refusal doc", "This task has no output a machine can check [T-01]."),
        ("disclaimer", "We do not claim this is compliant with anything."),
        ("plain heading", "## What we looked at\n\nOwner: ops.\n"),
        ("heading with a figure", "## Response within 4 hours\n\nOwner: ops.\n"),
        ("role not name", "Sales does this twice a week; rule 7 gives it BUILD [T-01]."),
        ("fenced example", "Run it:\n\n```\nscore_task.py --verifiability 3\nBUILD\n```\n\nOwner: ops.\n"),
    ]
    for name, body in MUST_PASS:
        fn = "acme-not-worth-automating.md" if "refusal" in name else "pack.md"
        r = run_check(body, R_PASS, names=["Marko"], filename=fn)
        check(f"pass/{name}", r.returncode == 0, f"exit {r.returncode}, out={r.stdout.strip()[:180]}")

    print("== mutations ==")

    PROBES = [
        ("The agent guarantees a score.", R, "FORBIDDEN"),
        ("The agent guar​antees a score.", R, "FORBIDDEN"),
        ("## Fully automated scoring\n\nOwner: ops.\n", R, "FORBIDDEN"),
        ("The task consumes 30 hours a month.", R, "UNSOURCED_NUMBER"),
        ("Rule 7 gives lead scoring BUILD [T-02].", R, "VERDICT_MISMATCH"),
        ("Rule 7 says BUILD [T-99].", R, "DANGLING"),
        ("Nothing cites anything.", {"T-02": rec("T-02", "REFUSE")}, "BURIED_REFUSAL"),
        ("Rule 7 gives it BUILD [T-01].", {"T-01": rec(fragile=True)}, "FRAGILE_UNMARKED"),
        ("Rule 7 gives lead scoring BUILD [T-01].", R_PASS, None),
        ("## Response within 4 hours\n\nOwner: ops.\n", R_PASS, None),
    ]

    MUTATIONS = [
        (CHECK, "stop removing invisible characters",
         ('    return INVISIBLE.sub("", text)', "    return text")),
        (CHECK, "stop reading headings",
         ('            if HEADING.match(raw):\n                head = re.sub(r"^\\s{0,3}#{1,6}\\s+", "", s).strip()\n                if head:\n                    out.append((i, head, True))\n', "")),
        (CHECK, "judge a heading like a sentence",
         ("    if heading:\n        return None\n", "")),
        (CHECK, "delete the untagged-number branch",
         ('    if num and not tagged and not marked:', "    if False:")),
        (CHECK, "accept a verdict that contradicts its record",
         ("            if actual and stated != actual:", "            if False:")),
        (CHECK, "stop resolving dangling tags",
         ("                    if tid not in records:", "                    if False:")),
        (CHECK, "stop reporting a buried refusal",
         ('            if rec.get("verdict") == "REFUSE":', "            if False:")),
        (CHECK, "stop marking a fragile verdict",
         ('            if rec.get("fragile") and stated == rec.get("verdict"):', "            if False:")),
        (CHECK, "empty the forbidden vocabulary",
         ("    for pat, name in FORBIDDEN:", "    for pat, name in []:")),
        (SCORE, "drop the sensitivity check",
         ("    if not missing:\n        for factor in (0.5, 2.0):", "    if False:\n        for factor in (0.5, 2.0):")),
        (SCORE, "allow a score of 3 with no written rule",
         ("    if a.verifiability >= 2 and not a.check_rule:", "    if False:")),
        (SCORE, "allow a wildcard in a task name",
         ("    if WILDCARD.search(a.task):", "    if False:")),
    ]

    for target, desc, (old, new) in MUTATIONS:
        original = target.read_text(encoding="utf-8")
        if old not in original:
            check(f"mutation/{desc}", False, "anchor not found — the mutation would be a no-op")
            continue
        target.write_text(original.replace(old, new, 1), encoding="utf-8")
        try:
            noticed = False
            for body, records, expect in PROBES:
                out = run_check(body, records)
                if expect is None:
                    if out.returncode != 0:
                        noticed = True
                        break
                elif expect not in out.stdout:
                    noticed = True
                    break
            if not noticed:
                with tempfile.TemporaryDirectory() as td:
                    td = Path(td)
                    o = score(td, per_month=350, minutes_each=10, **BASE)
                    got = json.loads((td / "T-01.json").read_text())
                    if not got["fragile"]:
                        noticed = True
                    if not noticed:
                        kw = dict(BASE, per_month=100, minutes_each=6, verifiability=2)
                        kw.pop("check_rule")
                        if score(td, **kw).returncode != 2:
                            noticed = True
                    if not noticed:
                        if score(td, per_month=100, minutes_each=6,
                                 **dict(BASE, task="unos *svih* podataka")).returncode != 2:
                            noticed = True
            check(f"mutation/{desc}", noticed, "the suite stayed green with the code weakened")
        finally:
            target.write_text(original, encoding="utf-8")

    print(f"\n{passed} passed, {failed} failed")
    for f in fails:
        print(f"  FAIL {f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
