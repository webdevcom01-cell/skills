---
name: geo-prompt-library
description: Generiše kvota-validiranu biblioteku kupčevih upita (30–50 intenata, SR+EN par) iz URL-a firme, vertikale i lokalea — verzionisan JSON kao ulaz za GEO/AI-search monitoring. Koristiti kad korisnik traži biblioteku upita, prompt set, query set, listu pitanja koja kupci postavljaju ChatGPT-u/Perplexity-ju/AI Overviews, promptove za praćenje brenda, pripremu za merenje vidljivosti u AI pretrazi, GEO ili AEO monitoring setup; kad samo da URL i pita šta bi ljudi pitali AI o toj firmi; ili kad već koristi alat za merenje (npr. Peec AI) pa mu treba ulazni seed set. Izlaz je samo taj zamrznuti seed set — skill ga NIKAD ne izvršava niti meri. Ne koristiti za izvršavanje upita u LLM-ovima, merenje vidljivosti ili share-of-voice, skorovanje odgovora, praćenje kroz vreme i alarme, klijentske izveštaje, pisanje SEO/GEO ili FAQ sadržaja, ni tehnički audit sajta — to su odvojeni downstream koraci.
compatibility: Zahteva WebFetch/WebSearch za istraživanje sajta firme i konkurenata, i Python 3 za bundlovane skripte (scripts/validate_library.py, scripts/orthographic_variants.py, scripts/verify_grounding.py) plus pip paket jsonschema. verify_grounding.py sam otvara HTTP konekcije (urllib, ne WebFetch tool) po jedinstvenom source_url iz izlaza — mrežni pristup van agentovog toolseta.
metadata:
  version: "0.2.0"
  status: "Merena i popravljena kroz stvaran end-to-end run (montenegrocharter.com, sr-ME, A/B v1↔v2 — vidi CHANGELOG.md). Nalazi iz A/B-a ugrađeni: Faza 4 grounding-u-glasu i registar-miks disciplina, ch/sh/th/ph digraf bug u orthographic_variants.py, same-host rate limit u verify_grounding.py. description polje ručno zategnuto i provereno protiv 20 eval upita. Svih 24 fixture-a + verify_workflow_sync.py prolaze."
  based_on: "BRIEF-geo-prompt-library.md v1.0, 2026-08-01"
---

# Geo Prompt Library

Iz URL-a firme, vertikale i lokalea generiše zamrznutu, verzionisanu, kvota-validiranu biblioteku od 30–50 kupčevih intenata (svaki u srpskoj i engleskoj varijanti = 60–100 upita) kao mašinski čitljiv JSON — ulaz za sledeći skill u GEO pipeline-u (merenje vidljivosti brenda u AI pretrazi).

Ovo nije generator teksta — to je **instrument za uzorkovanje**. Kvalitet se meri pokrivenošću i odsustvom pristrasnosti (prompt-set bias), ne lepotom upita. Zato ide tvrd, fail-closed deterministički gate na kraju, ne "model će valjda paziti".

## Pravila koja moraju preživeti skraćivanje tela

- **Anti-halucinacija:** nijedan upit ne tvrdi uslugu/proizvod/grad/segment bez citata sa `source_url` — izuzetak samo uz `"inferred": true` + `rationale`.
- **Matrica pre teksta:** `matrix_plan` ide u izlaz PRE generisanja ijednog upita.
- **Fail-closed:** gate i grounding provera nikad ne prolaze tiho — max 3 pokušaja, pa `passed: false` sa punim izveštajem.

## Zaključane odluke — ne otvaraj ponovo

- **O1 — Uparene stavke.** Svaki intent ima SR i EN verziju. 78% ne-engleskih ChatGPT sesija sadrži bar jedan podupit na engleskom (Peec AI) — biblioteka samo na srpskom sistemski meri pogrešnu populaciju.
- **O2 — Kanonski upit + `variants`.** Jedan red = jedan upit u jednom jeziku. Ortografske varijante (dijakritika/ASCII/ćirilica) su metapodatak generisan skriptom, ne model — degradacija `č`/`ć` → `c` nije invertibilna.
- **O3 — Skill sam istražuje konkurente.** Bez pravih imena, `comparison` kategorija (12–20% seta) je prazan placeholder.
- **O4 — Tvrd, fail-closed QA gate kao bundlovana Python skripta.** Prompt-set bias je #1 failure mode; instrukcija u ovom fajlu ga ne hvata pouzdano.

## Ulaz / Izlaz

| Parametar | Obavezan | Default | Napomena |
|---|---|---|---|
| `url` | da | — | URL firme, prihvatiti i goli domen |
| `locale` | da | `sr-RS` | `sr-RS`, `sr-ME`, `hr-HR`, `bs-BA`, `en-US`, `en-GB` — bira jezički transform sloj |
| `vertical` | ne | izvodi se sa sajta | ako je dat, ima prednost |
| `n_intents` | ne | `40` | opseg 30–50; ispod 30 → upozorenje o statističkoj snazi |
| `geo_scope` | ne | izvodi se | `national` \| `city` \| `multi_city` \| `global` — `global` gasi `local` kvotu na 0 |
| `competitors` | ne | istražuje se (Faza 3) | ako korisnik da listu, koristi je i ne istražuje |
| `personas` | ne | izvodi se sa sajta, do 3, sa `confidence` | korisnik ispravlja u rezimeu ako treba |
| `brand_aliases` | ne | izvodi se, uključujući transkribovanu srpsku formu | kritično za downstream parsing (npr. `Microsoft` → `Majkrosoft`) |

Izlaz — tri fajla u radnom direktorijumu:
1. `<slug>-library-v<N>.json` — glavni deliverable (šema u `references/schema.md` + `assets/library.schema.json`)
2. `<slug>-validation-v<N>.json` — izveštaj QA gate-a: stvarna distribucija, prolaz/pad po pravilu, dokazi
3. Kratak konzolni rezime korisniku (10–15 redova: broj intenata, stvarna distribucija, konkurenti, koliko `inferred`, upozorenja, broj pokušaja gate-a pre uspeha (`retry_count`, 0–3) i koja G-pravila su pala na prvi pokušaj ako ih je bilo, `verify_grounding.py` rezultat — `coverage_status` eksplicitno, ne samo "prošlo/nije prošlo") — nikad ceo JSON u chat

Bez dodatnog API troška — samo WebFetch/WebSearch i lokalna Python skripta.

## Kategorije i kvote

Kvota se popunjava ĆELIJAMA matrice `kategorija × (persona | use case | grad | konkurent)`, ne slobodnim pisanjem — slobodno generisanje "30-50 upita" pouzdano klasteruje oko onoga što model prvo pomisli, što je tačno prompt-set bias. Pune definicije, awareness stadijumi i po 3 primera svake u `references/taxonomy.md`.

| `category` | Kvota | Awareness |
|---|---|---|
| `problem_aware` | 15–22% | unaware, problem_aware |
| `category_shortlist` | 22–30% | solution_aware |
| `use_case` | 15–22% | solution_aware |
| `comparison` | 12–20% | solution/product_aware |
| `pricing` | 8–12% | product_aware |
| `local` | 5–15%, **donja granica → 0 ako `geo_scope=global`** | sve |
| `trust_risk` | 5–10% | product_aware |
| `branded` | 8–15%, **HARD CAP 15%** | product/most_aware |

**Zašto `branded` ima tvrd plafon, ne običnu kvotu:** kad ime brenda već stoji u upitu, pominjanje brenda u AI odgovoru je skoro zagarantovano — obična kvota bi i dalje dozvolila da se izmeri naduvan skor. Zato je 15% gornja granica bez tolerancije (formula ispod), ne raspon kao kod ostalih kategorija.

**Zašto `local` ima uslovnu donju granicu, ne fiksnu:** kad je `geo_scope=global`, lokalni upiti ne postoje po definiciji firme bez geografski ograničenog tržišta — pravilo je da `local` tada ide na tačno 0, ne na minimum od 5%, budžet se seli na `use_case`/`category_shortlist` (60/40, smernica modelu za Fazu 4, **ne gate pravilo** — dodavanje te raspodele kao G-pravila bi bila nova unakrsna referenca da se održava, tačno greška klase koja je ovo i uzrokovala, vidi CHANGELOG.md osma runda). Menja se SAMO donja granica za `local`; njena gornja granica i sve ostale kategorije ostaju nepromenjene.

Dodatna ograničenja: max 2–3 parafraze po intentu; nijedna persona > 40% seta; nijedan grad > 50% `local` kategorije kad je `multi_city`.

### Kvantizacija kvota (obavezna formula — inače gate uvek pada na N=30)

```
dozvoljeno[k] = [ floor(min%[k] × N) , ceil(max%[k] × N) ]   # za sve kategorije OSIM branded i local

# branded: floor na OBE strane (G4=G5 dele istu granicu), ne opšta formula —
# razlika se vidi tek kad 0.15×N nije ceo broj (N=30: ceil=5 ≠ floor=4).
# Zašto: references/research-basis.md, "QA gate kalibracija".
dozvoljeno[branded] = [ floor(0.08 × N) , floor(0.15 × N) ]

# local: donja granica pada na 0 SAMO kad je geo_scope=global — gornja granica
# ostaje ceil(0.15×N) kao i za sve ostale (0 je uvek unutar nje). Ništa drugo
# se ne menja.
dozvoljeno[local] = [ 0 ako geo_scope=global inače floor(0.05 × N) , ceil(0.15 × N) ]
```

## Workflow — 9 faza

Pre Faze 1, pročitaj `references/workflow.md` — puna mehanika (fallback-ovi, tačan format poziva skripti, tri-stanja grounding logika) je tamo. Ovo nije opciono, nego preduslov: izlazni JSON sam svedoči o svakoj fazi (`matrix_plan`, `competitors[]`, `validation.passed`, `coverage_status`), pa preskočena referenca ne prolazi neopaženo kao lošije formulisani upiti — pada na gate-u.

1. **Normalizacija ulaza**
2. **Ekstrakcija profila firme**
3. **Istraživanje konkurenata**
4. **Konstrukcija matrice**
5. **Formulisanje SR upita**
6. **EN parovi**
7. **Deterministički QA gate**
8. **Provera grounding-a**
9. **Isporuka**

## QA gate — pravila (fail-closed)

`scripts/validate_library.py <file.json>` → exit 0 (prošlo) / 1 (nevalidna biblioteka) / 2 (okruženje — npr. nedostaje `jsonschema`; gate NIJE ni pokrenut, poruka na stderr, ne meri se kao G1 pad) + JSON izveštaj sa `rule` + `detail` po proveri (čitaj izveštaj za konkretno objašnjenje pada, ne pamti napamet). Puna obrazloženja u `references/research-basis.md`.

G1 JSON Schema validnost · G2 `n_intents` u [30,50] · G3 uparenost (tačno 1 sr + 1 en po intentu) · G4 kvote po kategoriji (kvantizacija gore) · G5 branded cap (`floor`, ne `ceil`) · G6 placeholder regex · G7 near-duplicate — G7a ista kategorija: overlap koeficijent > 0.85; G7b različita kategorija: duplikat samo ako je normalizovani skup tokena identičan (grad/segment modifikator je legitimna razlika, ne duplikat) · G8 detekcija pogrešnog jezika po redu (zatvoren skup SR funkcijskih reči, ne statistička detekcija) · G9 dužina (SR 4–20 reči, EN 3–18) · G10 comparison integritet (mora sadržati ime iz `competitors[]` ili obrazac "alternativa za") · G11 geo konzistentnost (grad mora biti u `company.locations` ili istraženim konkurentskim lokacijama) · G12 grounding pokrivenost (`inferred` ≤ 25%) · G13 persona balans (≤ 40%) · G14 locale čistoća za HR/BS (stop-liste: -isati/-ovati, "da li", ekavica, srpski meseci) · G15 ortografske varijante = determinističko mapiranje · G16 `matrix_plan` (Faza 4) vs stvaran broj intenata po ćeliji `kategorija × persona × grad`.

Svaki JSON red nosi tri nezavisne ose (`awareness_stage`, `intent_type`, `micro_moment`) da pokrivenost bude proverljiva, ne subjektivna tvrdnja — pun opis u `references/schema.md`. Pokrivenost po kategoriji/personi/gradu posebno čuva `matrix_plan` (G16).

Upozorenja (ne obaraju): `n_intents < 35`, `competitors.confidence`/`company.confidence == "low"`, `local` prisutna a `geo_scope == "global"`.

**`scripts/verify_grounding.py` NIJE G-pravilo** — proverava da citati stvarno postoje na svom `source_url` (mrežni fetch), ne samo da polja postoje. Namerno van ove liste i van gate-a — vidi Fazu 8 u `references/workflow.md` za zašto i kada se pokreće.

## Šta ovaj skill NAMERNO ne radi

- Ne izvršava upite ni u jednom LLM-u, ne meri vidljivost, ne računa share of voice, ne skoruje
- Ne piše sadržaj ni preporuke za optimizaciju, ne radi tehnički SEO/GEO audit sajta
- Ne pravi klijentski izveštaj — izlaz je mašinski JSON (poseban downstream skill ako zatreba)
- Ne prati promene kroz vreme — generiše i zamrzava jednu verziju (refresh režim za v2 sa istim `intent_id`-ovima je odloženo u v1.1; šema već ima `library_version`/`frozen` da to podrži)
