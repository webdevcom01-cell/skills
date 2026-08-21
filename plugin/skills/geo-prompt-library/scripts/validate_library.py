#!/usr/bin/env python3
"""geo-prompt-library QA gate. Fail-closed: G1-G16, exit 0/1, JSON report on stdout.

Two rules deliberately deviate from a literal reading of the brief, because the
literal reading does not survive contact with real near-duplicate/language pairs
(see CHANGELOG.md, [0.1.0-draft] "QA gate calibration"):

G7 (near-duplicate) uses word-trigram OVERLAP COEFFICIENT (|A intersect B| /
min(|A|,|B|)), not symmetric Jaccard. Jaccard structurally cannot exceed
len(shorter)/len(longer) when one query is the other plus a trailing clause (e.g.
the same query with "u Srbiji" appended) -- for a 5-word query plus a 2-word
suffix that caps Jaccard around 0.73, always under the 0.85 threshold, so the
single most common real near-dup pattern in this domain would never trigger.
Overlap coefficient correctly reads that case as 1.0 (fully contained) while
still reading genuine paraphrases (little lexical overlap) as low.

But overlap-coefficient-alone reads 1.0 for ANY subset relationship, including
two queries that are legitimately different matrix cells -- e.g. a
category_shortlist query and the `local` query that is the same phrase plus a
city (the city IS the reason `local` is a separate cell; that pair should both
exist, not collapse to one). So G7 is split by whether the two queries share a
category:
  G7a (same category):      overlap coefficient > 0.85 -> duplicate.
  G7b (different category): duplicate only if the normalized token SET is
                             identical -- a category-appropriate modifier (a
                             city, a segment) changes the set and is exempt.

G8 (wrong-language-per-row) uses a closed-class Serbian function-word ratio, not
statistical language detection. Statistical detectors are unreliable on 5-8 word
strings, cannot separate sr/hr/bs reliably at all, and misfire on legitimate
mixed-code queries ("najbolji project management alat za male timove" -- mostly
English content words, still a grammatical Serbian sentence). Function words are
a closed set that does not depend on string length or vertical vocabulary.
"""

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from orthographic_variants import to_ascii, to_cyrillic  # noqa: E402

SCHEMA_PATH = SCRIPT_DIR.parent / "assets" / "library.schema.json"
GATE_VERSION = "0.1.0-draft"

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ENV_ERROR = 2

# --- Section 5 quotas, kept here as the executable source of truth (mirrored in
# references/taxonomy.md for humans once that file exists). ---
CATEGORY_QUOTA = {
    "problem_aware": (0.15, 0.22),
    "category_shortlist": (0.22, 0.30),
    "use_case": (0.15, 0.22),
    "comparison": (0.12, 0.20),
    "pricing": (0.08, 0.12),
    "local": (0.05, 0.15),
    "trust_risk": (0.05, 0.10),
    "branded": (0.08, 0.15),
}
BRANDED_CAP_FRACTION = 0.15

# Every entry here trades recall for precision: G8's whole premise (a closed
# SR function-word set beats statistical language detection, see module
# docstring) only holds if the words in the set are NOT also common English
# words -- add one that collides and G8 starts reading ordinary EN queries as
# SR. Checked before adding, not assumed: every word below was verified
# against fixtures/valid_library.json's EN rows before landing here.
# `int-001-en` in that fixture is a standing canary sentence built to contain
# every landmine listed below (i/a/to/on/me/no, plus "do") in one natural EN
# query -- add any of them to this set without checking and that fixture
# fails on the next `verify_fixtures.py` run, not silently in production.
#
# Known landmines for the NEXT addition to this set -- real SR function
# words, all rejected so far because they double as common English words:
# "i" (and) / "a" (but) -- the two most tempting to add, and the two most
# dangerous: both are single letters that collide with the English word "I"
# and the English article "a", which would misfire on nearly every EN row.
# Also "to" (that), "on" (he), "me" (me/to me), "no" (but/well), "sam" (I am)
# -- each is a common standalone English word or name. "do" was tried and
# reverted in round 9 (see below) as a concrete, measured instance of exactly
# this failure mode, not a hypothetical.
SR_FUNCTION_WORDS = {
    "da", "li", "je", "za", "u", "kako", "šta", "na", "se", "sa", "ili",
    # koji/koja/koje/koju/kojim -- Serbian agrees the relative/interrogative
    # pronoun in gender with its noun ("koji CRM" but "koja ordinacija"); the
    # original set had only the masculine form, which misread a genuinely
    # grammatical feminine-noun sentence as "not Serbian" (found via eval 0,
    # dentio.rs -- the sole retry on that run, see CHANGELOG.md).
    "koji", "koja", "koje", "koju", "kojim",
    # "do" deliberately excluded from this list despite being a real SR
    # preposition -- it collides with the common English verb "do" ("how do I
    # ...", "what should I do ..."), which flipped G8 to a false SR-positive
    # on every EN row containing it (measured: int-002-en, int-006-en,
    # int-039-en in fixtures/valid_library.json all false-failed on first
    # attempt at this fix). Every other addition here is checked SR-only
    # vocabulary with no common-English-word collision.
    "kod", "po", "od", "iz", "uz", "pri", "o",
}

PLACEHOLDER_RE = re.compile(
    r"\[[^\]]+\]|\{[^}]+\}|TODO|XXX|vaš (brend|proizvod)|your (brand|product)",
    re.IGNORECASE,
)

HR_BS_LOCALES = {"hr-HR", "bs-BA"}
# Non-exhaustive stop-lists, flagged as such in the brief (section 10/13): enough
# to catch the common cases, not a linguistic ground truth.
SR_ISATI_OVATI_STOPLIST = {
    "organizovati", "organizovao", "organizovala", "organizuje",
    "informisati", "informisao", "informisala", "informiše",
    "kontrolisati", "kontrolisao", "kontrolisala", "kontroliše",
    "definisati", "definisao", "definisala", "definiše",
}
SR_EKAVICA_STOPLIST = {"vreme", "vremena", "prevoz", "cena", "cene", "cenovnik", "cenom"}
SR_MONTHS = {
    "januar", "februar", "mart", "april", "maj", "jun", "jul", "avgust",
    "septembar", "oktobar", "novembar", "decembar",
}

WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def _words(text):
    return WORD_RE.findall(text.lower())


def _word_count(text):
    return len(text.split())


def _branded_max(n):
    return math.floor(BRANDED_CAP_FRACTION * n)


def _category_bounds(cat, n, geo_scope=None):
    """Lower/upper intent count for a category at this n_intents.

    branded's upper bound is `_branded_max(n)` -- the SAME function G5 calls, not
    a separately-derived ceil(). The brief states the general quantization formula
    as `[floor(min%xN), ceil(max%xN)]` and states the branded floor-both-sides
    exception in a different paragraph (section 5); a reader (or an implementer)
    who applies the general formula to branded without cross-referencing the
    exception gets ceil(0.15xN), which disagrees with G5 for any N where
    0.15xN isn't an integer (N=30: ceil=5, floor=4 -- see fixtures/p03_branded_over
    .json). Sharing one function removes the possibility of the two rules
    computing different numbers for the same category.

    local's lower bound drops to 0 when geo_scope=="global" -- SKILL.md
    documents this as a rule (`local` has 0 intents, budget redistributed to
    use_case/category_shortlist, for geo_scope=global), but that exception used
    to live only as a table footnote, never reaching this function: floor(0.05xN)
    is >=1 for every N in [30,50], so a correctly-built local=0 library could
    never pass G4 for any global-scope input (found via eval 4, savvycal.com --
    see CHANGELOG.md). ONLY the floor changes here, and ONLY for local: the
    upper bound stays ceil(0.15xN) (0 still satisfies it trivially), and every
    other category's bounds are untouched -- the redistribution ratio itself
    (60/40 to use_case/category_shortlist) is model guidance for Faza 4, not a
    gate rule; encoding it here would be a second unverified cross-reference
    of exactly the kind that caused this bug.
    """
    lo_pct, hi_pct = CATEGORY_QUOTA[cat]
    lo = math.floor(lo_pct * n)
    if cat == "local" and geo_scope == "global":
        lo = 0
    hi = _branded_max(n) if cat == "branded" else math.ceil(hi_pct * n)
    return lo, hi


def _trigrams(words, n=3):
    n = min(n, len(words)) or 1
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def _overlap_coefficient(words_a, words_b):
    tri_a, tri_b = _trigrams(words_a), _trigrams(words_b)
    if not tri_a or not tri_b:
        return 0.0
    intersection = len(tri_a & tri_b)
    return intersection / min(len(tri_a), len(tri_b))


def check_g1_schema(lib, checks):
    try:
        import jsonschema
    except ImportError:
        checks.append({
            "rule": "G1_schema",
            "passed": False,
            "detail": "jsonschema paket nije instaliran (pip install jsonschema) — "
                       "fail-closed, ne preskace se.",
        })
        return
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(lib, schema)
        checks.append({"rule": "G1_schema", "passed": True, "detail": "validno prema library.schema.json"})
    except jsonschema.ValidationError as exc:
        path = "/".join(str(p) for p in exc.absolute_path) or "(root)"
        checks.append({
            "rule": "G1_schema", "passed": False,
            "detail": f"schema violation na '{path}': {exc.message}",
        })


def check_g2_n_intents(lib, checks):
    n = len(lib.get("intents", []))
    ok = 30 <= n <= 50
    checks.append({"rule": "G2_n_intents", "passed": ok, "detail": f"{n} intenata (opseg [30,50])"})


def check_g3_pairing(lib, checks):
    primary = lib.get("locale", {}).get("primary", "sr-RS").split("-")[0]
    bad = []
    for intent in lib.get("intents", []):
        queries = intent.get("queries", [])
        langs = Counter(q.get("lang") for q in queries)
        if langs.get(primary, 0) != 1 or langs.get("en", 0) != 1 or len(queries) != 2:
            bad.append(intent.get("intent_id", "?"))
    ok = not bad
    detail = "svaki intent ima tacno 1 lokalni + 1 en upit" if ok else f"neuparen: {bad}"
    checks.append({"rule": "G3_pairing", "passed": ok, "detail": detail})


def check_g4_quotas(lib, checks):
    intents = lib.get("intents", [])
    n = len(intents)
    # Reads the REQUESTED scope from inputs.geo_scope, not intents[0].geo.scope --
    # the latter is per-intent and legitimately varies within a multi_city
    # library (that field answers "where is this one query about", not "what
    # scope did the user ask for"). inputs is optional (see schema), so this
    # is None for libraries written before it existed -- same as before, no
    # geo_scope exception applied, which was already every prior library's
    # actual behavior.
    geo_scope = lib.get("inputs", {}).get("geo_scope")
    counts = Counter(i.get("category") for i in intents)
    violations = []
    for cat in CATEGORY_QUOTA:
        lo, hi = _category_bounds(cat, n, geo_scope)
        count = counts.get(cat, 0)
        if not (lo <= count <= hi):
            violations.append(f"{cat}: {count} van [{lo},{hi}]")
    ok = not violations
    checks.append({"rule": "G4_category_quotas", "passed": ok, "detail": "; ".join(violations) or "sve kategorije u opsegu"})


def check_g5_branded_cap(lib, checks):
    intents = lib.get("intents", [])
    n = len(intents)
    cap = _branded_max(n)
    count = sum(1 for i in intents if i.get("category") == "branded")
    ok = count <= cap
    pct = (count / n * 100) if n else 0
    checks.append({
        "rule": "G5_branded_cap", "passed": ok,
        "detail": f"{count}/{n} = {pct:.1f}% <= {cap} (floor(15%*{n}))",
    })


def check_g6_placeholder(lib, checks):
    hits = []
    for intent in lib.get("intents", []):
        for q in intent.get("queries", []):
            if PLACEHOLDER_RE.search(q.get("text", "")):
                hits.append(q.get("query_id", "?"))
    ok = not hits
    checks.append({"rule": "G6_placeholder", "passed": ok, "detail": "nema placeholdera" if ok else f"placeholder u: {hits}"})


def check_g7_near_duplicate(lib, checks):
    by_lang = {}
    for intent in lib.get("intents", []):
        cat = intent.get("category")
        for q in intent.get("queries", []):
            by_lang.setdefault(q.get("lang"), []).append((q.get("query_id", "?"), q.get("text", ""), cat))

    violations = []
    for lang, rows in by_lang.items():
        for a in range(len(rows)):
            for b in range(a + 1, len(rows)):
                id_a, text_a, cat_a = rows[a]
                id_b, text_b, cat_b = rows[b]
                words_a, words_b = _words(text_a), _words(text_b)
                if cat_a == cat_b:
                    score = _overlap_coefficient(words_a, words_b)
                    if score > 0.85:
                        violations.append(f"{id_a}~{id_b} ({lang}, G7a {cat_a}) overlap={score:.2f}")
                else:
                    if words_a and set(words_a) == set(words_b):
                        violations.append(f"{id_a}~{id_b} ({lang}, G7b {cat_a}/{cat_b}) identican skup tokena")
    ok = not violations
    checks.append({
        "rule": "G7_near_duplicate", "passed": ok,
        "detail": "nema para preko praga" if ok else "; ".join(violations),
    })


def check_g8_language_per_row(lib, checks):
    primary = lib.get("locale", {}).get("primary", "sr-RS").split("-")[0]
    bad = []
    for intent in lib.get("intents", []):
        for q in intent.get("queries", []):
            lang = q.get("lang")
            hits = sum(1 for w in _words(q.get("text", "")) if w in SR_FUNCTION_WORDS)
            if lang == primary and hits == 0:
                bad.append(f"{q.get('query_id','?')}: lang={lang} ali 0 SR funkcijskih reci (deluje kao en)")
            elif lang == "en" and hits > 0:
                bad.append(f"{q.get('query_id','?')}: lang=en ali {hits} SR funkcijskih reci (deluje kao {primary})")
    ok = not bad
    checks.append({"rule": "G8_language_per_row", "passed": ok, "detail": "sve u redu" if ok else "; ".join(bad)})


def check_g9_length(lib, checks):
    primary = lib.get("locale", {}).get("primary", "sr-RS").split("-")[0]
    bad = []
    for intent in lib.get("intents", []):
        for q in intent.get("queries", []):
            wc = _word_count(q.get("text", ""))
            lang = q.get("lang")
            bounds = (4, 20) if lang == primary else (3, 18)
            if not (bounds[0] <= wc <= bounds[1]):
                bad.append(f"{q.get('query_id','?')}: {wc} reci van {bounds}")
    ok = not bad
    checks.append({"rule": "G9_length", "passed": ok, "detail": "sve u opsegu" if ok else "; ".join(bad)})


def check_g10_comparison_integrity(lib, checks):
    competitor_names = [c.get("name", "").lower() for c in lib.get("competitors", [])]
    bad = []
    for intent in lib.get("intents", []):
        if intent.get("category") != "comparison":
            continue
        ok_intent = False
        for q in intent.get("queries", []):
            text_lower = q.get("text", "").lower()
            if any(name and name in text_lower for name in competitor_names):
                ok_intent = True
            if "alternativa za" in text_lower or "alternative to" in text_lower:
                ok_intent = True
        if not ok_intent:
            bad.append(intent.get("intent_id", "?"))
    ok = not bad
    checks.append({
        "rule": "G10_comparison_integrity", "passed": ok,
        "detail": "svi comparison intenti pominju konkurenta ili 'alternativa za'" if ok else f"bez pokrica: {bad}",
    })


def check_g11_geo_consistency(lib, checks):
    known_cities = {loc.get("city", "").lower() for loc in lib.get("company", {}).get("locations", [])}
    known_cities |= {c.get("city", "").lower() for c in lib.get("competitors", []) if c.get("city")}
    bad = []
    for intent in lib.get("intents", []):
        city = intent.get("geo", {}).get("city")
        if city and city.lower() not in known_cities:
            bad.append(f"{intent.get('intent_id','?')}: geo.city={city!r} nije poznat")
    ok = not bad
    checks.append({"rule": "G11_geo_consistency", "passed": ok, "detail": "svi gradovi poznati" if ok else "; ".join(bad)})


def check_g12_grounding_coverage(lib, checks):
    intents = lib.get("intents", [])
    n = len(intents) or 1
    inferred = sum(1 for i in intents if i.get("inferred"))
    ratio = inferred / n
    ok = ratio <= 0.25
    checks.append({
        "rule": "G12_grounding_coverage", "passed": ok,
        "detail": f"inferred {inferred}/{n} = {ratio*100:.1f}% <= 25%",
    })


def check_g13_persona_balance(lib, checks):
    intents = lib.get("intents", [])
    n = len(intents) or 1
    counts = Counter(i.get("persona_id") for i in intents if i.get("persona_id"))
    bad = [f"{pid}: {c}/{n}={c/n*100:.0f}%" for pid, c in counts.items() if c / n > 0.40]
    ok = not bad
    checks.append({"rule": "G13_persona_balance", "passed": ok, "detail": "nijedna persona > 40%" if ok else "; ".join(bad)})


def check_g14_locale_purity(lib, checks):
    primary = lib.get("locale", {}).get("primary")
    if primary not in HR_BS_LOCALES:
        checks.append({"rule": "G14_locale_purity", "passed": True, "detail": f"n/a za locale={primary}"})
        return
    bad = []
    for intent in lib.get("intents", []):
        for q in intent.get("queries", []):
            if q.get("lang") != primary.split("-")[0]:
                continue
            text_lower = q.get("text", "").lower()
            words = set(_words(q.get("text", "")))
            markers = []
            if "da li" in text_lower:
                markers.append("'da li'")
            if words & SR_ISATI_OVATI_STOPLIST:
                markers.append(f"-isati/-ovati: {sorted(words & SR_ISATI_OVATI_STOPLIST)}")
            if words & SR_EKAVICA_STOPLIST:
                markers.append(f"ekavica: {sorted(words & SR_EKAVICA_STOPLIST)}")
            if words & SR_MONTHS:
                markers.append(f"srpski meseci: {sorted(words & SR_MONTHS)}")
            if markers:
                bad.append(f"{q.get('query_id','?')}: {', '.join(markers)}")
    ok = not bad
    checks.append({"rule": "G14_locale_purity", "passed": ok, "detail": "cist" if ok else "; ".join(bad)})


def check_g15_orthographic_variants(lib, checks):
    """Both variants.ascii and variants.cyrillic must equal the deterministic
    forward mapping of `text` -- never a reconstruction attempted the other way.
    ascii is lossy (č and ć both fold to c, O2), so there is no valid inverse to
    check against; checking the forward map only is the point, not a gap."""
    primary = lib.get("locale", {}).get("primary", "sr-RS").split("-")[0]
    bad = []
    for intent in lib.get("intents", []):
        for q in intent.get("queries", []):
            if q.get("lang") != primary or q.get("script") != "latin":
                continue
            text = q.get("text", "")
            variants = q.get("variants", {})
            expected_ascii = to_ascii(text)
            if variants.get("ascii") != expected_ascii:
                bad.append(f"{q.get('query_id','?')}: ascii={variants.get('ascii')!r} != ocekivano {expected_ascii!r}")
            expected_cyrillic = to_cyrillic(text)
            if variants.get("cyrillic") != expected_cyrillic:
                bad.append(f"{q.get('query_id','?')}: cyrillic={variants.get('cyrillic')!r} != ocekivano {expected_cyrillic!r}")
    ok = not bad
    checks.append({"rule": "G15_orthographic_variants", "passed": ok, "detail": "sve variante tacne" if ok else "; ".join(bad)})


def check_g16_matrix_consistency(lib, checks):
    """Delivered `matrix_plan` (Faza 4, written to the output) vs actual intents.

    Cell key is (category, persona_id, geo.city). For every planned cell, the
    actual intent count in that cell must equal `planned` exactly -- not just
    nonzero -- so this also catches a cell that got MORE intents than planned
    (silently stealing budget from another cell), not just empty ones. Any
    actual cell missing from the plan entirely is flagged too, and the two
    totals (sum of cell.planned, and planned_total vs n_intents) are cross-
    checked so a tampered plan can't just relabel its way around the per-cell
    check.
    """
    plan = lib.get("matrix_plan")
    intents = lib.get("intents", [])
    if not plan:
        checks.append({"rule": "G16_matrix_consistency", "passed": False, "detail": "matrix_plan nedostaje u izlazu"})
        return

    actual_counts = Counter()
    for intent in intents:
        key = (intent.get("category"), intent.get("persona_id"), intent.get("geo", {}).get("city"))
        actual_counts[key] += 1

    bad = []
    plan_keys = set()
    for cell in plan.get("cells", []):
        key = (cell.get("category"), cell.get("persona_id"), cell.get("geo_city"))
        plan_keys.add(key)
        planned, actual = cell.get("planned", 0), actual_counts.get(key, 0)
        if planned != actual:
            bad.append(f"{key}: planned={planned} actual={actual}")

    for key in set(actual_counts) - plan_keys:
        bad.append(f"{key}: actual={actual_counts[key]} nije u planu")

    sum_planned = sum(c.get("planned", 0) for c in plan.get("cells", []))
    planned_total = plan.get("planned_total")
    if planned_total != sum_planned:
        bad.append(f"planned_total={planned_total} != zbir cell.planned={sum_planned}")
    if planned_total != len(intents):
        bad.append(f"planned_total={planned_total} != n_intents={len(intents)}")

    ok = not bad
    checks.append({"rule": "G16_matrix_consistency", "passed": ok, "detail": "plan == stvarno" if ok else "; ".join(bad)})


CHECKS = [
    check_g1_schema, check_g2_n_intents, check_g3_pairing, check_g4_quotas,
    check_g5_branded_cap, check_g6_placeholder, check_g7_near_duplicate,
    check_g8_language_per_row, check_g9_length, check_g10_comparison_integrity,
    check_g11_geo_consistency, check_g12_grounding_coverage, check_g13_persona_balance,
    check_g14_locale_purity, check_g15_orthographic_variants, check_g16_matrix_consistency,
]


# A rule here is "derived" -- and excluded from Faza 7 retry-cell targeting -- when
# it fails ALONGSIDE any of its listed root rules in the same run. Not "whenever
# this rule fails": G16 failing alone (matrix_plan itself tampered) or G15 failing
# alone (a corrupted variants field with no text change) are independent findings,
# not an echo of something already reported elsewhere.
DERIVED_FROM = {
    "G16_matrix_consistency": {"G4_category_quotas", "G11_geo_consistency", "G13_persona_balance"},
    "G15_orthographic_variants": {"G6_placeholder"},
}


def _mark_derived(checks):
    status = {c["rule"]: c["passed"] for c in checks}
    for c in checks:
        roots = DERIVED_FROM.get(c["rule"])
        c["derived"] = bool(
            roots and not c["passed"] and any(not status.get(r, True) for r in roots)
        )


def build_warnings(lib):
    warnings = []
    n = len(lib.get("intents", []))
    if n < 35:
        warnings.append(f"n_intents={n} < 35 — margina greske veca nego preporuceno")
    if lib.get("company", {}).get("confidence") == "low":
        warnings.append("company.confidence == low")
    for c in lib.get("competitors", []):
        if c.get("confidence") == "low":
            warnings.append(f"competitor {c.get('name','?')}.confidence == low")
            break
    # Same source as check_g4_quotas -- inputs.geo_scope (the request), not
    # intents[0].geo.scope (per-intent, varies legitimately under multi_city).
    scope = lib.get("inputs", {}).get("geo_scope")
    if scope == "global" and any(i.get("category") == "local" for i in lib.get("intents", [])):
        warnings.append("local kategorija prisutna a geo_scope == global")
    return warnings


def validate(lib):
    checks = []
    for fn in CHECKS:
        fn(lib, checks)
    _mark_derived(checks)
    passed = all(c["passed"] for c in checks)
    return {
        "passed": passed,
        "gate_version": GATE_VERSION,
        "checks": checks,
        "warnings": build_warnings(lib),
    }


def _require_jsonschema():
    """Fail fast, before any check runs, if this interpreter can't import
    jsonschema -- otherwise check_g1_schema's own ImportError handling reports
    a normal failed G1 check, indistinguishable from a real schema violation
    in the JSON report or in exit code 1. That ambiguity already caused one
    false "G1 regression" (gate run under system python3, not the venv with
    jsonschema installed) that read as a library bug and wasn't. Exit code 2
    is reserved for this: the gate did not run at all, vs. exit 1 meaning it
    ran and found the library invalid."""
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        print(
            "FATAL: jsonschema nije instaliran u ovom interpreteru. "
            "Ovo NIJE G1 fail -- validacija nije ni pokrenuta. "
            "Koristi <scratchpad>/tok-venv/bin/python (vidi RESUME.md).",
            file=sys.stderr,
        )
        sys.exit(EXIT_ENV_ERROR)


def main():
    _require_jsonschema()
    parser = argparse.ArgumentParser(description="geo-prompt-library QA gate (G1-G16)")
    parser.add_argument("library_json", help="Path to <slug>-library-vN.json")
    args = parser.parse_args()

    path = Path(args.library_json)
    lib = json.loads(path.read_text(encoding="utf-8"))
    report = validate(lib)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(EXIT_PASS if report["passed"] else EXIT_FAIL)


if __name__ == "__main__":
    main()
