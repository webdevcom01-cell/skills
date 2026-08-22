#!/usr/bin/env python3
"""Gate the client-facing triage documents against the scored records.

Inherits what check_pack.py learned over three adversarial rounds: invisible
characters are removed before anything is read, an unterminated code fence is
reported rather than silently blinding the gate, headings are judged only on the
refused vocabulary, a negation governs only what follows it inside its own
clause, and a verdict is compared with the record cited in its own row item.

What it adds, because triage carries risks a delivery pack does not:

  * a verdict in a document must match the verdict in the record
  * a person's name must not appear in a client-facing document
  * a refusal must read as an observation about the task, not as advice
  * an unmeasured estimate must not be written as if it were measured

Usage:  check_triage.py FILE [FILE...] [--records DIR] [--names NAME ...] [--strict]
Exit:   0 clean · 1 findings · 2 a file could not be read
"""

import argparse
import json
import re
import sys
from pathlib import Path

INVISIBLE = re.compile(
    "[­͏؜ᅟᅠ឴឵᠋-᠎​-‏"
    "‪-‮  ⁠-⁤⁦-⁯ㅤ︀-️"
    "﻿ﾠ￹-￻\U000e0000-\U000e0fff]")

# engagement.md §3, plus the warranty family. Refused whatever the tag.
FORBIDDEN = [
    (r"\bguarantee[sd]?\b|\bgarantuj\w*\b|\bgarantovan\w*\b|\bgarancij\w*\b", "a guarantee"),
    (r"\b(is|are|fully)?\s*compliant\b|\busklađen\w*\s+sa\b|\bu skladu sa (GDPR|zakon\w*)",
     "a compliance conclusion"),
    (r"\b(lawful|defensible|legally (safe|sound|approved))\b|\bzakonit\w*\b|\bpravno (sigurn|valjan)\w*",
     "a legal conclusion"),
    (r"\bsufficient for (a|the) (regulator|supervisory authority)\b|\bdovoljno za (regulatora|inspekciju)\b",
     "sufficiency for a regulator"),
    (r"\b(GDPR|CCPA|HIPAA|ZZPL)\b(?![^.]*\[(?:REGULATOR|PROPIS))",
     "a named regulation the consultant cannot cite"),
    (r"\bresearch shows\b|\bstudies show\b|\bistraživanja pokazuju\b|\bstudije pokazuju\b",
     "industry research with no study named"),
    (r"\bwill (save|reduce|cut|eliminate)\b|\buštedeće\b|\bsmanjiće\b|\bukinuće\b",
     "a promised outcome"),
    (r"\b100\s?%|\b9\d[.,]\d+\s?%", "an absolute or near-absolute rate"),
    (r"\b(fully|completely) automat\w+\b|\bpotpuno automatizovan\w*\b", "full automation"),
    (r"\bproduction[-–— ]ready\b|\bspreman za produkciju\b", "production-ready"),
]

TAG = re.compile(r"\[(T-[A-Za-z0-9_-]+)\]")
GAP = re.compile(r"\bNOT MEASURED\b|\bTO CONFIRM\b|\bNIJE MERENO\b|\bZA POTVRDU\b", re.I)
VERDICT = re.compile(r"\b(BUILD|TRAIN|WATCH|REFUSE|DROP|ADVANCE)\b")

NUMBER = re.compile(
    r"(?<![\w-])\d{1,3}(?:[.,]\d+)?\s?%"
    r"|(?<![\w-])\d+(?:[.,]\d+)?\s*(?:h|hours?|sati|sata|min(?:utes?|uta)?|meseci|months?)\b"
    r"|(?<![\w-])\d+(?:[.,]\d+)?\s*(?:EUR|RSD|USD|€|\$|din)\b",
    re.I,
)

# Words that turn an estimate into a measurement.
MEASURED_VOICE = re.compile(
    r"\b(saves?|saved|reduces?|reduced|measured|we measured|cuts?|delivers?)\b"
    r"|\b(štedi|uštedelo|smanjuje|izmereno|merili smo|donosi)\b", re.I)

ADVICE = re.compile(
    r"\b(we recommend|we advise|our recommendation|you should not|do not automate)\b"
    r"|\b(preporučujemo|savetujemo|ne preporučujemo|naša preporuka|nemojte automatizovati)\b", re.I)

NEGATION = re.compile(
    r"\b(does not|do not|doesn't|don't|cannot|can't|will not|won't|is not|are not|never|neither|nor)\b"
    r"|\b(nothing|none of|no task|not one of)\b"
    r"|\bnije\b|\bnisu\b|\bneće\b|\bne može\b|\bništa\b|\bnijedan\b|\bnijedn\w+\b", re.I)

DISCLAIMED = re.compile(
    r"(?:\b(?:not|no|never|without|nor)\b|\b(?:ne|nije|nisu|neće|bez|niti)\b)[\s,\-–—]*$", re.I)
DISCLAIMER_LEAD = re.compile(
    r"\b(do|does|did|would|will|can)\s+not\s+(claim|promise|guarantee|assert|say|state)\b"
    r"|\bno (claim|promise|warranty|guarantee)\b|\bne (tvrdimo|obećavamo|garantujemo)\b", re.I)
CLAUSE_SPLIT = re.compile(
    r"[,;]|\b(?:though|although|but|however|while|mada|iako|ali|premda)\b", re.I)

HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
FENCE = re.compile(r"^\s*(```|~~~)")
REFUSAL_FILE = re.compile(r"not-worth-automating|ne-vredi-automatizovati", re.I)


def normalise(text):
    return INVISIBLE.sub("", text)


def fences_balanced(text):
    return sum(1 for line in text.split("\n") if FENCE.match(line)) % 2 == 0


def blank_fences(text, honour=True):
    if not honour:
        return text
    out, inside = [], False
    for raw in text.split("\n"):
        if FENCE.match(raw):
            inside = not inside
            out.append(" " * len(raw))
            continue
        out.append(" " * len(raw) if inside else raw)
    return "\n".join(out)


def logical_lines(text, honour_fences=True):
    """(line_no, text, is_heading), fences skipped, wrapped prose joined."""
    out, buf, start, inside = [], [], None, False
    for i, raw in enumerate(text.splitlines(), 1):
        if honour_fences and FENCE.match(raw):
            inside = not inside
            continue
        if inside:
            continue
        s = raw.strip()
        if not s or HEADING.match(raw) or set(s) <= set("-|=* "):
            if buf:
                out.append((start, " ".join(buf), False))
                buf, start = [], None
            if HEADING.match(raw):
                head = re.sub(r"^\s{0,3}#{1,6}\s+", "", s).strip()
                if head:
                    out.append((i, head, True))
            continue
        if raw.lstrip().startswith(("- ", "* ", "|", "> ")) or re.match(r"^\s*\d+[.)]\s", raw):
            if buf:
                out.append((start, " ".join(buf), False))
                buf, start = [], None
            out.append((i, s, False))
            continue
        if start is None:
            start = i
        buf.append(s)
    if buf:
        out.append((start, " ".join(buf), False))
    return out


def sentences(unit):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZŠĐČĆŽ\[])", unit)
    return [p.strip() for p in parts if p.strip()]


def clause_around(text, pos):
    bounds = list(CLAUSE_SPLIT.finditer(text))
    spans = list(zip([0] + [m.end() for m in bounds],
                     [m.start() for m in bounds] + [len(text)]))
    for s, e in spans:
        if s <= pos <= e:
            return text[s:e], pos - s
    return text, pos


def negated_before(clause, offset):
    m = NEGATION.search(clause)
    return bool(m) and m.start() < offset


def risk(text, heading=False):
    for pat, name in FORBIDDEN:
        for m in re.finditer(pat, text, re.I):
            cl, _ = clause_around(text, m.start())
            if DISCLAIMED.search(text[max(0, m.start() - 60):m.start()]) or DISCLAIMER_LEAD.search(cl):
                continue
            return "FORBIDDEN", f"{name} — {m.group(0).strip()!r}"
    if heading:
        return None

    tagged, marked = bool(TAG.search(text)), bool(GAP.search(text))
    num = NUMBER.search(text)
    if num and not tagged and not marked:
        return "UNSOURCED_NUMBER", f"figure {num.group(0).strip()!r} with no [T-...] tag"

    for m in MEASURED_VOICE.finditer(text):
        cl, off = clause_around(text, m.start())
        if negated_before(cl, off):
            continue
        if num or marked:
            return "ESTIMATE_AS_FACT", (f"{m.group(0).strip()!r} states as measured something the "
                                        "records hold only as a client estimate")
    return None


def load_records(directory):
    records, errs, seen = {}, [], {}
    d = Path(directory)
    if not d.is_dir():
        return records, [f"records directory not found: {directory}"]
    for f in sorted(d.glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            errs.append(f"{f.name}: unreadable ({e})")
            continue
        if not isinstance(rec, dict):
            errs.append(f"{f.name}: not a JSON object")
            continue
        if rec.get("schema") not in ("adp-triage-1", "adp-triage-screen-1"):
            errs.append(f"{f.name}: not a triage record")
            continue
        tid = rec.get("task_id")
        if not tid:
            errs.append(f"{f.name}: no task_id")
            continue
        key = ("screen:" if rec["schema"].endswith("screen-1") else "") + tid
        if key in seen:
            errs.append(f"DUPLICATE task_id {tid}: {seen[key]} and {f.name} both claim it — remove one")
            continue
        seen[key] = f.name
        records[key] = rec
    return records, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--records", default="triage")
    ap.add_argument("--names", nargs="*", default=[],
                    help="names collected on the call; none may appear in a client document")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on a scored task cited in no document")
    a = ap.parse_args()

    records, errs = load_records(a.records)
    findings = [("records", 0, "SETUP", e) for e in errs]
    referenced = set()

    for fp in a.files:
        try:
            text = normalise(Path(fp).read_text(encoding="utf-8"))
        except (FileNotFoundError, UnicodeDecodeError, IsADirectoryError) as e:
            sys.stderr.write(f"cannot read {fp}: {e}\n")
            return 2

        name = Path(fp).name
        balanced = fences_balanced(text)
        if not balanced:
            findings.append((name, 0, "UNCLOSED_FENCE",
                             "a code fence is opened and never closed; the file is checked as prose"))
        plain = blank_fences(text, honour=balanced)
        is_refusal_doc = bool(REFUSAL_FILE.search(name))

        for who in a.names:
            for m in re.finditer(rf"\b{re.escape(who)}\b", plain):
                findings.append((name, plain[:m.start()].count("\n") + 1, "NAMED_PERSON",
                                 f"{who!r} names a person in a client-facing document; use the role"))

        for lineno, unit, heading in logical_lines(text, honour_fences=balanced):
            for s in sentences(unit):
                for tid in TAG.findall(s):
                    referenced.add(tid)
                    if tid not in records:
                        findings.append((name, lineno, "DANGLING",
                                         f"[{tid}] resolves to no scored record"))
                r = risk(s, heading=heading)
                if r:
                    findings.append((name, lineno, r[0], f"{r[1]} :: {s[:110]}"))
                if is_refusal_doc:
                    m = ADVICE.search(s)
                    if m:
                        findings.append((name, lineno, "ADVICE_NOT_OBSERVATION",
                                         f"{m.group(0).strip()!r} — write what the task is, "
                                         f"not what the client should do :: {s[:90]}"))

        # A verdict belongs to the record cited in its own row item.
        for m in VERDICT.finditer(plain):
            line = plain[:m.start()].count("\n") + 1
            row_start = plain.rfind("\n", 0, m.start()) + 1
            row_end = plain.find("\n", m.start())
            row_end = row_end if row_end != -1 else len(plain)
            row = plain[row_start:row_end]
            seps = [row_start + i for i, ch in enumerate(row) if ch in ",|"]
            lo = max([row_start] + [s + 1 for s in seps if s < m.start()])
            hi = min([row_end] + [s for s in seps if s >= m.end()])
            tags = [(t.start() + row_start, t.group(1)) for t in TAG.finditer(row)]
            item = [(p, t) for p, t in tags if lo <= p < hi]
            ordered = [t for _, t in sorted((abs(p - m.start()), t) for p, t in (item or tags))]
            nearest = next((t for t in ordered if t in records), None)
            if nearest is None:
                continue
            rec = records[nearest]
            stated = m.group(0)
            if stated in ("DROP", "ADVANCE"):
                actual = rec.get("outcome")
            else:
                actual = rec.get("verdict")
            if actual and stated != actual:
                findings.append((name, line, "VERDICT_MISMATCH",
                                 f"the document says {stated} but {nearest} records {actual}"))
            if rec.get("fragile") and stated == rec.get("verdict"):
                window = plain[max(0, m.start() - 200):m.start() + 200]
                if not re.search(r"\bfragile\b|\bunmeasured\b|\bnemerena\b|\bprocena\b", window, re.I):
                    findings.append((name, line, "FRAGILE_UNMARKED",
                                     f"{nearest} is marked fragile — it turns on an unmeasured "
                                     "estimate — and nothing near this verdict says so"))
            if rec.get("rule") and not re.search(r"\brule\s*\d|\bpravilo\s*\d",
                                                 plain[max(0, m.start() - 160):m.start() + 160], re.I):
                findings.append((name, line, "RULE_UNSTATED",
                                 f"{stated} for {nearest} appears without the rule that produced it"))

    for key, rec in sorted(records.items()):
        if key.startswith("screen:"):
            continue
        if key not in referenced:
            if rec.get("verdict") == "REFUSE":
                findings.append(("records", 0, "BURIED_REFUSAL",
                                 f"{key} was scored REFUSE and no document mentions it"))
            elif a.strict:
                findings.append(("records", 0, "UNCITED",
                                 f"{key} ({rec.get('verdict')}) is scored but cited in no document"))

    if not findings:
        print(f"clean — {len(records)} record(s), {len(referenced)} referenced")
        return 0

    order = {"FORBIDDEN": 0, "VERDICT_MISMATCH": 1, "NAMED_PERSON": 2, "BURIED_REFUSAL": 3,
             "ESTIMATE_AS_FACT": 4, "FRAGILE_UNMARKED": 5, "ADVICE_NOT_OBSERVATION": 6,
             "DANGLING": 7, "UNSOURCED_NUMBER": 8, "RULE_UNSTATED": 9, "UNCLOSED_FENCE": 10}
    findings.sort(key=lambda f: (order.get(f[2], 12), f[0], f[1]))
    for fname, line, kind, detail in findings:
        loc = f"{fname}:{line}" if line else fname
        print(f"{loc}: {kind}: {detail}")
    print(f"\n{len(findings)} finding(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
