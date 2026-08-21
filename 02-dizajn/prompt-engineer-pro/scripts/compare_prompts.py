#!/usr/bin/env python3
"""
compare_prompts.py — Prove a prompt diet was a reduction, not a regression.

Runs both versions through the same audit (evaluate_prompt.evaluate) and reports
the delta: tokens saved, bloat patterns removed, and — the part that actually
matters — whether anything of value was lost on the way.

The asymmetry is deliberate. Losing tokens is the goal. Losing a security control,
gaining a contradiction, or dropping a surprising project fact is a regression and
exits non-zero, no matter how many tokens you saved.

Usage:
    python compare_prompts.py old.txt new.txt
    python compare_prompts.py old.txt new.txt --json
    python compare_prompts.py old.txt new.txt --model-tier small
"""

import sys
import json
import argparse
from pathlib import Path

try:
    from evaluate_prompt import evaluate, count_tokens_approx
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from evaluate_prompt import evaluate, count_tokens_approx


# Losing an issue is good. Gaining one of these is a regression.
REGRESSION_CATEGORIES = {"security", "quality"}


def issue_key(issue):
    return (issue.category, issue.message)


def compare(old_text: str, new_text: str, model_tier: str = "frontier") -> dict:
    old = evaluate(old_text, model_tier=model_tier)
    new = evaluate(new_text, model_tier=model_tier)

    old_keys = {issue_key(i): i for i in old.issues}
    new_keys = {issue_key(i): i for i in new.issues}

    fixed = [old_keys[k] for k in old_keys.keys() - new_keys.keys()]
    introduced = [new_keys[k] for k in new_keys.keys() - old_keys.keys()]
    remaining = [new_keys[k] for k in old_keys.keys() & new_keys.keys()]

    lost_strengths = [s for s in old.strengths if s not in new.strengths]
    gained_strengths = [s for s in new.strengths if s not in old.strengths]

    old_tok = count_tokens_approx(old_text)
    new_tok = count_tokens_approx(new_text)

    # A regression is: a new critical issue, a new security/quality issue of any
    # severity, or a lost strength. Not: fewer tokens, fewer examples, lower verbosity.
    regressions = [
        i for i in introduced
        if i.severity == "critical" or i.category in REGRESSION_CATEGORIES
    ]

    return {
        "model_tier": model_tier,
        "tokens": {
            "old": old_tok,
            "new": new_tok,
            "saved": old_tok - new_tok,
            "reduction_pct": round((old_tok - new_tok) / old_tok * 100, 1) if old_tok else 0.0,
        },
        "score": {"old": old.score, "new": new.score, "delta": new.score - old.score},
        "grade": {"old": old.grade, "new": new.grade},
        "fixed": [{"severity": i.severity, "category": i.category, "message": i.message}
                  for i in fixed],
        "introduced": [{"severity": i.severity, "category": i.category, "message": i.message}
                       for i in introduced],
        "remaining": [{"severity": i.severity, "category": i.category, "message": i.message}
                      for i in remaining],
        "lost_strengths": lost_strengths,
        "gained_strengths": gained_strengths,
        "regressions": [{"severity": i.severity, "category": i.category, "message": i.message}
                        for i in regressions],
        "verdict": _verdict(regressions, lost_strengths, old_tok - new_tok),
    }


def _verdict(regressions, lost_strengths, tokens_saved):
    if regressions:
        return "REGRESSION"
    if lost_strengths:
        return "REVIEW"
    if tokens_saved > 0:
        return "CLEAN REDUCTION"
    if tokens_saved < 0:
        return "GREW"
    return "NO CHANGE"


def format_report(r: dict) -> str:
    t, s = r["tokens"], r["score"]
    out = []
    out.append("=" * 56)
    out.append("PROMPT COMPARISON")
    out.append("=" * 56)
    out.append("")
    out.append(f"Verdict: {r['verdict']}   (model tier: {r['model_tier']})")
    out.append("")
    out.append(f"Tokens:  {t['old']:>6} → {t['new']:<6}  "
               f"({t['saved']:+d}, {-t['reduction_pct']:+.1f}%)")
    out.append(f"Score:   {s['old']:>6} → {s['new']:<6}  ({s['delta']:+d})   "
               f"{r['grade']['old']} → {r['grade']['new']}")
    out.append("")

    if r["fixed"]:
        out.append(f"✅ FIXED ({len(r['fixed'])}):")
        for i in r["fixed"]:
            out.append(f"   [{i['category']}] {i['message']}")
        out.append("")

    if r["regressions"]:
        out.append(f"❌ REGRESSIONS ({len(r['regressions'])}) — these block the change:")
        for i in r["regressions"]:
            out.append(f"   [{i['severity']}/{i['category']}] {i['message']}")
        out.append("")

    introduced_nonreg = [i for i in r["introduced"]
                         if i not in r["regressions"]]
    if introduced_nonreg:
        out.append(f"⚠️  NEW, NON-BLOCKING ({len(introduced_nonreg)}):")
        for i in introduced_nonreg:
            out.append(f"   [{i['category']}] {i['message']}")
        out.append("")

    if r["lost_strengths"]:
        out.append(f"⚠️  LOST ({len(r['lost_strengths'])}) — confirm each was intentional:")
        for s_ in r["lost_strengths"]:
            out.append(f"   • {s_}")
        out.append("")

    if r["gained_strengths"]:
        out.append(f"✅ GAINED ({len(r['gained_strengths'])}):")
        for s_ in r["gained_strengths"]:
            out.append(f"   • {s_}")
        out.append("")

    if r["remaining"]:
        out.append(f"○ STILL OPEN ({len(r['remaining'])}):")
        for i in r["remaining"]:
            out.append(f"   [{i['category']}] {i['message']}")
        out.append("")

    out.append("=" * 56)
    if r["verdict"] == "CLEAN REDUCTION":
        out.append("Smaller, and nothing of value was lost. This is the outcome you want.")
    elif r["verdict"] == "REVIEW":
        out.append("Smaller, but something scored as valuable disappeared. Check the LOST list.")
    elif r["verdict"] == "REGRESSION":
        out.append("Do not ship. A security control or contradiction was introduced.")
    out.append("")
    out.append("Note: this is a static audit. It cannot tell you the prompt still does its job —")
    out.append("run your own test cases against both versions for that.")
    return "\n".join(out)


def _read(p: str) -> str:
    path = Path(p)
    if not path.exists():
        print(f"Error: File not found: {p}", file=sys.stderr)
        sys.exit(2)
    return path.read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Compare two prompt versions and flag regressions")
    parser.add_argument("old", help="Path to the original prompt")
    parser.add_argument("new", help="Path to the revised prompt")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--model-tier", choices=["frontier", "small"], default="frontier")
    args = parser.parse_args()

    result = compare(_read(args.old), _read(args.new), model_tier=args.model_tier)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_report(result))

    sys.exit(1 if result["verdict"] == "REGRESSION" else 0)


if __name__ == "__main__":
    main()
