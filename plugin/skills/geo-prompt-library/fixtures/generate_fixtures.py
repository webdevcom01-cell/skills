#!/usr/bin/env python3
"""Builds the geo-prompt-library QA gate fixtures:

- fixtures/valid_library.json           -- 40 intents, sr-RS, fictitious B2B SaaS
                                            CRM company "CloudFlow CRM". Must PASS.
- fixtures/g01..g16_*.json              -- 16 derivatives, one targeted mutation
                                            each, one per G1-G16. Must FAIL.
- fixtures/p01..p04_*.json              -- 4 near-miss derivatives that LOOK like
                                            they should fail but are legitimate.
                                            Must PASS (a gate that rejects these is
                                            more expensive in production than one
                                            that misses a real duplicate).

Not part of the shipped skill -- a dev tool for regenerating/extending the gate's
test fixtures. Run: python -B fixtures/generate_fixtures.py
"""

import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = FIXTURES_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from orthographic_variants import variants_for  # noqa: E402

COMPANY = {
    "name": "CloudFlow CRM d.o.o.",
    "aliases": ["CloudFlow", "CloudFlow CRM", "Klaudflou CRM"],
    "url": "https://cloudflow.rs",
    "vertical": "CRM softver za mala i srednja preduzeća",
    "offerings": [
        {"name": "CRM za prodajni tim", "source_url": "https://cloudflow.rs/proizvod",
         "evidence": "CRM za prodajni tim — pratite lead-ove, ponude i zatvorene poslove na jednom mestu."},
        {"name": "automatizacija marketinga", "source_url": "https://cloudflow.rs/marketing",
         "evidence": "Automatizacija marketinga — email kampanje i segmentacija kontakata bez ručnog rada."},
        {"name": "integracija sa računovodstvenim softverom", "source_url": "https://cloudflow.rs/integracije",
         "evidence": "Integracija sa računovodstvenim softverom — sinhronizujte fakture i uplate automatski."},
        {"name": "mobilna aplikacija za teren", "source_url": "https://cloudflow.rs/mobilna-app",
         "evidence": "Mobilna aplikacija za teren — unosite podatke sa terena i van kancelarije."},
        {"name": "cenovnik", "source_url": "https://cloudflow.rs/cenovnik",
         "evidence": "Cenovnik — planovi od 19 EUR po korisniku mesečno, besplatna proba 14 dana."},
    ],
    "locations": [{"city": "Beograd", "country": "RS", "source_url": "https://cloudflow.rs/kontakt"}],
    "site_language": "sr",
    "confidence": "high",
}

COMPETITORS = [
    {"name": "Pipedrive", "url": "https://pipedrive.com", "how_found": "websearch: najbolji CRM alati Srbija", "confidence": "medium"},
    {"name": "HubSpot", "url": "https://hubspot.com", "how_found": "websearch: CRM softver Srbija", "confidence": "medium"},
    {"name": "Bitrix24", "url": "https://bitrix24.com", "how_found": "websearch: CRM alternativa Bitrix24 Srbija", "confidence": "medium"},
    {"name": "Followup CRM", "url": "https://followupcrm.com", "how_found": "websearch: CloudFlow CRM alternativa", "confidence": "low"},
]

PERSONAS = [
    {"id": "p1", "label": "vlasnik male firme koji prvi put uvodi CRM", "derived_from": "site:/o-nama", "confidence": "medium"},
    {"id": "p2", "label": "sales menadžer u rastućem timu", "derived_from": "site:/proizvod", "confidence": "medium"},
    {"id": "p3", "label": "IT osoba zadužena za integracije", "derived_from": "site:/integracije", "confidence": "low"},
]

OFFERING_URL = {o["name"]: o["source_url"] for o in COMPANY["offerings"]}
PRICING_URL = OFFERING_URL["cenovnik"]

# (category, awareness_stage, intent_type, micro_moment, expected_answer_type,
#  sr_text, en_text, grounding_url_or_None, inferred)
# Order matters: valid_library.json uses this list unfiltered, in order, so
# intent_id (int-NNN) assignment is 1-indexed position in this exact list. Do not
# reorder existing rows -- several mutate_* functions below address specific
# int-NNN ids.
RAW_INTENTS = [
    ("problem_aware", "unaware", "informational", "i_want_to_know", "explanation",
     "gubim previše vremena na ručno praćenje kontakata i ponuda",
     "I keep losing track of leads and follow-ups in spreadsheets",
     None, True),
    ("problem_aware", "problem_aware", "informational", "i_want_to_do", "explanation",
     "kako da prestanem da gubim lead-ove između prodavaca",
     "how do I stop losing leads between sales reps",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("problem_aware", "problem_aware", "informational", "i_want_to_do", "explanation",
     "kako da automatizujem slanje ponuda klijentima",
     "how to automate sending quotes to clients",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("problem_aware", "problem_aware", "informational", "i_want_to_know", "explanation",
     "zašto mi se prodajni tim gubi u excel tabelama",
     "why does my sales team get lost in spreadsheets",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("problem_aware", "problem_aware", "informational", "i_want_to_know", "explanation",
     "kako da imam uvid u prodaju u realnom vremenu",
     "how can I track sales in real time",
     OFFERING_URL["integracija sa računovodstvenim softverom"], False),
    ("problem_aware", "problem_aware", "informational", "i_want_to_know", "explanation",
     "šta da radim kada mi se ponude gube u imejlovima",
     "what should I do when quotes get lost in email",
     OFFERING_URL["CRM za prodajni tim"], False),

    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "list",
     "najbolji CRM za male firme",
     "best CRM software for small businesses",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "list",
     "koji CRM je najbolji za mala preduzeća",
     "which CRM works best for small companies",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "list",
     "koji su najbolji CRM alati u Srbiji",
     "what are the top CRM tools in Serbia",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "list",
     "koji CRM softver ima najbolje ocene korisnika",
     "which CRM software has the best user ratings",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "list",
     "top CRM rešenja za srpsko tržište",
     "top CRM platforms built for the Serbian market",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "single_recommendation",
     "koji CRM preporučujete za rastuću firmu",
     "which CRM would you recommend for a growing company",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "list",
     "lista najboljih CRM programa za preduzetnike",
     "list of the best CRM programs for entrepreneurs",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "single_recommendation",
     "koji je najpopularniji CRM u regionu",
     "what is the most popular CRM in the region",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "list",
     "najbolje ocenjeni CRM sistemi za timove do 20 ljudi",
     "highest rated CRM systems for teams under 20 people",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("category_shortlist", "solution_aware", "commercial_investigation", "i_want_to_know", "list",
     "koji CRM ima najbolju podršku na srpskom jeziku",
     "which CRM offers the best support in Serbian",
     OFFERING_URL["CRM za prodajni tim"], False),

    ("use_case", "solution_aware", "commercial_investigation", "i_want_to_do", "single_recommendation",
     "najbolji CRM za prodaju nekretnina",
     "best CRM for real estate sales",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("use_case", "solution_aware", "commercial_investigation", "i_want_to_do", "single_recommendation",
     "koji CRM koristiti za timove koji rade na terenu",
     "what CRM works best for field sales teams",
     OFFERING_URL["mobilna aplikacija za teren"], False),
    ("use_case", "solution_aware", "commercial_investigation", "i_want_to_do", "explanation",
     "CRM za praćenje ponuda i ugovora u građevini",
     "CRM for tracking quotes and contracts in construction",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("use_case", "solution_aware", "commercial_investigation", "i_want_to_do", "single_recommendation",
     "najbolji alat za automatizaciju email marketinga",
     "best tool for automating email marketing campaigns",
     OFFERING_URL["automatizacija marketinga"], False),
    ("use_case", "solution_aware", "commercial_investigation", "i_want_to_do", "explanation",
     "kako izabrati CRM za mali tim od 5 ljudi",
     "how to choose a CRM for a five person team",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("use_case", "solution_aware", "commercial_investigation", "i_want_to_do", "single_recommendation",
     "CRM koji povezuje prodaju i računovodstvo",
     "CRM that connects sales and accounting",
     OFFERING_URL["integracija sa računovodstvenim softverom"], False),
    ("use_case", "solution_aware", "commercial_investigation", "i_want_to_do", "single_recommendation",
     "koji CRM ima mobilnu aplikaciju za rad na terenu",
     "which CRM has a mobile app for fieldwork",
     OFFERING_URL["mobilna aplikacija za teren"], False),
    ("use_case", "solution_aware", "commercial_investigation", "i_want_to_do", "single_recommendation",
     "najbolji CRM za agencije koje rade sa više klijenata",
     "best CRM for agencies managing multiple clients",
     OFFERING_URL["CRM za prodajni tim"], False),

    ("comparison", "solution_aware", "commercial_investigation", "i_want_to_know", "comparison_table",
     "CloudFlow CRM ili Pipedrive, šta je bolje",
     "CloudFlow CRM vs Pipedrive, which is better",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("comparison", "solution_aware", "commercial_investigation", "i_want_to_know", "comparison_table",
     "alternativa za HubSpot koja je jeftinija",
     "cheaper alternative to HubSpot",
     OFFERING_URL["cenovnik"], False),
    ("comparison", "product_aware", "commercial_investigation", "i_want_to_know", "comparison_table",
     "koja je razlika između CloudFlow CRM i Bitrix24",
     "what is the difference between CloudFlow CRM and Bitrix24",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("comparison", "product_aware", "commercial_investigation", "i_want_to_know", "comparison_table",
     "da li je bolji Followup CRM ili CloudFlow",
     "is Followup CRM better than CloudFlow",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("comparison", "solution_aware", "commercial_investigation", "i_want_to_know", "comparison_table",
     "alternativa za Bitrix24 sa jednostavnijim interfejsom",
     "simpler alternative to Bitrix24",
     OFFERING_URL["CRM za prodajni tim"], False),

    ("pricing", "product_aware", "transactional", "i_want_to_buy", "fact",
     "koliko košta CloudFlow CRM za mesec dana",
     "how much does CloudFlow CRM cost per month",
     PRICING_URL, False),
    ("pricing", "product_aware", "commercial_investigation", "i_want_to_buy", "explanation",
     "da li se isplati platiti godišnju CloudFlow pretplatu",
     "is it worth paying for an annual CloudFlow subscription",
     PRICING_URL, False),
    ("pricing", "product_aware", "transactional", "i_want_to_buy", "fact",
     "cenovnik CloudFlow CRM za tim od 10 ljudi",
     "CloudFlow CRM pricing for a ten person team",
     PRICING_URL, False),

    ("local", "product_aware", "navigational", "i_want_to_go", "fact",
     "CloudFlow CRM podrška u Beogradu",
     "CloudFlow CRM support office in Belgrade",
     COMPANY["locations"][0]["source_url"], False),
    ("local", "solution_aware", "navigational", "i_want_to_go", "fact",
     "gde se nalazi kancelarija CloudFlow CRM u Beogradu",
     "where is the CloudFlow CRM office located in Belgrade",
     COMPANY["locations"][0]["source_url"], False),
    ("local", "product_aware", "informational", "i_want_to_know", "fact",
     "da li CloudFlow CRM ima predstavnika u Beogradu",
     "does CloudFlow CRM have a representative in Belgrade",
     COMPANY["locations"][0]["source_url"], False),

    ("trust_risk", "product_aware", "informational", "i_want_to_know", "explanation",
     "kakva su iskustva korisnika sa CloudFlow CRM",
     "what are user experiences with CloudFlow CRM",
     None, True),
    ("trust_risk", "product_aware", "commercial_investigation", "i_want_to_know", "explanation",
     "da li je CloudFlow CRM pouzdan za veće timove",
     "is CloudFlow CRM reliable for larger teams",
     None, True),

    ("branded", "most_aware", "navigational", "i_want_to_go", "fact",
     "CloudFlow CRM prijava na nalog",
     "CloudFlow CRM account login page",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("branded", "product_aware", "informational", "i_want_to_do", "explanation",
     "kako da otkažem CloudFlow CRM pretplatu",
     "how do I cancel my CloudFlow CRM subscription",
     PRICING_URL, False),
    ("branded", "product_aware", "transactional", "i_want_to_buy", "fact",
     "da li CloudFlow CRM nudi besplatnu probu",
     "does CloudFlow CRM offer a free trial",
     PRICING_URL, False),
]

# Extra branded raw intents, NOT part of valid_library.json's default 40 (that set
# stays at branded=3, unchanged). Only pulled in via N30_POOL for p02/p03, which
# need up to 5 branded intents to exercise the floor-vs-ceil cap at N=30.
EXTRA_BRANDED = [
    ("branded", "most_aware", "navigational", "i_want_to_go", "fact",
     "kako zakazati CloudFlow CRM demo",
     "how to schedule a CloudFlow CRM demo",
     OFFERING_URL["CRM za prodajni tim"], False),
    ("branded", "product_aware", "informational", "i_want_to_know", "fact",
     "da li CloudFlow CRM ima API za integracije",
     "does CloudFlow CRM have an API for integrations",
     OFFERING_URL["integracija sa računovodstvenim softverom"], False),
]

N30_POOL = RAW_INTENTS + EXTRA_BRANDED

CATEGORY_QUOTA = {
    "problem_aware": (0.15, 0.22), "category_shortlist": (0.22, 0.30),
    "use_case": (0.15, 0.22), "comparison": (0.12, 0.20), "pricing": (0.08, 0.12),
    "local": (0.05, 0.15), "trust_risk": (0.05, 0.10), "branded": (0.08, 0.15),
}


def _query_row(intent_id, lang, text):
    words = text.split()
    return {
        "query_id": f"{intent_id}-{lang}",
        "lang": lang,
        "text": text,
        "script": "latin",
        "orthography": "diacritic" if lang != "en" else "n/a",
        "word_count": len(words),
        "variants": variants_for(text) if lang != "en" else {},
    }


def _matrix_plan(intents):
    cell_counts = Counter(
        (i["category"], i["persona_id"], i["geo"]["city"]) for i in intents
    )
    cells = [
        {"category": cat, "persona_id": pid, "geo_city": city, "planned": count}
        for (cat, pid, city), count in sorted(
            cell_counts.items(), key=lambda kv: (kv[0][0], kv[0][1] or "", kv[0][2] or "")
        )
    ]
    return {"planned_total": len(intents), "cells": cells}


def select_intents(raw_pool, wanted_counts):
    """Pick the first N raw intents per category from raw_pool, N = wanted_counts[cat]."""
    by_cat = {}
    for raw in raw_pool:
        by_cat.setdefault(raw[0], []).append(raw)
    selected = []
    for cat, count in wanted_counts.items():
        pool = by_cat.get(cat, [])
        if len(pool) < count:
            raise ValueError(f"not enough {cat} raw intents: need {count}, have {len(pool)}")
        selected.extend(pool[:count])
    return selected


def build_library(raw_intents, library_id):
    intents = []
    for idx, raw in enumerate(raw_intents, start=1):
        category, stage, itype, moment, answer_type, sr_text, en_text, ground_url, inferred = raw
        intent_id = f"int-{idx:03d}"
        is_local = category == "local"
        is_branded = category == "branded"
        competitors_mentioned = [
            c["name"] for c in COMPETITORS if c["name"].lower() in (sr_text + " " + en_text).lower()
        ]
        intents.append({
            "intent_id": intent_id,
            "category": category,
            "awareness_stage": stage,
            "intent_type": itype,
            "micro_moment": moment,
            "buying_stage": {"unaware": "awareness", "problem_aware": "awareness",
                              "solution_aware": "consideration", "product_aware": "consideration",
                              "most_aware": "decision"}[stage],
            "persona_id": PERSONAS[(idx - 1) % 3]["id"],
            "priority": "tier1" if idx % 4 != 0 else "tier2",
            "branded": is_branded,
            "brand_mentioned": "CloudFlow" if is_branded else None,
            "competitors_mentioned": competitors_mentioned,
            "geo": {
                "country": "RS",
                "city": "Beograd" if is_local else None,
                "scope": "city" if is_local else "national",
            },
            "expected_answer_type": answer_type,
            "rationale": f"Intent u kategoriji {category}, awareness_stage={stage}.",
            "grounding": (
                {"type": "site_page", "url": ground_url, "quote": "vidi source_url"}
                if ground_url else {"type": None, "url": None, "quote": None}
            ),
            "inferred": inferred,
            "queries": [_query_row(intent_id, "sr", sr_text), _query_row(intent_id, "en", en_text)],
        })

    n = len(intents)
    counts = {}
    for i in intents:
        counts[i["category"]] = counts.get(i["category"], 0) + 1

    lib = {
        "schema_version": "1.0.0",
        "library_id": library_id,
        "library_version": 1,
        "frozen": True,
        "content_hash": "sha256:" + hashlib.sha256(library_id.encode()).hexdigest(),
        "generated_at": "2026-08-01T12:00:00Z",
        "generator": {"skill": "geo-prompt-library", "skill_version": "0.1.0-draft"},
        "company": COMPANY,
        "competitors": COMPETITORS,
        "personas": PERSONAS,
        "locale": {"primary": "sr-RS", "script_default": "latin", "paired_language": "en"},
        "distribution": {
            "target": {k: list(v) for k, v in CATEGORY_QUOTA.items()},
            "actual": {k: round(v / n, 4) for k, v in counts.items()},
            "n_intents": n,
            "n_queries": n * 2,
        },
        "matrix_plan": _matrix_plan(intents),
        "intents": intents,
        "notes_for_downstream": {
            "freeze_policy": "Ne menjati set unutar mernog perioda.",
            "reporting": "Izveštavati n kao broj prompt-run-ova, ne broj upita.",
            "recommended_runs": "3 izvršavanja po upitu po engine-u po periodu.",
        },
    }
    return lib


def find_intent(lib, intent_id):
    return next(i for i in lib["intents"] if i["intent_id"] == intent_id)


def find_by_category(lib, category):
    return [i for i in lib["intents"] if i["category"] == category]


# --- G1-G16: must FAIL, one targeted mutation each ---

def mutate_g01_bad_schema(lib):
    lib = copy.deepcopy(lib)
    lib["frozen"] = "yes"  # should be boolean
    return lib


def mutate_g02_n_intents(lib):
    lib = copy.deepcopy(lib)
    lib["intents"] = lib["intents"][:25]
    lib["distribution"]["n_intents"] = 25
    return lib


def mutate_g03_unpaired(lib):
    """Realistic bug: both rows in queries[] end up lang='sr' (a generation pass
    wrote the SR query, then wrote a second SR paraphrase into the slot meant for
    the EN pair, instead of translating). 2 items, so schema minItems/maxItems:2
    still passes -- this isolates G3 as the check actually catching it, not G1."""
    lib = copy.deepcopy(lib)
    intent = find_intent(lib, "int-007")
    en_query = next(q for q in intent["queries"] if q["lang"] == "en")
    en_query["lang"] = "sr"
    en_query["query_id"] = "int-007-sr2"
    en_query["text"] = "najbolji CRM softver za male firme"
    en_query["orthography"] = "diacritic"
    en_query["word_count"] = len(en_query["text"].split())
    en_query["variants"] = variants_for(en_query["text"])
    return lib


def mutate_g04_bad_quota(lib):
    lib = copy.deepcopy(lib)
    for i in find_by_category(lib, "local"):
        i["category"] = "pricing"
    return lib


def mutate_g05_branded_cap(lib):
    lib = copy.deepcopy(lib)
    extra = find_by_category(lib, "category_shortlist")[:4]
    for i in extra:
        i["category"] = "branded"
        i["branded"] = True
        i["brand_mentioned"] = "CloudFlow"
    return lib


def mutate_g06_placeholder(lib):
    lib = copy.deepcopy(lib)
    q = find_intent(lib, "int-033")["queries"][0]
    q["text"] = "CloudFlow CRM podrška u [grad]"
    return lib


def mutate_g07_near_duplicate(lib):
    lib = copy.deepcopy(lib)
    # int-012 is category_shortlist, same category as int-007 -> G7a applies
    # (overlap coefficient), not G7b -- this is the should-fail pair from the
    # brief: same query + trailing city clause, no new coverage.
    q = find_intent(lib, "int-012")["queries"][0]
    q["text"] = "najbolji CRM za male firme u Srbiji"
    q["word_count"] = len(q["text"].split())
    q["variants"] = variants_for(q["text"])
    return lib


def mutate_g08_wrong_language(lib):
    lib = copy.deepcopy(lib)
    q = find_intent(lib, "int-007")["queries"][0]
    assert q["lang"] == "sr"
    q["text"] = "best CRM software for small businesses"
    q["word_count"] = len(q["text"].split())
    q["variants"] = variants_for(q["text"])
    return lib


def mutate_g09_length(lib):
    lib = copy.deepcopy(lib)
    q = find_intent(lib, "int-030")["queries"][0]
    q["text"] = "da li CRM"  # 3 words (< min 4), keeps SR function words so G8 stays
    # isolated, and isn't a trigram-substring of any other same-category query
    q["word_count"] = len(q["text"].split())
    q["variants"] = variants_for(q["text"])
    return lib


def mutate_g10_comparison_integrity(lib):
    lib = copy.deepcopy(lib)
    intent = find_intent(lib, "int-027")
    intent["queries"][0]["text"] = "koja je razlika između CloudFlow CRM i drugim sistemima"
    intent["queries"][1]["text"] = "what is the difference between CloudFlow CRM and other systems"
    for q in intent["queries"]:
        q["word_count"] = len(q["text"].split())
    intent["queries"][0]["variants"] = variants_for(intent["queries"][0]["text"])
    intent["competitors_mentioned"] = []
    return lib


def mutate_g11_geo_consistency(lib):
    lib = copy.deepcopy(lib)
    find_intent(lib, "int-033")["geo"]["city"] = "Niš"
    return lib


def mutate_g12_grounding(lib):
    lib = copy.deepcopy(lib)
    for i in lib["intents"][:11]:
        i["inferred"] = True
    return lib


def mutate_g13_persona_balance(lib):
    lib = copy.deepcopy(lib)
    for i in lib["intents"][:20]:
        i["persona_id"] = "p1"
    return lib


def mutate_g14_locale_purity(lib):
    lib = copy.deepcopy(lib)
    lib["locale"]["primary"] = "hr-HR"
    for intent in lib["intents"]:
        for q in intent["queries"]:
            if q["lang"] == "sr":
                q["lang"] = "hr"
                q["query_id"] = q["query_id"].replace("-sr", "-hr")
    return lib


def mutate_g15_orthographic_variants(lib):
    lib = copy.deepcopy(lib)
    q = find_intent(lib, "int-007")["queries"][0]
    q["variants"]["ascii"] = "pogresna vrednost koja ne odgovara mapiranju"
    return lib


def mutate_g16_matrix_consistency(lib):
    lib = copy.deepcopy(lib)
    lib["matrix_plan"]["cells"][0]["planned"] += 2
    return lib


def mutate_g18_cyrillic_variant(lib):
    """variants.ascii stays correct; only variants.cyrillic is corrupted. Before
    G15 was extended to check cyrillic too, this field was written but never
    validated -- this fixture only means something once that gap is closed."""
    lib = copy.deepcopy(lib)
    q = find_intent(lib, "int-007")["queries"][0]
    q["variants"]["cyrillic"] = "погрешна ћирилична варијанта"
    return lib


MUTATIONS = [
    ("g01_bad_schema", mutate_g01_bad_schema),
    ("g02_n_intents", mutate_g02_n_intents),
    ("g03_unpaired", mutate_g03_unpaired),
    ("g04_bad_quota", mutate_g04_bad_quota),
    ("g05_branded_cap", mutate_g05_branded_cap),
    ("g06_placeholder", mutate_g06_placeholder),
    ("g07_near_duplicate", mutate_g07_near_duplicate),
    ("g08_wrong_language", mutate_g08_wrong_language),
    ("g09_length", mutate_g09_length),
    ("g10_comparison_integrity", mutate_g10_comparison_integrity),
    ("g11_geo_consistency", mutate_g11_geo_consistency),
    ("g12_grounding", mutate_g12_grounding),
    ("g13_persona_balance", mutate_g13_persona_balance),
    ("g14_locale_purity", mutate_g14_locale_purity),
    ("g15_orthographic_variants", mutate_g15_orthographic_variants),
    ("g16_matrix_consistency", mutate_g16_matrix_consistency),
    ("g18_cyrillic_variant", mutate_g18_cyrillic_variant),
]


# --- p01-p04: near-miss, must PASS ---

def build_p01_mixed_code(valid):
    """More EN content words than SR ones, but still a grammatical SR sentence
    (via function words) -- must not trip G8."""
    lib = copy.deepcopy(valid)
    intent = find_intent(lib, "int-020")
    intent["queries"][0]["text"] = "najbolji project management alat za male timove"
    intent["queries"][1]["text"] = "best project management tool for small teams"
    for q in intent["queries"]:
        q["word_count"] = len(q["text"].split())
    intent["queries"][0]["variants"] = variants_for(intent["queries"][0]["text"])
    return lib


def build_p02_branded_floor(_valid):
    """N=30, branded=4 -> 13.3%, exactly floor(0.15*30). Must PASS G4 and G5."""
    counts = {
        "problem_aware": 4, "category_shortlist": 7, "use_case": 4, "comparison": 4,
        "pricing": 3, "local": 2, "trust_risk": 2, "branded": 4,
    }
    return build_library(select_intents(N30_POOL, counts), "cloudflow-crm-rs-2026-08-p02")


def build_p03_branded_over(_valid):
    """N=30, branded=5 -> 16.7%, one over floor(0.15*30)=4. Must FAIL G4 and G5.
    At N=40 floor(0.15*40) == ceil(0.15*40) == 6, so this off-by-one is invisible
    at the default n_intents -- only N=30 (or any N where 0.15*N isn't an integer)
    exposes it."""
    counts = {
        "problem_aware": 4, "category_shortlist": 6, "use_case": 4, "comparison": 4,
        "pricing": 3, "local": 2, "trust_risk": 2, "branded": 5,
    }
    return build_library(select_intents(N30_POOL, counts), "cloudflow-crm-rs-2026-08-p03")


def build_p04_cross_cat(valid):
    """Same core phrase as int-007 (category_shortlist) plus a city, but in a
    different category (local) -- the city IS the reason it's a separate cell.
    Must not trip G7 (would have at overlap=1.0 under the old flat rule)."""
    lib = copy.deepcopy(valid)
    intent = find_intent(lib, "int-033")
    assert intent["category"] == "local"
    intent["queries"][0]["text"] = "najbolji CRM za male firme u Beogradu"
    intent["queries"][1]["text"] = "best CRM for small businesses in Belgrade"
    for q in intent["queries"]:
        q["word_count"] = len(q["text"].split())
    intent["queries"][0]["variants"] = variants_for(intent["queries"][0]["text"])
    return lib


def build_g17_diacritic_collapse(valid):
    """Text carries both c-caron (c) and c-acute (c) at once. ascii folding maps
    BOTH to plain 'c' (O2: the fold is not invertible), so this only proves the
    generator computes the forward map and does not attempt to round-trip back to
    distinct diacritics from the ascii form -- there is no correct inverse to
    attempt. Must PASS: the forward map is well-defined even when both letters
    appear in the same query."""
    lib = copy.deepcopy(valid)
    intent = find_intent(lib, "int-002")
    intent["queries"][0]["text"] = "koliko košta praćenje za ključne prodajne prilike"
    intent["queries"][1]["text"] = "how much does tracking key sales opportunities cost"
    for q in intent["queries"]:
        q["word_count"] = len(q["text"].split())
    intent["queries"][0]["variants"] = variants_for(intent["queries"][0]["text"])
    return lib


def build_g19_digraph_transliteration(valid):
    """Text carries an unadapted English digraph loanword ('chat') in SR mixed
    code. Regression guard for the ch/sh/th/ph digraph bug in
    orthographic_variants.py: before the fix, to_cyrillic() mapped 'c' and 'h'
    letter by letter (-> 'cxat'-equivalent, wrong) instead of treating 'ch' as
    one sound (-> 'chat', correct) -- see CHANGELOG.md for the round that
    fixed it. Must PASS: proves the digraph pass produces the right cyrillic
    variant, not just that the gate runs."""
    lib = copy.deepcopy(valid)
    intent = find_intent(lib, "int-020")
    intent["queries"][0]["text"] = "koji CRM ima ugrađen chat za podršku korisnicima"
    intent["queries"][1]["text"] = "which CRM has built-in chat for customer support"
    for q in intent["queries"]:
        q["word_count"] = len(q["text"].split())
    intent["queries"][0]["variants"] = variants_for(intent["queries"][0]["text"])
    return lib


NEAR_MISSES = [
    ("g17_diacritic_collapse", build_g17_diacritic_collapse),
    ("g19_digraph_transliteration", build_g19_digraph_transliteration),
    ("p01_mixed_code", build_p01_mixed_code),
    ("p02_branded_floor", build_p02_branded_floor),
    ("p03_branded_over", build_p03_branded_over),
    ("p04_cross_cat", build_p04_cross_cat),
]


def main():
    valid = build_library(RAW_INTENTS, "cloudflow-crm-rs-2026-08")
    (FIXTURES_DIR / "valid_library.json").write_text(
        json.dumps(valid, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote valid_library.json ({len(valid['intents'])} intents)")

    for name, fn in MUTATIONS:
        broken = fn(valid)
        out_path = FIXTURES_DIR / f"{name}.json"
        out_path.write_text(json.dumps(broken, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {out_path.name}")

    for name, fn in NEAR_MISSES:
        lib = fn(valid)
        out_path = FIXTURES_DIR / f"{name}.json"
        out_path.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {out_path.name} ({len(lib['intents'])} intents)")


if __name__ == "__main__":
    main()
