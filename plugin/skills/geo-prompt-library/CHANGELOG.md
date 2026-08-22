## [0.2.0] — 2026-08-22 (formalizacija verzije, bez zabeleženog delta-a)

- **Verzija u `SKILL.md` frontmatteru (`0.2.0`) do sada nije imala odgovarajući unos ovde.** Svih
  četrnaest prethodnih rundi zabeleženo je pod oznakom `[0.1.0-draft]`, dok `git log` pokazuje da je
  `version: "0.2.0"` postojao već u prvom commit-u ovog repoa (`f794eaa`) — nema zapisa o tome šta se
  promenilo pri prelasku sa `0.1.0-draft` na `0.2.0`. Ovaj unos postoji da bi frontmatter i vrh
  CHANGELOG-a bili usklađeni, i **ne tvrdi da je ovog datuma promenjeno išta u sadržaju skilla**.
  Sadržaj koji `0.2.0` obuhvata su runde zabeležene ispod.
- **Dodat `scripts/requirements.txt`** (`jsonschema>=4.0`). Zavisnost je do sada postojala samo kao
  proza u `compatibility:` opisu, iako je `validate_library.py` bez nje fail-closed — `_require_jsonschema()`
  izlazi sa kodom 2 ("gate nije ni pokrenut"), što je namerno različito od izlaza 1 (biblioteka nevalidna).

## [0.1.0-draft] — 2026-08-02, četrnaesta runda (description tightening — ručno, ne kroz automatski loop)

- **Automatski description-optimization loop (skill-creator-pro) pokrenut i odustao — pravi bug, ne šum.** Dva pokušaja (10 workera/30s timeout, pa 4 workera/90s timeout) su gotovo svi `claude -p` pozivi timeout-ovali. Dijagnoza: podprocesi su bili živi minutima ali sa skoro 0% CPU — blokirani, ne spori. Root cause potvrđen izolovano: `skill-creator-pro/scripts/run_eval.py`'s `subprocess.Popen()` nije postavljao `stdin=`, pa nasleđuje stdin OVE sesije — kad je `run_eval.py` pozvan iz VEĆ aktivne Claude Code sesije (nested `claude -p`), taj fd nije TTY sa kog dete bezbedno može da čita, pa blokira čekajući ulaz koji nikad ne stiže. Popravljeno (`stdin=subprocess.DEVNULL`) i potvrđeno: identičan poziv koji je ranije visio sad završava za 4.3s. **Ovo je popravka u skill-creator-pro (odvojen alat, van ovog skill bundla)** — pomenuto ovde samo zato što objašnjava zašto ovaj krug NIJE koristio izmereni loop.
- **`SKILL.md` `description` polje ručno zategnuto**, pošto je automatski loop bio neupotrebljiv. Prvi predlog (moj) je bio 1236/1024 znakova — quick_validate bi ga odbio. Korisnikova finalna verzija: **894/1024 znakova**, potvrđeno `len()`. Uklonjen blok "Isto i na srpskom — ..." — bio je čist ostatak iz prvog nacrta (opis zamišljen na engleskom sa SR trigerima nakalemljenim na kraju); pošto je ceo opis sad na srpskom, taj blok je dupli rio prvu trigger rečenicu (~180 znakova viška bez nove pokrivenosti).
- **Tri konkretna gapa zatvorena** (nađena ručnim pregledom 20 eval upita — 10 should-trigger/10 should-not-trigger, hand-authored, ne izmereno): `klijentske izveštaje`, `praćenje kroz vreme i alarme`, `FAQ ... sadržaja` nisu bili u `description` isključenju iako ih SKILL.md telo već zabranjuje ("Šta ovaj skill NAMERNO ne radi") — sad eksplicitni u trigger poljima. Dodata i oštrija granica trigger/exclude: "Izlaz je samo taj zamrznuti seed set — skill ga NIKAD ne izvršava niti meri" (ranije: "priprema ZA merenje vidljivosti" nasuprot "merenje vidljivosti" delili su skoro isti rečnik).
- **Ručna re-provera svih 20 eval upita posle izmene:** 9/10 should-trigger i dalje čvrsto pokriveno (1 — "prompt set za AI vidljivost za klijenta" — izgubilo tačnu kolokvijalnu frazu iz uklonjenog bloka, oba pojma i dalje prisutna odvojeno, nije rupa nego tanja redundansa); 10/10 should-not-trigger i dalje ispravno isključeno (3 konkretno popravljena, 1 dodatno pojačano). Nije izmereni skor — automatski loop nikad nije proizveo stvaran rezultat zbog gore opisanog buga.
- **SKILL.md telo NEDIRANO ovog kruga** — samo frontmatter `description` menjan. 3335/5000 tokena (cl100k_base proxy), 108 linija.
- Svih 24 fixture-a + `verify_workflow_sync.py` i dalje prolaze.

## [0.1.0-draft] — 2026-08-01, trinaesta runda (dva nalaza iz korisnikovog A/B-a: 40/60 nije kvota, rate limit u verify_grounding.py)

Korisnik je sam izmerio v1↔v2 A/B (enciklopedijski obrazac 5/40→0/40, digraf 29→0, raspon dužine 7-13→4-15 uz isti prosek, citat-eho nestao) i našao dva sitna, odvojena nalaza:

- **"Odnos 40/60 je orijentir, NE kvota" dodato u `references/workflow.md` Faza 4 (Registar sekcija).** Nalaz: int-036/int-038 su u v1 već bili dobri, a v2 ih je produžio bez dobitka ("bez iskusnog skipera" → "bez iskusnog skipera na brodu", "kako da rezervišem" → "kako mogu da rezervišem") — kad model cilja tačan 40/60 split (16/24 = tačno pogođeno u v2), konvertuje i ono što nije trebalo dirati da bi izašao na tačan broj. Pravilo sad eksplicitno kaže da nesrazmera (npr. 15/25 umesto 16/24) je jeftinija od naduvane rečenice. **Ne primenjeno retroaktivno** — korisnik je eksplicitno rekao da se ne regeneriše v3 zbog ovoga, važi za sledeći run.
- **Same-host rate limit delay + logovanje u `scripts/verify_grounding.py`.** Nalaz: coverage je pao sa 27/50 (v1) na 5/50 (v2) na IDENTIČNOM sajtu (montenegrocharter.com) između dva runa istog dana — brzi sekvencijalni zahtevi ka istom hostu izgleda okidaju nešto na njihovoj strani (greške dolaze kao SSL handshake timeout, ne čist 429, pa je ovo courtesy pacing, ne 429-triggered backoff). Dodato: `SAME_HOST_DELAY_SECONDS = 0.75` (sredina korisnikovog opsega 0.5-1s) — minimalna pauza između uzastopnih zahteva ka ISTOM hostu (grupisano po `urlparse(url).netloc`, ne blanket pauza za sve zahteve). Dodato: `_is_rate_limit_like()` heuristika (timeout/429/"too many requests" u poruci greške) koja NE menja klasifikaciju verified/not_found/unreachable (i dalje tri stanja, ne dva) — samo dodaje vidljivost. Novo polje `urls_rate_limited` u JSON izveštaju + `warnings[]` unos + stderr log linija tokom rada (JSON na stdout ostaje čist za downstream parsing, log ide na stderr). Testirano: `fixtures/grounding_live_dentio.json` i dalje prolazi čisto (`urls_rate_limited: 0`, 3/3 verified) — izmena je aditivna, ne menja postojeće ponašanje kad nema rate limita.
- Svih 24 fixture-a (`fixtures/verify_fixtures.py`) i sync provera (`fixtures/verify_workflow_sync.py`) i dalje prolaze.
- **Van dometa i ovog kruga:** gate (`validate_library.py`), šema, kategorijske kvote — nijedno nije dirano. v3 montenegrocharter regeneracija namerno PRESKOČENA po korisnikovom zahtevu.

## [0.1.0-draft] — 2026-08-01, dvanaesta runda (Faza 4: grounding-u-glasu fix + registar miks, ch/sh/th/ph digraf bug)

Pokrenuto korisnikovim pregledom stvarnog izlaza (`montenegrocharter-me-library-v1.json`, prvi stvaran end-to-end run na charter/nautičkoj vertikali) — dve odvojene, ponovljene greške pronađene u samom sadržaju, ne u gate logici:

- **Faza 4 razdvojena na 4a (slepo pisanje) / 4b (provera dopustivosti prema dokazu), `references/workflow.md`.** Dijagnoza: svaki loš upit iz v1 nosio je otisak svog izvornog citata — "Situated next to the old town of Budva" → "...u Budvi blizu starog grada"; CEO/o-nama stranica → "ko je vlasnik ili direktor"; hrvatska destinacijska stranica → "...preko crnogorskog chartera". G12 (anti-halucinacija) je bio čist — model nije izmišljao činjenice — ali je citat i dalje oblikovao SAMU REČENICU upita, ne samo njenu dopustivost. Koren: čitanje citata PRE pisanja teksta. Faza 4 sad eksplicitno traži 4a (upit napisan sa samo `category`/`persona`/`awareness_stage`/`grad`, dokaz fizički nije u kontekstu pisanja) pa TEK ONDA 4b (provera protiv `company.offerings[]` iz Faze 2 — revizija ili `inferred:true`). Obrazloženje ZAŠTO je redosled nosiv, ne kozmetički, upisano direktno u `workflow.md`, ne samo pravilo. **Napomena o ispravci:** korisnikov zahtev je referencirao "evidence iz Faze 1" — u ovom bundlu Faza 1 drži samo normalizaciju ulaza (`n_intents`/`locale`/...), dokaz sa citatima živi u Fazi 2 ("Ekstrakcija profila firme", evidence-first WebFetch). Referenca u novom tekstu ispravljena na Fazu 2 — inače bi uputstvo pokazivalo na fazu koja nema šta da isporuči.
- **Registar miks (~40% kratko-pretraživački / ~60% razgovorno-sebičan) + zabranjen enciklopedijski registar**, dodato u istu sekciju Faze 4. Tabela od 7 stvarnih loših primera iz v1 nasuprot ljudskom obliku ("koje su najbolje kompanije za X u Y" nasuprot "najbolji X Y") upisana doslovno (dijakritika vraćena radi konzistentnosti sa ostatkom fajla — sav ostali sadržaj/registar u tabeli nepromenjen u odnosu na korisnikov zahtev).
- **Digraf bug u `scripts/orthographic_variants.py` (`to_cyrillic`).** Latin→ćirilica prolaz je već imao digraf mapu za izvorne srpske digrafe (`lj`, `nj`, `dž`) PRE slovo-po-slovo prolaza, ali ne i za neprilagođene strane digrafe iz žargona — `ch`, `sh`, `th`, `ph`. Rezultat: "charter" (nautički žargon, vertikala GA TAKO ZOVE, ne "iznajmljivanje") transliterisan slovo-po-slovo u "цхартер" umesto ispravnog "чартер" — pogodilo 29/40 SR redova u v1. Dodato u `_DIGRAPHS`: `ch→ч, sh→ш, th→т, ph→ф` (ista mehanika, ista pravila case-a kao postojeći lj/nj/dž unosi), PRE slovo-po-slovo prolaza. Testirano direktno: `charter→чартер`, `Charter→Чартер`, `CHARTER→ЧАРТЕР`, `shopping→шоппинг`, `thriler→трилер`, `photo→фото`, uz potvrdu da native digrafi (`džbunast`, `ljubav`, `njemu`) ostaju nepromenjeni.
- **Novi fixture `g19_digraph_transliteration.json`** (must PASS, isti obrazac kao `g17_diacritic_collapse.json`) — `int-020` tekst nosi neprilagođenu englesku pozajmljenicu "chat" (SR mešani kod, `locale-sr.md` sekcija 4), dokazuje da `variants.cyrillic` sad ispravno daje "чат". Registrovan u `fixtures/expectations.json`. Nijedan od postojećih 23 fixture-a ne sadrži `ch`/`sh`/`th`/`ph` (provereno regex-om pre izmene) — popravka je izolovana, svih 24 fixture-a (`fixtures/generate_fixtures.py` → `fixtures/verify_fixtures.py`) prolazi bez promene ijednog postojećeg očekivanja.
- **Van dometa ovog kruga, eksplicitno:** gate (`validate_library.py`), šema, kategorijske kvote — nijedno nije dirano.

**Regeneracija — `montenegrocharter-me-library-v2.json`.** Isti ulazi kao v1 (`sr-ME`, "charter jahti i plovila", `multi_city`, `n=40`); `company`/`competitors[]`/`personas`/`matrix_plan`/`distribution.target` iz v1 ponovo iskorišćeni BEZ IZMENE (potvrđeno programski: identični), da jedina varijabla u A/B-u bude nova Faza 4/5/6. Rezultat:

- `validation.passed: true`, `retry_count: 0`, `first_attempt_failures: []` — prošlo iz prve, svih 16 pravila.
- `inferred_ratio: 6/40 = 15.0%` (int-010, 014, 018, 019, 035, 037) — pod G12 plafonom od 25%, identičan broj kao v1 (druga raspodela po intentu, isti ukupan procenat).
- Grounding (`verify_grounding.py`): `coverage_status: "ok"`, `coverage: 1.0`, `claims_not_found: 0` — ali `claims_verified: 5/50`, `unreachable: 45` (sajt je u ovom pokušaju agresivnije rate-limitovao/timeout-ovao nego pri v1 runu, koji je dobio 27/50) — nula lažnih citata potvrđeno, ali pokrivenost je tanka, ne kriti to iza `passed: true`.
- **Registar miks stvarno postignut:** 16/40 (40%) kratko-pretraživački, 24/40 (60%) razgovorno-sebičan — tačan ciljani split, ručno klasifikovano nad svih 40 SR upita (`montenegrocharter-me-validation-v2.json` ne nosi ovo polje, izveštaj je u odgovoru agenta koji je run izvršio).
- **Nijedan loš obrazac iz v1 tabele nije preživeo** u spot-proveri: nula pojava "provajder"/"najpouzdaniji"/"najbolje kompanije za" (regex provera nad svih 40 SR redova), citat-echo primeri (Budva "blizu starog grada", Dubrovnik "preko crnogorskog chartera", CEO/vlasnik formulacija) prepisani nezavisno, kraći i lični.
- Digraf fix potvrđen u stvarnom izlazu: `variants.cyrillic` za sve upite koji sadrže "charter"/"chartera"/"Chartera" sad ispravno daje "чартер"/"чартера"/"Чартера" (ranije bi bilo "цхартер").

## [0.1.0-draft] — 2026-08-01, jedanaesta runda (schema_version rešava G4 "treće stanje", G8 canary red)

- **`inputs` odsutnost prestaje da bude tiha.** Prethodna runda je ostavila G4 da nedostatak `inputs`/`inputs.geo_scope` tiho tretira kao "nije global" — tačno "tri stanja, ne dva" problem primenjen na sopstvenu popravku (global / nije global / NE ZNAM, poslednja dva nerazlučiva). Rešeno kroz VERZIONISANJE koje šema već ima, bez novog gate pravila: `assets/library.schema.json` dobija root-level `if`/`else` — `schema_version` koji NE odgovara `^1\.0\.\d+$` (tj. `1.1.0` i dalje) sad zahteva `inputs`; `inputs` sam po sebi (kad postoji, na bilo kojoj verziji) zahteva sva svoja polja. Biblioteka koja tvrdi `1.1.0+` a nema `inputs` sad je G1 pad (schema violation), glasno, ne tih `None` u G4 logici. `1.0.x` ostaje izuzeto PO VERZIJI (23 fixture-a, svi `1.0.0`, netaknuta) — ne po tome što se `inputs` slučajno ne pojavljuje. Testirano eksplicitno: fixture sa `schema_version:"1.1.0"` i bez `inputs` → G1 pada sa `"'inputs' is a required property"`.
- **Sve 4 postojeće biblioteke iz iteracije 1 bump-ovane na `1.1.0`** (sad imaju kompletan `inputs`, pa ispunjavaju ugovor te verzije) — `content_hash` ponovo izračunat (verzija je deo sadržaja), `validation-v1.json` ponovo generisan za sve 4, i dalje `passed: true`. `references/schema.md` (novi red u tabeli + Primer 1 ažuriran na `1.1.0` + `inputs`) i `references/workflow.md` Faza 9 (eksplicitno: piši `1.1.0`, ne `1.0.0`) ažurirani. `benchmark.json`/`review.html` regenerisani još jednom (četvrti put ovog kruga) da static viewer odražava finalno stanje — bez ijednog novog agent poziva.
- **G8 canary red.** `fixtures/valid_library.json`'s `int-001-en` prepisan u "should I hire a consultant to do this for me, or is it on my own, no rush" (18 reči, unutar G9 EN granice 3-18) — sadrži SVIH 6 imenovanih mina (`i/a/to/on/me/no`) plus `do`, u jednoj prirodnoj EN rečenici. Komentar iznad `SR_FUNCTION_WORDS` sad upućuje na ovaj red. Ako neko doda bilo koju od tih reči u listu bez provere, ovaj "must-pass" fixture pada na sledećem `verify_fixtures.py` — mehanička ograda, ne oslanjanje na to da se neko seti da proveri ručno.
- Svih 23 fixture-a + `verify_workflow_sync.py` i dalje prolaze. SKILL.md telo nepromenjeno ovim krugom: 3336/5000 (67%).

**Iteracija 2 i dalje NIJE pokrenuta.** Korisnik čita `review.html` — nema daljih izmena dok se ne javi.

## [0.1.0-draft] — 2026-08-01, deseta runda (inputs provenijencija, G8 mine-dokumentacija, retry_count tooling_affected)

- **`inputs` blok u šemi (provenijencija zahteva).** `assets/library.schema.json` dobija opciono `inputs: {url, locale, vertical, n_intents, geo_scope, competitors_source}` (opciono namerno — 23 postojeća fixture-a ne diraju se, nijedan ne testira `geo_scope=global`). G4 i `build_warnings()` sad čitaju `inputs.geo_scope`, NE `intents[0].geo.scope` — potonje je fragilno jer kod `multi_city` različiti intenti legitimno imaju različit `geo.scope`; "prvi intent" nije pouzdan izvor za "šta je korisnik tražio za CELU biblioteku". Ovo NIJE novo gate pravilo (nema G17) — rupa u provenijenciji, ne u validaciji. `references/schema.md` i `references/workflow.md` (Faza 1 hvata, Faza 9 piše — PRE `content_hash`, ne posle, inače je hash pogrešan čim se `inputs` doda) ažurirani.
- **Backfill 4 postojeće biblioteke iz iteracije 1** (`inputs` vrednosti rekonstruisane iz `evals.json` prompt teksta — eksplicitno dato vs. izvedeno pažljivo razdvojeno, npr. "nacionalni domet" u eval 1 NIJE tretiran kao formalni `geo_scope` override, isto kao "uglavnom lokalni klijenti" u eval 0). `content_hash` ponovo izračunat za sva 4 (dodavanje `inputs` menja sadržaj, stari hash bi bio pogrešan) i `validation-v1.json` ponovo generisan — sva 4 i dalje `passed: true`, gate sad čita `inputs.geo_scope` umesto stare fragilne putanje.
- **G8 dokumentacija budućih mina.** Komentar iznad `SR_FUNCTION_WORDS` sad imenuje `i/a/to/on/me/no/sam` kao poznate SR funkcijske reči koje NE treba dodavati bez provere protiv EN redova — sve su i uobičajene engleske reči, `i`/`a` najopasnije (kolidiraju sa "I" i "a"). `do` iz prošle runde ostaje isključen (razlog već dokumentovan).
- **`blocked_by_tooling` prošireno na `retry_count`.** `eval-4-global-saas-no-local/with_skill/grading.json` dobija `execution_metrics.retry_count=3` + `retry_count_tooling_affected: true`, plus zapis u `user_notes_summary.needs_review` (isti razlog kao A4 — sve 3 pokušaja pale na IDENTIČNOM G4 bug-u, sadržaj se nije menjao između pokušaja). Ova beleška je izvučena u `benchmark.json`-ov `runs[].notes` preko postojećeg `aggregate_benchmark.py` mehanizma (`user_notes_summary.needs_review` → `notes`), vidljiva u revieweru. `benchmark.json`/`benchmark.md`/`review.html` regenerisani treći put ovog kruga — bez ijednog novog agent poziva.
- Svih 23 fixture-a + `verify_workflow_sync.py` i dalje prolaze. SKILL.md telo: 3336/5000 tokena (67%), nepromenjeno ovim krugom (dirane su samo reference i workspace fajlovi).

**Iteracija 2 i dalje NIJE pokrenuta** — korisnik čita `review.html`.

## [0.1.0-draft] — 2026-08-01, deveta runda (popravke iz osme runde: G4 geo_scope, G8 rod, blocked_by_tooling)

- **G4 fix.** `_category_bounds()` prima `geo_scope`; `local`-ova donja granica pada na 0 SAMO kad je `geo_scope=="global"` (čita se iz `intents[0].geo.scope`, isti izvor koji `build_warnings()` već koristi). Gornja granica `local`-a i SVE ostale kategorije nepromenjene — korisnik je proverio zadovoljivost zbira min/max (22–41 na N=30, 32–53 na N=40, 41–66 na N=50) pre nego što je tražio ovu, i samo ovu, izmenu. 60/40 redistribucija OSTAJE smernica modelu (Faza 4 u `references/workflow.md`), namerno NIJE kodirana kao gate pravilo — dodavanje bi bilo nova neproverena unakrsna referenca, tačno klasa greške koja je izazvala originalni bug. Ponovo pokrenut gate nad `eval-4-global-saas-no-local`-ovim već postojećim `savvycal-library-v1.json` (bez ponovnog pokretanja skilla) — sad prolazi čisto, 0 izmena sadržaja.
- **G8 fix.** `SR_FUNCTION_WORDS` dobija `koja/koje/koju/kojim` (srpski se slaže u rodu — "koji CRM" ali "koja ordinacija", stara lista je imala samo muški rod) i `kod/po/od/iz/uz/pri/o`. Korisnikova originalna lista je uključivala i `do` — **namerno izostavljeno**: `do` je uobičajena engleska reč ("how do I...", "what should I do...") i njeno dodavanje je lažno oborilo G8 na SVA tri EN reda u `valid_library.json` (`int-002-en`, `int-006-en`, `int-039-en`) pri prvom pokušaju ove izmene — uhvaćeno punim fixture prolazom pre commit-a, ne posle. Svih 23 fixture-a potvrđeno prolaze sa ispravljenom listom (bez `do`).
- **`blocked_by_tooling` za iteraciju 1.** `eval-4-global-saas-no-local/with_skill/grading.json`-ov A4 zapis dobija `"blocked_by_tooling": true`, isključen iz `pass_rate` imenioca (isti obrazac kao `ungraded_manual`) umesto da tiho postane `passed: true` ili da ostane obična statistička greška. Razlog: da iteracija 2 (kad se pokrene) ne izgleda kao da se SKILL popravio kad se zapravo popravio VALIDATOR — pass rate za eval 4 u iteraciji 1 sad ispravno čita 14/14 (100%, tooling-blocked stavka izuzeta, ne obrisana) umesto 14/15 (93%, lažna statistička kazna za bug koji nije bio u sadržaju). `benchmark.json`/`benchmark.md`/`review.html` regenerisani (`aggregate_benchmark.py` + `generate_review.py --static`) — bez ponovnog pokretanja bilo kog with_skill/baseline agenta, samo ponovno gradiranje već postojećih izlaza.
- **SKILL.md**: fusnota o `local`/`geo_scope=global` u tabeli kvota promovisana u properly stated pravilo (paragraf analogan branded-ovom, plus red u kvantizacionoj formuli). Telo i dalje 3336/5000 tokena (67%).

**Iteracija 2 NIJE pokrenuta** — korisnik čita `review.html` iteracije 1 prvo.

## [0.1.0-draft] — 2026-08-01, osma runda (PRVI stvarni eval run, otkriven G4/geo_scope bug)

- **Prvi put pokrenut skill end-to-end protiv pravih sajtova.** 4 with_skill runa (eval 0 dentio.rs, eval 1 pausal.rs, eval 2 instar-informatika.hr, eval 4 savvycal.com) + 1 baseline (eval 0, bez skilla, samo za zapisnik). Standardni skill-creator-pro loop: `geo-prompt-library-workspace/iteration-1/`, `eval_metadata.json` po eval-u, `timing.json` po run-u, gradiranje PROGRAMSKI (ne LLM grader-agent) iz sopstvenih `validation-vN.json`/`verify_grounding.py` izveštaja svakog run-a — najveći deo A1-A17 je već mehanički proverljiv iz gate-a samog, pa dodatni grader-poziv ne bi doneo novu informaciju (Korak 4.1 iz skill-creator-pro SKILL.md eksplicitno preporučuje skriptu nad "eyeball" gde je moguće). `scripts/aggregate_benchmark.py` + `eval-viewer/generate_review.py --static` → `iteration-1/benchmark.json`, `benchmark.md`, `review.html`.
- **Rezultat: 3/4 runa `validation.passed: true` iz PRVE ili DRUGE gate iteracije.** Eval 0: pao na pokušaju 1 samo na `G8_language_per_row` (rečenice sa "koja"/"kod" — nisu u zatvorenom skupu SR funkcijskih reči, samo "koji" jeste — realan, uzak gap u G8, ne generalna greška), prošao na pokušaju 2. Eval 1: prošao iz prve, 0 padova. Eval 2 (hr-HR): prošao iz prve, 0 Serbian-marker curenja u G14. Grounding (`verify_grounding.py`) na sva 3: `coverage_status: ok`, 0 lažnih citata.
- **OTKRIVEN STVARAN BUG: `G4_category_quotas` nema izuzetak za `geo_scope=global`.** Eval 4 (savvycal.com, `geo_scope=global`) je pao na SVA 3 pokušaja, uvek na istom pravilu: `local: 0 van [2,6]`. `CATEGORY_QUOTA["local"] = (0.05, 0.15)` u `scripts/validate_library.py` se primenjuje bezuslovno — `floor(0.05×N) >= 1` za SVAKO N u [30,50], pa `local=0` (koje SKILL.md/taxonomy.md eksplicitno nalažu kad je `geo_scope=global`, uz redistribuciju budžeta 60/40 na `use_case`/`category_shortlist`) STRUKTURNO ne može zadovoljiti G4, ni za jedno N — matematički dokazano, ne opaženo na jednom primeru. Skill je ispravno napravio 0 `local` intenata i vidljivo redistribuirao budžet (`use_case` 9/40 na gornjoj granici, `category_shortlist` 11/40 blizu gornje) — problem je isključivo u gate skripti, ne u sadržaju biblioteke niti u tome kako je skill protumačio zahtev. Agent NIJE izmislio lokalne upite da forsira prolaz gate-a (to bi bilo direktno kršenje eksplicitnog `geo_scope=global` zahteva). Programsko gradiranje ovo razdvaja: A4 (mehanički, direktno iz G4) FAILS, A12 (protiv DOKUMENTOVANE specifikacije, ne protiv G4 samog) PASSES — 14/15 assertion-a prošlo na ovom run-u. **Popravka nije sprovedena ovog kruga** — na čekanju korisnikove odluke.
- Manuelno pregledano (ne mehanički gradirano): mešani kod u pausal.rs upitima (5+ upita sa "online"/"AI"/"webshop" u srpskoj rečeničnoj strukturi, prag je >=2 — prošlo), i da EN upiti u savvycal.com run-u nisu doslovni prevod SR parova (12 parova ručno pročitano, svaki nezavisno formulisan — prošlo, A15).
- Svih 5 `timing.json` snimljeno iz task-notifikacija (tokeni + trajanje), ništa nagađano.

**Sledeće:** korisnik odlučuje da li/kad popraviti G4 (dodati `geo_scope` uslov u `CATEGORY_QUOTA`/`_category_bounds` za `local`) pre nego što se eval 4 smatra "prošlim". Eval 3 (thin-site-fallback) i dalje čeka URL.

## [0.1.0-draft] — 2026-08-01, sedma runda (izvučen workflow.md, sync-provera, 9 zastarelih brojeva faza)

- **Faze 1–9 izvučene u `references/workflow.md`.** SKILL.md telo je nosilo pun tekst svih 9 faza (1756 od 4550 tokena tela, 38.6%) pored tabela, kvota i QA gate liste. Sad SKILL.md ima tanak orkestrator (9 imena faza + jedan pasus objašnjenja), pun tekst je u `references/workflow.md`. **QA gate — pravila (G1-G16) NIJE premešteno** — ostaje u telu namerno: gate-ov JSON objašnjava posle, lista u telu treba modelu DOK piše, da ne generiše naslepo i ne oslanja se na retry. Rezultat: telo **4550 → 3021/5000 tokena (60%)**, marža ~1979 (bila 428 pre šeste runde) — oko 4 runde prostora po dosadašnjem proseku rasta, umesto manje od jedne.
- **`references/workflow.md` nosi garanciju, ne apel na dobru volju.** Prvi nacrt obrazloženja ("model treba da pročita fajl") je bio slabiji argument od stvarnog: izlazni JSON sam svedoči o svakoj fazi (`matrix_plan`→Faza 4/G16, `competitors[]`+citati→Faze 2-3/G12/G10, `validation.passed`→Faza 7, `coverage_status`→Faza 8) — model koji improvizuje umesto da pročita referencu neće proizvesti te artefakte ispravno, i to hvata fail-closed gate, ne dobra volja. Ovo obrazloženje je upisano u sam `workflow.md`, ne samo u CHANGELOG.
- **Backup pre restrukturiranja:** `geo-prompt-library-pre-restructure/` (sused direktorijum, `cp -r`, potvrđen `diff -rq` identičan pre prve izmene) — restrukturiranje menja ponašanje (referenca umesto inline teksta), pa mora postojati A/B baza ako prva iteracija evala pokaže nešto sumnjivo.
- **9 zastarelih "(Faza N)" referenci pronađeno i ispravljeno, van workflow-extrakcije.** Sweep pre izvlačenja workflow-a je otkrio da je numeracija faza već tiho driftovala na devet mesta, sve van za jedan broj: `SKILL.md` (`competitors` red: Faza 2→3; G16 opis: Faza 3→4), `references/locale-sr.md` (naslov: Faza 4→5; fallback red: Faza 1→2), `references/taxonomy.md` (comparison kvota: Faza 2→3; matrix kvota: "Faza 3/4"→Faza 4), `scripts/verify_grounding.py` (docstring: Faza 6→7), `scripts/validate_library.py` (2 docstring mesta: Faza 3→4, Faza 6→7). Ovo potvrđuje tačno ono što je predviđeno pre izvlačenja: brojanje faza je već promašeno više puta u ovom projektu (7 faza nad 8 stavki, 17+5=22 umesto 23 fixture-a) i ostaje tih dok se ne pročita pažljivo.
- **`fixtures/verify_workflow_sync.py` — nov, dev-only skript.** Parsira SKILL.md orkestrator (9 `N. **Ime**` stavki) i `references/workflow.md` (9 `## Faza N — Ime` naslova), proverava da se broj, redosled i imena TAČNO poklapaju. Ovo ne hvata svaku moguću "(Faza N)" grešku u prozi (to bi zahtevalo semantičko znanje šta svaka rečenica TREBA da referencira) — hvata samo drift između dva kanonska spiska faza, što je tačno mehanizam koji je upravo omogućio gornjih 9 grešaka da se dogode nezapaženo. Testirano namernim kvarom jednog imena (FAIL, tačna poruka) i vraćanjem (OK). Nema zavisnosti (samo `re`/`pathlib`), radi i pod sistemskim `python3`, ne zahteva venv.
- Svih 23 gate fixture-a i dalje prolaze (`fixtures/verify_fixtures.py`) posle svih izmena — restrukturiranje i ispravke brojeva nisu dirali `assets/library.schema.json` ni gate logiku.

## [0.1.0-draft] — 2026-08-01, šesta runda (telo pred eval, G1 exit-kod, imenovan princip)

- **SKILL.md telo preuređeno za skraćivanje, ne za sadržaj.** 91% popune (4572/5000) uz prosečan rast +468 tokena po rundi (marža 428) je bila premala margina baš kad eval faza po definiciji dodaje sadržaj. Dodato: kompaktan blok "Pravila koja moraju preživeti skraćivanje tela" (anti-halucinacija, matrica pre teksta, fail-closed) odmah posle uvoda — ako telo ikad bude odsečeno na 5000 tokena, ova tri pravila su u prvih par stotina tokena, ne na kraju. Uklonjeno: `## Sledeći koraci (skill-creator-pro loop)` — opisivao je bundle rad koji je već završen (duplirano i zastarelo u odnosu na frontmatter `metadata.status`, koji se učitava nezavisno od dužine tela). Skraćen inline komentar oko branded gornje granice u kvantizacionoj formuli (obrazloženje već postoji u sekciji "QA gate kalibracija" ispod). Neto rezultat: **4550/5000 tokena** (merenje `tiktoken` cl100k_base na telu posle frontmatter-a) — malo niže nego pre, uz dodatnu zaštitu.
- **G1 gate: treći exit kod za grešku okruženja.** Sesija je jednom pokrenula gate sistemskim `python3` bez `jsonschema` i dobila lažnu masovnu "G1_schema fail" regresiju — fail-closed je radio ispravno, ali exit kod 1 je identičan i za "biblioteka nevalidna" i za "gate se nikad nije izvršio". `scripts/validate_library.py` sad ima `_require_jsonschema()` koji proverava import PRE bilo kog check-a i izlazi sa **exit 2** + FATAL poruka na stderr ako `jsonschema` nedostaje — exit 0/1/2 su sad tri odvojena stanja, ne dva. SKILL.md QA gate sekcija ažurirana da to dokumentuje. Svih 23 fixture-a i dalje prolaze (`fixtures/verify_fixtures.py`) posle promene.
- **Imenovan princip u `references/research-basis.md`: "tri stanja, ne dva".** Isti bug se pojavio TRI puta nezavisno (G16 pre `matrix_plan`-a, G12/A8 vs `verify_grounding.py`, `coverage_status` u 5. rundi, sad i G1 exit-kod) — zajednički koren je provera koja ne ume da prijavi da NIJE izvršena, pa se to treće stanje tiho stopi sa "prošlo" ili "palo". Prethodno je ovo bilo razbacano po CHANGELOG fusnotama; sad je imenovan princip sa pravilom za svaku BUDUĆU proveru (novi G-rule, novi skript, novo polje šeme): mora izraziti tri stanja, ne samo `if passed`.

## [0.1.0-draft] — 2026-08-01, peta runda (coverage_status, expectations.json, stvarni URL-ovi)

- **Ispravka pogrešnog stava iz 4. runde: eval 3 URL NIJE smeo ostati simboličan.** Prošli put sam napisao "eval 3 je namerno thin-site scenario, taj URL ostaje simboličan" — pogrešno. Izmišljen/nepostojeći domen testira `ConnectionError`/NXDOMAIN, fetch pukne PRE HTTP-a. Realan `thin-site-fallback` slučaj je HTTP 200 + JS ljuska bez izvučivog teksta — suštinski druga grana koda (skill mora prepoznati "imam 200, nemam sadržaj", ne "sajt ne postoji"). Eval 3 ostaje `PENDING_REAL_URL` dok se ne dobije stvaran tanak sajt — vidi `evals/README.md`.
- **`scripts/verify_grounding.py` — dodat `coverage_status`.** Test iz 4. runde (`valid_library.json`, fiktivan domen) je pokazao tačno problem koji je korisnik predvideo: svih 42 tvrdnje `unreachable` → `passed: true`. Ako svi fetch-evi padnu (Cloudflare, rate limit, mreža), skript je govorio "prošlo" a nije proverio ništa — ista klasa greške kao stari G16 proxy. Dodato: `coverage = verified / (verified + not_found)` (unreachable namerno NIJE u imeniocu — inače 0/0 izgleda kao "nema šta da se proveri" umesto "nismo uspeli ništa da proverimo"). Četiri stanja, ne dva: `ok` (coverage ≥ 0.5), `insufficient` (< 0.5), `no_data` (tvrdnje postojale, 0 stvarno provereno), `no_claims` (nije bilo tvrdnji — legitimno, npr. ceo set inferred). `passed` sad zavisi i od `coverage_status`, ne samo od odsustva lažnih citata. Prvi pokušaj implementacije je imao bug: `no_data` grana se nikad nije aktivirala jer je proveravala `verified or not_found`, koji su PO DEFINICIJI oba 0 kad je imenilac 0 — popravljeno da koristi `unreachable > 0` kao razlikovni signal. Uhvaćeno testiranjem, ne code review-om.
- **Pozitivan test sa više citata na stvarnom sajtu.** Jedini prethodni pozitivan test je bio 1 citat na `example.com`. Dodato `fixtures/grounding_live_dentio.json`: 3 stvarne tvrdnje (izvučene uživo sa `https://dentio.rs` i `https://dentio.rs/cenovnik/`, tačan sadržaj potvrđen kroz istu `fetch()`/normalizacija funkciju koju sam `verify_grounding.py` koristi) preko 2 jedinstvena URL-a — dokazuje i tačnost provere i fetch-once-po-URL dedup (`urls_checked: 2` za 3 tvrdnje). Rezultat: `coverage: 1.0`, `passed: true`.
- **`fixtures/expectations.json` + `fixtures/verify_fixtures.py`.** Prethodna "verifikacija" je nagađala očekivan ishod iz PREFIKSA imena fajla (`g`=fail, `p`=pass) — `p03_branded_over.json` je jedini `p`-fixture koji namerno pada, i bez eksplicitnog zapisa bi ga neko posle `/clear` protumačio kao mismatch i "popravio" ispravan fixture. `expectations.json` sad drži po fixture-u: `expect`, `failing_rules`, `derived_rules`, `note` (sa eksplicitnim upozorenjem na `p03`). `verify_fixtures.py` čita taj fajl (ne imena), ima `--capture` mod za regeneraciju posle promene gate-a. Svih 23 fixture-a potvrđeno poklapanje.
- **Brojanje fixture-a ispravljeno: 23, ne 22.** Prošli put: "17 must-fail + 5 must-pass = 22" — netačna aritmetika (must-fail je 18: g01–g16 + g18 + p03; must-pass je 5: valid + g17 + p01/p02/p04). `g18_cyrillic_variant.json` **postoji** i radi — potvrđeno da lomi G15 (cyrillic provera iz 3. runde), `verify_fixtures.py` to sad potvrđuje mašinski, ne prepričavanjem.
- **`evals.json` — 4 stvarna URL-a od korisnika, DNS+HTTP200 nezavisno potvrđeno:** `dentio.rs` (eval 0), `pausal.rs` (eval 1), `instar-informatika.hr` (eval 2), `savvycal.com` (eval 4, namerno biran umesto cal.com/linear.app da izbegne rizik da model napiše biblioteku iz sećanja trening podataka umesto sa stvarnog fetch-a). Eval 3 i dalje `PENDING_REAL_URL`.
- **SKILL.md Faza 8** ažurirana da eksplicitno kaže: čitaj `coverage_status`, ne samo exit kod / `passed` polje — `insufficient`/`no_data` nije isto što i lažan citat (retry/eskalacija, ne "vrati se na Fazu 2"), ali ni "sve u redu". Faza 9 (rezime) mora prikazati `coverage_status` eksplicitno korisniku.

**SKILL.md telo: ~4572/5000 tokena (91%)** — marža se smanjuje iz runde u rundu. Ako sledeća iteracija (evali) pokaže da telo treba još sadržaja, prvo proveriti da li ide u `references/` umesto.

## [0.1.0-draft] — 2026-08-01, četvrta runda (izmišljeni eval URL-ovi + verify_grounding + eval protokol)

- **evals.json je imao 5 izmišljenih URL-ova.** Korisnik proverio prvi (`stomatoloskaordinacijaosmeh.rs`) → NXDOMAIN. Provereno `host` komandom za svih 5 — **svih pet NXDOMAIN**, ne samo prvi. Da su evali pušteni takvi, sva 5 bi pala na thin-site fallback granu i mereno bi bilo pokvarene test podatke, ne skill. Zamenjeno `PENDING_REAL_URL` placeholder-om u sva 4 relevantna prompt-a (eval 3 je namerno thin-site scenario, taj URL ostaje simboličan). `evals/README.md` dodat sa tvrdim pravilom: DNS + HTTP 200 provera pre pokretanja bilo kog eval-a, bez izuzetka, bez izmišljanja zamena.
- **`scripts/verify_grounding.py` — nova, zasebna skripta.** Gate proverava da `source_url`/`evidence`/`grounding.quote` POSTOJE; ništa nije proveravalo da citat STVARNO STOJI na toj stranici — model koji hoće nizak `inferred` može napisati uverljiv izmišljen citat i gate ga pušta. Namerno odvojeno od `validate_library.py`: gate mora ostati brz/offline (vrti se u retry petlji, Faza 7), ovo zahteva mrežu po jedinstvenom `source_url` i sme da padne iz prolaznih razloga. Mrežna greška → `warning`; citat koji nije pronađen na (fetched, HTML-stripped, whitespace-normalizovanoj) stranici → tvrd `exit 1`. Testirano uživo: `https://example.com` sa tačnim citatom → `verified`; izmišljenim citatom → `not_found`, `passed: false`; `valid_library.json` (fiktivan `cloudflow.rs` domen) → svih 42 tvrdnje `unreachable`/warning, `passed: true` (mrežna nedostupnost ne obara). Pozvano u novoj Fazi 8 u SKILL.md (workflow sad 9 faza), posle gate-a. Dodat eval assertion A17.
- **Eval protokol dopunjen u `evals/README.md`.** Baseline (bez skilla) poređenje ovde meri malo — subagent bez skilla neće ni pokušati šemu, `A1`–`A17` će biti ~0, što dokazuje da skill postoji, ne da je dobar. Prava metrika: da li izlaz prolazi sopstveni gate na stvarnom sajtu i iz kog pokušaja. Iz svakog with_skill run-a sad se zapisuje `validation.passed`, `retry_count`, `first_attempt_failures`, `inferred_ratio` — `retry_count` i `first_attempt_failures` sad idu i u skillov sopstveni konzolni rezime (Faza 9 u SKILL.md), ne zahtevaju posebnu instrumentaciju.

**Evali NISU pokrenuti** — blokirano na 5 stvarnih URL-ova od korisnika. Vidi `RESUME.md` za puno stanje projekta.

## [0.1.0-draft] — 2026-08-01, treća runda (spec fix + derived + 3 fixture-a)

- **Ispravka spec-a: G4/G5 sudar za `branded`.** Brief sekcija 5 daje opštu formulu
  `[floor(min%×N), ceil(max%×N)]` za sve kategorije, a `branded` izuzetak (floor na
  obe strane) navodi odvojeno. Za N gde `0.15×N` nije ceo broj (30/35/45/50) te dve
  formule daju različit odgovor za isti broj (N=30, branded=5: legalno po opštoj
  formuli primenjenoj bukvalno na branded, ilegalno po izuzetku) — N=40 je jedini
  N u tom skupu gde se `floor` i `ceil` poklapaju, pa je bug bio nevidljiv na
  default-u. Kod je već pozivao istu `_branded_max()` funkciju iz G4 i G5 (nije bio
  aktivan bug u skripti), ali je refaktorisan u `_category_bounds()` da to bude
  strukturno očigledno, ne slučajno tačno. SKILL.md sekcija o kvantizaciji sad
  eksplicitno piše `dozvoljeno[branded] = [floor(0.08×N), floor(0.15×N)]` kao svoju
  formulu, ne kao fusnotu uz opštu.
- **`derived` polje u validation report-u.** Faza 6 kaže "regeneriši samo pogođene
  ćelije", ali kad G16/G15 padnu kao posledica G4/G11/G13/G6 (isti koren, ne
  dodatna pogođena ćelija), skill ranije nije imao način da to razlikuje od
  nezavisnog nalaza. Svaki red u `validation.checks` sad ima `"derived": true/false`
  (`DERIVED_FROM` mapa u skripti: G16←{G4,G11,G13}, G15←{G6}) — true samo kad
  pravilo padne ISTOVREMENO sa jednim od svojih root pravila, ne kad padne samo
  (npr. `g16_matrix_consistency.json`, gde je jedino G16 pao jer je sam plan
  petljan, ostaje `derived: false` — to je pravi nezavisan nalaz). SKILL.md Faza 6
  sad kaže da se `derived: true` redovi izostavljaju iz retry-cell targeting-a.
- **G15 proširen na `variants.cyrillic`.** Ranije je proveravao samo `ascii`; polje
  `cyrillic` je postojalo u šemi ali ga ništa nije validiralo. Ista logika
  (deterministički forward mapping, `to_cyrillic()` iz `orthographic_variants.py`).

**Tri nova fixture-a:**
- `g17_diacritic_collapse.json` (must PASS) — upit sa č i ć istovremeno
  ("praćenje" + "ključne" u istoj rečenici). ASCII fold mapira oba u isto slovo `c`
  (nije invertibilno, O2) — fixture dokazuje da se forward mapping ispravno računa
  i kad se oba slova pojave zajedno, bez pokušaja rekonstrukcije nazad.
- `g18_cyrillic_variant.json` (must FAIL, tek posle G15 proširenja) — `ascii` tačan,
  `cyrillic` pokvaren. Pre proširenja G15 ovo bi prošlo neopaženo.
- **Provera `g06`** (ne novi fixture, direktna verifikacija): `to_ascii()` na tekstu
  sa `[grad]` daje `'...u [grad]'` — uglaste zagrade prolaze kroz `str.translate()`
  netaknute jer nisu u mapi. Uzrok G15 pada u `g06_placeholder.json` je isključivo
  to što `mutate_g06_placeholder` menja `text` a ne regeneriše `variants` — stored
  `variants.ascii` i dalje doslovno sadrži `"Beogradu"` iz teksta pre mutacije.
  Potvrđeno, ne bracket-mapping bug.

Pun set (23 fixture-a: valid + g01–g16 + g18 must-fail, g17 + p01–p04 must-pass)
prošao kroz `scripts/validate_library.py` sa očekivanim ishodom.

## [0.1.0-draft] — 2026-08-01, druga runda (korisnička revizija bundla)

Tri ispravke na prvu verziju bundla, sve na zahtev korisnika posle pregleda
gate-a nad fixture-ima:

- **G16 — artefakt, ne pravilo.** Proxy (category↔awareness_stage konzistentnost)
  zamenjen pravim `matrix_plan` blokom u šemi: Faza 3 sad piše `{planned_total,
  cells: [{category, persona_id, geo_city, planned}]}` u izlaz, G16 poredi to sa
  stvarnim brojem intenata po ćeliji. Bonus: to je i revizorski trag pokrivenosti
  za klijenta, ne samo interna provera. SKILL.md Faza 3 eksplicitno kaže da se
  plan upisuje u izlaz.
- **G7 — cepanje na G7a/G7b.** Overlap coefficient sa pragom 0.85 primenjen na BILO
  KOJI par davao je 1.00 i za legitimne različite ćelije matrice (npr.
  category_shortlist upit + isti upit sa dodatim gradom u `local` — grad je razlog
  zašto je to druga ćelija, ne duplikat). G7a (ista kategorija): overlap >= 0.85 =
  duplikat, kao pre. G7b (različita kategorija): duplikat samo ako je normalizovan
  skup tokena identičan — modifikator koji pravi kategoriju drugačijom (grad,
  segment) je eksplicitno izuzet.
- **g03 fixture je testirao pogrešan failure mode.** "1 upit umesto 2" hvata već
  schema `minItems:2` na `queries[]` — G3 nije bio nezavisno dokazan. Zamenjeno
  realnim bugom: 2 upita, oba `lang:"sr"` (model napisao SR upit, pa umesto EN
  para napisao još jednu srpsku parafrazu). Schema i dalje prolazi (2 validna
  objekta), G3 sad hvata to sam.

Dodata 4 near-miss fixture-a (`p01`–`p04`) koja MORAJU proći — do sada je set
imao 16 fail-testova i samo 1 pass-test, a lažni pozitiv (gate odbija ispravnu
biblioteku) je skuplji bug u produkciji od lažnog negativa. `p03_branded_over`
namerno pokazuje da floor/ceil bug iz kvantizacije nije vidljiv na N=40 (gde je
`floor(0.15×40) == ceil(0.15×40) == 6`) nego tek na N koje nije deljivo lepo sa
0.15, npr. N=30.

Svih 21 fixture-a (17 + 4) prošlo kroz `scripts/validate_library.py` sa
očekivanim ishodom posle ovih izmena. Nekoliko "fail" fixture-a sad kaskadno
pada i na G16 pored svog primarnog pravila (`g02`, `g04`, `g05`, `g11`, `g13`) —
očekivano, jer `geo.city` i `persona_id` jesu deo `matrix_plan` ključa ćelije, pa
promena jednog nužno raskorači plan od stvarnosti. To je realna posledica
podataka, ne greška u izolaciji testa.

## [0.1.0-draft] — 2026-08-01

Prvi draft, napisan pomoću `skill-creator-pro`, faza Interview and Research, na osnovu
`BRIEF-geo-prompt-library.md` v1.0 (2026-08-01).

### Otvorena pitanja iz brief sekcije 12 — potvrđeno sa korisnikom pre pisanja drafta

Sva pitanja odgovorena u skladu sa brief-ovim sopstvenim predlogom:

1. **Ime skilla:** `geo-prompt-library` (ne `geo-query-library`) — "prompt" je ustaljen
   termin u GEO industriji, lakše se prepoznaje.
2. **`n_intents` default:** `40` — uz `notes_for_downstream` preporuku od 3 izvršavanja
   × 2 jezika = 240 prompt-run-ova, MoE pada na ~±6pp, čime 30–50 opseg postaje branljiv.
3. **Ćirilične varijante:** generišu se **uvek** po default-u — deterministički jeftino
   (`scripts/orthographic_variants.py`), downstream skill sam bira da li ih izvršava.
4. **Persone:** **automatski** se izvode sa sajta i označavaju `confidence` poljem —
   korisnik ispravlja u rezimeu ako treba, bez usporavanja svakog poziva skilla.
5. **Refresh režim** (v1→v2 sa identičnim `intent_id`-ovima, za paired merenje kroz
   vreme): **odloženo za v1.1**, nije u ovom draftu. Šema već ima `library_version` i
   `frozen` polja koja to podržavaju kasnije bez loma ugovora.

### Kompresija tela (nakon merenja stvarnih tokena)

- Body izmeren na 3499 tokena (cl100k_base proxy, pravi Claude tokenizer nije dostupan
  offline) pri prvom draftu — unutar budžeta od 5000, ali bez marže za bundle koraka.
- Uklonjena sekcija "Otvorena pitanja iz interview-a" iz tela (provenijencija — sada
  ovde) i ASCII mapa fajl-strukture bundla (dobija se sa `ls`, ne treba trajno u
  budžetu koji se učitava pri svakom triggeru).
- `compatibility` polju uklonjena rečenica o odsustvu API troška — to je prodajni
  argument, ne podatak o kompatibilnosti; premeštena u telo (Ulaz/Izlaz sekcija).
- Dodato eksplicitno obrazloženje ZAŠTO `branded` ima tvrd plafon (ne samo broj 15%).
- Posle ovih izmena: 3169 tokena (cl100k_base proxy), 102 linije.

### QA gate kalibracija (`scripts/validate_library.py`)

Dva pravila namerno odstupaju od bukvalnog čitanja brief sekcije 8, otkriveno
računski pri gradnji fixtures-a (ne stilska odluka):

- **G7 (near-duplicate).** Brief kaže "trigram Jaccard sličnost > 0.85". Simetrični
  Jaccard strukturno ne može preći `len(kraći)/len(duži)` kad je jedan upit drugi plus
  dodata fraza — za "najbolji CRM za male firme" (5 reči) + " u Srbiji" (2 reči) to je
  ~0.73, uvek ispod 0.85, za bilo koju veličinu n-grama (proveren i word-trigram i
  char-trigram). Najčešći stvarni near-dup obrazac u ovom domenu (ista jezgra + dodat
  grad) nikad ne bi okinuo gate. Zamenjeno sa **overlap coefficient**
  (`|A∩B| / min(|A|,|B|)`, isti prag 0.85, isto ime pravila) — na istom paru daje 1.0
  (potpuno sadržan), a na pravoj parafrazi ("koji CRM je najbolji za mala preduzeća")
  daje 0.0. Oba granična slučaja potvrđena u `fixtures/valid_library.json` (parafraza,
  ne sme okinuti) i `fixtures/g07_near_duplicate.json` (dupli sadržaj, mora okinuti).
- **G8 (jezik po redu).** Implementirano tačno po specifikaciji iz razgovora: zatvoren
  skup SR funkcijskih reči (`da, li, je, za, u, koji, kako, šta, na, se, sa, ili`), ne
  statistička detekcija jezika — pouzdano i na upitima od 3 reči, i na mešanom kodu
  ("najbolji CRM za male firme" i dalje ima "za").
- **G16 (prazne ćelije matrice).** Isporučeni JSON ne čuva Faza-3 plan, pa se bukvalno
  "ćelija koju je matrica predvidela a ostala prazna" ne može proveriti iz samog fajla.
  Zamenjeno dvodelnim proxy-jem: (a) `awareness_stage` svakog intenta mora biti u
  dozvoljenom skupu za njegovu `category` (fiksna mapa iz sekcije 5), (b) svaka
  kategorija sa nenultim minimumom kvote mora imati ≥1 intent (izuzev `local` kad je
  `geo_scope == global`). Vidi docstring `check_g16_matrix_consistency` u skripti.

### Fixtures (`fixtures/`)

`fixtures/generate_fixtures.py` (dev alat, van isporučenog skill bundla) gradi
`valid_library.json` (40 intenata, sr-RS, izmišljena B2B SaaS firma "CloudFlow CRM" —
isti vertikal kao G7 primeri iz razgovora) i po jedan namerno pokvaren fixture za
svako od G1–G16, jednom ciljanom mutacijom po fajlu. Svih 17 fajlova prošlo kroz
`scripts/validate_library.py`: validan prolazi sve, svaki pokvaren pada tačno na
predviđeno pravilo (uz očekivane kaskadne padove kad mutacija realno dira više
provera odjednom — npr. brisanje 15 intenata u G2 fixture-u nužno probija i G4
kvote i G16 prazne kategorije; to je odraz stvarnog stanja podataka, ne greška u
izolaciji testa).
