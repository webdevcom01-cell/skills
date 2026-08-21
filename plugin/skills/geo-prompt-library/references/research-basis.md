# Zašto su kvote i pravila baš ovakvi

Ovaj fajl nije dekoracija — model koji razume ZAŠTO branded cap postoji (jer naduvava skor) donosi bolje granične odluke od modela koji zna samo broj 15%. Čitaj kad treba da opravdaš odluku korisniku, ili kad procenjuješ granični slučaj koji tabele u `taxonomy.md`/SKILL.md ne pokrivaju eksplicitno.

## Sadržaj

1. [Zašto ovaj skill uopšte postoji](#zašto-ovaj-skill-uopšte-postoji)
2. [Kvote — izvori kompozicije](#kvote--izvori-kompozicije)
3. [Uparivanje SR/EN — izvor O1](#uparivanje-sren--izvor-o1)
4. [Ortografske varijante — izvor O2](#ortografske-varijante--izvor-o2)
5. [Okviri (awareness_stage, intent_type, micro_moment)](#okviri)
6. [QA gate kalibracija — G4/G5, G7, G8, G16](#qa-gate-kalibracija)
7. [Princip: tri stanja, ne dva](#princip-tri-stanja-ne-dva)
8. [Eksplicitne praznine](#eksplicitne-praznine)
9. [Izvori](#izvori)

---

## Zašto ovaj skill uopšte postoji

Merenje vidljivosti brenda u ChatGPT/Perplexity/AI Overviews je smisleno samo ako je set upita reprezentativan. Industrija to i dalje radi ručno. Istraživanje je pokazalo nešto važnije od "automatizuj ručni posao": **najčešći način na koji GEO izveštaj laže je pristrasan set upita** — MaxAEO ga zove *prompt-set bias*, set nakrivljen ka onome u čemu je brend jak umesto ka onome što tržište stvarno pita. Drugi po redu failure mode je **preteška zastupljenost brendiranih upita** — kad ime brenda stoji u upitu, pominjanje je skoro zagarantovano, pa se skor naduva (odatle `branded` hard cap, sekcija 6).

Zaključak za dizajn: ovaj skill je **instrument za uzorkovanje**, ne generator teksta. Kvalitet se meri pokrivenošću i odsustvom pristrasnosti — zato fail-closed deterministički gate, ne "model će valjda paziti" (O4).

## Kvote — izvori kompozicije

| Izvor | Šta objavljuje |
|---|---|
| MaxAEO | Category shortlist 25–35%, use-case 20–30%, competitor comparison 15–25%, problem-solution 10–20%, branded accuracy 5–10%, risk/reputation 5–10%. |
| Conductor | Jedini vendor koji objavljuje branded/unbranded split: **~75/25**. 8-intent enum (osnova za taksonomiju u `taxonomy.md`). |
| DeepSmith | Awareness 50 / Consideration 30 / Decision 20 — grubi funnel-nivo sanity check za `awareness_stage` distribuciju. |
| Nightwatch, SE Ranking, Otterly | 4-tip, 5-tip, 5-tip taksonomije — unakrsno provereno protiv MaxAEO/Conductor pri spajanju u 8 kategorija. |
| Aggarwal et al. (KDD 2024, arXiv 2311.09735) | **Jedina peer-reviewed taksonomija.** GEO-bench, 10.000 upita, 80/10/10 info/trans/nav split — koristi se kao spoljna provera da `intent_type` distribucija (Broder + komercijalna) nije izmišljena. |

Kvote u SKILL.md sekciji 5 su usaglašene sa sva tri vendor izvora, sa originalnih pet ručnih kategorija (`problem-aware`, `poređenje`, `cena`, `lokalno`, `brendirano`) zadržanih kao imenovane kante unutar 8-kategorijske taksonomije.

**Ograničenje koje treba držati na umu:** većina ovih brojeva je vendor-research, ne peer-review (izuzetak: Aggarwal et al.). Ne prezentuj kvote korisniku kao naučno utvrđene — prezentuj ih kao "usaglašeno sa objavljenom industrijskom praksom", što jesu.

## Uparivanje SR/EN — izvor O1

Peec AI (10M+ promptova, 20M fan-out-ova, 5 jezika): **78% ne-engleskih ChatGPT sesija sadrži bar jedan pretraživački podupit na engleskom**; 43% svih fan-out-ova ide na engleski web; nijedan jezik ispod 60%, turski 94%. SR/HR/BS/ME imaju manji korpus od turskog → očekivano na vrhu tog raspona.

**Eksplicitno ograničenje:** Peec podaci su vendor-research, ne peer-review, i **SR nije bio u uzorku** — primena na srpsko tržište je ekstrapolacija po analogiji (mali korpus jezik → veći udeo engleskog fallback-a), ne merenje. Ne tvrdi korisniku da je 78% broj izmeren za srpski.

## Ortografske varijante — izvor O2

Krstev et al. (CLIB 2018, diacritic restoration in Serbian): degradacija dijakritike ide `š→s, ž→z, č→c, ć→c, đ→dj`. **`č` i `ć` oba kolabiraju u `c`** — transformacija nije invertibilna. Zato se varijante generišu determinističkom skriptom (`scripts/orthographic_variants.py`) kao METAPODATAK uz kanonski upit, ne kao zaseban red u `intents[]` — pokušaj da se ascii forma tretira kao nezavisan upit bi udvostručio brojanje bez nove informacije, a pokušaj da se iz ascii forme rekonstruiše originalni tekst bi bio pogrešan po definiciji (nema jedinstvenog inverza za `c`).

## Okviri

- **Awareness stadijum** — Schwartz 5 stadijuma (unaware → problem_aware → solution_aware → product_aware → most_aware), standardna marketing copywriting taksonomija.
- **Intent type** — Broder (SIGIR 2002, "A Taxonomy of Web Search") + komercijalna četvrta kategorija (`commercial_investigation`) koju sam Broder nije imao ali je postala standard u SEO/GEO praksi.
- **Micro-moment** — Google-ova "4 I-want-to" taksonomija. Ovo je osa koja tera geo (`i_want_to_go`) i task/how-to (`i_want_to_do`) upite — one koje "samo funnel stadijum" razmišljanje sistemski ispušta, jer i `unaware` i `most_aware` kupac mogu imati `i_want_to_go` potrebu.

**Zašto sve tri ose istovremeno:** bez njih je "pokrivenost" subjektivna tvrdnja. Sa njima (i sa `matrix_plan`, vidi ispod), gate može programski proveriti da nijedna planirana ćelija nije prazna.

## QA gate kalibracija

Ove četiri odluke odstupaju od bukvalnog čitanja originalnog brief-a — svaka otkrivena računski ili kroz fixture-e, ne stilski izbor. Pun kod u `scripts/validate_library.py`, puna hronologija u `CHANGELOG.md`.

**G4/G5 (branded gornja granica).** Opšta kvantizaciona formula `[floor(min%×N), ceil(max%×N)]` primenjena bukvalno na `branded` daje `ceil(0.15×N)`, što se za N=30 (`ceil=5`) razlikuje od G5-ovog `floor(0.15×N)=4`. N=40 je jedini N u {30,35,40,45,50} gde se ta dva broja poklapaju — bug je bio nevidljiv na default-u. Ispravka: `branded` ima SVOJU kompletnu formulu (`[floor(0.08×N), floor(0.15×N)]`), G4 i G5 dele istu `_branded_max()` funkciju umesto dve nezavisno tačne formule.

**G7 (near-duplicate).** Brief traži "trigram Jaccard sličnost > 0.85". Simetrični Jaccard strukturno ne može preći `len(kraći)/len(duži)` kad je jedan upit drugi plus dodata fraza (npr. isti upit + " u Srbiji") — za realne dužine to je ~0.73, uvek ispod praga. Najčešći stvaran near-dup obrazac u ovom domenu nikad ne bi okinuo gate. Zamenjeno **overlap coefficient**-om (`|A∩B|/min(|A|,|B|)`), pa dodatno **razdvojeno na G7a/G7b** jer overlap-coefficient-alone daje 1.0 za BILO KOJI podskup, uključujući legitimne različite ćelije matrice (category_shortlist upit + isti upit sa gradom u `local` — grad je RAZLOG zašto je to druga ćelija, ne duplikat).

**G8 (jezik po redu).** Statistička detekcija jezika je nepouzdana na upitima od 5–8 reči, praktično ne razlikuje sr/hr/bs, i pogrešno klasifikuje legitiman mešani kod ("najbolji project management alat za male timove" — više engleskih sadržajnih reči nego srpskih, a nesumnjivo srpska rečenica). Zamenjeno zatvorenim skupom srpskih funkcijskih reči (`da, li, je, za, u, koji, kako, šta, na, se, sa, ili`) — pouzdano nezavisno od dužine stringa i vertikalnog rečnika.

**G16 (prazne ćelije).** Prvobitno implementirano kao proxy (category↔awareness_stage konzistentnost) jer isporučeni JSON nije čuvao Faza-3 plan — bukvalno pravilo nije bilo proverivo. Ispravljeno dodavanjem `matrix_plan` bloka u šemu (vidi `schema.md`): plan se sad piše u izlaz, G16 poredi plan sa stvarnošću po ćeliji. Ovo je i revizorski trag pokrivenosti za klijenta, ne samo interna provera.

## Princip: tri stanja, ne dva

Ovaj bug se pojavio TRI puta nezavisno, sa različitim simptomom svaki put — što znači da je zajednički koren, ne slučajnost, i da važi za svaku SLEDEĆU proveru koja se doda ovom skillu, ne samo za ove tri:

1. **G16 (`matrix_plan`), pre 2. runde.** Prvobitna implementacija je proveravala samo `category`↔`awareness_stage` konzistentnost — proxy koji nije mogao da vidi da li je ćelija matrice prazna zato što nije bila planirana, ili prazna zato što je generisanje nešto tiho preskočilo. "Nema podataka o ćeliji" i "ćelija je prazna po planu" su izgledali identično. Ispravka nije bila u pravilu nego u artefaktu: `matrix_plan` se sad piše u izlaz, pa G16 ima nešto stvarno da poredi.
2. **G12 / A8 (grounding pokrivenost) vs `verify_grounding.py`.** G12 proverava da je polje `inferred`/`evidence` POPUNJENO i da je odnos ≤ 25% — to je "tvrdnja postoji", ne "tvrdnja je tačna". Model koji hoće nizak `inferred` može upisati uverljiv izmišljen citat i G12 ga pusti. `verify_grounding.py` postoji isključivo zato što "polje popunjeno" i "citat stvaran" nisu ista provera.
3. **`verify_grounding.py` `coverage_status`, 5. runda.** Prvi test je pokazao da kad SVI fetch-evi padnu (mreža, rate limit), `passed: true` — nula lažnih citata je izgledalo kao "sve čisto", a stvarno je značilo "ništa nije provereno". Popravka: `coverage_status` razdvaja `ok`/`insufficient`/`no_data`/`no_claims` — "nismo mogli da proverimo" nikad se ne prijavljuje kao ni "prošlo" ni "palo".
4. **G1 schema (`validate_library.py`), ova runda.** Kad `jsonschema` paket nije instaliran u pozvanom interpreteru, stari kod je upisivao `G1_schema: passed=False` — identično izgleda kao stvarna schema violation, isti exit kod 1. Neko ko pročita samo exit kod ili samo `checks` listu zaključi "biblioteka je nevalidna" kad je stvarno "gate se nikad nije izvršio". Popravka: `_require_jsonschema()` prijavljuje FATAL na stderr i izlazi sa **exit 2**, pre nego što bilo koji check pokrene — treće, odvojeno stanje od exit 0 (prošlo) / exit 1 (nevalidna biblioteka).

**Zajednički koren:** provera koja ume da kaže samo "prošlo" ili "palo" ne ume da kaže "nisam ni pokrenuta" — pa se treće stanje tiho stopi sa jednim od druga dva. Stapanje na stranu "prošlo" je opasnije (lažna potvrda), ali stapanje na stranu "palo" takođe šteti (trošak istrage sumnja na pogrešno mesto — kod umesto okruženja).

**Pravilo za svaku buduću proveru (novo G-pravilo, novi skript, novo polje u šemi):** mora ume da izrazi TRI stanja, ne dva — `passed` / `failed` / `did_not_run` (ili ekvivalent specifičan za taj kontekst: `unreachable`, `no_data`, `coverage_status`, exit kod rezervisan za okruženje) — i treće stanje se nikad ne sme tiho stopiti sa druga dva u jednom booleanu ili jednom exit kodu bez detalja. Ako novi kod ima samo `if passed: ... else: ...`, to je signal da nedostaje treće stanje, ne da je logika gotova.

## Eksplicitne praznine

Tri praznine treba da stoje eksplicitno svaki put kad se ova metodologija predstavlja korisniku — ne prezentuj hipotezu kao činjenicu:

1. **Ne postoji objavljena studija o padežima u srpskim AI-search upitima.** Preporuka za rečenični padež (`locale-sr.md`, sekcija 3) je obrazložena hipoteza.
2. **Ne postoji objavljena studija o jeziku kojim ljudi u regionu promptuju AI** (mešani kod preporuka u `locale-sr.md` sekcija 4 je zaključivanje iz opšteg anglosrpskog registra, ne merenje AI-prompt specifičnog ponašanja).
3. **Peec studija o engleskom fan-out-u ne pokriva nijedan ex-yu jezik** — primena na SR (O1 iznad) je ekstrapolacija.

## Izvori

**Metodologija i kvote**
- MaxAEO — [AI Visibility Sample Size](https://maxaeo.ai/blog/ai-visibility-sample-size/) · [How Many Prompts to Test AI Visibility](https://maxaeo.ai/blog/how-many-prompts-to-test-ai-visibility/)
- Conductor — [AI Prompt Tracking](https://www.conductor.com/academy/ai-prompt-tracking/)
- DeepSmith — [How Many AI Prompts to Track](https://deepsmith.ai/blog/how-many-ai-prompts-to-track)
- Profound — [How to Design Prompts for AI Visibility Tracking](https://www.tryprofound.com/blog/how-to-design-prompts-for-ai-visibility-tracking) · [AI Search Intent Study](https://www.tryprofound.com/blog/chatgpt-intent-landmark-study)
- Nightwatch — [How to Measure LLM Visibility](https://nightwatch.io/blog/how-to-measure-llm-visibility/) · SE Ranking — [How to Choose Prompts to Track](https://seranking.com/blog/how-to-choose-prompts-to-track/) · Otterly — [What Search Prompts Should You Track](https://otterly.ai/blog/prompts-tracking-research-chatgpt/)
- Aggarwal et al. — [GEO: Generative Engine Optimization, KDD 2024 (arXiv 2311.09735)](https://arxiv.org/abs/2311.09735)

**Jezik i tržište**
- Peec AI — [ChatGPT searches in English, even when you don't](https://peec.ai/blog/chatgpt-searches-in-english-even-when-you-don-t) · [20M query fan-outs, country analysis](https://peec.ai/blog/country-analysis-20-million-search-qfos)
- Krstev et al. — [Diacritic Restoration in Serbian, CLIB 2018](https://aclanthology.org/2018.clib-1.7.pdf)
- [Wikipedia — Comparison of Serbo-Croatian standard varieties](https://en.wikipedia.org/wiki/Comparison_of_Serbo-Croatian_standard_varieties)
- [Netokracija — Anglicizmi u savremenom poslovanju](https://www.netokracija.rs/anglicizmi-u-savremenom-poslovanju-201109)
- [DZS Hrvatska ZTI-2025](https://podaci.dzs.hr/2025/hr/97121) · [eCommerce Srbija / RZS IKT 2025](https://ecommserbia.org/2026/06/01/generacijske-razlike-u-koriscenju-elektronske-trgovine-uredaja-i-digitalnih-usluga)
- Weglot — [Untranslated Means Invisible](https://www.weglot.com/blog/ai-search-and-language) · Evertune — [International GEO](https://www.evertune.ai/resources/insights-on-ai/international-geo-how-to-optimize-ai-visibility-in-non-english-markets)

**Okviri**
- Broder — [A Taxonomy of Web Search, SIGIR 2002](https://sigir.org/files/forum/F2002/broder.pdf) · Schwartz 5 stadijuma preko [Serpstat](https://serpstat.com/blog/5-stages-of-awareness-in-seo-copywriting/) · [Think with Google — Micro-Moments](https://business.google.com/uk/think/marketing-strategies/how-micromoments-are-changing-rules/)
- Growth Memo — [Make your prompt tracking more accurate](https://www.growth-memo.com/p/how-to-make-prompt-tracking-much) — 2.2% citation persistence kroz 3 izvršavanja, osnova za `notes_for_downstream.recommended_runs`.
