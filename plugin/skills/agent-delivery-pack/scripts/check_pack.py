#!/usr/bin/env python3
"""Gate the client-facing files of a delivery pack against the recorded evidence.

The rule this enforces
----------------------
In a document a client may hold you to, every statement that the agent DOES
something, and every figure about how well it does it, carries either an
evidence tag [EV:CASE-ID] that resolves to a recorded run, or a gap marker.
There is no third option.

A tag is not enough on its own. Where the record can settle the question, the
tag is checked against what the record actually says: a verdict word must agree
with the recorded verdict, and a duration must lie inside the durations the
cited records measured. A tag that resolves but contradicts its own record is
worse than an untagged sentence, because it looks checked.

Stating a limitation needs no evidence — "it does not send email" under-promises,
and an under-promise is not the failure that costs money. Claiming a capability
over-promises, and that is the one this gate exists to stop.

Some phrases are refused outright, tag or no tag: nothing in a delivery pack
guarantees anything, is compliant with anything, is secure, or never fails.

Files marked INTERNAL in their first 400 characters are skipped and said to be
skipped. The internal note is where you write what you think; gating it would
force you to dress up your own doubts.

Usage:  check_pack.py FILE [FILE...] [--evidence DIR] [--strict]
Exit:   0 clean · 1 findings · 2 a file could not be read
"""

import argparse
import json
import math
import re
import sys
from bisect import bisect_left, bisect_right
from pathlib import Path

# ---------------------------------------------------------------- vocabularies

# Refused outright. No evidence can support these in a document of this kind,
# because they are claims about law, about the future, or about all inputs.
FORBIDDEN = [
    (r"\bguarantee[sd]?\b|\bgarantuj\w*\b|\bgarantovan\w*\b|\bgarancij\w*\b", "guarantee"),
    (r"\b100\s?%|\b9\d[.,]\d+\s?%", "an absolute or near-absolute rate"),
    (r"\bnever fails?\b|\bnikad(a)? ne (pada|greši|otkaz\w+)\b", "never fails"),
    (r"\bzero (errors?|downtime|risk)\b|\bbez (grešaka|rizika)\b", "zero errors, downtime or risk"),
    (r"\b(fully|completely) automat\w+\b|\bpotpuno automatizovan\w*\b", "fully automated"),
    (r"\b(is|are|fully)?\s*compliant\b|\busklađen\w*\s+sa\b|\bu skladu sa (GDPR|zakon\w*)", "compliance"),
    (r"\bGDPR[- ]compliant\b|\blegal(ly)? (safe|sound|approved)\b", "legal approval"),
    (r"\b(bug|error)[- ]free\b", "freedom from defects"),
    # Only the predicative use is a warranty. "secure your sign-off", "a secure
    # password manager" and "podaci se prenose bezbedno" describe work and stay
    # legal; "the agent is secure" does not.
    (r"\b(is|are|was|were|remains?|stays?|seems?|looks?)\s+(fully\s+|completely\s+|entirely\s+)?secure\b"
     r"|\b(je|su|ostaje|ostaju|deluje)\s+(potpuno\s+)?bezbed(an|na|ni)\b", "security"),
    (r"\bproduction[-\u2013\u2014 ]ready\b|\bready for production\b|\bspreman za produkciju\b",
     "production-ready"),
    (r"\balways (works|returns|catches)\b|\buvek (radi|vraća|hvata)\b", "always"),
]

# Characters that render as nothing and split a refused word in two.
INVISIBLE = re.compile(
    "[\u00ad\u034f\u061c\u115f\u1160\u17b4\u17b5\u180b-\u180e\u200b-\u200f"
    "\u202a-\u202e\u2028\u2029\u2060-\u2064\u2066-\u206f\u3164\ufe00-\ufe0f"
    "\ufeff\uffa0\ufff9-\ufffb\U000e0000-\U000e0fff]")


def normalise(text):
    """Remove characters a reader cannot see but a regex can trip over.

    Only zero-width and format characters go; nothing else moves, so a newline
    count taken from the result still names the right line in the original.
    """
    return INVISIBLE.sub("", text)


EV_TAG = re.compile(r"\[EV:([A-Za-z0-9_\-]+)\]")
GAP = re.compile(
    r"\bNOT (TESTED|MEASURED|KNOWN|VERIFIED)\b|\bTO CONFIRM\b|\bTO AGREE\b|\bUNVERIFIED\b"
    r"|\bNIJE (TESTIRANO|MERENO|POZNATO|PROVERENO)\b|\bZA POTVRDU\b|\bZA DOGOVOR\b",
    re.I,
)

# A figure that could be read as performance. Bare years and list numbering are not.
FIGURE = re.compile(
    r"(?<![\w-])\d{1,3}(?:[.,]\d+)?\s?%"          # 87%, 12,5 %
    r"|(?<![\w-])\d+(?:[.,]\d+)?\s*(?:x|puta)\b"  # 3x, 3 puta
    r"|(?<![\w-])\d+(?:[.,]\d+)?\s*(?:h|hours?|sati|sata|min(?:utes?|uta)?|s|sec(?:onds?)?|sekund\w*"
    r"|ms|millisec(?:onds?)?|milisekund\w*)\b"
    r"|(?<![\w-])\d+\s*(?:of|od)\s*\d+\b"         # 7 of 7
    r"|(?<![\w-])\d+\s*/\s*\d+(?![\d/])",         # 7/7
    re.I,
)

# The subset of figures a record can actually settle: a time with a unit.
DURATION = re.compile(
    r"(?<![\w-])(\d+(?:[.,]\d+)?)\s*(millisec(?:onds?)?|milisekund\w*|ms|sec(?:onds?)?|sekund\w*|s"
    r"|min(?:utes?|uta)?|hours?|sati|sata|h)\b",
    re.I,
)
_UNIT_MS = {"ms": 1, "millisecond": 1, "milliseconds": 1, "millisec": 1, "milisekund": 1,
            "s": 1000, "sec": 1000, "second": 1000, "seconds": 1000,
            "min": 60_000, "minute": 60_000, "minutes": 60_000, "minuta": 60_000,
            "h": 3_600_000, "hour": 3_600_000, "hours": 3_600_000,
            "sati": 3_600_000, "sata": 3_600_000}

# Present-tense capability assertions.
ASSERTIVE = re.compile(
    r"\b(passes|passed|fails on|handles|blocks|refuses|rejects|catches|detects|returns|scores"
    r"|validates|routes|extracts|classifies|answers|processes|was tested|has been tested|we tested"
    r"|verified|proven|achieves|reduces|saves)\b"
    r"|\b(prolazi|prošao|obrađuje|blokira|odbija|hvata|otkriva|vraća|ocenjuje|validira|rutira"
    r"|izvlači|klasifikuje|odgovara|testiran\w*|testirali smo|provereno|dokazano|smanjuje|štedi)\b",
    re.I,
)

# Statements about how the agent is configured rather than how it behaves: the
# model, the node count, an id, an eval suite. No acceptance case can evidence
# these — they come from as_get_agent, and they need a config record of their own.
CONFIG_FACT = re.compile(
    r"\bmodel\s*[:=]\s*\S*[-\d]"
    r"|\b(gpt|claude|gemini|llama|mistral|deepseek|qwen)[\w.]*-[\w.]+\b"
    r"|\b(gpt|claude|gemini|llama|mistral|deepseek|qwen)\s+[a-z]+\s*\d"
    r"|(?<![\w-])\d+\s*(nodes?|čvorov\w*|čvora)\b"
    r"|\b(flow|agent|execution)\s+`?[a-z0-9]{16,}`?"
    r"|\bgolden set\b|\bzlatni skup\b",
    re.I,
)

# Negations of capability — under-promises, exempt.
NEGATION = re.compile(
    r"\b(does not|do not|doesn't|don't|cannot|can't|will not|won't|is not|are not|no longer|never claims)\b"
    r"|\b(nothing|none of|no case|no test|not one of|never|neither|nor)\b"
    r"|\bne (radi|obrađuje|blokira|vraća|zna|može|šalje|menja|čuva|odlučuje)\b"
    r"|\bnije\b|\bnisu\b|\bneće\b|\bne može\b|\bništa\b|\bnijedan\b|\bnijedn\w+\b",
    re.I,
)

# A refused phrase immediately preceded by a negation is a disclaimer of that
# phrase, not the phrase itself. "These are intentions, not guarantees" is the
# wording references/maintenance.md prescribes; a checker that refuses it forces
# the author to delete the safest sentence in the document.
DISCLAIMED = re.compile(
    r"(?:\b(?:not|no|never|without|nor)\b|\b(?:ne|nije|nisu|neće|bez|niti)\b)[\s,\-–—]*$",
    re.I,
)

# An explicit refusal to claim something. "We do not claim the agent is secure"
# is the sentence a careful consultant writes, and a checker that refuses it
# teaches the author to say nothing at all — the opposite of what this gate wants.
# Advice addressed to the reader about their own arrangements. "Make sure your
# keys are secure" is a task for them, not a warranty from you.
ADVICE = re.compile(
    r"\b(make sure|makes sure|ensure|ensures|ensuring|check that|verify that|confirm that"
    r"|it is your responsibility|your responsibility)\b"
    r"|\b(proverite|obezbedite|vodite računa|uverite se)\b", re.I)

DISCLAIMER_LEAD = re.compile(
    r"\b(do|does|did|would|will|can)\s+not\s+(claim|promise|guarantee|assert|say|state|suggest|imply|warrant)\b"
    r"|\bno (claim|promise|warranty|guarantee)\b"
    r"|\bnothing (in|here|about)\b[^.]{0,80}?\b(should|can|may|must) (be|not be) (read|taken|construed|understood)\b"
    r"|\bne (tvrdimo|obećavamo|garantujemo|obavezujemo)\b|\bnijedna (tvrdnja|garancija)\b",
    re.I,
)

# Clause boundaries. A hedge at the end of a sentence does not negate a claim
# made at its start: "It blocks every lead, though nothing is perfect" asserts.
CLAUSE_SPLIT = re.compile(
    r"[,;]|\b(?:though|although|but|however|while|whereas|mada|iako|ali|premda)\b", re.I)

# A number given as a limit is not a measurement, and must not be compared with
# what the runs measured: "inside the 60 s timeout" states a setting.
# A configured limit, or a conditional instruction. Either makes the number a
# setting rather than a measurement — but only where it stands next to it, or a
# stray "timeout" earlier in the sentence would shield a fabricated figure.
THRESHOLD = re.compile(
    r"\b(timeout|limit|cap|budget|deadline|sla|threshold|maximum|minimum|at least|no faster than)\b"
    r"|\b(if|when|whenever|should it|cancel|abort|retry|allow)\b"
    r"|\b(ograničenj\w*|najviše|najmanje|u roku od|ako|kada|otkažite|prekinite|predvidite)\b",
    re.I,
)

# A question mark, and nothing looser. "How the agent blocks X is described
# below" opens with an interrogative and is still an assertion.
QUESTION = re.compile(r"\?\s*$")

# Prose about method rather than result.
# Instructions to the reader, not statements about the agent. "This document
# shows the agent blocks X" was in here once, and it exempted the claim.
METHOD = re.compile(
    r"\b(the test below|to run this|open |click |paste )\b"
    r"|\b(test ispod|da biste|otvorite|kliknite|nalepite)\b",
    re.I,
)

HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
FENCE = re.compile(r"^\s*(```|~~~)")
DRAFT = re.compile(r"DRAFT\b|NACRT\b|NOT YET SENT|NIJE POSLATO", re.I)
PLACEHOLDER = re.compile(r"\[(TO AGREE|TO CONFIRM|DATE|DATUM|NAME|IME|PRICE|CENA|X+)\]", re.I)
# Case-sensitive and anchored to the start of a line: "your internal CRM" in a
# delivery note must not switch the gate off for the whole document.
# A marker line carries no lower-case prose: "INTERNAL sections have been
# stripped" is a sentence in a client document, not a marker on one.
INTERNAL = re.compile(
    r"^[^\S\n]*#{0,6}[^\S\n]*\**[^\S\n]*(INTERNAL|INTERNO)\b"
    r"(?:[\s\W]*(?:NOT FOR THE CLIENT|NIJE ZA KLIJENTA))?[\s\W]*$"
    r"|^[^\S\n]*#{0,6}[^\S\n]*\**[^\S\n]*(NOT FOR THE CLIENT|NIJE ZA KLIJENTA)[\s\W]*$", re.M)

DRAFT_WINDOW = 1000   # the marker belongs at the top, where a reader meets it
INTERNAL_WINDOW = 400

VERDICT_WORD = re.compile(r"\b(PASS|FAIL|PASSED|FAILED|PROŠAO|PAO)\b")
VERDICT_SOFT = re.compile(r"\b(passed|failed|prošao|prošla|pao|pala)\b")
# A lower-case "failed" is a verdict only where a case is named outside its tag.
BARE_CASE = re.compile(r"(?<!\[EV:)\b[A-Z]{2,}-\d{1,4}\b|\bcase\b|\bslučaj\w*\b", re.I)
_VERDICT_OF = {"PASS": "PASS", "PASSED": "PASS", "PROŠAO": "PASS", "PROŠLA": "PASS",
               "FAIL": "FAIL", "FAILED": "FAIL", "PAO": "FAIL", "PALA": "FAIL"}


def is_case_record(rec):
    """A configuration snapshot is not an acceptance run and cannot verdict one."""
    return (rec or {}).get("kind", "case") != "config"


# A clause opening with one of these continues the one before it rather than
# starting a new assertion: "no case checks X, only that the agent answers Y"
# is one statement, and its negation governs both halves.
CONTINUATION = re.compile(r"^\W*(only|merely|just|simply|samo|jedino|već|nego)\b", re.I)

# ...and it only continues a statement *about the suite*. "The agent does not
# guess, only detects every duplicate" is an assertion wearing a hedge.
SCOPE_NEGATION = re.compile(
    r"\b(nothing|none of|no case|no test|not one of|neither)\b"
    r"|\bnijedan\b|\bnijedn\w+\b|\bništa\b", re.I)


def clause_and_offset(text, pos, spans):
    """The governing clause, and where `pos` sits inside it."""
    cl = clause_around(text, pos, spans)
    idx = text.find(cl)
    return cl, (pos - idx if idx != -1 else pos)


def clause_spans(text):
    bounds = list(CLAUSE_SPLIT.finditer(text))
    return list(zip([0] + [m.end() for m in bounds],
                    [m.start() for m in bounds] + [len(text)]))


def negated_before(clause, offset):
    """True where a negation stands earlier in the clause than the match.

    "It never returns a decision" is a denial; "it blocks every domain and never
    lets one through" asserts, then hedges. A negation cannot reach backwards.
    """
    m = NEGATION.search(clause)
    return bool(m) and m.start() < offset


def clause_around(text, pos, spans=None):
    """The span whose negation, if any, governs a match at `pos`.

    Computed spans are passed in by callers that look at many matches in one
    sentence; recomputing them per match made a long line quadratic.
    """
    spans = clause_spans(text) if spans is None else spans
    for i, (s, e) in enumerate(spans):
        if s <= pos <= e:
            prev = text[spans[i - 1][0]:spans[i - 1][1]] if i else ""
            if i and CONTINUATION.match(text[s:e]) and SCOPE_NEGATION.search(prev):
                return prev + text[s:e]
            return text[s:e]
    return text


def fences_balanced(text):
    return sum(1 for line in text.split("\n") if FENCE.match(line)) % 2 == 0


# ------------------------------------------------------------------- splitting

def blank_fences(text, honour=True):
    """Return text with fenced blocks replaced by spaces, offsets preserved.

    Every check that reads raw text — the verdict scan, the placeholder scan —
    must see the same document the sentence-level checks see. A command example
    that prints PASS is not a claim that anything passed.
    """
    if not honour:
        return text
    out, in_fence = [], False
    for raw in text.split("\n"):
        if FENCE.match(raw):
            in_fence = not in_fence
            out.append(" " * len(raw))
            continue
        out.append(" " * len(raw) if in_fence else raw)
    return "\n".join(out)


def logical_lines(text, honour_fences=True):
    """Yield (line_no, text) with hard-wrapped prose joined and code fences skipped.

    A citation split from its claim by a line break is still a cited claim; a
    checker that reads raw lines invents findings that are not there.
    """
    out, buf, start, in_fence = [], [], None, False
    for i, raw in enumerate(text.splitlines(), 1):
        if honour_fences and FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = raw.strip()
        if not s or HEADING.match(raw) or set(s) <= set("-|=* "):
            if buf:
                out.append((start, " ".join(buf)))
                buf, start = [], None
            # A heading is read by the client like any other line, and a claim
            # parked in one used to be invisible to every check.
            if HEADING.match(raw):
                head = re.sub(r"^\s{0,3}#{1,6}\s+", "", s).strip()
                if head:
                    out.append((i, "\x01" + head))
            continue
        if raw.lstrip().startswith(("- ", "* ", "|", "> ")) or re.match(r"^\s*\d+[.)]\s", raw):
            if buf:
                out.append((start, " ".join(buf)))
                buf, start = [], None
            out.append((i, s))
            continue
        if start is None:
            start = i
        buf.append(s)
    if buf:
        out.append((start, " ".join(buf)))
    return out


def sentences(unit):
    """Split on sentence ends, keeping common abbreviations intact."""
    protected = re.sub(r"\b(d\.o\.o|a\.d|npr|tj|itd|e\.g|i\.e|vs)\.", lambda m: m.group(0).replace(".", "\x00"), unit, flags=re.I)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZŠĐČĆŽ\[])", protected)
    return [p.replace("\x00", ".").strip() for p in parts if p.strip()]


# --------------------------------------------------------------------- risking

def risk(text):
    """Return (category, detail) or None.

    Order matters, and it matters in exactly the way that bit us before: the
    forbidden vocabulary is checked before anything can exempt it, and figures
    are checked before any exemption, because every exemption below is a phrase
    an author can add to a sentence that also carries a number.
    """
    spans = clause_spans(text)
    for pat, name in FORBIDDEN:
        for m in re.finditer(pat, text, re.I):
            # DISCLAIMED is end-anchored, so only the tail before the match can
            # ever match it. Slicing the whole prefix made a long line quadratic.
            before = text[max(0, m.start() - 60):m.start()]
            cl = clause_around(text, m.start(), spans)
            if DISCLAIMED.search(before) or DISCLAIMER_LEAD.search(cl):
                continue
            if name == "security" and ADVICE.search(cl):
                continue
            return "FORBIDDEN", f"{name} — {m.group(0).strip()!r}"

    tagged = bool(EV_TAG.search(text))
    marked = bool(GAP.search(text))

    fig = FIGURE.search(text)
    if fig:
        if tagged:
            return None
        # "The pack does not promise 100% accuracy" states the absence of a
        # claim. Only the explicit refusals in DISCLAIMER_LEAD qualify; a bare
        # negation elsewhere in the sentence still does not excuse a figure.
        if DISCLAIMER_LEAD.search(clause_around(text, fig.start(), spans)):
            return None
        if marked:
            return "MIXED", f"figure {fig.group(0).strip()!r} in a sentence that also carries a gap marker"
        return "FIGURE", f"untagged figure {fig.group(0).strip()!r}"

    if tagged or marked:
        return None
    if QUESTION.search(text) or METHOD.search(text):
        return None
    # Negation is judged clause by clause. A blanket exemption let any hedge
    # anywhere in the sentence switch the checker off, which is a one-word escape
    # from every remaining category.
    for m in CONFIG_FACT.finditer(text):
        cl, off = clause_and_offset(text, m.start(), spans)
        if not negated_before(cl, off):
            return "CONFIG_CLAIM", f"configuration fact {m.group(0).strip()!r} with no record behind it"
    if len(text.split()) < 4:
        return None
    for m in ASSERTIVE.finditer(text):
        cl, off = clause_and_offset(text, m.start(), spans)
        if not negated_before(cl, off):
            return "CLAIM", f"capability claim {m.group(0).strip()!r} with no evidence tag"
    return None


# -------------------------------------------------------------------- evidence

def load_evidence(d):
    ev = {}
    p = Path(d)
    if not p.is_dir():
        return ev, [f"evidence directory not found: {d}"]
    errs = []
    seen = {}
    for f in sorted(p.glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            errs.append(f"{f.name}: unreadable ({e})")
            continue
        if not isinstance(rec, dict):
            errs.append(f"{f.name}: not a JSON object")
            continue
        if rec.get("schema") != "adp-evidence-1":
            errs.append(f"{f.name}: not an adp-evidence-1 record")
            continue
        cid = rec.get("case_id")
        if not cid:
            errs.append(f"{f.name}: no case_id")
            continue
        # Silently letting the second file win is how a recorded FAIL disappears.
        if cid in seen:
            errs.append(f"DUPLICATE case_id {cid}: {seen[cid]} and {f.name} both claim it "
                        f"({ev[cid].get('verdict')} and {rec.get('verdict')}) — remove one")
            continue
        seen[cid] = f.name
        ev[cid] = rec
    return ev, errs


def record_durations(rec):
    """Every duration in milliseconds the record actually measured."""
    out = []
    for holder, key in ((rec.get("returned") or {}, "round_trip_ms"),
                        (rec.get("server_execution") or {}, "duration_ms")):
        v = holder.get(key) if isinstance(holder, dict) else None
        if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
            out.append(float(v))
    return out


def duration_ms(value_text, unit_text):
    unit = unit_text.lower()
    for k in sorted(_UNIT_MS, key=len, reverse=True):
        if unit.startswith(k):
            return float(value_text.replace(",", ".")) * _UNIT_MS[k], _UNIT_MS[k]
    if unit.startswith("sekund"):
        return float(value_text.replace(",", ".")) * 1000, 1000
    return None, None


def rounding_margin(value_text, unit_ms):
    """Half of the last digit the author wrote, in milliseconds.

    "about 10 s" is a correct rounding of 9.73 s; "21 s" is not a rounding of
    anything at or below 20.463 s. The margin is what separates the two.
    """
    frac = value_text.replace(",", ".").split(".")
    step = 1.0 if len(frac) == 1 else 10 ** -len(frac[1])
    return 0.5 * step * unit_ms


def check_durations(sentence, cited, ev):
    """Findings for durations that do not match the records the sentence cites.

    Returns (category, detail) pairs. A number given as a limit — "inside the
    60 s timeout" — states a setting, not a measurement, and is left alone.
    """
    resolved = [c for c in cited if c in ev]
    cases = [c for c in resolved if is_case_record(ev[c])]
    timings = list(DURATION.finditer(sentence))
    if not timings:
        return []
    if resolved and not cases:
        return [("WRONG_RECORD_KIND",
                 f"a duration is cited to {sorted(resolved)}, which hold no run — "
                 "a configuration snapshot cannot time anything")]
    pool = []
    for cid in cases:
        pool.extend(record_durations(ev[cid]))
    if not pool:
        return []
    lo, hi = min(pool), max(pool)
    out = []
    for m in timings:
        val, unit_ms = duration_ms(m.group(1), m.group(2))
        if val is None:
            continue
        margin = rounding_margin(m.group(1), unit_ms)
        # A configured limit or a conditional instruction, standing next to the
        # number, makes it a setting. A bare comparative does not: "answers in
        # under 2 seconds" is a speed claim the runs can contradict.
        if THRESHOLD.search(sentence[max(0, m.start() - 20):m.end() + 20]):
            continue
        if val < lo - margin or val > hi + margin:
            out.append(("FIGURE_OUTSIDE",
                        f"{m.group(0).strip()!r} is outside {lo / 1000:.3g}–{hi / 1000:.3g} s, "
                        f"the range actually measured by {sorted(set(cases))}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--evidence", default="evidence")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on WEAK corroboration and on unreferenced evidence")
    a = ap.parse_args()

    ev, ev_errs = load_evidence(a.evidence)
    findings = [("evidence", 0, "SETUP", e) for e in ev_errs]
    referenced = set()
    skipped = []

    for fp in a.files:
        try:
            text = Path(fp).read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeDecodeError, IsADirectoryError) as e:
            sys.stderr.write(f"cannot read {fp}: {e}\n")
            return 2

        text = normalise(text)
        name = Path(fp).name
        if INTERNAL.search(text[:INTERNAL_WINDOW]):
            skipped.append(name)
            continue

        is_draft = bool(DRAFT.search(text[:DRAFT_WINDOW]))
        # An unterminated fence would otherwise blank the rest of the file and
        # take every check with it. Read it as prose, and say why.
        balanced = fences_balanced(text)
        if not balanced:
            findings.append((name, 0, "UNCLOSED_FENCE",
                             "a code fence is opened and never closed; the file is checked as prose"))
        plain = blank_fences(text, honour=balanced)

        for lineno, unit in logical_lines(text, honour_fences=balanced):
            # A heading is a label, not a sentence. Judging it for untagged
            # figures and capability verbs condemns "## How the agent scores a
            # lead" and "## Response within 4 hours", which are section titles.
            heading = unit.startswith("\x01")
            unit = unit.lstrip("\x01")
            for s in sentences(unit):
                cited = EV_TAG.findall(s)
                for cid in cited:
                    referenced.add(cid)
                    if cid not in ev:
                        findings.append((name, lineno, "DANGLING", f"[EV:{cid}] resolves to no evidence record"))
                r = risk(s)
                if r and (not heading or r[0] == "FORBIDDEN"):
                    findings.append((name, lineno, r[0], f"{r[1]} :: {s[:120]}"))
                for kind, detail in check_durations(s, cited, ev):
                    findings.append((name, lineno, kind, f"{detail} :: {s[:120]}"))

        # A verdict word must come from evidence, not from the author — and it
        # must be the verdict the evidence actually recorded.
        seen_at, row_tag_cache = set(), {}
        for m in list(VERDICT_WORD.finditer(plain)) + list(VERDICT_SOFT.finditer(plain)):
            if m.start() in seen_at:
                continue
            seen_at.add(m.start())
            shouted = m.group(0).isupper()
            line = plain[:m.start()].count("\n") + 1
            row_start = plain.rfind("\n", 0, m.start()) + 1
            row_end = plain.find("\n", m.start())
            row_end = row_end if row_end != -1 else len(plain)
            row = plain[row_start:row_end]
            if row_start not in row_tag_cache:
                row_tag_cache[row_start] = (
                    [(tg.start() + row_start, tg.group(1)) for tg in EV_TAG.finditer(row)],
                    [row_start + i for i, ch in enumerate(row) if ch in ",|"])
            row_tags, seps = row_tag_cache[row_start]
            # A row can hold several results — "PASS on the warm lead [EV:AT-01],
            # FAIL on the duplicate [EV:AT-02]". The item is the unit that owns
            # the verdict; the row is only the fallback.
            li = bisect_left(seps, m.start())
            hi_i = bisect_right(seps, m.end() - 1)
            item_lo = seps[li - 1] + 1 if li else row_start
            item_hi = seps[hi_i] if hi_i < len(seps) else row_end
            # A lower-case "failed" is a verdict only where a case is named in
            # the open. "A lead that failed validation" is ordinary prose.
            if not shouted and not BARE_CASE.search(row):
                continue
            # The tag that owns this verdict is the one on its own row, and
            # preferably the one before it — a results row reads "[EV:AT-01] …
            # PASS", so the next row's tag would otherwise be nearer.
            # The tag nearest the verdict on its own row owns it, whichever side
            # it sits. A results list writes "[EV:AT-01] … PASS"; the prescribed
            # block writes "PASS [EV:AT-01]"; both are one row.
            item_tags = [(pos, c) for pos, c in row_tags if item_lo <= pos < item_hi]
            if item_tags:
                candidates = [c for _, c in sorted((abs(pos - m.start()), c) for pos, c in item_tags)]
            else:
                # Nothing in this cell. A table reads left to right, so the label
                # column before the verdict owns it before anything after does.
                candidates = ([c for _, c in sorted(((m.start() - pos), c)
                                                    for pos, c in row_tags if pos < m.start())]
                              + [c for _, c in sorted(((pos - m.start()), c)
                                                      for pos, c in row_tags if pos >= m.start())])
            if not candidates:
                lo = max(0, m.start() - 200)
                candidates = [c for _, c in sorted(
                    (abs(lo + t.start() - m.start()), t.group(1))
                    for t in EV_TAG.finditer(plain[lo:m.start() + 200]))]
            if not candidates:
                if shouted:
                    findings.append((name, line, "UNSOURCED_VERDICT",
                                     f"{m.group(0)!r} with no [EV:...] within 200 characters"))
                continue
            stated = _VERDICT_OF[m.group(0).upper()]
            nearest = next((cid for cid in candidates if cid in ev), None)
            if nearest is None:
                continue
            if not is_case_record(ev[nearest]):
                findings.append((name, line, "WRONG_RECORD_KIND",
                                 f"{m.group(0)} is cited to {nearest}, a configuration snapshot, "
                                 "which records no run and no verdict"))
                continue
            recorded = ev[nearest].get("verdict")
            if recorded and stated != recorded:
                findings.append((name, line, "VERDICT_MISMATCH",
                                 f"the document says {m.group(0)} but {nearest} records {recorded}"))

        if not is_draft:
            for m in PLACEHOLDER.finditer(plain):
                line = plain[:m.start()].count("\n") + 1
                findings.append((name, line, "PLACEHOLDER",
                                 f"{m.group(0)} left in a file carrying no DRAFT marker in its "
                                 f"first {DRAFT_WINDOW} characters — the marker belongs at the top"))

    # Evidence that exists but is cited nowhere. A recorded FAIL that no document
    # mentions is the failure mode this catches.
    for cid, rec in sorted(ev.items()):
        if cid not in referenced:
            sev = "BURIED_FAIL" if rec.get("verdict") == "FAIL" else "UNCITED"
            if sev == "BURIED_FAIL" or a.strict:
                findings.append(("evidence", 0, sev,
                                 f"{cid} ({rec.get('verdict')}) is recorded but cited in no document"))
        if rec.get("attribution") == "unmatched":
            findings.append(("evidence", 0, "UNATTRIBUTED",
                             f"{cid}: {rec.get('server_execution_note') or 'no execution in the list matched this response'}"))
        if rec.get("corroboration") == "NONE":
            findings.append(("evidence", 0, "UNCORROBORATED",
                             f"{cid} has no server execution record — {rec.get('corroboration_note')}"))
        elif rec.get("corroboration") == "WEAK" and a.strict:
            findings.append(("evidence", 0, "WEAK_CORROBORATION",
                             f"{cid}: {rec.get('corroboration_note')}"))

    for n in skipped:
        print(f"{n}: skipped — marked INTERNAL, and the internal note is not gated")

    if not findings:
        print(f"clean — {len(ev)} evidence record(s), {len(referenced)} referenced")
        return 0

    order = {"FORBIDDEN": 0, "VERDICT_MISMATCH": 1, "WRONG_RECORD_KIND": 2, "UNSOURCED_VERDICT": 3,
             "DANGLING": 4, "BURIED_FAIL": 5, "UNATTRIBUTED": 6, "UNCLOSED_FENCE": 7,
             "FIGURE_OUTSIDE": 8, "FIGURE": 9, "MIXED": 10, "CONFIG_CLAIM": 11, "CLAIM": 12}
    findings.sort(key=lambda f: (order.get(f[2], 12), f[0], f[1]))
    for fname, line, kind, detail in findings:
        loc = f"{fname}:{line}" if line else fname
        print(f"{loc}: {kind}: {detail}")
    print(f"\n{len(findings)} finding(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
