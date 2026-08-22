#!/usr/bin/env python3
"""Flag claims in a dossier that carry no source, and citations that point nowhere.

Two checks run:

  1. Every claim carries a citation, or a gap marker (UNVERIFIED / NOT FOUND / TO CONFIRM).
  2. Every citation label used inline is defined in the Sources block.

## Why figures are checked before every exemption

An earlier version applied the question, ignorance and gap-marker exemptions to a whole
sentence before looking for numbers, so appending five words defeated the gate:

    "They employ 400 people and moved 12,000 tonnes."            -> flagged
    "...400 people and 12,000 tonnes, though the basis is unclear." -> passed

Worse, the dossier format induces exactly that shape: section 9 is where two sources
disagree, and "the site claims 400 while the filing gives 260 — which basis is used is
unclear" is the natural way to write it. Figures are now checked first and independently,
so an uncited number cannot be talked out of the gate.

## Language

The heuristics are strongest in English and cover common Serbian forms. Assertions in
other languages will not be detected — the figure, registration, field and table checks
are language-neutral and still apply, but treat a non-English pack as partially checked
and read it yourself. `--lang-warn` prints a reminder when the file looks non-English.

Usage:
    python3 check_sources.py <company>-dossier.md --strict

Exit codes: 0 clean, or findings without --strict. 1 findings with --strict. 2 bad input.
"""

import argparse
import re
import sys

# --- citations -----------------------------------------------------------------------

LABEL = re.compile(r"\[([^\]\n]{2,80})\]")
URL = re.compile(r"https?://\S+")
NOT_A_LABEL = re.compile(r"\b(tbd|to be checked|to check|check before|verify|todo|to do|"
                         r"placeholder|xxx|\?\?)\b|^\s*\?+\s*$", re.I)
FOOTNOTE = re.compile(r"^\^?\d+$")
# Text inside quotation marks. Editorial insertions there — "we import [and blend] oils"
# — are part of the quotation, not citations, and the adverse-findings procedure
# requires verbatim quotes.
QUOTED = re.compile(r"[\"“”«»']([^\"“”«»']{4,400})[\"“”«»']")

GAP_MARKER = re.compile(
    r"\b(?:UNVERIFIED|NOT FOUND|NOT ESTABLISHED|TO CONFIRM|TO AGREE|NOT ATTEMPTED|"
    r"UNAVAILABLE|NIJE UTVR[ĐD]ENO|NIJE PRONA[ĐD]ENO|NEPOZNATO|ZA POTVRDU|NEPOTVR[ĐD]ENO)\b")

# --- claims --------------------------------------------------------------------------

CURRENCY = r"(?:USD|EUR|GBP|NGN|RSD|CHF|ZAR|GHS|XOF|din\.?|\$|€|£|₦)"
MAGNITUDE = r"(?:k|m|bn|mn|million|billion|thousand|trillion|miliona|milijardi|hiljada)"
UNIT = (r"(?:%|per\s?cent|percent|posto|odsto|MT|tonnes?|tons?|tona|kg|containers?|"
        r"kontejnera|shipments?|po[šs]iljk\w*|TEU|employees?|staff|people|zaposlen\w*|"
        r"radnik\w*|headcount|years?|godin\w*|months?|meseci|markets?|tr[žz]i[šs]t\w*|"
        r"countries|zemalja|offices?|kancelarij\w*|sites?|plants?|depots?|vessels?)")

NUMBER = re.compile(
    rf"(?:{CURRENCY}\s?\d[\d,. ]*\s*{MAGNITUDE}?"
    rf"|\b\d[\d,. ]*\s*{MAGNITUDE}\b"
    rf"|\b\d[\d,. ]*\s*{UNIT}\b"
    rf"|\b\d[\d,. ]*\s*{CURRENCY})", re.I)
NUMBER_LOOSE = re.compile(rf"\b\d[\d,. ]*\s*{MAGNITUDE}?\s*{CURRENCY}", re.I)
# The unit often precedes the figure — "Headcount is 400", "employees: 120". Without
# this the number is invisible and the sentence escapes through a hedge.
NUMBER_PRE = re.compile(rf"{UNIT}\w*\b[\s:=]*(?:is|are|of|was|were|reached|stood at|je|iznosi)?[\s:=]*\d", re.I)
REG = re.compile(r"\b(?:RC|CAC|PIB|MB|VAT|reg(?:istration)?\.?\s*(?:no|number)?|"
                 r"company\s+(?:no|number)|mati[čc]ni\s+broj)\b[\s:.#-]*(?=[\w-]*\d)[\w-]{4,}",
                 re.I)
YEAR = re.compile(r"\b(?:18|19|20)\d{2}\b")
ASSERTIVE = re.compile(r"\b(?:is|are|was|were|has|have|had|operates?|trades?|employs?|"
                       r"owns?|runs?|exports?|imports?|founded|incorporated|headquartered|"
                       r"based|holds?|supplies|manufactures?"
                       r"|je|su|bio|bila|ima|imaju|posluje|posluju|zapo[šs]ljava|izvozi|"
                       r"uvozi|osnovan\w*|sedi[šs]te|dr[žz]i|proizvodi)\b", re.I)

# --- non-claims ----------------------------------------------------------------------

IGNORANCE = re.compile(
    r"\b(?:not (?:known|established|stated|published|disclosed|available|attempted|"
    r"confirmed|clear|resolved)|no (?:public|published|independent) (?:information|record|"
    r"source|data)|could not (?:be )?(?:found|fetched|established|confirmed|reached)|"
    r"unknown|unclear|remains? open|we do not know|nothing (?:published|found)|robots|"
    r"paywall|iza pla[ćc]anja|nis[uc]? javno|nije javno|nije (?:poznato|utvr[đd]eno|"
    r"jasno|dostupno)|nema (?:javn\w+|podataka))\b",
    re.I)
OPEN_QUESTION = re.compile(
    r"\b(?:whether|what the|which (?:one|system|entity|basis|form)|who the|why the|how long|"
    r"to be (?:confirmed|established|verified)|ask on the call|on the agenda"
    r"|da li|koji|koja|koje|koliko|kada|kako|gde|ko je|ko su|za[šs]to|"
    r"raspodela nije|nije poznat\w*)\b", re.I)

# Prose about the research itself — which sources were tried, why a step degraded, what
# language the pack is in. The governing rule is "every factual claim ABOUT THE COMPANY",
# and flagging the consultant's own method notes trains the writer to reword good prose.
# Figures are never exempted by this: only the assertion heuristic backs off.
METHOD_PROSE = re.compile(
    r"\b(?:dossier|this file|this pack|the call|the agenda|section \d|research(?:ed)?|"
    r"degraded|aggregator|registry (?:access|search)|could not be (?:fetched|reached)|"
    r"source[s]? (?:were|was|are|is)|quoted|translat\w+|language of the pack"
    r"|dosije\w*|paket\w*|agend\w+|razgovor\w*|istra[žz]iva\w+|degradira\w+|"
    r"degradacij\w+|agregator\w*|APR|pretrag\w+|prevo[dđ]\w+|jezik\w* (?:paketa|analize)|"
    r"citat\w*|napomen\w+|izvor\w* (?:su|je|nis[uc])|posredn\w+)\b", re.I)
STRUCTURE = re.compile(r"^\s*(?:#{1,6}\s|>\s*$|```|---+\s*$|\*\*\*+\s*$|\d+\.\s*$|[-*+]\s*$)")
# The mandated first-line block: internal header, research date, deletion date.
FILE_HEADER = re.compile(r"^\s*\*{0,2}(?:INTERNAL|DRAFT)\b|^\s*(?:\*\*)?(?:Research(?:ed)? date"
                         r"|Delete (?:by|this file)|Datum istra[žz]ivanja|Obrisati)\b", re.I)
# "Sources", optionally numbered and optionally qualified — "## Sources (fetched 2026-07-30)"
# is a Sources block. "Sources of supply" is not.
SOURCES_HEADING = re.compile(r"^\s*#{1,6}\s*(?:\d+\.\s*)?(?:sources?|izvori)\s*"
                             r"(?:[:.]|\(|\[|,|—|-|$)", re.I)
NOT_SOURCES = re.compile(r"^\s*#{1,6}\s*(?:\d+\.\s*)?sources?\s+(?:of|for|from)\b", re.I)
TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")
# Abbreviations whose internal periods must not end a sentence.
ABBREV_END = re.compile(r"(?:\b[A-Za-zČĆŠĐŽčćšđž]\.|\b(?:d\.o\.o|a\.d|d\.d|s\.r\.o|Ltd|Inc|"
                        r"No|pp|str|god)\.)\s*$", re.I)


def is_sources_heading(line):
    return bool(SOURCES_HEADING.match(line)) and not NOT_SOURCES.match(line)


def strip_quoted(text):
    return QUOTED.sub(" ", text)


def real_labels(text):
    """Citation labels, excluding editorial insertions inside quotations and footnotes."""
    return [m for m in LABEL.findall(strip_quoted(text))
            if not NOT_A_LABEL.search(m) and not FOOTNOTE.match(m.strip())]


def is_citation(text):
    return bool(URL.search(text)) or bool(real_labels(text))


def split_sentences(line):
    """Sentences, keeping trailing citation groups and abbreviations intact."""
    raw = re.split(r"(?<=[.!?])\s+", line)
    joined, buf = [], ""
    for part in raw:
        buf = (buf + " " + part).strip() if buf else part.strip()
        if not ABBREV_END.search(buf):
            joined.append(buf)
            buf = ""
    if buf:
        joined.append(buf)

    merged = []
    for p in [s for s in joined if s.strip()]:
        bare = LABEL.sub("", URL.sub("", p)).strip(" .,;:-")
        if merged and not bare:
            merged[-1] = merged[-1] + " " + p
        else:
            merged.append(p)
    return merged


def units(line):
    stripped = line.strip()
    if stripped.startswith("|") or (stripped.count("|") >= 2 and not stripped.startswith("#")):
        yield stripped, "table row"
        return
    if re.match(r"^\s*(?:[-*+]\s+)?\*\*[^*]{2,60}:?\*\*\s*:?\s*$", stripped):
        return
    if re.match(r"^\s*(?:[-*+]\s+)?(?:\*\*)?[\w /()'-]{2,40}(?:\*\*)?\s*:\s*\S", line):
        yield stripped, "field"
        return
    for s in split_sentences(stripped):
        yield s, "sentence"


def has_figure(text):
    return bool(NUMBER.search(text) or NUMBER_LOOSE.search(text)
                or NUMBER_PRE.search(text) or REG.search(text))


def risk(text, kind):
    """Risk label for an uncited unit, or None if it is not a claim.

    Order matters. Figures are checked before any exemption, because every exemption
    below is a phrase an author can add to a sentence that also contains a number.
    """
    if has_figure(text):
        return "MIXED" if GAP_MARKER.search(text) else "NUMBER"
    if GAP_MARKER.search(text):
        return None
    if text.rstrip().endswith("?") or OPEN_QUESTION.search(text) or IGNORANCE.search(text):
        return None
    words = len(text.split())
    if kind in ("table row", "field"):
        return "VALUE" if words >= 2 and re.search(r"\d|\w{4,}", text) else None
    if words < 5:
        return None
    if METHOD_PROSE.search(text):
        return None                      # a note about the research, not a claim about them
    if YEAR.search(text) and words >= 8:
        return "DATE"
    if ASSERTIVE.search(text) and words >= 6:
        return "ASSERTION"
    return None


def parse_sources_block(text):
    defined, in_block = set(), False
    for line in text.splitlines():
        if is_sources_heading(line):
            in_block = True
            continue
        if in_block and re.match(r"^\s*#{1,6}\s", line):
            break
        if in_block:
            for m in real_labels(line):
                defined.add(m.strip().lower())
            if URL.search(line):
                if line.strip().startswith("|"):
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if cells and cells[0] and not URL.search(cells[0]):
                        defined.add(cells[0].strip("*` ").lower())
                else:
                    head = re.split(r"—|–|\s-\s|:\s|https?://", line.strip().lstrip("-*+ "), 1)[0]
                    head = head.strip("*`[] ")
                    if head and len(head) <= 80:
                        defined.add(head.lower())
    return defined


def logical_lines(text):
    """Join hard-wrapped prose into one logical line before checking.

    The checker is line-based, so a claim on one line and its [label] on the next read as
    uncited. Both trial runs hit this and one spent an extra pass on it.
    """
    out, buf, start = [], "", 0
    in_code = False
    for n, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            if buf:
                out.append((start, buf)); buf = ""
            out.append((n, line))
            continue
        structural = (not s or in_code or STRUCTURE.match(line) or TABLE_SEP.match(line)
                      or s.startswith("|") or is_sources_heading(line))
        if structural:
            if buf:
                out.append((start, buf)); buf = ""
            out.append((n, line))
            continue
        if buf:
            buf += " " + s
        else:
            buf, start = s, n
    if buf:
        out.append((start, buf))
    return out


def main():
    ap = argparse.ArgumentParser(description="Flag uncited claims and undefined citations.")
    ap.add_argument("path")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if anything is flagged (use as a delivery gate)")
    args = ap.parse_args()

    try:
        with open(args.path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"Could not read {args.path}: {exc}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as exc:
        print(f"{args.path} is not UTF-8 ({exc}). Re-save it as UTF-8 and re-run.",
              file=sys.stderr)
        return 2

    defined = parse_sources_block(text)
    uncited, undefined = [], []
    in_sources = in_code = False

    lines = text.splitlines()
    header_rows = {i for i in range(len(lines) - 1) if TABLE_SEP.match(lines[i + 1])}

    for n, line in logical_lines(text):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if is_sources_heading(line):
            in_sources = True
            continue
        if in_sources and re.match(r"^\s*#{1,6}\s", line):
            in_sources = False
        if (in_sources or not stripped or STRUCTURE.match(line) or TABLE_SEP.match(line)
                or FILE_HEADER.match(stripped)):
            continue
        # A table header row is column names — unless it carries a figure, in which case
        # the table has no header row and this is data.
        if n - 1 in header_rows and not has_figure(stripped):
            continue

        for used in real_labels(stripped):
            key = used.strip().lower()
            if key not in defined:
                why = "not listed in Sources" if defined else "no Sources block to check against"
                undefined.append((n, used, why))
        for used in LABEL.findall(strip_quoted(stripped)):
            if NOT_A_LABEL.search(used):
                undefined.append((n, used, "note, not a source"))

        for text_unit, kind in units(stripped):
            if is_citation(text_unit):
                continue
            label = risk(text_unit, kind)
            if label:
                uncited.append((n, label, kind, text_unit))

    urls = sorted(set(URL.findall(text)))
    print(f"Checked {args.path}")
    print(f"  source labels defined: {len(defined)}   URLs listed: {len(urls)}")

    problems = 0
    if not defined:
        # Fail closed: with no Sources block every inline label is unverifiable, and the
        # earlier version simply stopped checking them.
        print("  WARNING: no Sources block found, so no citation can be validated. Add a "
              "'## Sources' section listing every label with its URL and fetch date.")
        problems += 1
    if not urls:
        print("  WARNING: no URLs anywhere in the file.")
        problems += 1

    non_ascii = sum(1 for c in text if ord(c) > 127)
    if non_ascii > len(text) * 0.01:
        print("  NOTE: this file looks non-English. Figure, field and table checks are "
              "language-neutral, but assertion detection covers English and Serbian only — "
              "read the prose yourself.")

    if undefined:
        problems += len(undefined)
        print(f"\n  {len(undefined)} citation(s) pointing nowhere:\n")
        for n, used, why in undefined:
            print(f"  line {n:>4}  [{used[:60]}]  — {why}")

    if uncited:
        problems += len(uncited)
        order = {"NUMBER": 0, "VALUE": 1, "MIXED": 2, "DATE": 3, "ASSERTION": 4}
        print(f"\n  {len(uncited)} claim(s) with no source and no gap marker:\n")
        for n, label, kind, s in sorted(uncited, key=lambda f: (order[f[1]], f[0])):
            print(f"  line {n:>4}  [{label}/{kind}]  {s[:140]}")

    if not problems:
        print("  Clean: every claim carries a source or a gap marker, and every label resolves.")
        return 0

    print("\n  Fix each one of two ways: add a source label that is defined in the Sources "
          "block, or mark it UNVERIFIED / NOT FOUND / TO CONFIRM.")
    print("  A figure is never exempted by a hedge, a question or a gap marker elsewhere in "
          "the sentence — cite it, or move it out of the sentence.")
    print("  NUMBER and VALUE findings first: figures are what a prospect checks and quotes back.")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
