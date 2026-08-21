<!-- Part of a derivative work of anthropics/skills@b29e7cf6 (skills/skill-creator), by buky <webdevcom01@gmail.com>, 2026-07-30. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md. -->

# Changelog

Fork od `anthropics/skills`, putanja `skills/skill-creator`, upstream commit
`b29e7cf65e5cb78a5ac33d582270551bc74a14eb` (2026-07-24). Licenca Apache-2.0.

Checksum se računa nad sadržajem i relativnim putanjama, nezavisno od lokacije:

```bash
(cd <skill> && find . -type f | LC_ALL=C sort \
  | while read -r f; do printf '%s  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "${f#./}"; done \
  | sha256sum | cut -d' ' -f1)
```

---

## [1.0.0] — u toku

Prva verzionisana revizija. Pre nje nijedna verzija nije bila deklarisana, pa nema
prethodne oznake na koju bi se nadovezala — odatle `1.0.0`, a ne `1.1.0`.

Osnova: nasleđeno stanje forka, checksum
`689128ccc3ec26c1982589967ee621143f09bdc3646c2636bfc8659cd2911856`.
Upstream u istom trenutku:
`f6e18a2581b8926895a5b07e968d7b69c1ea2798e7b176aa8de409869e08a394`.

### Popravljeno

- **N-32** — `LICENSE.txt` je nosio nepopunjen Apache-2.0 boilerplate
  `Copyright [yyyy] [name of copyright owner]`. Vraćena atribucija iz izvorne forme:
  `Copyright 2026 Anthropic, PBC.` Fajl je sada bajt-identičan upstream-u.
  Osnov: Apache-2.0 §4(c) — „You must retain, in the Source form of any Derivative
  Works that You distribute, all copyright, patent, trademark, and attribution
  notices from the Source form of the Work".

- **T-03 / §4a** — opis nije imao ni jedan trigger na srpskom, iako ih 20+ instaliranih
  skillova nosi, ni negativnu granicu, dok je tri suseda imaju. Dodato: 12 srpskih
  trigger fraza i granica koja isključuje AgentStack/SOMA agente, SOMA pipeline evale i
  API/chat promptove. Opis 319 → 799 znakova (limit 1024, listing cap 1536 → 816).
  Osnov: `agentskills.io/skill-creation/optimizing-descriptions` — „Err on the side of
  being pushy. Explicitly list contexts where the skill applies"; i enterprise.md
  koegzistencija u obrnutom smeru.
  Verifikovano pre primene: nula od 12 fraza ne postoji ni u jednom drugom opisu;
  diskriminanta je čista (svi susedi sa istim glagolima koriste `agenta`/`prompt`/`eval`,
  nijedan `skill`); `yaml.safe_load` i `utils.parse_skill_md` daju **identičan** string.
  Zadržan plain jednolinijski scalar, ne `>` blok — jer bi blok dodao 10 linija a
  `SKILL.md` je na 493/500. Posledica na deljeni listing budžet: +480 znakova (+1,5%).

### Dodato

- **N-22** — `license: Apache-2.0` u frontmatter-u (spec dopušta naziv licence ili
  referencu na bundle-ovan fajl), `metadata.version` i `metadata.upstream`. Do sada
  nije postojao način da se razlikuje jedna revizija od druge, ni da se detektuje
  drift od upstream-a.
- Ovaj `CHANGELOG.md`.

### Popravljeno — Blok 1, merni sloj (T-08 + T-16), 2026-07-30

Sve u `scripts/aggregate_benchmark.py`. Jedini izmenjen fajl; za ispravan ulaz je
`benchmark.json` **bajt-identičan** prethodnom (dokazano poređenjem), pa se već
proizvedeni izveštaji ne menjaju.

- **N-01** — agregacija je tiho vraćala nule na rasporedu koji `SKILL.md:180` i
  `agents/grader.md:92` propisuju (`<config>/grading.json` bez `run-*` nivoa), sa
  `exit 0` i bez upozorenja. Sada se taj raspored čita, a kad nijedan run nije
  upotrebljiv ništa se ne upisuje i izlazi se sa `EXIT_NO_DATA = 3`, uz stderr koji
  imenuje pregledane direktorijume. **Dodatno** (nađeno pri primeni): i kad je
  *jedna* konfiguracija bez upotrebljivih run-ova a druga ima podatke, izveštaj se
  odbija — jer bi `0% ± 0%` za nemerenu konfiguraciju bilo nerazlučivo od izmerene
  nule. Sva upozorenja premeštena sa stdout na stderr (zatvara i jednu asertaciju N-17).
- **N-38** — `.get(k, default)` ne štiti kad ključ **postoji sa vrednošću `null``**
  (default važi samo kad ključ nedostaje). Jedanaest numeričkih polja iz
  `grading.json`/`timing.json` — koje piše LLM agent — rušilo je agregaciju
  `TypeError`-om u `calculate_stats`. Svako numeričko polje sada ide kroz `_number`,
  koji odbija run sa imenom fajla u poruci; narativna polja (`user_notes_summary`)
  se tolerišu uz upozorenje, jer ne ulaze ni u jednu statistiku.
- **N-39** — `int(run_dir.name.split("-")[1])` na `:178` nije imao `try/except` koji
  identičan obrazac na `:162` ima → `run-retry` je rušio celu agregaciju. Sada pada
  na pozicioni indeks uz upozorenje. Čitanje `timing.json` sada hvata i `OSError`,
  ne samo `json.JSONDecodeError` — nedoslednost sa `:156`.
- **N-41** (nov, nađen pri primeni) — `eval_id: null` u jednom od dva eval
  direktorijuma rušio je `sorted(set(...))` sa `TypeError: '<' not supported between
  'int' and 'NoneType'`. Sortiranje sada koristi tipski-particionišući ključ.
  **Vrednost se namerno NE normalizuje** — koercija `eval_id` u broj sprečila bi da
  payload stigne do `eval-viewer/viewer.html:1133` (koji ostaje neescape-ovan i
  dosežan preko ručno pisanog `benchmark.json`, `SKILL.md:231`) i time bi lažno
  „popravila" N-02b. Escaping pripada vieweru — tiket T-06.

Uvedeni distinktni exit kodovi (`EXIT_OK=0`, `EXIT_USAGE=1`, `EXIT_NO_DATA=3`) i dva
nova metapodatka (`runs_loaded`, `runs_rejected`) plus `data_quality` lista u
`benchmark.json`/`benchmark.md`, da smanjenje `n` više ne bude nevidljivo.

Verifikovano pre primene: ugovor protiv `grader.md`/`schemas.md`, bajt-identičnost za
ispravan ulaz, legacy `runs/` raspored, stvarna izmerena nula i single-config i dalje
rade, nema drugih pozivalaca funkcije, viewer ignoriše nova polja. Predikcija
prevrtanja zapisana pre koda; ostvareno **12 prevrnuto, 0 regresije**.

### Popravljeno — Blok 1, detektor trigera (T-09), 2026-07-30

Sve u `scripts/run_eval.py` (jedini izmenjen fajl, 546 → 572 linija).

- **N-04** (CRITICAL) — `run_single_query` je zaključivao „nije trigerovao" pre nego
  što je skenirao celu poruku/stream, na tri mesta: streaming grana je na svaki
  ne-Skill/Read alat vraćala `False` (`:262`), na Skill/Read blok koji se ne poklapa
  takođe `False` (`:284`), a fallback grana je `return`-ovala **unutar** petlje pa
  gledala samo prvi `tool_use` item (`:314`). Pošto `SKILL.md:491` izričito nalaže
  modelu da stavi korake u TodoList (dakle da zove `TodoWrite`), realan tok
  „TodoWrite pa Skill" bio je sistematski prijavljivan kao netrigerovanje, a cela
  optimizacija opisa birala je „najbolju" iteraciju po iskrivljenim labelama.
  Sada je terminalno samo `message_stop` / `result` / kraj strima; ne-poklapajući
  blok resetuje stanje i skeniranje se nastavlja.

**Obavezna napomena o uporedivosti:** posle ove izmene trigger rate-ovi **rastu** —
Skill pozvan posle drugog alata više se ne gubi. Svi rezultati merenja opisa od pre
ove izmene su **neuporedivi** sa novima; bez ove napomene izgledalo bi kao da je novi
opis bolji. (Ovo je bila stavka iz „Planirano" liste, sada aktivirana.)

Verifikacija pre primene: matrica od 15 oblika ulaza (streaming + fallback) dokazala
**0 True→False regresija** — fix pretvara isključivo False→True; `via`
(`real_skill`/`decoy`) očuvan; rečnik događaja bajt-identičan; `run_eval` agregacija
ispravno broji trigere. Diff ne dira nijedan `return True`.

### Popravljeno — Blok 1, jedinice i statistika (T-07), 2026-07-30

Dva fajla: `scripts/aggregate_benchmark.py` i `references/schemas.md`.

- **N-07** (jedinice tokena) — kolona „Tokens" i token delta su prikazivali
  `output_chars` (broj **znakova**, grader.md:207 ga zove „proxy for tokens"),
  a kod mešanih konfiguracija poredili prave tokene sa znakovima → besmislena
  delta red veličine prevelika. Sada: `tokens` dolazi isključivo iz
  `timing.total_tokens`; bez njega je `null` („nije mereno", ≠ izmerena 0);
  `output_chars` je zaseban ključ i nikad ne puni `tokens`; token stat
  konfiguracije je `null` ako **ijedan** run u njoj nema pravi broj; delta je
  `"n/a"` kad strane nisu u istoj valuti.
- **N-09** (lažni `n`, model, `± 0`) — `runs_per_configuration` je bio hardkodiran
  `3` bez obzira na stvarni broj run-ova; sada je **izmeren**, sa
  `runs_per_configuration_by_config` razradom. `calculate_stats` nosi `n`;
  `benchmark.md` pri `n=1` prikazuje `(n=1)` umesto lažnog `± 0` (koji se čita
  kao savršena reproduktivnost), pri `n≥2` `± stddev (n=N)`. `executor_model` /
  `analyzer_model` više nisu `<model-name>` template — dolaze iz CLI
  (`--executor-model` / `--analyzer-model`) ili su pošteno `"unspecified"`.
- **`schemas.md`** — dokumentacioni ugovor je usklađen sa stvarnim izlazom
  (`schemas.md:315` traži da ga ručni autori slede): dokumentovani `tokens` kao
  `null`-abilan pravi broj, `output_chars` kao zaseban, `n` u stat objektima,
  izmereni `runs_per_configuration` + `by_config`, i T-08 polja koja shema nije
  pominjala (`runs_loaded`, `runs_rejected`, `data_quality`).

**Obavezna napomena o uporedivosti:** jedinice tokena i prikaz `n` se menjaju, pa
se **stariji `benchmark.json` / `benchmark.md` artefakti ne smeju porediti** sa
novima. (Bila stavka „Planirano", sada izmirena.)

Verifikacija pre primene: matrica scenarija (svi pravi / nijedan / mešano /
parcijalno-u-konfiguraciji / stvarna-0 / raz-broj-run-ova) — svaki tačan; za
ispravan ulaz sa pravim tokenima brojevi ostaju tačni uz pravi stddev; viewer
bezbedan sa `null` tokenima; primer u shemi parsiran kao validan JSON. N-28 i N-30
namerno ostaju otvoreni (zasebni tiketi).

### Popravljeno — Blok 1, podela eval skupa (T-15), 2026-07-30

Sve u `scripts/run_loop.py`.

- **N-36** (duplirani upit) — isti tekst upita je išao u **oba** skupa (holdout nije
  neviđen, jer test filter poredi po tekstu), i dobijao **dvostruku težinu** (run_eval
  agregira po tekstu). Nov `dedupe_by_query` svodi ponovljen tekst na prvo pojavljivanje;
  koristi se u `split_eval_set` (skupovi disjunktni) i u `run_loop` (prijavljene veličine
  odgovaraju broju merenih upita). Konfliktan `should_trigger` na duplikatu se prijavljuje.
- **N-35** (degenerisana podela) — `split_eval_set` uzima najmanje 1 primer po klasi u
  **test**, bez donje granice za **train**. Sa malim skupom (npr. 1 poz + 1 neg i bilo
  koji `holdout > 0`) train ostane prazan, a `run_loop` bi to pročitao kao „all_passed"
  (0 od 0) — lažno zeleno. Sada: prazan train → `ValueError` (u `main` gracidozno
  `exit 1`); train kome fali cela klasa (npr. 9 poz + 1 neg → 0 negativnih) → upozorenje
  na stderr sa „negative"/„positive". Stratifikacija, fiksan `seed(42)` i determinizam
  („keep the split fixed across iterations", SKILL.md) su **očuvani** — za skup bez
  duplikata podela je bajt-identična prethodnoj.

Verifikacija pre primene: matrica podele (normalan / prazan-train / bez-klase / duplikati
/ ekstremni holdout) — sve tačno; refuse se aktivira samo na stvarno degenerisanom
train-u; end-to-end `run_loop` prijavljuje veličine koje se poklapaju sa rezultatima.

### Popravljeno — Blok 1, vidljivost nesigurnosti (T-10), 2026-07-30

Dva fajla: `scripts/generate_report.py` i `scripts/run_loop.py`.

- **N-14** (odbačena nesigurnost) — upit čiji su **svi run-ovi u grešci** je
  inconclusive (nema dokaza ni za ni protiv: `trigger_rate=None`, `runs=0`), a
  renderovao se **identično stvarnom netrigerovanju** (`✗ 0/0`), pa se nije
  razlikovalo „mereno, nije trigerovalo" od „nije moglo da se izmeri". Fix na
  dve površine istog nalaza: (1) `generate_report.py` — nov `result_cell`
  renderuje inconclusive ćeliju kao `⚠ inconclusive (N errors)`, svoja CSS
  klasa; (2) `run_loop.py` — `print_eval_stats` pri svim-greškama je ispisivao
  `precision=100% recall=100%` bez pomena nesigurnosti; sada dodaje
  `, N inconclusive (M errored runs)`.

Verifikacija pre primene: za izveštaj bez inconclusive rezultata izlaz je
**bajt-identičan** prethodnom (jedina razlika je dodata CSS klasa); inconclusive
ima prednost nad ✓; stari format bez `inconclusive` ključa i dalje renderuje ✓/✗.

### Popravljeno — Blok 1 završen: T-17 + T-14a + T-14b, 2026-07-30

Tri fajla: `scripts/run_loop.py`, `scripts/generate_report.py`,
`scripts/improve_description.py`.

- **N-40** (`--max-iterations 0`) — argparse prihvata 0 (`type=int`, bez minimuma),
  a tada telo petlje nikad ne izvrši, `history` ostane prazan i `max(history, …)`
  digne `ValueError: max() arg is an empty sequence` — pad bez izlaza posle
  potencijalno mnogo plaćenih eval poziva. Sada `run_loop` odbija vrednost `< 1`
  uz jasan razlog (`main` to prevodi u čist ne-nulti izlaz), a `generate_html`
  čuva prazan `history` (`best_iter = None`) pa se i izveštaj „ništa nije
  pokrenuto" može napisati.
- **N-11** (opis preko limita) — dve stvari: (a) rezultat retry-ja se nije ponovo
  proveravao, pa je „skraćeni" opis od 1100 znakova prolazio; sada postoji tvrda
  kapa na 1024 (rez na granici reči, sa fallback-om na tvrdi rez kad bi granica
  reči pojela više od petine budžeta); (b) kad model ne emituje
  `<new_description>` tagove ili doda uvodnu rečenicu, cela replika je postajala
  opis („Sure! Here's the improved description: …"); nov `_parse_description`
  izvlači telo iz tagova i skida uvodnu rečenicu, koristi se na oba mesta.
- **N-12** (`--holdout 0` ruši loop) — pri `holdout=0` loop upisuje
  `"test_results": None`; ključ **postoji**, pa `.get(k, [])` podrazumevana
  vrednost nikad ne važi i `aggregate_runs(None)` iterira `None` → `TypeError`,
  rušeći ceo izveštaj — uključujući live izveštaj koji se piše posle svake
  iteracije. Sada se fallback aktivira samo na odsutan-ili-`null`; eksplicitno
  prazna lista ostaje prazna (razlika prema v2 postoji **isključivo** na `null`
  slučajevima, što je i cilj popravke).

Verifikacija pre primene našla i ispravila **dve greške u samoj popravci**:
`or []` je bio preširok (swallow-ovao legitimnu praznu listu) → pooštreno na
eksplicitnu `None` proveru; tvrda kapa je bila preagresivna (degenerisan ulaz
`"Use " + 1300 znakova` sekla na 3 znaka) → dodat fallback na tvrdi rez.

### Popravljeno — Blok 2, XSS u eval vieweru (T-06), 2026-07-30

`eval-viewer/viewer.html` (1325 → 1416 linija). **Najveći CRITICAL.**

`renderBenchmark` i `renderGrades` su gradile HTML string-konkatenacijom i predavale
ga `innerHTML`-u. Od svih interpolacionih mesta u njima, većina nije pozivala
**nikakav** escaping, a jedno je pozivalo helper koji ne escape-uje navodnike i
koristilo ga **unutar vrednosti atributa**. Rezultat: šest dokazanih puteva do
izvršavanja proizvoljnog JS-a u strani koja hostuje same-origin endpoint za upis u
`feedback.json` — a `SKILL.md` nalaže Claude-u da taj fajl pročita i po njemu
prepiše skill.

Obe funkcije su prevedene na `createElement` / `textContent` preko malog `el()`
helpera. Podatak više **nikad ne prolazi kroz HTML parser**, pa je površina
strukturno imuna umesto da zavisi od toga da se escaping ne zaboravi:

| Put | Polje | Bilo | Sada |
|---|---|---|---|
| N-02a | `expectations[].evidence` u `title="…"` | `escapeHtml` ne escape-uje navodnike | `node.title = value` (property) |
| N-02b | `metadata.evals_run` | bez escaping-a | `textContent` + `Array.isArray` guard |
| N-02c | `configLabel` (ime direktorijuma na disku) | bez escaping-a | `textContent` |
| N-02d | `run.run_number` | bez escaping-a | `textContent` |
| N-02e | `delta.*` | bez escaping-a | `textContent` |
| **N-02f** | `grading.summary.passed/failed/total` | bez escaping-a | `textContent` |

- **N-02f je nov nalaz**, otkriven pri implementaciji T-06 — nije bio među pet puteva
  iz audita. `renderGrades` je interpolirao ta polja na pretpostavci da su brojevi, a
  `grading.json` piše grader agent (model, iz izlaza testiranog skilla). Dokazano
  izvršavanje JS-a; posle popravke vrednost ostaje **vidljiva kao tekst**.
- `escapeHtml` sada escape-uje i `"` i `'`, pa je bezbedan i u atributskoj poziciji
  (ostaje globalan — koristi se i izvan ove dve funkcije).
- `fmtStat` je sada **n-aware**: pri `n=1` prikazuje `(n=1)` umesto `± 0`, čime je
  ispunjena obaveza zabeležena u T-07 (viewer deo N-09).

Verifikacija pre primene: šest različitih oblika payload-a (`img-onerror`,
`svg-onload`, breakout dvostrukim i jednostrukim navodnikom, `<script>`, `</td>`
breakout), svaki ubrizgan istovremeno u **svako** polje — nijedan nije probio. Za
ispravne podatke prikaz je strukturno identičan prethodnom (iste tabele, redovi i
`span[title]`), uz jedinu namernu razliku: `(n=…)` oznake.

**Van obima ovog tiketa, zabeleženo:** CSP i migracija inline handler-a ostaju
T-06b; `viewer.html:849` (`XLSX.utils.sheet_to_html` → `innerHTML`) je **neproveren**
jer se SheetJS ne može učitati bez mreže — vidi `PLAN.md`, kandidat N-43.

### Popravljeno — Blok 2, CSRF na feedback endpoint-u (T-12), 2026-07-30

`eval-viewer/generate_review.py` i `eval-viewer/viewer.html`.

- **N-03** (CRITICAL) — `POST /api/feedback` piše `feedback.json`, koji `SKILL.md`
  nalaže Claude-u da pročita i po njemu prepiše skill. Endpoint je prihvatao **bilo
  koji** POST: bez `Origin` provere, bez `Content-Type` provere, bez tokena. Zato je
  **bilo koja veb strana** otvorena u brauzeru dok review server radi mogla da mu piše
  „simple request"-om — bez preflight-a, dakle bez CORS saglasnosti, i **bez XSS-a**.

Uvedena su četiri nezavisna sloja, od najjeftinijeg ka najskupljem:

1. **Kapa na veličinu** (`MAX_FEEDBACK_BYTES`, 5 MB) pre čitanja tela → `413`.
2. **`Content-Type` mora biti `application/json`** → `415`. Cross-origin „simple
   request" ne može da postavi taj tip bez preflight-a, koji server nikad ne odobrava.
3. **`Origin`**, ako je poslat, mora biti ovaj server → `403`.
4. **Per-run CSRF token** (`secrets.token_urlsafe(32)`, poređenje
   `secrets.compare_digest`) → `403`. Token se generiše pri pokretanju servera i
   ubacuje u stranu koju taj isti server servira, pa ga zna samo dokument učitan sa
   ovog origin-a; server ne šalje nijedno `Access-Control-*` zaglavlje, pa strana
   strana ne može da pročita ni stranu ni token.

Klijent šalje token kroz `feedbackHeaders()` u oba upisa. U `--static` modu tokena
nema (nema ni servera), pa se ponašanje ne menja — fetch padne i radi se fallback na
preuzimanje fajla, kao i pre.

Verifikacija pre primene: svaki sloj izmeren posebno (200 / 403 / 403 / 415 / 403 /
413), plus 14 pokušaja zaobilaženja — `Origin: null`, drugi port, poddomen-trik
(`127.0.0.1.evil.com`), `multipart/form-data`, `form-urlencoded`, `PUT`/`DELETE`/
`PATCH` (501), i provera da `GET /api/feedback` **ne curi token**. Legitimni oblici
(`; charset=utf-8`, velika slova, ispravan `Origin`) prolaze. Kontrola auto-save-a
zelena pre i posle.

Verifikacija je našla i grešku u samoj popravci: odbijanje **pre** čitanja tela
rušilo je vezu dok klijent još šalje, pa je umesto `413` stizao transportni otkaz.
Dodato bounded pražnjenje tela (`MAX_DRAIN_BYTES`, čitanje-i-odbacivanje u komadima)
uz `Connection: close`.

### Popravljeno — Blok 2, ljudska kapija (T-13), 2026-07-30

`eval-viewer/viewer.html` i `SKILL.md`. Server (`generate_review.py`) **nije diran** —
`do_POST` upisuje payload doslovno i validira samo da je objekat sa ključem `reviews`,
pa nova polja prolaze bez ijedne serverske izmene.

- **N-05** (CRITICAL) — kapija se otvarala bez ijednog pročitanog izlaza. `visitedRuns`
  je postojao u memoriji strane i **bio odbačen pri POST-u**, iako komentar iznad
  petlje tvrdi suprotno („include ALL runs so the model can distinguish 'no feedback'
  from 'not reviewed'"). Posledica: Submit kliknut sekundu posle učitavanja proizvodi
  **bajt-identičan** `feedback.json` kao pažljivo pročitanih šest izlaza, a
  `SKILL.md` prazan feedback čita kao odobrenje. Jedina kontrola koja u ovom dizajnu
  razdvaja autora od recenzenta (`enterprise.md`: „Skill authors should not be their
  own reviewers") time postaje formalna.
- **N-06** (CRITICAL) — `closeDoneDialog` je zvao `saveCurrentFeedback()`, čiji
  reducirani payload vraća `status` na `in_progress` **i** gradi `reviews` samo iz
  nepraznih unosa. Klik na „OK" — jedino dugme u dijalogu koji piše „Your feedback has
  been saved" — brisao je celu završenu recenziju: `{"reviews": [], "status":
  "in_progress"}`. Režim otkaza na **podrazumevanom** putu, ne na rubnom.

Izmene:

1. **Jedan oblik payload-a za svaki upis** (`buildFeedbackPayload(status)`): uvek svi
   run-ovi, `viewed: true|false` po run-u, plus `reviewed_count` i `total_count`.
2. **Dugme prijavljuje šta se potpisuje** — `Submit All Reviews (2 of 3 reviewed)`.
   Dugme se i dalje **ne blokira**; blokada bi se izigrala klikanjem kroz run-ove.
3. **`closeDoneDialog` više ne obara `complete`.** Zadržana je originalna namera
   (pokupiti tekst otkucan između Submit i OK), ali se šalje **isti** kompletan
   payload.
4. **Auto-save ne može da obori `complete`** (`submittedComplete` zastavica). Ovo gate
   ne hvata — on čita fajl odmah posle OK — a izveštaj tu regresiju imenuje izričito:
   golo brisanje poziva iz `closeDoneDialog` dalo bi zeleno u kapiji, a recenzija bi
   pala 800 ms kasnije, na prvi sledeći taster.
5. **`SKILL.md` razlikuje tri stanja** umesto dva: neprazan feedback = konkretna
   primedba; prazan + `viewed: true` = odobreno; prazan + `viewed: false` = **nije
   pregledano, ne računaj kao prolaz, pitaj čoveka**. Uz obavezu da model prijavi kad
   je `reviewed_count < total_count`, i uputstvo da **odsutno** `viewed` polje znači
   *nepoznato*, a ne *odobreno*.

`viewer.html` i `SKILL.md` moraju ići **zajedno**: poslati `viewed` a ne izmeniti
instrukciju ne menja ništa u ponašanju i lako bi se pogrešno proglasilo popravkom.

**Napomena o kompatibilnosti:** oblik `feedback.json` je proširen. Stari čitači koji
gledaju samo `reviews[].feedback` i `status` rade nepromenjeno. Ali auto-save sada
upisuje **sve** run-ove (pre samo neprazne), pa kod koji je broj unosa tumačio kao
„broj komentara" mora gledati neprazan `feedback`.

Verifikacija pre primene, u pravom Chromium-u, šest snimaka fajla kroz jedan prolaz
(kucanje → Next → Submit → OK → **kucanje posle OK** → uređivanje ranijeg run-a):
pre popravke `complete`/3 unosa pada na `in_progress`/1 unos već na OK i tu ostaje;
posle popravke svih šest snimaka je `complete`, 3 unosa, `2/3 viewed`, sa run-om koji
čovek nikad nije otvorio trajno označenim kao `viewed: false`. Statični režim
(`--static`) proveren zasebno: isto ponašanje, isti broj konzolnih poruka, nijedan
`pageerror`.

**Dva lažno crvena testa u samoj kapiji, nađena pri pripremi ovog tiketa** (popravke su
u `regression/`, ne u skillu): `conftest.py` je pokretao tokenizator iz `tmp_path`-a —
Node razrešava `require` relativno na direktorijum skripta, ne na `cwd`, pa su oba N-08
testa padala na `MODULE_NOT_FOUND` i njihove tvrdnje se nikad nisu izvršile; i
`test_ok_ne_brise_recenziju` je koristio `text=OK`, što se u Playwright-u poklapa i sa
`<strong>Tokens</strong>` u skrivenom panelu, pa je klik isticao posle 30 s. Posle obe
popravke vektor prolaza je nepromenjen, a testovi padaju iz pravih razloga.

### Popravljeno — Blok 2, validacija postaje obavezna (T-11), 2026-07-30

`scripts/utils.py`, `scripts/run_eval.py`, `scripts/quick_validate.py`, `SKILL.md`, i
nov `evals/`. Tri nalaza u jednom tiketu jer su isti korak: validator prestaje da bude
opcion.

- **N-33** (MAJOR) — `run_eval.py` je gradio putanju temp command fajla iz `name` polja
  tuđeg `SKILL.md`-a, a `parse_skill_md` to polje ne validira. Izmereno:
  `name: ../../pwned` upisuje `myrepo/pwned-skill-<hex>.md`, **dva nivoa iznad**
  `.claude/commands/`.
  **Šire nego što je bilo zapisano:** apsolutno ime (`/tmp/x`) izlazi iz baze potpuno,
  jer apsolutna desna strana u `pathlib` poništava levu — izmereno,
  `apsolutno/upad-skill-fd51cff9.md`. Isti nevalidirani `name` stiže i do
  `Path.glob` u `cleanup_stale_command_files`, gde apsolutan obrazac diže
  `NotImplementedError`. Dva mesta, jedan uzrok.
  **Šta ovo nije:** ime fajla je uvek `<name>-skill-<8 hex>.md` sa nepredvidivim
  `uuid4` sufiksom, pa se **ne** može ciljati postojeći fajl. Provereno: postojeći
  fajl na ciljnoj putanji ostaje netaknut. Reč je o upisu novog fajla van cilja.
- **N-10** (MAJOR) — `quick_validate` nikad nije poredio `name` sa imenom
  direktorijuma, iako je to po Tier-1 spec-u normativna obaveza („Must match the parent
  directory name"). Referentni `skills-ref` to hvata, ovaj nije, a `package_skill.py:72`
  konsultuje **samo** ovaj — pa se neusklađen skill pakovao bez primedbe, i pošto ime
  `.skill` fajla dolazi iz imena direktorijuma, neusklađenost je prelazila u artefakt.
- **N-20** (MAJOR) — skill je nalagao korisnicima da pišu evale a sam nije imao nijedan,
  i nijednom nije pomenuo ni sopstveni validator ni `skills-ref`.

Izmene:

1. Nova `utils.validate_skill_name()` — **jedno mesto istine**, `^[a-z0-9-]{1,64}$`.
2. `run_eval.py` je zove na **dva** mesta: u `main()` odmah posle `parse_skill_md`
   (fail-loud, exit 1) i na ulazu u `run_single_query`, pre nego što se išta gradi.
   Nije redundancija: `run_single_query` se zove i direktno, a unutar
   `ProcessPoolExecutor`-a bi kasan izuzetak bio zabeležen kao „greška po upitu"
   umesto kao odbijanje celog prolaza.
3. `quick_validate.py` — provera `skill_path.resolve().name == name`, poruka po uzoru
   na `skills-ref`.
4. Nov `evals/` — `evals.json` (5 slučajeva, prag je 3), `trigger_queries.json`
   (20 upita: 10 should-trigger, 10 near-miss negativa), `README.md`.
5. `SKILL.md` — validacija je sada korak u toku autorstva, sa napomenom da se ponovi
   posle Description Optimization-a (ta putanja može vratiti opis preko 1024 znaka).

**Promena ponašanja:** `package_skill` od sada **odbija** skill čije se `name` ne
poklapa sa imenom direktorijuma. To je namera, ali će svaki skill u razvoju sa
razmimoilaženjem odjednom prestati da se pakuje. `SKILL.md:442-445` propisuje kopiranje
u `/tmp/skill-name/` pri uređivanju — direktorijum kopije mora nositi isto ime.

**`evals/` ne ulazi u `.skill` artefakt** — `package_skill.py` i `quick_validate.py`
isključuju `evals/` na korenu skilla. To je postojeće uzvodno ponašanje, ovde samo
zabeleženo; izmereno na spakovanom artefaktu (20 unosa, nijedan iz `evals/`).

Verifikacija pre primene: četiri oblika imena kroz stvarni kod, sa snimkom **u toku**
poziva (fajl se u `finally` briše, pa snimak posle poziva ništa ne pokazuje) —
`my-skill` prolazi i piše u cilj, `../../pwned`, apsolutna putanja i prazno ime dižu
`ValueError` **pre ijednog upisa**. Oba validatora nad neusklađenim fixture-om daju
exit 1 sa istom porukom; nad samim skillom oba daju exit 0. Predloženi `evals.json` je
pre ubacivanja proveren protiv `references/schemas.md:17-48` i **ispravljen na tri
mesta** — uklonjeni nedokumentovani ključevi `_comment` i `_why`, a `files: null`
(oblik iz N-38) zamenjen izostavljanjem opcionog polja. Iz `trigger_queries.json`
uklonjen je vodeći `{"_comment": …}` element, koji bi u `run_eval` digao `KeyError` na
`item["query"]`; oba teksta su premeštena u `evals/README.md`.

### Popravljeno — Blok 2, viewer više ne ubija tuđe procese (T-14c), 2026-07-30

`eval-viewer/generate_review.py`. Jedini izmenjen fajl u skillu.

- **N-13** (MAJOR) — `_kill_port` je pozivan **bezuslovno**, pre vezivanja socket-a, i
  slao `SIGTERM` svakom procesu koji sluša na traženom portu. Jedini kriterijum je bio
  poklapanje broja porta; nikakve provere da je to instanca ovog viewer-a. Nijedna
  poruka nije govorila da je nešto ubijeno — jedina linija na stderr je bila za slučaj
  kad `lsof` **ne postoji**.

Izmereno pre izmene: nezavisan proces koji sluša na `127.0.0.1:3117` biva ubijen
(`returncode=-15`) čim se viewer pokrene. Isto važi i za proces vezan na `0.0.0.0`,
dakle za mrežno dostupnu uslugu — ta tvrdnja iz izveštaja je posebno proverena, ne
prepisana.

**Destruktivni korak nikad nije bio potreban.** Kod već ima nedestruktivan put ka istom
cilju: `except OSError` pri `bind`-u uzima slobodan port i ispisuje URL sa tim portom.
Izmereno na kopiji u kojoj je poziv samo neutralisan — žrtva preživi, viewer objavi
`http://localhost:37733`. Kontrola sa praznim portom: ponašanje identično sa i bez
`_kill_port`. Zato je popravka **brisanje**, a ne dodavanje zaštite.

Uz funkciju odlaze i **četiri mrtva import-a** — `os`, `signal`, `subprocess` i `time`
su se koristili isključivo unutar nje (provereno `ast` obilaskom: nijedan uvezen naziv
u fajlu više nije neiskorišćen).

**Promena ponašanja:** kad je traženi port zauzet, tuđi proces sada preživi a viewer ode
na drugi port. `SKILL.md:242-247` pokreće viewer sa `> /dev/null 2>&1 &`, pa se URL
linija baca — jedini kanal koji stvarno radi je `webbrowser.open(url)`, koji već koristi
tačan port. Ako on zakaže (Cowork/headless), čovek ne vidi novi URL. Razmena je
ispravna — alternativa je ubijanje tuđeg procesa — ali je ovde zapisana. Vidljivost
izabranog porta je zaseban nalaz (**N-21**, observability), ne rešava se ovde.

**Nalaz je iz „ručne provere" prešao u gate.** `regression/README.md` je tvrdio da N-13
ne može biti pokriven jer bi test morao da veže žrtvu na **fiksni** port 3117, što je
rizik u CI-ju. Izmerom opovrgnuto: `_kill_port(port)` uzima `args.port`, ne konstantu,
pa test veže žrtvu na **efemerni** slobodan port i taj port prosledi kroz `--port` —
dodiruje isključivo proces koji je sam pokrenuo. Nov `test_n13_viewer_ne_ubija_tudji_proces`
je pre prihvatanja izmeren kao **crven na nepopravljenom v2** i zelen na popravljenom.
README je ispravljen na oba mesta.

### Popravljeno — Blok 2, „+ Add Query" fokusira pravi red (T-14d), 2026-07-30

`assets/eval_review.html`. Jedini izmenjen fajl.

- **N-15** (MAJOR) — `addRow` je fokusirao `inputs[inputs.length - 1]`, što je tačno
  samo za nesortiranu listu. Ali `render()` **sortira** po polarnosti, a nov red ima
  `should_trigger: true` pa ide u **prvu** grupu — dakle `inputs[length-1]` je uvek
  poslednji **negativ**. Sudar dve dobre odluke (sortiranje radi čitljivosti,
  autofokus radi UX-a), ne nemarnost.

Izmereno pre izmene, 2 pozitiva + 2 negativa, klik „+ Add Query" pa kucanje:

```
fokusiran indeks 4 od 5 | vrednost 'NEGATIV DVA near-miss'
indeks STVARNO novog praznog reda: 2
POSLE KUCANJA: [..., 'MOJ NOVI UPITNEGATIV DVA near-miss']
summary: 5 queries total: 3 should trigger, 2 should not trigger   ← tačan, i time uveravajući
IZVOZ: 4 upita (od 5 redova) — tiho odbačeno: 1
```

Posledica je dvostruka: near-miss negativ se korumpira ali **zadržava** labelu
`should_trigger: false` (a near-miss negativi su po
`agentskills.io/skill-creation/optimizing-descriptions` najvrednija klasa slučajeva), a
prazan red se pri izvozu tiho odbacuje.

Izmene:

1. `render()` dodaje `data-idx="${idx}"` na svaki `.query-input`; `addRow` fokusira
   **po identitetu** (`.query-input[data-idx="<novi>"]`), ne po poziciji, plus
   `scrollIntoView({block:'nearest'})` da nov red bude vidljiv u dugačkoj listi.
2. `exportEvalSet` više ne filtrira nečujno — prebrojava odbačene prazne redove i
   ispisuje ih u nov `<p id="export-note" role="status">`. Namerno **nije**
   `confirm()`/`alert()`: modalni dijalog blokira i browser automatizaciju i gate.

Regresija koju izveštaj izričito imenuje — da `deleteRow` i `updateTrigger` i dalje rade
nad ispravnim indeksima posle više dodavanja — proverena zasebno, van gate-a: tri
uzastopna `addRow` sa kucanjem, pa `updateTrigger` nad konkretnim redom, pa `deleteRow`,
pa još jedno dodavanje, pa brisanje preko UI dugmeta. Svaka operacija pogađa tačan red.
Na nepopravljenom kodu ista sonda ne prođe ni prvi korak — sva tri teksta se slepe u
jedan negativ (`'NOVI CNOVI BNOVI AN2'`), što je dodatan dokaz težine nalaza.

**Jedan kandidat proverom odbačen:** `updateQuery` je `onchange`, a
`updateTrigger`/`deleteRow` odmah zovu `render()` koji rekonstruiše DOM iz `evalItems` —
sumnja je bila da se necommit-ovano kucanje gubi. Izmereno: ne gubi se, jer klik na
toggle prvo skida fokus i `change` se okine pre `render()`. Bez izmene.

`scripts/render_eval_review.py` nije diran — izmereno da supstituiše samo tri
placeholder-a, nijedan u izmenjenom delu.

### Popravljeno — Blok 2, jednosmerna supstitucija placeholder-a (T-14e), 2026-07-30

`scripts/render_eval_review.py`. Jedini izmenjen fajl. **Poslednji tiket odobrenog obima.**

- **N-34** (MINOR) — `render()` je radio tri uzastopna `.replace()` u redosledu
  ime → opis → eval podaci, pa je **svaka kasnija supstitucija skenirala tekst koji je
  ranija ubacila**. `html.escape()` escape-uje `&`, `<`, `>` i navodnike, ali **ne** `_`,
  pa placeholder token preživi escaping netaknut i uđe u sledeći `.replace()`.

**Zapisani obim je bio uži od stvarnog.** Umesto provere jednog primera, obiđena je cela
matrica kombinacija tri tokena kroz stvarni kod. Procuruju **tri para**, ne jedan:

| Slučaj | Pre popravke | Status |
|---|---|---|
| opis sadrži `__EVAL_DATA_PLACEHOLDER__` | opis postaje eval JSON | zapisan kao N-34 |
| ime sadrži `__EVAL_DATA_PLACEHOLDER__` | ime postaje eval JSON | **nov** |
| ime sadrži `__SKILL_DESCRIPTION_PLACEHOLDER__` | ime postaje opis | **nov** |
| opis sadrži `__SKILL_NAME_PLACEHOLDER__` | netaknuto | bezbedno |
| opis sadrži `__SKILL_DESCRIPTION_PLACEHOLDER__` | netaknuto | bezbedno |

Poslednja dva su bezbedna jer `str.replace` u jednom pozivu zameni sve pojave i **ne
skenira ponovo** ono što je ubacio. Ranjivi su tačno oni parovi u kojima ranije ubačen
tekst sadrži token koji tek dolazi na red. Dosežnost druga dva: `render_eval_review.py`
je zaseban ulaz sa sopstvenim `--skill-name` i **ne uvozi nikakvu validaciju** —
`validate_skill_name` iz T-11 živi u `run_eval.py` i `quick_validate.py`, a `SKILL.md:383`
nalaže modelu da skriptu pozove direktno.

Popravka: **jedan prolaz** (`re.sub` sa alternacijom preko sva tri tokena) umesto tri
uzastopna `.replace()`. Ubačen tekst više nikad nije kandidat za dalju zamenu, pa sva tri
para nestaju odjednom i redosled prestaje da bude semantički bitan.

Zamena ide kroz **callable**, ne kroz string: u `re.sub` sa string zamenom `\` i `\g`
imaju posebno značenje. Izmereno — `re.sub("__X__", r"C:\temp\g<1>", …)` diže
`error: invalid group reference 1`, dok `lambda m: vrednost` vraća tekst doslovno.

Verifikacija pre primene: za ulaz **bez** placeholder tokena izlaz je **bajt-identičan**
starom u svih sedam slučajeva — čist ulaz, navodnici + `<` + `>` + `&`, obrnuta kosa crta
sa `\g<1>` i `\1`, doslovan `</script>`, srpski + emoji, prazan opis, ime od 64 znaka.
Da se ijedan razlikovao, promenio bih escaping umesto redosleda.

### Dodato — Apache-2.0 §4(b) napomene i registarsko polje `Owner` (T-18), 2026-07-30

Dve odluke koje su čekale vlasnika forka od početka prolaza. Vlasnik ih je doneo
2026-07-30: atribucija `buky <webdevcom01@gmail.com>`, zaglavlje u svim izmenjenim
fajlovima, i kratka atribucija i u novim.

**Obim je izmeren, ne prepisan.** Upstream `b29e7cf6` je dopremljen i upoređen fajl po
fajl (upstream checksum `f6e18a25…` se poklapa sa zapisom u `PLAN.md` §0):

| Status | Broj |
|---|---|
| izmenjenih | **15** |
| bajt-identičnih sa upstream-om | 3 — `LICENSE.txt`, `scripts/__init__.py`, `scripts/package_skill.py` |
| novih | 5 |
| obrisanih | 0 |

Audit je beležio **10** izmenjenih; naš rad je dodao još pet. Na tri identična fajla
napomena **ne ide** — nisu izmenjeni, a `LICENSE.txt` mora ostati bajt-identičan
upstream-u (N-32/T-01), što je posle izmene i provereno `cmp`-om.

- **Apache-2.0 §4(b)** (`LICENSE.txt:98-99`): „You must cause any modified files to
  carry prominent notices stating that You changed the files." Zaglavlje sada nosi
  **17 tekstualnih fajlova** (14 izmenjenih + 3 nova), a `SKILL.md` napomenu nosi u
  frontmatter-u kao `metadata.modified`.
- **`Owner`** — peto registarsko polje iz `platform.claude.com/…/enterprise`
  („Purpose · Owner · Version · Dependencies · Evaluation status"). Sada
  `metadata.owner`. Time su četiri od pet polja popunjena: `Purpose` (opis),
  `Owner` (novo), `Version` (T-02), `Evaluation status` (`evals/`, T-11).
  **`Dependencies` ostaje otvoren** — to je N-25 (`compatibility`), Blok 3.

**Zašto `SKILL.md` odstupa od forme.** Telo je na **497/500** linija; komentar u telu bi
ostavio jednu liniju rezerve za ceo Blok 3. Frontmatter je prva stvar u fajlu, dakle i
dalje vidljivo mesto, i uz to mašinski čitljiv. Provereno da `metadata.owner` i
`metadata.modified` prolaze `quick_validate` **i** `skills-ref validate` (oba exit 0),
da naivni parser `utils.parse_skill_md` ostaje nepromenjen, i da telo ostaje na 497.

**Dva JSON fajla** (`evals/evals.json`, `evals/trigger_queries.json`) ne mogu nositi
komentar — JSON ga nema, a dodavanje ključa bi prekršilo shemu iz `references/schemas.md`
koju smo tek u T-11 počeli da poštujemo. Pokriveni su centralno kroz `evals/README.md`.

Verifikacija posle izmene: `LICENSE.txt` bajt-identičan upstream-u; svih 11 `.py` fajlova
zadržalo `__doc__` (komentar nije naredba, pa docstring ostaje prva naredba) i isti
`--help` status kao pre — uključujući dva koja i dalje padaju, što je N-17 i nije
regresija; obe HTML površine se učitavaju u Chromium-u u `CSS1Compat` režimu (komentar je
**posle** `<!DOCTYPE html>`, jer bi pre njega uveo quirks mode) bez ijednog `pageerror`.

**Ispravka moje aritmetike:** predikcija je govorila o 18 tekstualnih zaglavlja; tačan
broj je **17**, jer su od pet novih fajlova dva JSON. Zapisano jer se predikcija ne
prepravlja retroaktivno.

### Popravljeno — validator i učitavanje JSON-a (T-19), 2026-07-30

Sedam fajlova u `scripts/`. Oba nalaza dolaze iz **enumeracije prolaza 2**, ne iz
čitanja izveštaja.

- **N-44** (MAJOR) — `compatibility: null` je prolazio kao validan. `.get('compatibility','')`
  vraća `None` kad ključ postoji sa vrednošću `null`, pa je `if compatibility:` bilo
  netačno i provera `isinstance` se **preskakala u celini** — za razliku od `name` i
  `description`, gde stoji bezuslovno. Izmereno oba validatora: bundle-ovani „Skill is
  valid!" exit 0, `skills-ref validate` „Field 'compatibility' must be a string" exit 1.
  Isti obrazac kao **N-10**, a `package_skill.py:72` konsultuje samo bundle-ovani.
  Popravka: provera tipa je sada bezuslovna.
- **N-45** (MINOR) — pet skripti je zvalo `json.loads` golo, pa je nevalidan ili
  nepostojeći fajl davao **sirov traceback** na prvom što skripta uradi.

**Obim N-44 je proveren i NE širi se.** Null-zamka je probana na svakom frontmatter
polju kroz oba validatora; razilaze se **samo** na `compatibility`. *(Zapaženo i
zabeleženo, ne dirano: za `description: null` bundle-ovani je **stroži** od
referentnog — neslaganje u obrnutom smeru.)*

**Obim N-45 JESTE širi — po četvrti put.** Zapisano je bilo
`render_eval_review.py:95,97`. `ast` obilazak svih devet skripti dao je **osam
nepokrivenih mesta u pet skripti**: `render_eval_review.py` (2), `run_eval.py` (1),
`run_loop.py` (1), `generate_report.py` (2), `improve_description.py` (2). Svih pet
izmereno pojedinačno — svaka je davala traceback.

Uzor je već postojao u istom repou: `aggregate_benchmark.py` (3 mesta) i
`generate_review.py` (6) svoje pozive **imaju** u `try/except (JSONDecodeError, OSError)`.
Kod je dakle protivrečio sopstvenoj konvenciji. Uveden je jedan
`utils.load_json_arg(izvor, *, what)` — isti oblik kao `validate_skill_name` (T-11) i
`_number` (T-08) — i pozvan na svih osam mesta. `eval-viewer/generate_review.py` se
**ne dira**: već je zaštićen i nije u paketu `scripts`.

Poruka sada imenuje **šta** se učitavalo i **odakle**, plus red i kolonu za JSON grešku:

```
Error: eval set from '/put/do/los.json' is not valid JSON (line 1, column 3): …
Error: cannot read eval data from '/put/do/nema.json': No such file or directory
```

Pomoćnik **namerno i dalje izlazi sa 1**: distinktni kodovi po tipu otkaza su ugovor
prema agentu kroz svih devet skripti (**N-17**), a uvođenje u pet od devet zamenilo bi
jednu nedoslednost drugom.

Uz to je uklonjen `import json` iz `generate_report.py`, koji je posle izmene ostao mrtav
(provereno `ast` obilaskom — nijedan uvezen naziv u sedam izmenjenih fajlova nije
neiskorišćen).

Verifikacija pre primene: za **ispravan** ulaz `render_eval_review` i `generate_report`
daju **bajt-identičan** izlaz kao pre, i za putanju i za `-` (stdin) — četiri sha256
poklapanja. `--help` status svih devet skripti nepromenjen, uključujući dva koja i dalje
padaju po N-17.

### Popravljeno — Blok 3, progresivno otkrivanje (T-04), 2026-07-30

`SKILL.md` plus tri nova fajla u `references/`. **Prvo restrukturiranje** u ovom prolazu.

- **N-08** (MAJOR) — telo je imalo **7.597 tokena** naspram preporuke od 5.000, a Claude
  Code posle auto-kompakcije re-prilaže **samo prvih 5.000**. Granica je padala između
  `Step 1: Generate trigger eval queries` (4.957) i `Step 2: Review with user` (5.420).
  Tiho se gubilo: ceo Description Optimization podtok, oba grananja po okruženju, i —
  na tokenu **6.924** — ALL-CAPS instrukcija `GENERATE THE EVAL VIEWER`. Autor ju je
  napisao velikim slovima **zato što ju je model preskakao**, a bila je tačno u delu
  koji nestaje u dugačkoj sesiji, kakva je za ovaj skill tipična.

**Preporuka iz izveštaja je bila nedovoljna, izmereno.** Predlagala je premeštanje tri
sekcije = 2.412 tokena; telo bi ostalo na **5.345**, i dalje preko. Izmerene varijante:

| Varijanta | Telo posle | Tokena | |
|---|---:|---:|---|
| A — tri sekcije iz preporuke | 374 | 5.345 | ✘ |
| B — A + Blind + Report/Commit primeri | 350 | 5.122 | ✘ |
| **C — A + `Skill Writing Guide`** (izabrano) | 282 | 4.524 | ✔ |
| D — C bez Cowork | 290 | 4.778 | ✔ |

Premešteno **doslovno** (bajt-identično, dokazano poređenjem bloka sa ciljnim fajlom):
`Skill Writing Guide` → `references/skill-writing-guide.md`; `Description Optimization` →
`references/description-optimization.md`; `Claude.ai-specific` i `Cowork-Specific` →
`references/environments.md`. Izmena je isključivo **lokacija**.

**Nosiva instrukcija nije premeštena nego podignuta.** Jedina pojava
`GENERATE THE EVAL VIEWER` bila je u Cowork sekciji; premeštanje bi je uklonilo iz tela
u celini i oborilo `test_nosive_instrukcije_prezivljavaju_kompakciju` — ne zato što je
predaleko, nego zato što je nema. Umesto slabljenja testa, instrukcija je podignuta u
`Step 4`, na **token 2.665**.

Rezultat: telo **303 linije / 4.698 tokena** (limiti 500 / 5.000). Sva tri pokazivača na
premešten sadržaj su unutar prozora — 1.231, 4.273 i 4.360.

**Tri testa bi se lažno prevrnula — uhvaćeno i zatvoreno.** Progresivno otkrivanje
menja šta znači „ono što skill uči": do sada telo, od sada telo **+ `references/`**.
Testovi koji gledaju samo telo prevrnu se u zeleno čim se sporni tekst premesti, iako
defekt stoji. Izmereno na tri: `test_metadata_je_u_tokenima_ne_recima` i
`test_toc_prag_je_100_linija` (N-18), i `test_bez_all_caps_direktive_u_primeru` (N-28) —
`~100 words`, `>300 lines` i `ALWAYS use this exact template` su svi preživeli u
`references/skill-writing-guide.md`. Umesto pojedinačne provere, **sistematski** su
nabrojani svi testovi koji čitaju samo telo i četiri prevedena na novi pomoćnik
`_sve_sto_skill_uci()`. Posle ispravke polaritet je **identičan na v2 i na
popravljenoj kopiji**.

**Dva nova testa** koja restrukturiranje čini merljivim: `test_nijedna_referenca_ne_visi`
(kontrola — pokazivač mora razrešavati na postojeći fajl; takav test **nije postojao**,
provereno `grep`-om) i `test_pokazivaci_na_premesten_sadrzaj_su_u_prozoru`, koji prvo
tvrdi da pokazivači **postoje** pa tek onda da su u prvih 5.000 tokena — da ne bi prošao
prazno.

**Razmena koju ovaj tiket uvodi, zapisana namerno:** sadržaj je do sada bio *prisutan* u
kratkoj sesiji i *odsečen* u dugoj; od sada je *odsutan dok ga model ne dohvati* — u obe.
Dobitak postoji samo dok su pokazivači imperativni i u prozoru, što gate sada meri.

### Popravljeno — Blok 3, ono čemu skill uči i šta deklariše (T-05), 2026-07-31

Tri fajla: `SKILL.md` (samo frontmatter), `references/skill-writing-guide.md`,
`references/schemas.md`. **Nijedna izmena ne troši budžet tela** — telo je ostalo
bajt-identično, **303 linije / 4.698 tokena**, rezerva 197 linija / 302 tokena netaknuta.
To je direktna posledica T-04: nastavni sadržaj sada živi u `references/`, koji ne ulazi
u prozor od 5.000 tokena.

- **N-18** (MAJOR) — skill je učio **tri pogrešne granice**. `~100 words` za nivo 1, dok
  spec meri u **tokenima**; `>300 lines` kao prag za TOC, dok norma kaže **100**; i nigde
  limit od **5.000 tokena**, pa je autor koji prati samo linijski limit prekoračivao ga
  ne znajući. Dodata je i eksplicitna napomena da su dva limita **konjunktivna** (500
  linija *i* 5.000 tokena) i da je token-limit onaj koji nijedan validator ne proverava,
  uz razlog zašto to boli baš u dugačkoj sesiji.
- **N-18, glas** — dva Tier-2 izvora protivreče: `platform.claude.com` traži **treće
  lice**, `agentskills.io` traži **imperativ**. Skill je do sada birao stranu prećutno.
  Sada objavljuje neslaganje, oba citata doslovno, i navodi na čemu se izvori **slažu**
  (šta + kada; bez prvog i drugog lica), plus napomenu da nijedan validator u ovom
  skillu ne proverava glas. Norma koja se krši nije „izaberi treće lice" nego obaveza
  objavljivanja neizvesnosti u alatu koji uči druge.
- **N-28** (MINOR) — `ALWAYS use this exact template:` u primeru koji uči korisnike,
  protivno sopstvenom savetu o „yellow flag" formulacijama; zamenjeno vendor-ovom
  formulacijom `Use this template, adapting sections as needed:`. I drugi anti-pattern:
  `SKILL.md` kaže **`assertions`**, a JSON polje, `agents/*.md` i skripte kažu
  **`expectations`**. Mapiranje sada postoji u `references/schemas.md`, sa izmerenom
  posledicom: `assertions` ne pada na validaciji, nego se čita kao **prazna lista**
  (`scripts/aggregate_benchmark.py:398`, `grading.get("expectations") or []`) i run tiho
  oceni nula očekivanja.
- **N-30** (MINOR) — `run_summary` ugovor o **redosledu ključeva** nije bio nigde zapisan,
  a viewer se na njega oslanja: `eval-viewer/viewer.html:1264-1266` uzima ključeve
  redom umetanja i prvi šalje u kolonu A, drugi u kolonu B. `SKILL.md` dopušta ručno
  pisan `benchmark.json`; obrnut redosled zamenjuje kolone i **obrće znak svake delte**,
  bez poruke i bez greške validacije. `schemas.md` sada nosi ugovor sa citatom koda.
- **N-25** (MINOR) — dodato `compatibility` polje (277 znakova, limit 500).

**Lista zavisnosti je izmerena iz koda, ne prepisana iz izveštaja.** Izveštaj navodi
„claude CLI, lsof, browser, dva CDN-a". Mereno:

| Zavisnost | Stanje |
|---|---|
| `claude` CLI | ✔ `run_eval.py:180`, `improve_description.py:28` |
| **`lsof`** | ✘ **0 pojava u kodu** — **T-14c** ga je uklonio sa `_kill_port`. Jedina pojava u celom stablu je istorijska proza u ovom CHANGELOG-u |
| `webbrowser` + display | ✔ `run_loop.py:371`, `generate_review.py:552` |
| CDN | ✔ **tri**, ne dva: `cdn.sheetjs.com`, `fonts.googleapis.com`, `fonts.gstatic.com` |
| `PyYAML` | ✔ **jedini** paket van stdlib (`quick_validate.py:10`) — izveštaj ga ne pominje |

Prepisivanje liste iz izveštaja deklarisalo bi zavisnost koju smo sami uklonili i
propustilo jedinu pravu instalacionu. Razlikovan je i način otkaza: fontovi imaju
fallback (`'Lora', Georgia, serif`), a bez `cdn.sheetjs.com` pregled `.xlsx` priloga
ispisuje grešku u samom okviru (`viewer.html` `catch` na `renderXlsx`) — nije isto i
nije opisano isto. U `compatibility` je uneta i deklaracija da skill **izvršava shell
komande i piše van svog direktorijuma**, kako izveštaj preporučuje uz N-31; to je
jedina stavka koja izlazi iz slova predikcije i ovde je zapisana kao takva.

**Izmereno, a ne pretpostavljeno — budžet metapodataka.** Predikcija je tražila proveru
da li `compatibility` ulazi u deljeni listing budžet. Merenje: `name` + `description`
su **već 195 tokena** (cl100k) naspram spec-ove smernice od „~100 tokena" za nivo 1.
Da li `compatibility` ulazi u taj budžet **nije bilo moguće izmeriti** iz ovog okruženja
— zato je polje namerno kratko (64 tokena) umesto prve, iscrpne verzije od 461 znaka /
101 tokena. Puna proza o prerekvizitima nije dodata u `references/` da se ne bi izašlo
iz obima tiketa; zabeleženo kao kandidat.

**Namerno odloženo:** izveštaj uz N-18 preporučuje i istu napomenu o glasu u prompt
stringu `improve_description.py`. To je jedina od pet stavki koja **menja izlaze**
optimizatora, pa traži eval pre/posle — nije rađena ovde.

**Gate: 16 / 104 od 120**, 8 preokrenuto, **0 regresija** (`comm` nad sortiranim
listama padova). Prvi tiket u ovom prolazu u kome se izmereni rezultat poklopio sa
predikcijom **bez ijednog odstupanja**. Provera lažnog zelenila (pouka iz T-04)
ponovljena: sva tri negativna stringa (`~100 words`, `>300 lines`,
`ALWAYS use this exact template`) su **nula puta** u celom stablu, ne samo u telu.

### Nasleđeno stanje i napredak gate-a

| Tačka | Gate |
|---|---|
| Nasleđena osnova forka (pre Bloka 0) | 63 pada / 12 prolazi (od 75) |
| Posle Bloka 0 (T-01, T-02, T-03) | 73 / 27 (od 100) |
| Posle T-08 + T-16 (N-01, N-38, N-39, N-41) | 61 / 39 (od 100) |
| Posle T-09 (N-04) | 59 / 44 (od 103) |
| Posle T-07 (N-07, N-09) | 54 / 49 (od 103) |
| Posle T-15 (N-35, N-36) | 50 / 53 (od 103) |
| Posle T-10 (N-14) | 49 / 55 (od 104) |
| Posle T-17 + T-14a + T-14b (N-40, N-11, N-12) — Blok 1 završen | 44 / 60 (od 104) |
| Posle T-06 (N-02 a–f) | 36 / 69 (od 105) |
| Posle T-12 (N-03) | 35 / 70 (od 105) |
| Posle T-13 (N-05, N-06) — svih 7 CRITICAL zatvoreno | 33 / 72 (od 105) |
| Posle T-11 (N-33, N-10, N-20) | 29 / 76 (od 105) |
| Posle T-14c (N-13) | 29 / 77 (od 106) — nov test, 0 prevrnuto |
| Posle T-14d (N-15) | 27 / 80 (od 107) |
| Posle T-14e (N-34) — odobreni obim ZAVRŠEN | 26 / 83 (od 109) |
| Posle T-18 (§4(b) + Owner) | 26 / 85 (od 111) — dva nova testa, 0 prevrnuto |
| Posle enumeracije prolaza 2 | 28 / 85 (od 113) — +2 pada su nova nalaza N-44, N-45 |
| Posle T-19 (N-44, N-45) | 26 / 92 (od 118) |
| Posle T-04 (N-08) — Blok 3 počeo | 24 / 96 (od 120) |
| **Posle T-05 (N-18, N-25, N-28, N-30)** | **16 / 104 (od 120)** |

**Blok 1 (merni sloj) je završen, a sa T-13 su zatvorena i svih sedam CRITICAL nalaza**
(N-01, N-02 a–f, N-03, N-04, N-05, N-06, N-07). **Sa T-14e je završen prvobitno odobreni
obim** — Blok 0, Blok 1 i Blok 2 — a T-18, T-19, T-04 i T-05 su ušli u Blok 3.

Brojanje je izvedeno iz **§0a ERRATA** izveštaja, gde je lista otvorenih nalaza
programski utvrđena, a ne procenjena ovde. Tamo je stanje bilo 25 zatvoreno / **17
otvoreno** od 42 numerisana. Od tada: T-19 zatvara N-44 i N-45, T-04 zatvara N-08, T-05
zatvara N-18, N-25, N-28 i N-30. Dakle **32 zatvoreno / 10 otvoreno**, i dalje **nijedan
CRITICAL**. (Raniji broj „27 zatvoreno" je bio pogrešan — mešao je nalaze sa ne-nalaznim
radnim stavkama; ispravka je u istoj §0a.)

Otvoreno: **N-16, N-17, N-19, N-21, N-23, N-24, N-26, N-27, N-29, N-31.**

> **ISPRAVKA 2026-07-31:** brojanje iznad je bilo **nepotpuno**. N-42 i N-43 nose brojeve
> nalaza a nisu bili ubrojani ni u zatvorene ni u otvorene; uz njih su 2026-07-31 dodati
> **N-46** i **N-47**. Tačno stanje: **46 numerisanih, 32 zatvorena, 14 otvorenih**,
> nijedan CRITICAL. Otvorenima se dodaju **N-42, N-43, N-46, N-47**.

### Popravljeno — `package_skill.py` i `quick_validate.py` sada imaju `--help` i distinktne exit kodove (T-33, N-17)

`scripts/package_skill.py`, `scripts/quick_validate.py`, i (posledično)
`regression/test_dokument_i_governance.py`.

Obe skripte su čitale `sys.argv` direktno, bez `argparse`, pa je `--help` završavao
kao ime direktorijuma: `package_skill.py --help` je pokušao da upakuje direktorijum
`--help` (exit 1, „Skill folder not found"), a `quick_validate.py --help` je isto
tražio `SKILL.md` u direktorijumu `--help` (exit 1, „SKILL.md not found"). Izmereno
direktno nad svih **9** skripti iz `SKRIPTE` (`test_dokument_i_governance.py:23-28`),
ne pretpostavljeno: ostalih sedam (`run_eval`, `run_loop`, `improve_description`,
`aggregate_benchmark`, `generate_report`, `render_eval_review`,
`eval-viewer/generate_review.py`) već su koristile `argparse` i ispravno odgovarale
na `--help` sa exit 0 — obrazac je preuzet od njih, ne izmišljen.

**`package_skill.py`** — usage tekst u docstring-u i u `main()` je reklamirao
`python utils/package_skill.py`, putanju koja ne postoji (fajl je uvek bio u
`scripts/`, nikad u `utils/`). Zamenjeno tačnom invokacijom
(`python3 -B -m scripts.package_skill ...`, isti obrazac kao `SKILL.md:78` za
`quick_validate`). Fajl time prestaje da bude bajt-identičan upstream-u — bio je
jedan od tri u `UPSTREAM_IDENTICNI` uz `LICENSE.txt` i `scripts/__init__.py` u
testu za Apache-2.0 §4(b) — pa dobija napomenu istog oblika kao ostale izmenjene
skripte, i uklonjen je iz tog skupa u testu da ne postane nov, neplaniran pad.

**`quick_validate.py`** — dodati distinktni exit kodovi (`EXIT_OK=0`,
`EXIT_INVALID=1`, `EXIT_NOT_FOUND=3`; kod 2 namerno preskočen jer ga `argparse`
sam koristi za sopstvene usage greške — isti razmak kao `EXIT_NO_DATA=3` u
`aggregate_benchmark.py`, T-08/T-16). Ranije je i nepostojeća putanja i nevalidan
frontmatter davalo isti exit 1, pa agent nije mogao razlikovati „nije nađeno" od
„nevalidno" bez parsiranja stdout teksta.

Uz N-17 popravljen je i `package.json`: `npm install gpt-tokenizer` bez
`package.json` u ovom radnom folderu instalira na pogrešno mesto (npm se penje
naviše do najbližeg projekta), pa je `test_tokenizator_je_dostupan` i sva tri
`TestN08Limiti` ostajala neizmerena zbog okruženja, ne zbog skilla.

Izmereno pre: **12** crvenih (4 zbog okruženja — `gpt-tokenizer` nedostupan, N-08
neizmeren; 4× N-17; 4× N-16, svesno odbačeno). Izmereno posle: **4** crvena, sva
`TestN16Pristupacnost`, nepromenjena. `comm` nad sortiranim `FAILED` listama
pre/posle: tačno 8 nestalo, **0 novih**, 4 identična u oba.

### Popravljeno — dokumentovana komanda više ne poništava proveru integriteta (T-32, N-27)

`SKILL.md`, `references/description-optimization.md`.

`python -m scripts.X` zahteva da je radni direktorijum **sam skill** — pa Python upisuje
`__pycache__` **unutar** njega. Izmereno nad čistom kopijom, jedan poziv:

```
pre  : 0 __pycache__
posle: scripts/__pycache__/quick_validate.cpython-311.pyc
       scripts/__pycache__/__init__.cpython-311.pyc
```

**Posledica nije kozmetička.** Checksum se pomera sa `75947904…` na `27430fec…` — dakle
tačno ona provera koju `PROCITAJ-ME.md` propisuje za utvrđivanje da je isporučeno stanje
netaknuto. Posle jednog pokretanja validatora više se ne može dokazati da se ništa nije
promenilo, iako se stvarno nije.

**Obim: 5 mesta, dva oblika.** `python -m scripts.X` na pet mesta i jedan direktan poziv
`generate_review.py` (koji piše `__pycache__` pored sebe, dakle opet u skillu). Uslov da
se pokreće iz direktorijuma skilla bio je zapisan **na jednom mestu od pet**.

> Nalaz je govorio o „tri oblika"; izmereno su **dva oblika i pet mesta**. Prvi put da je
> broj u zapisu bio *veći* od izmerenog — vredi zabeležiti i taj smer.

**Popravka: `-B` uz svaki poziv.** Obe varijante su izmerene i obe daju 0 `.pyc`
(`python3 -B -m …` i `PYTHONDONTWRITEBYTECODE=1 …`); izabran je `-B` jer je deo same
komande, pa se kopira zajedno s njom i ne gubi pri prenošenju u drugi terminal.

**Rešenje u kodu ne postoji i to je zapisano:** `sys.dont_write_bytecode = True` na vrhu
skripte je **prekasno** — `scripts/__init__.py` i sam modul se kompajliraju pre nego što
ijedan red korisničkog koda krene. Popravka mora biti u komandi.

Uz `-B`, svaki `-m` poziv sada nosi i **odakle se pokreće** — ranije rečeno jednom od pet
puta, a bez toga `scripts` paket nije na `sys.path`.

**Test je bihevioralan namerno:** čita komandu iz same dokumentacije, izvršava je nad
kopijom skilla i poredi checksum pre i posle. Provera oblika (`'-B' in tekst`) prošla bi i
da `-B` stoji na pogrešnom mestu u komandnoj liniji.

**Telo `SKILL.md`-a je bilo na 4999 od 5000 tokena** — jedan token rezerve. Da bi stalo
objašnjenje o `-B` i radnom direktorijumu, skraćen je jedan pasus u „Communicating with
the user" koji je istu pretpostavku iznosio dvaput. Posle izmene: **4981**.

### Popravljeno — čitljivost: kontrast na tri ekrana i osvežavanje koje se može isključiti (T-31, N-16 delimično)

`eval-viewer/viewer.html`, `assets/eval_review.html`, `scripts/generate_report.py`,
`scripts/run_loop.py`.

**Prvo je popravljen test, pa tek onda boje.** Postojeći test kontrasta nosio je komentar
„vrednosti se čitaju iz CSS-a" a imao je **doslovne literale**. Da je paleta promenjena,
tih šest testova bi i dalje merilo **stare** brojeve i prijavljivalo isti rezultat —
popravka bi izgledala kao da radi a ne bi dokazivala ništa. Sada se parovi izvode
parsiranjem `:root` bloka, uz kontrolni test koji pada ako `:root` nestane ili se
promenljive preimenuju (inače bi se tiho merio prazan skup i sve bi „prošlo").

**Obim je bio 75 pojava boja u tri fajla, ne šest parova.** Samo `viewer.html` ima `:root`;
druga dva ekrana istu paletu nose kao **literale** (`#b0aea5` 9 puta ukupno, `#e8e6dc` 8,
`#c44` 7). Izmena samo u `:root` popravila bi **jedan ekran od tri** — zato uz boje ide i
test koji zabranjuje stare vrednosti u sva tri fajla.

Izmereno je da pada **jedanaest** situacija, a test je proveravao **šest**. Van testa su
bili: `#f57f17` (2,51), `#d97706` na svojoj pozadini (2,86), `#6a9bcc` kao tekst i kao
podloga belog teksta (2,93) i **`#b8860b` za `.inconclusive` (3,25)** — dakle baš stanje
koje je N-46 uveden da učini vidljivim, prikazano najslabije vidljivom bojom.

| | Pre | Posle | Najgori odnos posle |
|---|---|---|---|
| `--text-muted` | `#b0aea5` (2,22) | `#716e63` | 4,52 |
| `--accent` | `#d97757` (3,12) | `#c0502c` | 4,50 (belo na njemu 4,75) |
| `--green` | `#788c5d` (3,24) | `#63734d` | 4,52 |
| `--red` | `#c44` (4,04) | `#c73636` | 4,51 |
| plava | `#6a9bcc` (2,93) | `#3b74ac` | 4,51 (belo na njemu 4,91) |
| `.inconclusive` | `#b8860b` (3,25) | `#956c09` | 4,50 |
| `#f57f17` / `#d97706` | 2,51 / 2,86 | `#b65908` / `#a75c05` | 4,51 / 4,52 |

**Granica je razdvojena od površine, i to je bila prava odluka a ne kozmetika.** `#e8e6dc`
se koristio **i kao granica i kao pozadina** (traka zaglavlja u `eval_review.html`, hover
podloga u vieweru). Bezuslovna zamena bi trake zaglavlja pretvorila u sive blokove. Zato:
`--border: #969590` (3,00:1, vidljiva ivica) i nov `--surface-alt: #e8e6dc` za pozadine,
gde ništa ne krši — tamni tekst na njoj ima 14,7:1.

Ton granice je odabran **nisko zasićen namerno**: algoritamsko tamnjenje uz zadržan topao
ton daje `#9e956b`, dakle **maslinasto zelenu** ivicu. Ovo je jedina odluka u tiketu doneta
po izgledu, a ne po broju, i zato je zapisana odvojeno.

**Osvežavanje je isključivo, a nije dobijeno kompromisom sa bezbednošću.** Bio je tvrd
`<meta http-equiv="refresh" content="5">` na **dva** mesta — u izveštaju i na
„Starting optimization loop…" placeholder strani — bez načina da se zaustavi; strana se
reloaduje pod čitaocem i odnese poziciju usred poređenja (WCAG 2.2.1).

Dugme u samoj strani **nije moguće**: izveštaj nosi `script-src 'none'`, što je stvarna
odbrana za stranu koja prikazuje vrednosti iz spoljnog JSON-a. Kupiti checkbox
popuštanjem `script-src`-a značilo bi zameniti odbranu koja radi za udobnost. Kontrola
zato živi pri generisanju: nov `--report-refresh SECONDS`, **podrazumevano ugašen**.

**Test osvežavanja je zamenjen jačim.** Stari je zabranjivao da se niz `http-equiv="refresh"`
**pojavi u izvoru** — provera oblika, koja bi zabranila i osvežavanje koje je korisnik
izričito tražio. Novi meri **ponašanje**: podrazumevano nema osvežavanja, a sa zadatim
periodom osvežava se tačno njime.

**Ostaju svesno odbačene četiri stavke** — pristupačno ime checkbox-a, dosežnost
collapsible odeljaka tastaturom i dva `lang` atributa. Odbačene su odlukom od 2026-08-01
(skill je za ličnu upotrebu) i vraćaju se u obavezu ako skill ode nekom drugom ili ako se
rezultati počnu pregledati tastaturom.

### Popravljeno — otkaz se više ne manifestuje kao odsustvo (T-30, N-21, svih pet delova)

`SKILL.md`, `scripts/run_loop.py`, `scripts/run_eval.py`.

Pet zasebnih stavki čiji je **zbir** sistem u kome se otkaz vidi kao **odsustvo**, a
odsustvo se ne razlikuje od uspeha:

**(a) Ceo dijagnostički kanal viewera išao je u `/dev/null`.** `generate_review.py` svoje
jedine dve fatalne poruke (`is not a directory`, `No runs found in …`) piše na `stderr` i
izlazi sa 1 — obe su završavale u ništavilu. Sada `> <workspace>/viewer.log 2>&1`, uz
nalog da se log pročita kad viewer ne odgovara. `log_message` **ostaje prazan**: steelman
iz nalaza je tačan, HTTP log svakih par sekundi bi zatrpao agentov transkript, a fatalne
poruke sada ionako stižu u fajl.

**(b) `VIEWER_PID=$!` je bila promenljiva shell-a**, a između nje i `kill` stoji ceo
ljudski review ciklus. Nov `Bash` poziv ili restart terminala značio je server koji radi
neograničeno i koji se više ne može imenovati. Sada `echo $! > <workspace>/viewer.pid`, a
`kill` čita iz fajla i **više ne guta** sopstveni promašaj (`2>/dev/null` je uklonjen —
skrivao je „nije bilo koga ubiti").

**(c) One-shot hvatanje bez ijedne alternativne putanje.** Uz „ovo je jedina prilika" sada
stoji degradacija: izmeri vreme sopstvenim satom oko spawn-a i sačuvaj ga **označeno kao
rezervu**. Propuštena notifikacija tako daje lošiji podatak umesto nikakvog. Za tokene
rezerve nema — zapiši ih odsutne umesto da ih pogađaš, pa agregator ispiše `—` umesto
izmišljenog zbira.

**(d) `improve_description` nije bio u `try`.** `improve_description.py` ima `timeout=300`
čiji `TimeoutExpired` je propagirao do vrha; pad u iteraciji 3 od 5 rušio je ceo run, a
`results.json` se piše tek posle povratka iz petlje — pa je sve plaćeno u iteracijama 1–2
nestajalo iz mašinski čitljivog izlaza. Sada je `except` **usko oko tog jednog poziva**
(širi bi progutao greške koje treba da se vide), razlog se **imenuje** u `exit_reason`
(tip i poruka, ne „nešto je stalo"), petlja staje i sve izmereno prolazi normalnim
povratnim putem.

> Obim ove stavke je bio **uži** nego što je zapisano, i to je izmereno pre popravke:
> `run_loop` upisuje parcijalni izveštaj u živi HTML posle **svake** iteracije, pa su
> iteracije 1–2 preživljavale kao HTML. Nisu preživljavale kao JSON, ni razlog pada.
> Prvi put u ovom radu da je izmereni obim uži od zapisanog — obrazac ide u oba smera.

**(e) `stderr=subprocess.DEVNULL` na `claude -p`.** Do 300 poziva po runu čiji je otkaz
postojao samo kao jedna `query failed: <exception>` linija, bez ijednog detalja iz CLI-ja.

**Očigledna popravka je izmerena i odbačena.** `stderr=subprocess.PIPE` **kvari alat**:
petlja čita **samo `stdout`**, pa se dete blokira čim napuni bafer cevi (~64 KB) i nikad
ne izađe. Izmereno:

```
PIPE  -> proces zavrsio u 6 s?  False   | poll = None     <-- ZAGLAVLJEN
FAJL  -> proces zavrsio u 6 s?  True    | poll = 0
        procitano sa stderr fajla: 300000 bajtova
```

To bi „izgubljenu dijagnostiku" pretvorilo u „svaki pričljiv poziv visi do `--timeout`" —
tiho **gore** od defekta koji se popravlja. Zato `stderr` ide u **privremeni fajl**
(`tempfile.TemporaryFile`, briše se zatvaranjem), a repić se čita na **svakom** izlaznom
putu uključujući timeout — jer timeout je tačno trenutak kad razlog najviše treba.

**Kontrola koja je uhvatila regresiju.** Prva verzija ovih izmena je oborila
`test_telo_pod_token_limitom`: telo `SKILL.md`-a je otišlo na **5186 tokena** (limit 5000),
gde bi se sve preko granice tiho odsecalo posle auto-kompakcije (N-08). Tekst je skraćen u
tri koraka do **ispod granice**, uz zadržan operativni sadržaj — obrazloženja žive ovde, u
CHANGELOG-u, ne u telu skilla.

### Popravljeno — 300+ poziva sada ima plan, kapu i vidljiv gubitak (T-29, N-24 delimično)

`scripts/run_loop.py` i `references/description-optimization.md`.

**Aritmetika izvedena iz koda, ne iz opisa.** `ast` obilazak svih 13 `add_argument`, plus
struktura petlje: `improve_description` se poziva **samo kad petlja ne prekine**, dakle na
iteracijama `1 … max_iterations-1`, i ima jedan uslovni retry kad opis pređe 1024 znaka.
Za dokumentovani poziv i 20 upita koje `references/description-optimization.md` propisuje:

```
20 upita × 3 runa × 5 iteracija     = 300 procesa `claude -p`
+ improve_description × 4 iteracije =   4
+ do 4 retry-ja                     =   4
                                    = 304 – 308
```

**Nijedna od tih brojki se nije prikazivala pre pokretanja.** `grep` po svim skriptama i
dokumentaciji za `budget|cost|backoff|rate.?limit|max.?calls|estimate|USD`: nula pogodaka
koji se tiču cene ili kape. U kapiji: nijedan test nad ovom putanjom.

**Uvedeno:**

- `plan_calls()` — tačan broj procesa, izveden iz strukture petlje, ne procenjen.
- **Pre-flight na `stderr` pre prvog poziva**, sa razlaganjem. Predstavljen kao
  **„up to"**, jer petlja staje čim svi train upiti prođu — precenjena procena je isto
  netačna kao potcenjena.
- **`--max-calls`, fail-closed.** Plan iznad kape → izlaz **pre ijednog poziva**, sa
  planom, kapom i tim šta smanjiti. Default **500 je izveden, ne izabran**: dokumentovani
  najgori slučaj je 308, pa 500 pušta dokumentovani tok a hvata nesreće reda
  `--runs-per-query 10 --max-iterations 20` (4000+). `--max-calls 0` gasi kapu.
- **`--cost-per-call`, bez default-a.** Cena po pozivu ne postoji u kodu i zavisi od
  modela, plana i dužine konteksta. Upisati uverljiv iznos bilo bi tačno ono što je
  prijavljeno kao N-49 — vrednost koja izgleda popunjeno a izmišljena je. Broj poziva se
  prikazuje uvek (tačan je), dolari **samo ako ih pozivalac zada**. U tekstu pomoći stoji
  izmereni raspon **sa poreklom**: `0,108–0,197 $ po pozivu, u jednom sandbox-u sa 148
  učitanih slash komandi; tvoja vrednost će se razlikovati`.
- **Gubitak je vidljiv.** `run_eval` hvata grešku po runu, broji je i ide dalje — što je
  ispravno, ali je gubitak činilo nevidljivim: nalet rate-limita kroz 10 radnika tiho
  smanji uzorak na kome se bira pobednički opis. Sada se prijavljuje koliko je runova
  izgubljeno i koliki je to udeo, **uvek a ne samo pod `--verbose`**, jer dokumentovani
  poziv radi u pozadini. Uz to `runs_lost_to_errors`, `runs_attempted` i `planned_calls`
  ulaze u izlazni JSON.

**Backoff NIJE dodat, i to je odluka a ne propust.** Ne postoji nijedno merenje ponašanja
pri rate-limitu; da bi ga bilo, trebalo bi namerno izazvati 429 pravim pozivima. Slep
retry **udvostručuje potrošnju** tačno u trenutku kad nešto već ne valja. To je isti
obrazac kao popravka koja je uvela N-48: napisana iz čitanja, i u praksi pogoršala stvar.
Umesto toga je gubitak učinjen vidljivim, a ograničenje **zapisano kao ograničenje** u
`references/description-optimization.md`.

**Zato se N-24 zatvara delimično** — plan i kapa da, backoff ne — i tako je i prijavljeno.

### Popravljeno — vrednost ćelije iz `.xlsx` više ne može da postane atribut na `<td>` (T-28, N-43)

`eval-viewer/viewer.html`, funkcija `renderXlsx`.

**Ovaj nalaz je bio pogrešno zaveden kao „nije reprodukovan".** Reprodukovan je u
Chromium-u, na **SheetJS 0.18.5** — na istoj verziji na kojoj je prethodno merenje
zaključilo da je bezopasan:

```
window.__PWN2__ = 1
```

**Proizvoljan JavaScript izvršen bez ijedne korisničke akcije**, iz vrednosti ćelije.

**Zašto je prethodno merenje promašilo.** `XLSX.utils.sheet_to_html()` **ispravno**
escape-uje `<` i `>` u **tekstu** ćelije, i test je gledao baš to — da li se pojavi
`<img>` ili `<script>` element. Ali istu vrednost stavlja i u atribut `data-v="…"`, gde
**dvostruki navodnik nije escape-ovan**. Payload izlazi iz atributa i postaje **stvaran
atribut na `<td>`**:

| Ulaz u ćeliji | Izmereni atributi na `<td>` | Ishod |
|---|---|---|
| `y" autofocus onfocus="…" tabindex="0` | `autofocus=""`, `onfocus="…"`, `tabindex="0"` | **JS izvršen, bez interakcije** |
| `x" onmouseover="…"` | `onmouseover="…"` | handler ugrađen |
| `z" style="position:fixed;…100vw;100vh"` | `style="…"` | sloj preko celog ekrana (clickjacking) |

`<td>` pri tom **gubi svoj `id`** — dokaz da je parser izašao iz atributa.

**CSP dodat u T-26 ovo ne zaustavlja.** `script-src 'unsafe-inline'` dozvoljava inline
event handlere. To je tačno ograničenje koje je tada zapisano kao rezerva; ovde je
pokazano konkretno.

**Lanac posledice je isti kao kod ostalih XSS nalaza u vieweru:** `.xlsx` proizvodi skill
koji se testira, skript izvršen u vieweru piše u `feedback.json`, a `SKILL.md` nalaže
Claude-u da ga pročita i po njemu prepiše skill.

**Pinovana verzija se ne može izmeriti — i to nije stvar truda.** `cdn.sheetjs.com` vraća
CONNECT 403 u ovom okruženju, a SheetJS je posle **0.18.5 prestao da objavljuje na npm**,
pa `0.20.3` ne postoji ni tamo. Zato popravka ne pokušava da izmeri pinovanu verziju nego
**uklanja zavisnost od bilo koje**.

**Šta je promenjeno.** Tabela se sada **gradi**, ne parsira iz stringa:
`sheet_to_json({header:1, raw:false, defval:""})` → `createElement` + **`textContent`**,
uz ručno prenošenje `!merges` u `colSpan`/`rowSpan`. `textContent` ne može da napravi ni
element ni atribut, pa ispravnost više ne zavisi od escaping-a treće strane koja se
učitava sa mreže. Time `innerHTML` **nestaje sa poslednje dinamične tačke u vieweru**.

**Izmereno da izmena ništa ne gubi:** isti broj redova (7 → 7), isti `colspan` (`["2"]`),
ista ćelija sa formulom (prazna u oba puta), payload **i dalje vidljiv analitičaru kao
tekst** — tiho brisanje sadržaja bilo bi druga vrsta lažnog izveštaja. Merene vrednosti
`__PWN1__/__PWN2__/__XSS__` idu sa `0/1/0` na **`0/0/0`**, uz **nijedan** atribut na
`<td>` van `colspan`/`rowspan` i **0** injektovanih `[style]` elemenata.

**SheetJS ostaje potreban** za parsiranje binarnog `.xlsx` formata, pa `<script src>`,
`integrity` (SRI) i CSP origin ostaju. Menja se samo to što se **njegov izlaz više ne
tretira kao HTML**.

Uz popravku idu i **dva testa u Chromium-u**: jedan koji je pre izmene bio crven na v1 i
na v2 (injekcija atributa), i jedan **kontrolni** koji je i pre bio zelen i mora takav
ostati — spojena ćelija mora zadržati `colspan="2"`, da popravka ne bi tiho polomila
prikaz.

### Popravljeno — benchmark sada kaže čime je meren, i svaki broj stoji uz svoju imenicu (T-27, N-49 + N-50)

`scripts/aggregate_benchmark.py`, `references/schemas.md`, `SKILL.md`. **Oba nalaza su
izašla iz prvog pravog benchmark-a (40 runova), nijedan iz čitanja koda.**

**N-49 — artefakt koji ne identifikuje sam sebe, i ne žali se na to.** Četiri polja
identiteta (`skill_name`, `skill_path`, `executor_model`, `analyzer_model`) imaju
`default=''` i nijedno nije `required`. Dva su dobijala `"<...>"` šablonski placeholder —
tačno onaj oblik koji komentar **dva reda ispod njih** zabranjuje jer „silently makes the
whole benchmark non-reproducible", i koji `references/schemas.md` zapisuje kao normu.
Pravilo je bilo primenjeno na modele, ne i na ime i putanju samog skilla.

Izmereno na 40 pravih runova: `skill_path: "<path/to/skill>"`, oba modela
`"unspecified"`, **exit 0, prazan stderr** — artefakt izgleda kompletan i ne identifikuje
ništa.

**Obim je bio širi od koda.** `SKILL.md` je jedini dokumentovani poziv agregatora u celom
skillu i prosleđivao je **jednu od četiri** zastavice. Onaj benchmark nije bio nesrećan
slučaj nego tačno ono što skill nalaže da se uradi. Popravka samo u Pythonu bi upozorenje
pretvorila u šum koji se pali na svakom ispravnom pokretanju, pa `SKILL.md` ulazi u istu
izmenu. Da je vrednost poznata u tom trenutku, dokazuje `agents/analyzer.md` — analitičar
**prima `skill_path` kao ulazni parametar**.

**Šta je promenjeno:** sva četiri polja dobijaju `"unspecified"` — jedna reč za sve vrste
neznanja, jer `"<skill-name>"` izgleda kao zaboravljeno polje a `"unspecified"` je iskren
iskaz o odsustvu, i čitalac ta dva ne razlikuje na prvi pogled. Uz to, **po jedno
upozorenje za svako nedostajuće polje**, na `stderr` **i** u `data_quality` — tj. i u
samom artefaktu, jer dokumentovana pokretanja preusmeravaju izlaz, gde dijagnostika samo
na `stderr` ne stiže do nikoga. To je isti razlog zbog kojeg `data_quality` uopšte
postoji; njegova definicija u `schemas.md` je proširena da to pokrije, da ponašanje i
ugovor ne odu jedno od drugog.

**Derivacija imena je probana i odbačena merenjem.** `eval-viewer/generate_review.py` već
izvodi ime iz `<skill-name>-workspace/`, pa je delovalo elegantno prepisati to. Pušteno
nad **stvarnom** putanjom onog benchmark-a: workspace se zvao doslovno `workspace`, pa bi
derivacija upisala `"workspace"` kao ime skilla — **uverljivo pogrešan** identitet, što je
gore od vidljivo odsutnog. Zapisano u `schemas.md` da se ne pokuša ponovo.

**Nije `required=True`:** benchmark bez identiteta je i dalje upotrebljiv, samo nije
reproducibilan — i to sada piše u njemu. Glasno upozorenje sa upotrebljivim izlazom je
ispravna jačina; tvrd otkaz bi oborio svakog postojećeg pozivaoca.

**N-50 — broj je bio tačan, imenica uz njega nije.** `benchmark.md` je pisao
`**Evals**: 1, 2, 3, 4, 5 (20 runs each per configuration)`. Prebrojano po
`(configuration, eval_id)` na istom fajlu: 40 runova ukupno, **20 po konfiguraciji**,
**4 po evalu**. Broj 20 je tačan — ali stoji zalepljen uz listu evala, pa se čita kao „20
iza svakog evala". Faktor greške u čitanju je **5**, u smeru koji benchmark čini
ubedljivijim nego što jeste. Tabela je pri tom bila ispravna: `n=20` u ćelijama je stvarno
20 po konfiguraciji.

To je **isti defekt koji je N-09 već jednom popravio**, jedan nivo granularnosti niže —
tada je gledan broj, a ne imenica uz broj. Komentar u kodu i dalje opisuje stariju
varijantu: „a benchmark built from a single run announced *3 runs each per configuration*,
which reads as triple the statistical weight it has."

Sada su dva reda, svaki uz svoju imenicu:

```
**Evals**: 1, 2, 3, 4, 5
**Runs**: 20 per configuration (4 per eval x 5 evals)
```

Broj po evalu je **prebrojan, ne izveden deljenjem** — deljenje bi izmislilo broj čim
raspored nije ravnomeran, što je tačno klasa tihe netačnosti koju ovaj fajl postoji da
odbije. Kad se evali ne slažu, štampa se `at least N`, a `runs_per_config_per_eval_is_uniform`
nosi tu činjenicu u JSON-u.

**Kontrola na stvarnim podacima:** ista 40-runska agregacija puštena kroz popravljen kod
daje `runs` i `run_summary` **identične do bajta** originalu; promenjeno je tačno
`skill_path`, dodata su dva nova polja i tri stavke u `data_quality` — i ništa drugo.
Dokumentovan poziv sa sve četiri zastavice daje **0 bajtova na stderr**.

### Popravljeno — brojevi iz JSON-a više ne mogu da nose markup, i sve tri HTML površine imaju CSP (T-26, N-42 + T-06b)

**N-42 — obim je 12 vrednosti, ne 4 tačke.** PLAN je zapisao „četiri tačke"; to su četiri
mesta u kodu. Mašinski obilazak (`ast`, svaki `JoinedStr` → `FormattedValue`) dao je 24
interpolacije bez `html.escape`, od kojih je **12 iz spoljnog JSON-a**: `best_score`,
`iterations_run`, `train_size`, `test_size`, `iteration`, `train_correct`, `train_runs`,
`test_correct`, `test_runs`, `errors`, `triggers`, `runs`. Ostalih 12 je bezbedno po
konstrukciji (izračunato u kodu), a `args.output` ide u `stderr`, ne u HTML.

**Koercija, ne escape.** Svih 12 *treba* da budu brojevi. `html.escape` bi payload učinio
inertnim ali bi ga **propustio** kao tekst koji izgleda kao podatak; broj ne može da nosi
markup uopšte. Kad koercija ne uspe, vraća se **escape-ovan original** umesto tihe nule —
sakriti pokvaren podatak je gore nego prikazati ga.

**CSP — tri površine, tri različita odgovora, i jedan je jak.** Izmereno:

| Površina | `<script>` | Polisa |
|---|---|---|
| izlaz `generate_report.py` | **0 tagova** | **`script-src 'none'`** |
| `eval-viewer/viewer.html` | 2 (1 CDN) | `'unsafe-inline'` + imenovani origini |
| `assets/eval_review.html` | 1 inline | isto |

Izveštaj **nema nijedan JavaScript**, pa je tu `script-src 'none'` stvarna odbrana:
i da promakne interpolacija, injektovan markup se ne izvršava. Koercija i CSP se
udvostručuju baš na površini na kojoj N-42 živi.

**Iskreno o dometu na viewerima:** podatak se ubacuje **unutar** inline skripte
(`viewer.html:651`), pa se sadržaj skripte menja po generisanju i statički `sha256-` hash
ne radi. Otuda `'unsafe-inline'` — a to **ne zaustavlja** klasu XSS-a zbog koje je N-02
postojao. Šta stvarno daje: blokira spoljne skripte osim imenovanih origina, zabranjuje
`<object>`/`<embed>`, zaključava `base-uri` i `form-action`. Slabija odbrana, ne odsustvo
odbrane — i tako je zapisano u samom kodu, da se ne pročita kao „viewer je zaštićen".

**Kontrola koja je odlučivala:** CSP može tiho da polomi stranicu. Svih 25 testova u
Chromium-u pušteno pre i posle — **nijedan nov pad**, 14 → 11 (tri prevrnuta u zeleno).

### Popravljeno — nula u trigger rate-u sada nosi dokaz koji je objašnjava (T-25, N-46)

`scripts/run_eval.py`. Do sada je `trigger_rate: 0.0` sa `errors: 0` i
`inconclusive: false` mogao da znači **dve različite stvari**, a alat ti nije rekao koju:

- opis nije privukao — model je posegnuo za **drugim** alatima;
- upit nije tražio alat — model je odgovorio iz znanja i pozvao **nijedan**.

Razlikuju se samo u transkriptu, a transkript se odbacivao. `run_single_query` je te
podatke **video** pa vraćao samo `(triggered, via)`.

Izmereno dvaput na pravim pozivima, oba puta sa punim transkriptom:

| Upit | Alati | Izveštaj |
|---|---|---|
| „napravi mi skill od ovoga što smo sad radili" (CAL-01) | **nijedan** | `0/3, errors=0, inconclusive=false` |
| „kako da izmerim da li jedan skill uopšte nešto donosi" (CAL-03/P3) | **nijedan** | isto |

U drugom slučaju model je dao **tačan i koristan** odgovor o A/B poređenju. Nula nije bila
o opisu — a iz izveštaja se to nije videlo.

**Šta je promenjeno:** `run_single_query` vraća `(triggered, via, tools_seen)`. Po upitu
se agregira `runs_without_any_tool` i `tools_seen`, oba ulaze u izlazni JSON, a `--verbose`
dodaje red kad je `trigger_rate == 0` a nijedan alat nije pozvan — da nula nikad ne stoji
sama.

**Semantika presude nije dirana.** `pass`, `trigger_rate` i `inconclusive` rade isto.
Ovo je **dopuna dokaza**, ne promena odluke — menjanje `pass` logike bi promenilo koje
opise `run_loop.py` bira, a za to nemamo eval pre/posle.

**Ograničenje zapisano u samom kodu:** run koji **okine** vraća se rano i proces se ubija,
pa je njegov `tools_seen` nepotpun. Dijagnostika je smislena samo za runove koji nisu
okinuli — a to su tačno oni kod kojih nula traži objašnjenje. Potvrđeno na pravom
transkriptu: run koji je okinuo dao je `tools_seen = ['Skill']` (bez kasnijeg `Read`),
run koji nije — `[]`.

### Popravljeno — detektor trigera je vraćao False pre nego što model pozove alat (T-24, N-48)

`scripts/run_eval.py`. **Nađeno pravim pozivima, ne čitanjem** — 19 `claude -p` poziva
2026-07-31. Detektor je prijavljivao `trigger_rate: 0.0` sa `inconclusive: false` i
`errors: 0` za potez u kome je `Skill` **stvarno pozvan**, dokazano transkriptom.

Dva prevremena izlaza, oba uklonjena:

- `:349` — `return` na kraju grane `assistant`. Sa uključenim extended thinking prva
  `assistant` poruka je **uvek** blok razmišljanja bez ijednog `tool_use`; izmereno, ona
  je događaj **13**, a `tool_use/Skill` događaj **15**. Detektor je odlazio na 13.
- `:313` — `message_stop` kao terminalan. Završava **jednu** poruku, a potez ih rutinski
  ima više (izmereno tri: thinking+Skill, thinking+Read, thinking+tekst).

Terminalni su sada samo `result` i kraj procesa; oba su i ranije vraćala `(triggered, via)`
ispravno.

**Ovo je bila regresija uvedena tiketom T-09 ovog istog rada, ne nasleđeni defekt.** U
upstream/v1 verziji `return` stoji **unutar** `for` petlje, pa poruka sa samo `thinking`
prođe kroz `continue` i skeniranje se nastavlja — **v1 je na toj putanji ispravan**. T-09
je `return` izmestio iz petlje da bi rešio N-04 („Skill nije bio prvi tool call") i time
uveo bezuslovni izlaz na svakoj poruci. Neto: popravka je detektor u praksi pogoršala,
jer je „prva poruka je thinking" učestalije od „prvi tool_use nije naš".

Posledica po korisnika: **svaki trigger rate izmeren verzijama između T-09 i T-24 je
nula bez obzira na opis.** Ako si pokretao `run_eval.py` ili `run_loop.py` u tom
prozoru, ti brojevi ne znače ništa i optimizacija opisa birana po njima nije validna.

Predviđene posledice popravke, još neizmerene: run koji ne okida više se ne prekida rano
pa mu cena raste (procena ~+30 %), a podrazumevani `--timeout 30` postaje tesan — pun
potez je izmeren na **27,4 s**. Default nije menjan; to traži merenje, ne pretpostavku.

### Poznat defekt u ovom paketu — `evals/trigger_queries.json` (N-47)

**Ovaj skill se isporučuje sa eval setom koji ne meri ono što tvrdi da meri.** Sedam od
deset pozitivnih upita pretpostavlja stanje kojeg u `claude -p` runu nema: istoriju
razgovora („napravi mi skill od **ovoga što smo sad radili**", „skill koji sam **juče**
napravio") ili konkretnu putanju u fajl-sistemu (`~/.claude/skills/pdf-filler`,
„**this** SKILL.md"). Dva su izmerena pravim pozivima i **oba su blokirana** iz razloga
koji nemaju veze sa opisom; ostalih pet je klasifikovano čitanjem.

Ko pokrene set dobiće trigger rate blizu nule i može zaključiti da mu opis ne valja.
**Negativi su dobri** — pravi near-miss upiti — i zadržavaju se.

Defekt je uveden tiketom **T-11** ovog istog rada i isporučen. Popravka je zaseban tiket.

Uz njega ide i **N-46**: `run_eval.py` takav ishod prijavljuje kao
`pass=false, inconclusive=false, errors=0` — dakle sa punim samopouzdanjem, jer kategorija
„upit nije stigao do odluke o skillu" u njegovom modelu ne postoji.

**Izmerena cena, da se planira pre trošenja:** 0,108 $ i 0,196 $ po pozivu (mereno
`total_cost_usd` iz `result.usage`, u okruženju sa 148 učitanih komandi). Dokumentovani
obim od 20 upita × 3 runa ≈ **6–12 $**.

Od preostalih **16** padova kapije, prebrojano iz gate izlaza:

| Nalaz | Padova | Zašto još stoji |
|---|---:|---|
| **N-16** pristupačnost (WCAG 2.2 AA) | 11 | traži odluku vlasnika: vrednost zavisi od toga kako se recenzije stvarno rade |
| **N-17** interfejs skripti | 4 | dve skripte bez `--help`, usage reklamira `utils/package_skill.py` koje ne postoji, exit kodovi nisu distinktni |
| **CSP** (ostatak N-02 / T-06b) | 1 | nijedna HTML površina nema `Content-Security-Policy` |

Preostalih **osam** otvorenih nalaza (N-19, N-21, N-23, N-24, N-26, N-27, N-29, N-31)
**nema nijedan pad u kapiji** — neki zato što traže ljudsku odluku, neki zato što se ne mogu
izmeriti testom. Najizrazitiji je **N-19** (ne-engleski trigeri): traži ~180 pravih
`claude -p` poziva. Odsustvo crvenog testa ovde **nije** dokaz da nalaz ne stoji.

Kandidati zabeleženi bez popravke: N-42, N-43 (neproveren protiv pinovanog SheetJS
0.20.3), validacija `--skill-name` u `render_eval_review.py`, `THIRD_PARTY_NOTICES.md`
(§4(d), ne §4(b)). Detalji po nalazu: `PLAN.md`, `regression/README.md`.

---

## Planirano — obavezne napomene pri objavi

Ove stavke moraju biti zapisane **u trenutku** kad se primene, jer menjaju značenje
ranijih rezultata ili nose pravnu obavezu:

- **N-04** (detektor trigera) — **primenjeno u T-09** (vidi sekciju „Blok 1, detektor
  trigera" gore); napomena o neuporedivosti trigger rate-ova je tamo zapisana. Ostaje
  ovde nabrojano samo kao trag da je obaveza izmirena.
- **N-07 / N-09** (jedinice tokena, lažni `n`) — **primenjeno u T-07** (vidi sekciju
  „Blok 1, jedinice i statistika" gore); napomena o neuporedivosti starijih
  `benchmark` artefakata je tamo zapisana. Ostaje ovde nabrojano kao trag da je
  obaveza izmirena.
- **Apache-2.0 §4(b)** — „You must cause any modified files to carry prominent
  notices stating that You changed the files." **Deset** fajlova je izmenjeno u odnosu
  na upstream (`SKILL.md`, `LICENSE.txt`, `agents/analyzer.md`, `agents/comparator.md`,
  `agents/grader.md`, `eval-viewer/generate_review.py`, `references/schemas.md`,
  `scripts/aggregate_benchmark.py`, `scripts/quick_validate.py`,
  `scripts/run_eval.py`) i jedan je nov (`scripts/render_eval_review.py`).
  **Nijedan još ne nosi takvu napomenu.** Obaveza se aktivira pri distribuciji, a
  `scripts/package_skill.py` postoji upravo da proizvede distribuirajući `.skill`.
  Formulacija zahteva odluku vlasnika forka — vidi `PLAN.md` §6.
- **Registarsko polje `Owner`** (enterprise.md) još nije popunjeno; zahteva identitet
  vlasnika.
