# JSON šema — pun opis polja

Ovo je prozni pratilac uz `assets/library.schema.json` (JSON Schema draft 2020-12, mašinski izvor istine). Čitaj ovaj fajl kad treba objašnjenje ZAŠTO polje postoji ili primer punog oblika; čitaj `.schema.json` kad treba tačan tip/enum za validaciju.

## Sadržaj

1. [Top-level polja](#top-level-polja)
2. [`matrix_plan`](#matrix_plan)
3. [`intents[]`](#intents)
4. [`queries[]`](#queries)
5. [Enumeracije](#enumeracije)
6. [Primer 1 — lokalni servis (stomatološka ordinacija)](#primer-1--lokalni-servis-stomatološka-ordinacija)
7. [Primer 2 — B2B SaaS (CloudFlow CRM)](#primer-2--b2b-saas-cloudflow-crm)

---

## Top-level polja

| Polje | Tip | Napomena |
|---|---|---|
| `schema_version` | string `"N.N.N"` | Bump na svaku promenu šeme — downstream skill parsira po ovome, ne po nagađanju. **Piši `1.1.0`** (ne `1.0.0`) — `assets/library.schema.json` uslovno zahteva `inputs` za sve verzije OSIM `1.0.x` (`if`/`else` na `schema_version`, ne novo gate pravilo). `1.0.x` je izuzeto po verziji jer je 23 fixture-a iz pre-`inputs` ere tako tagovano; svaka nova biblioteka prolazi kroz Fazu 1/9 i uvek nosi `inputs`, pa uvek ide na `1.1.0`. Zaboravljen `inputs` na `1.1.0+` sad je G1 pad (schema violation), ne tiho `None` u gate logici. |
| `library_id` | string | Slug, npr. `acme-rs-2026-08`. |
| `library_version` | integer | `1` za prvo generisanje. Refresh režim (v1→v2 sa istim `intent_id`-ovima) je van scope-a za v0.1 — vidi CHANGELOG.md, odloženo za v1.1. Polje već postoji da to podrži bez loma šeme kasnije. |
| `frozen` | boolean | `true` čim je isporučeno — set se ne menja unutar mernog perioda (vidi `notes_for_downstream.freeze_policy`). |
| `content_hash` | string `"sha256:…"` | Hash sadržaja, za downstream integritet. |
| `generated_at` | string, ISO 8601 date-time | |
| `inputs` | object, opciono | Provenijencija ZAHTEVA (ne izvedenog rezultata) — vidi ispod. Opciono u šemi (stare biblioteke ga nemaju), ali svaka nova treba da ga piše — bez njega se zamrznuta, verzionisana biblioteka ne može kasnije audit-ovati ili re-derivovati iz istih parametara. |
| `generator.skill` / `generator.skill_version` | string | Provenijencija — koji skill i koja verzija je ovo generisala. |
| `company` | object | Vidi ispod. |
| `competitors[]` | array | Vidi ispod. |
| `personas[]` | array | Do 3, sa `confidence`. |
| `locale` | object | `{primary, script_default, paired_language}`. |
| `distribution` | object | `{target, actual, n_intents, n_queries}` — `target` su kvota RASPONI po kategoriji (iz `taxonomy.md`), `actual` je stvarna frakcija posle generisanja. |
| `matrix_plan` | object | Vidi sekciju ispod — ovo je novo u odnosu na prvi draft, dodato posle korisničke revizije. |
| `intents[]` | array | Glavni sadržaj. |
| `validation` | object, opciono | Ilustrativno u ovoj šemi; stvarni QA izveštaj ide u **poseban fajl** `<slug>-validation-vN.json` (Faza 7/8 u SKILL.md), ne u ovo polje. |
| `notes_for_downstream` | object | `freeze_policy`, `reporting`, `recommended_runs` — uputstva za skill koji ovo koristi za merenje. |

### `company`

| Polje | Napomena |
|---|---|
| `name`, `aliases[]` | `aliases` MORA uključiti transkribovanu srpsku formu stranih imena (`Microsoft` → `Majkrosoft`) — kritično za downstream parsing pominjanja brenda u AI odgovorima. |
| `url`, `vertical`, `site_language`, `confidence` | |
| `offerings[]` | `{name, source_url, evidence}` — svaka stavka MORA imati doslovni citat sa sajta (anti-halucinacijsko pravilo, Faza 2 u SKILL.md). |
| `locations[]` | `{city, country, source_url}` — koristi ga G11 (geo konzistentnost) kao izvor poznatih gradova. |

### `competitors[]`

`{name, url, how_found, confidence, city?}` — `city` je opciono, koristi se ako je konkurent istražen sa poznatom lokacijom (G11 ga uzima u obzir pored `company.locations`).

### `inputs`

`{url, locale, vertical, n_intents, geo_scope, competitors_source}` — normalizovani ulaz iz Faze 1-3 (SKILL.md "Ulaz / Izlaz"), ne izvedeni rezultat. `vertical` i `geo_scope` su `null` ako ih korisnik nije eksplicitno dao (izvedeni su umesto toga — vidi `company.vertical` i `intents[].geo.scope` za izvedene vrednosti).

**Zašto ovo postoji odvojeno od `intents[].geo.scope`:** G4 (kvote) i `build_warnings()` moraju znati da li je korisnik tražio `geo_scope=global` da bi ispravno primenili izuzetak za `local` kategoriju (donja granica pada na 0). Čitanje scope-a sa prvog intenta je fragilno — kod `multi_city` biblioteka različiti intenti legitimno imaju različit `geo.scope`, pa "prvi intent" nije pouzdan izvor za "šta je korisnik tražio za celu biblioteku". `inputs.geo_scope` je jedan zapis po biblioteci, ne nagađanje iz podskupa redova (otkriveno kao rupa u proveniјenciji, ne kao zahtev za novo gate pravilo — vidi CHANGELOG.md deveta runda).

---

## `matrix_plan`

Dodato posle prve revizije korisnika (vidi CHANGELOG.md, treća runda) — zamena za proxy proveru koja je pogađala pokrivenost iz `awareness_stage` polja. Sad je plan iz Faze 3 (SKILL.md) eksplicitan artefakt u izlazu, ne samo korak u radnoj memoriji.

```json
"matrix_plan": {
  "planned_total": 40,
  "cells": [
    { "category": "branded", "persona_id": "p1", "geo_city": null, "planned": 1 }
  ]
}
```

Ćelija = `(category, persona_id, geo_city)`. `geo_city` je `null` za sve kategorije osim `local` (gde nosi grad). G16 gate poredi `planned` po ćeliji sa stvarnim brojem intenata u toj ćeliji — bilo koji nesklad (previše, premalo, ili ćelija koja postoji u stvarnosti a nije u planu) obara gate. Ovo je i revizorski trag pokrivenosti za klijenta, ne samo interna provera.

---

## `intents[]`

| Polje | Napomena |
|---|---|
| `intent_id` | `int-NNN`, sekvencijalno. |
| `category` | Jedna od 8 — vidi `taxonomy.md`. |
| `awareness_stage` | Schwartz 5 stadijuma. Mora biti u dozvoljenom skupu za `category` (vidi tabelu u `taxonomy.md` po kategoriji). |
| `intent_type` | Broder taksonomija + komercijalna 4. |
| `micro_moment` | Google micro-moments — osa koja tera geo (`i_want_to_go`) i task (`i_want_to_do`) upite. |
| `buying_stage` | Slobodan tekst (`awareness`/`consideration`/`decision`), izveden iz `awareness_stage`. |
| `persona_id` | Referenca na `personas[].id`, ili `null`. Deo `matrix_plan` ključa ćelije. |
| `priority` | `tier1` \| `tier2`. |
| `branded`, `brand_mentioned` | `branded: true` samo za `category == "branded"`. |
| `competitors_mentioned[]` | Imena iz `competitors[]` koja se pojavljuju u tekstu upita — koristi ga G10. |
| `geo` | `{country, city, scope}`. `city` je deo `matrix_plan` ključa ćelije — mora se poklapati sa `company.locations` ili istraženim konkurentskim lokacijama (G11). |
| `expected_answer_type` | `list` \| `single_recommendation` \| `explanation` \| `comparison_table` \| `fact`. |
| `rationale` | Zašto ovaj intent postoji — objašnjenje, ne samo oznaka. |
| `grounding` | `{type, url, quote}` — sve `null` ako `inferred: true`. |
| `inferred` | `true` ako nema doslovnog citata sa sajta (Faza 2 anti-halucinacijsko pravilo). Udeo preko cele biblioteke ≤ 25% (G12). |
| `queries[]` | Tačno 2 — jedan lokalni jezik, jedan `en` (G3). |

---

## `queries[]`

| Polje | Napomena |
|---|---|
| `query_id` | `{intent_id}-{lang}`. |
| `lang` | Dvoslovni kod (`sr`, `hr`, `en`, ...). |
| `text` | Finalni tekst. Nikad placeholder (G6), 4–20 reči lokalni / 3–18 EN (G9). |
| `script` | `latin` \| `cyrillic` — trenutno se generiše samo `latin` primarno, ćirilica ide kroz `variants`. |
| `orthography` | `diacritic` za lokalne redove, `n/a` za `en`. |
| `word_count` | `len(text.split())` — mora se slagati sa stvarnim tekstom (skript ga preračunava, ne veruje polju slepo). |
| `variants.ascii` | Determinističko mapiranje `š→s, ž→z, č→c, ć→c, đ→dj` (`scripts/orthographic_variants.py`). Nije invertibilno — `č` i `ć` oba kolabiraju u `c`. Prazno `{}` za `en` redove. |
| `variants.cyrillic` | Deterministička Latinica→ćirilica transliteracija. Obe varijante proverava G15 (prošireno u trećoj reviziji — ranije je proveravao samo `ascii`). |

---

## Enumeracije

| Polje | Vrednosti |
|---|---|
| `category` | `problem_aware`, `category_shortlist`, `use_case`, `comparison`, `pricing`, `local`, `trust_risk`, `branded` |
| `awareness_stage` | `unaware`, `problem_aware`, `solution_aware`, `product_aware`, `most_aware` |
| `intent_type` | `informational`, `navigational`, `commercial_investigation`, `transactional` |
| `micro_moment` | `i_want_to_know`, `i_want_to_go`, `i_want_to_do`, `i_want_to_buy` |
| `expected_answer_type` | `list`, `single_recommendation`, `explanation`, `comparison_table`, `fact` |
| `priority` | `tier1`, `tier2` |
| `confidence` | `high`, `medium`, `low` |

---

## Primer 1 — lokalni servis (stomatološka ordinacija)

Skraćen na jedan intent radi čitljivosti — pun fajl ima 30–50.

```json
{
  "schema_version": "1.1.0",
  "library_id": "acme-rs-2026-08",
  "library_version": 1,
  "frozen": true,
  "content_hash": "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7a",
  "generated_at": "2026-08-01T12:00:00Z",
  "inputs": {
    "url": "https://acme.rs",
    "locale": "sr-RS",
    "vertical": "stomatološke ordinacije",
    "n_intents": 40,
    "geo_scope": null,
    "competitors_source": "researched"
  },
  "generator": { "skill": "geo-prompt-library", "skill_version": "0.1.0-draft" },
  "company": {
    "name": "Acme d.o.o.",
    "aliases": ["Acme", "Acme Srbija", "Akme"],
    "url": "https://acme.rs",
    "vertical": "stomatološke ordinacije",
    "offerings": [
      { "name": "implantologija", "source_url": "https://acme.rs/usluge", "evidence": "Implantologija — ugradnja zubnih implanata uz garanciju." }
    ],
    "locations": [{ "city": "Novi Sad", "country": "RS", "source_url": "https://acme.rs/kontakt" }],
    "site_language": "sr",
    "confidence": "high"
  },
  "competitors": [
    { "name": "Beta Dental", "url": "https://beta.rs", "how_found": "websearch:najbolje stomatološke ordinacije Novi Sad", "confidence": "medium" }
  ],
  "personas": [{ "id": "p1", "label": "roditelj koji traži ordinaciju za dete", "derived_from": "site:/o-nama" }],
  "locale": { "primary": "sr-RS", "script_default": "latin", "paired_language": "en" },
  "distribution": { "n_intents": 40, "n_queries": 80, "target": {}, "actual": {} },
  "matrix_plan": {
    "planned_total": 40,
    "cells": [
      { "category": "category_shortlist", "persona_id": "p1", "geo_city": null, "planned": 1 },
      { "category": "local", "persona_id": "p1", "geo_city": "Novi Sad", "planned": 1 }
    ]
  },
  "intents": [
    {
      "intent_id": "int-001",
      "category": "local",
      "awareness_stage": "solution_aware",
      "intent_type": "commercial_investigation",
      "micro_moment": "i_want_to_go",
      "buying_stage": "consideration",
      "persona_id": "p1",
      "priority": "tier1",
      "branded": false,
      "brand_mentioned": null,
      "competitors_mentioned": [],
      "geo": { "country": "RS", "city": "Novi Sad", "scope": "city" },
      "expected_answer_type": "list",
      "rationale": "Kupac koji zna da mu treba implantologija ali ne zna kome da ode u svom gradu.",
      "grounding": { "type": "site_page", "url": "https://acme.rs/usluge", "quote": "Implantologija — ugradnja zubnih implanata" },
      "inferred": false,
      "queries": [
        {
          "query_id": "int-001-sr", "lang": "sr", "text": "koja je najbolja ordinacija za implantologiju u Novom Sadu",
          "script": "latin", "orthography": "diacritic", "word_count": 8,
          "variants": { "ascii": "koja je najbolja ordinacija za implantologiju u Novom Sadu", "cyrillic": "која је најбоља ординација за имплантологију у Новом Саду" }
        },
        {
          "query_id": "int-001-en", "lang": "en", "text": "best dental implant clinic in Novi Sad Serbia",
          "script": "latin", "orthography": "n/a", "word_count": 7, "variants": {}
        }
      ]
    }
  ],
  "notes_for_downstream": {
    "freeze_policy": "Ne menjati set unutar mernog perioda.",
    "reporting": "Izveštavati n kao broj prompt-run-ova, ne broj upita.",
    "recommended_runs": "3 izvršavanja po upitu po engine-u po periodu."
  }
}
```

Uporedi sa `int-007` u primeru 2 ispod: "koja je najbolja ordinacija za implantologiju **u Novom Sadu**" (kategorija `local`, grad je strukturni deo) vs "najbolji CRM za male firme" (kategorija `category_shortlist`, nema grad). Ovo je tačno G7b slučaj iz SKILL.md — dva upita mogu deliti većinu reči ako ih kategorija legitimno razlikuje.

## Primer 2 — B2B SaaS (CloudFlow CRM)

Ovo je stvaran intent iz `fixtures/valid_library.json` (koji prolazi ceo gate) — ne ručno pisan primer, nego izvučen iz fajla koji `scripts/validate_library.py` stvarno validira. Koristi ga kao referencu za tačan oblik, ne samo ilustraciju.

```json
{
  "intent_id": "int-007",
  "category": "category_shortlist",
  "awareness_stage": "solution_aware",
  "intent_type": "commercial_investigation",
  "micro_moment": "i_want_to_know",
  "buying_stage": "consideration",
  "persona_id": "p1",
  "priority": "tier1",
  "branded": false,
  "brand_mentioned": null,
  "competitors_mentioned": [],
  "geo": { "country": "RS", "city": null, "scope": "national" },
  "expected_answer_type": "list",
  "rationale": "Intent u kategoriji category_shortlist, awareness_stage=solution_aware.",
  "grounding": { "type": "site_page", "url": "https://cloudflow.rs/proizvod", "quote": "vidi source_url" },
  "inferred": false,
  "queries": [
    {
      "query_id": "int-007-sr", "lang": "sr", "text": "najbolji CRM za male firme",
      "script": "latin", "orthography": "diacritic", "word_count": 5,
      "variants": { "ascii": "najbolji CRM za male firme", "cyrillic": "најбољи ЦРМ за мале фирме" }
    },
    {
      "query_id": "int-007-en", "lang": "en", "text": "best CRM software for small businesses",
      "script": "latin", "orthography": "n/a", "word_count": 6, "variants": {}
    }
  ]
}
```

Pun fajl (`fixtures/valid_library.json`, 40 intenata) i sva 22 fixture-a (should-pass i should-fail) su najpouzdaniji izvor "šta stvaran izlaz izgleda" — čitaj ih direktno ako primeri ovde nisu dovoljni.
