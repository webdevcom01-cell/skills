# Ojačavanje — Stavka #3: `checker-verify.sh` heuristika za "test pokriva promenu"

*16. septembar 2026.*

## Polazna tačka

Stavka #3 je u dogovorenom redosledu (1→5→2→3→4) opisana kratko: "`checker-verify.sh` heuristika za 'test pokriva promenu' je gruba (samo proverava da li je BILO KOJI test fajl dotaknut)". Baseline provera je pokazala da je ta gruba heuristika zapravo **najmanji** od tri problema — postojao je jedan ozbiljniji, ranije nedokumentovan bag, plus jedan bag klasifikacije koji je taj heuristiku dodatno kvario.

## Baseline nalazi (pre ispravke)

### Nalaz A — pogrešna git diff referenca (KRITIČNIJI od originalno opisanog problema)

`checker-verify.sh` je računao ceo diff preko `git diff --name-only HEAD` — jedan-ref poređenje radnog direktorijuma sa **poslednjim commit-om na trenutnoj grani**. Ako Maker komituje progresivno posle svake iteracije (što je preporučeno obrazac u ovom istom projektu — isti obrazac bag-a već je nađen i ispravljen u `prepare-checker-bundle.sh`, ali nikad prenet ovde), radni direktorijum je u trenutku kad se checker pokrene **čist**. `git diff HEAD` tad vraća prazno, `TOUCHES_LOGIC`/`TOUCHES_TEST` ostaju oba `false`, i `max_confidence` tiho ostaje `"CONFIRMED"` (default vrednost), bez obzira koliko je logike zaista promenjeno na toj grani ili da li ijedan test postoji za nju.

**Dokazano na realnom uređaju**, na pravom `word-freq-bridge` worktree-u (sve komitovano, čist working tree): `git diff --name-only HEAD` → prazno; `git diff --name-only main` → ispravno prikazuje 4 promenjena fajla.

**Dokazano i na sintetičkom repou** (reprodukcija bag-a namerno, ne kroz teoriju): grana koja dodaje potpuno netestiranu `divide()` funkciju (bez provere deljenja nulom) preko `add()`-a koji ima test, sve komitovano. Neizmenjeni originalni `checker-verify.sh` je vratio:
```json
{"deterministic_status": "PASS", "max_confidence": "CONFIRMED", "requires_human_review": false}
```
— lažno "potvrđeno", iako `divide()` nema nijedan test.

### Nalaz B — klasifikacija fajlova: redosled grana + slepo pod-string poređenje

Originalni `case` blok je prvo proveravao `*test*|*spec*` obrazac, PA TEK ONDA doc/config ekstenzije. Posledica: dokumentacioni fajl čije ime SLUČAJNO sadrži "test" kao podstring (npr. `contest_notes.md`, `latest_changes.md`) je bio pogrešno klasifikovan kao `TOUCHES_TEST` umesto ignorisan kao dokumentacija. Isti slepi podstring-obrazac je pogrešno klasifikovao i stvarnu, netestiranu logiku — npr. fajl po imenu `attestation.py` (sadrži "test" kao podstring: a-**test**-ation) — kao test fajl.

**Dokazano na sintetičkom repou**: grana koja dodaje `contest_notes.md` (dokumentacija) i `attestation.py` (stvarna, netestirana logika) — originalni `case` blok bi oba pogrešno svrstao, sakrivajući baš onu promenu logike koju heuristika treba da uhvati.

### Nalaz C — nedostaje `git add -N` pre diff-a

Isti obrazac kao već ispravljen u `prepare-checker-bundle.sh`: bez `git add -N -A` pre `git diff`, potpuno novi (nikad `git add`-ovani) fajlovi su nevidljivi u diff izlazu, bez obzira na referencu.

## Ispravka

1. **Base-branch parametar** — `checker-verify.sh <worktree-dir> [base-branch]`. Kad je prosleđen, koristi se direktno. Kad nije, skripta pokušava `main` pa `master` kao lokalne grane (`git show-ref --verify --quiet refs/heads/<ime>`); ako ni jedna ne postoji, pada nazad na staro `git diff HEAD` ponašanje uz **glasno upozorenje na stderr** — nikad tiho.
2. `git add -N -A` dodato pre `git diff --name-only "${DIFF_REF}"`.
3. **`classify_file()`** — doc/config ekstenzije (`*.md|*.json|*.yaml|*.yml|*.lock|*.txt|*.toml|LICENSE*|.gitignore`) proveravaju se PRVE. Test-obrazac je sužen na konkretne, ustaljene konvencije po imenu fajla (`test_*.py`, `*_test.py`, `*.test.js`, `*.spec.ts`, `Test*.java`, `*Test.java`, `*_test.go`, `*_test.rb`, itd.) i po test-direktorijumu (`*/tests/*`, `*/test/*`, `*/__tests__/*`, `*/spec/*`), umesto slepog "sadrži 'test' bilo gde".
4. **Novi, jači signal — merena pokrivenost linija (Python)**: kad je `pytest-cov` dostupan (`pytest_cov_available()`, analogno postojećem `ruff_in_use()`/`mypy_in_use()` obrascu), `unit_tests` sloj se pokreće sa `--cov=. --cov-report=json:.agent/coverage.json` (bez duplog pokretanja testova). Novi `coverage_check.py` skript parsira `git diff -U0 <base> -- *.py` hunk header-e da dobije TAČNO koje su linije promenjene/dodate u ne-test `.py` fajlovima, pa ih ukrsti sa `coverage.py`-jevim `executed_lines` iz izveštaja. Rezultat: da li su STVARNO IZMENJENE linije STVARNO IZVRŠENE tokom testova — mnogo jači signal od "da li test fajl postoji negde u diff-u". Fail-safe: fajl promenjen ali odsutan iz `coverage.json` (nikad uvezen tokom testova) tretira se kao POTPUNO nepokriven, ne preskače se ćutke.
5. Kad `--cov` flegovi sami puknu (npr. verzija pytest-cov nekompatibilna) — prepoznato po tekstu greške, ne po golom exit kodu — skripta briše lažni FAIL zapis i proba goli `pytest -q`, isti obrazac kao već validirana `run_py_tool`-ova uv/PATH ispravka. (Ova grana je pregledana u kodu ali NIJE uživo reprodukovana — vidi "Šta nije testirano" ispod.)
6. Kad merena pokrivenost NIJE primenljiva (nije Python, `pytest-cov` nedostupan, coverage run neuspešan), pada se nazad na (ispravljenu) heuristiku po imenu fajla. Izlazni JSON sad ima `"confidence_basis"` polje koje transparentno kaže na osnovu čega je `max_confidence` određen: `"merena_linija_pokrivenost"` | `"heuristika_po_imenu_fajla"` | `"heuristika_po_imenu_fajla_slaba"` | `"nema_izmena_logike"`.

## Retest — rezultati

Sve provere rađene direktno na Mac-u (`device_bash`), sa realnim `git`/`pytest`/`ruff`/`mypy` komandama, ne simulirano.

### 1. Git-diff-referenca — bag potvrđeno ispravljen

Ista sintetička `divide()` grana, poređenje STARE (backup) i NOVE skripte na identičnom repou:

| | `max_confidence` | `confidence_basis` |
|---|---|---|
| STARA skripta (`git diff HEAD`) | **CONFIRMED** (lažno) | — |
| NOVA skripta, `main` kao base (eksplicitno) | **PLAUSIBLE** | `merena_linija_pokrivenost` |
| NOVA skripta, bez argumenta (auto-detekcija `main`) | **PLAUSIBLE** | `merena_linija_pokrivenost` (identično eksplicitnom) |

Merena pokrivenost je konkretno pokazala `uncovered_lines` uključujući telo `divide()` funkcije — ne samo grubo "nema testa", nego TAČNO koja linija nije izvršena.

### 2. Klasifikacija — bag potvrđeno ispravljen, jedan preostali rub-slučaj nađen

Sintetički repo sa `contest_notes.md` + `attestation.py`: `contest_notes.md` ispravno isključen (nije čak ni u skupu ne-test `.py` fajlova koje `coverage_check.py` razmatra), `attestation.py` ispravno prepoznat kao logika i ispravno prijavljen kao nepokriven.

Direktan jedinični test same `classify_file()` funkcije (14 slučajeva, van punog skripta) potvrdio je ispravku na svim originalnim slučajevima I otkrio **jedan preostali, uži rub-slučaj**: fajl po imenu `Testament.java` (stvarna logička klasa čije ime SLUČAJNO počinje sa "Test") se i dalje pogrešno klasifikuje kao test fajl, jer odgovara `Test*.java` obrascu — što je zvanična JUnit/Maven konvencija imenovanja test-klasa, ne proizvoljan podstring. Ovo je ista KLASA problema kao originalni bag, ali suženog obima (prefiks-poklapanje na ustaljenu konvenciju, ne slepo "sadrži negde u imenu") i pogađa samo ne-Python ekosisteme (Java/C#/Kotlin) gde merena pokrivenost (stavka 4 ispravke) uopšte ne postoji kao dodatna zaštita. Nije ispravljeno dalje — nema čistog načina da se imenom fajla razlikuje "TestFoo.java = test za Foo" od "Testament.java = klasa koja se zove Testament" bez čitanja sadržaja fajla (npr. traženje `@Test`/`import org.junit`), što je van obima ove ispravke. **Svesno priznat, dokumentovan gap.**

### 3. Auto-detekcija base grane i fallback bez main/master

- Repo SA lokalnim `main`, bez eksplicitnog argumenta → ispravno auto-detektovan i korišćen (identičan rezultat kao eksplicitan `main` argument).
- Repo BEZ `main`/`master` uopšte (samo `trunk` grana), bez argumenta → ispravno palo nazad na staro `HEAD` ponašanje, uz glasno `UPOZORENJE` na stderr — bez pada/greške skripta.

### 4. Realan `word-freq-bridge` worktree — merena pokrivenost stvarno vredna

Pre instaliranja `pytest-cov`-a na Mac-u, ovaj worktree je (ispravno) pao nazad na heuristiku po imenu fajla (`confidence_basis: heuristika_po_imenu_fajla_slaba`, CONFIRMED — i logika i test fajl su promenjeni, pa heuristika ne downgrade-uje).

Posle instaliranja `pytest-cov`-a (`pip install --user pytest-cov`), ista skripta na ISTOM worktree-u je aktivirala mereni put i vratila:
```json
{"max_confidence": "PLAUSIBLE", "confidence_basis": "merena_linija_pokrivenost",
 "coverage_check": {"all_changed_lines_covered": false, ...}}
```
Konkretno: `wordfreq.py` ima 57 promenjenih linija, od kojih je pokriveno samo 15 — `uncovered_lines` tačno pokazuje da CLI ulazna tačka (`main()`, linije ~36–53: parsiranje argumenata, čitanje fajla, stopwords logika) NIJE nijednom izvršena tokom testova, koji testiraju samo `top_words()` direktno. Ovo je **stvaran, prethodno nevidljiv nalaz** — stara heuristika (test fajl postoji → CONFIRMED) bi ovo potpuno progutala, jer test fajl DOSTA testira, samo ne CLI omotač. Merena pokrivenost je ovde strogo iskrenija od heuristike, ne samo teorijski nego i na pravom kodu.

### 5. Regresija na nepromenjenim slojevima

- **Lint (ruff)**: instaliran ruff na Mac-u, testiran sintetički repo sa stvarnim I001 lint greškama → ispravno `lint:FAIL`, fail-fast (unit_tests se ne pokreće). Posle `ruff --fix` → `lint:PASS`, nastavlja na typecheck.
- **Typecheck (mypy)**: instaliran mypy, ista grana → ispravno `typecheck:FAIL` na realnoj tip-grešci (mypy je otkrio referencu na nepostojeći atribut), fail-fast (unit_tests se ne pokreće). Ovaj deo koda nije menjan u stavci #3 — ponašanje potvrđeno identično kao pre.
- **Pokvaren/orphan worktree** (`cirilica-konverter`, ranije poznat orphan iz stavke #1): `git show-ref`/`git diff` pucaju sa "fatal: not a git repository" i u STAROJ i u NOVOJ skripti, identično — obe i dalje vraćaju `CONFIRMED` bez pada procesa (unit_tests ne zavisi od git-a). Nema regresije, ponašanje jednako lošeg/dobrog kvaliteta kao pre (orphan worktree je poznat, zaseban, još neodlučen nalaz iz stavke #1).

## Šta NIJE testirano (svesno priznat gap)

- Grana koja hvata "`--cov` flegovi sami puknu zbog nekompatibilne verzije pytest-cov" (linija koja briše lažni FAIL zapis i proba goli `pytest -q`) je pregledana u kodu i prati već validiran obrazac (`run_py_tool`-ova uv/PATH ispravka), ali NIJE uživo reprodukovana — trebalo bi namerno instalirati nekompatibilnu verziju `pytest-cov`-a da bi se ovo uživo okinulo, što nije urađeno zbog vremena/prioriteta.
- Ne-Python coverage (JS/TS `nyc`/`c8`, Java JaCoCo, itd.) — merena pokrivenost je implementirana SAMO za Python (`coverage.py`/`pytest-cov`). Za sve druge jezike i dalje važi (ispravljena) heuristika po imenu fajla, uključujući rub-slučaj iz Nalaza 2 iznad.
- `Testament.java`-tipa rub-slučaj (dokumentovan gore) nije ispravljen, samo priznat.

## Šta ova ispravka namerno ne rešava

- Coverage se meri na nivou LINIJA, ne grana (branch coverage) — linija izvršena jednom (npr. `if` telo nikad testirano sa `False` granom) i dalje broji kao "pokrivena".
- Ne proverava KVALITET testova (asertacije), samo da li je linija IZVRŠENA tokom test run-a — test bez asertacija bi i dalje "pokrio" liniju.

## Fajlovi

- `agentic-loop-engineer/scripts/checker-verify.sh` — izmenjen (base-branch parametar, ispravljena klasifikacija, coverage-svesan `unit_tests` sloj, novo `confidence_basis`/`coverage_check` polje u izlazu). Stara verzija sačuvana kao `checker-verify.sh.pre-stavka3-backup` u istom folderu na Mac-u.
- `agentic-loop-engineer/scripts/coverage_check.py` — nov fajl (linija-nivo coverage ukrštanje sa diff-om).

**Distributivni `.skill` fajl još nije ažuriran** — čeka zajedničko pakovanje na kraju (#1, #5, #2, #3, buduće #4), po Bukyjevoj eksplicitnoj odluci od 16. septembra.

## Runda review — nezavisan adversarijalan review (16. sept, isti dan)

Po ustaljenom obrascu, spawn-ovan je svež subagent (nula konteksta, sam testira preko `device_bash`-a na pravom Mac-u) da nezavisno proveri gorenavedene tvrdnje. Rezultat: **sva tri originalna baga (git-diff referenca, klasifikacija, `git add -N`) potvrđena kao stvarno ispravljena** — nezavisno reprodukovano OLD-vs-NEW ponašanje. Hipoteza o heredoc/JSON-injection riziku (nekvotovan heredoc u `checker-verify.sh` koji embeduje `coverage_check.py`-jev JSON izlaz) je **eksplicitno opovrgnuta** — testirano direktno sa fajl-imenima koja sadrže `$(...)`/backtick payload-e, nema command-execution rizika (bash nekvotovani heredoc radi samo JEDAN prolaz supstitucije, bez re-skeniranja za dalju ekspanziju).

Ali review je našao **četiri nova, stvarna, reprodukovana baga koje je SAMA stavka #3 ispravka unela** (svi u fail-safe smeru — nijedan ne uzrokuje lažni CONFIRMED, samo netačan/prestrog izlaz):

- **B2 (najozbiljniji, direktno pogađa ovaj projekat)** — `git diff` po default-u (`core.quotePath=true`) kvotuje/oktalno-eskejpuje putanje sa ne-ASCII karakterima (npr. **ćirilica** — projekat ima žive `cirilica-konverter`/`cirilica-history-cleanup` demo worktree-ove) u `+++ ` diff header-ima. `coverage_check.py`-jevo parsiranje putanje se potpuno lomilo na takvim imenima — nikad se ne poklopi sa `coverage.json` ključem, SVAKA linija fajla lažno prijavljena kao nepokrivena, bez obzira na stvarnu pokrivenost. Dokazano na sintetičkom repou sa fajlom `ćirilica_модул.py`, delimično pokrivenim.
- **B3** — `coverage_check.py`-jev `is_test_file()` nije prepoznavao `spec/` direktorijum ni `spec_*.py`/`*_spec.py` obrazac, za razliku od bash `classify_file()` (koji ima `*/spec/*` granu) — nekonzistentnost je značila da BDD-stil spec fajlovi (koje pytest ne diskoveruje jer nemaju `test_*` ime) bivaju tretirani kao "logika koju treba pokriti" umesto ispravno isključeni kao test kod.
- **B4** — `changed_python_lines()` je uzimao CEO opseg hunk header-a, uključujući prazne linije i komentare, koje `coverage.py` nikad ne beleži u `executed_lines` (nisu "statements") — pa je SVAKA takva linija bila lažno prijavljena kao "nepokrivena", čak i za funkciju koja je 100% pokrivena a promena čisto kozmetička (dodat komentar/prazna linija). Ovo je direktno potkopavalo baš onu preciznost koju stavka #3 obećava.
- **B5** — u `--cov`-recovery grani (kad `--cov` flegovi sami puknu zbog nekompatibilne verzije), `LAYER_FAILED` se nikad nije resetovao posle uspešnog recovery-ja — izlazni JSON je davao samoprotivrečan rezultat (`deterministic_status: PASS` ali `layer_failed: unit_tests`).

Proverene i ODBAČENE hipoteze (review ih je testirao, nije našao problem): path-normalizacija za fajlove u pod-direktorijumima (radi ispravno jer skripta uvek radi `cd` u worktree pre bilo kog `git diff`/`pytest --cov` poziva, pa se putanje uvek poklapaju); `git mv` preimenovanje sa izmenom sadržaja (ispravno hendlovano); potpuno brisanje fajla (`+++ /dev/null`, ispravno hendlovano, pada nazad na heuristiku).

### Ispravke (B2–B5)

- **B2**: `-c core.quotePath=false` dodato na SVAKI `git diff` poziv koji čita putanje — i u `checker-verify.sh`-ovom `DIFF_FILES` i u `coverage_check.py`-jevoj `changed_python_lines()`.
- **B3**: `is_test_file()` proširen — `spec_*.py`/`*_spec.py` imenski obrazac i `spec` direktorijum dodati, u skladu sa bash `classify_file()`.
- **B4**: nova logika u `coverage_check.py` — presek promenjenih linija sa "trackable" skupom (`executed_lines ∪ missing_lines` iz `coverage.json`); linije van tog skupa (prazne/komentar) se potpuno izbacuju iz razmatranja, ne broje se ni kao pokrivene ni kao nepokrivene. Kad `missing_lines` polje nije prisutno (stariji `coverage.py` bez njega), pada se nazad na staro (konzervativnije, ali B4-osetljivo) ponašanje — namerno, ne može se pouzdano razlikovati prazna linija od stvarno nepokrivenog statement-a bez tog polja.
- **B5**: `LAYER_FAILED=""` dodato uz `STATUS="PASS"` reset u recovery grani.

### Retest posle ispravki B2–B5 (na pravom Mac-u)

- **B2 fix potvrđen**: isti sintetički `ćirilica_модул.py` repo — `coverage_check` sada ispravno prijavljuje `covered_lines: [1,2,5]`, `uncovered_lines: [6]` (samo stvarno neizvršeno telo `cyr_untested()`), umesto ranije svih linija kao nepokrivenih.
- **B3 fix potvrđen**: direktan poziv `is_test_file('spec/mathlib_spec.py')` → `True`; pun run ispravno vraća `"nema izmenjenih ne-test .py fajlova..."` (spec fajl potpuno isključen iz coverage analize).
- **B4 fix potvrđen**: isti fix i dalje radi na starim reprodukcijama — `divide-repo`: `uncovered_lines` sad `[5]` umesto ranijeg `[3, 5]` (linija 3 je bila prazna linija, sad ispravno izbačena iz razmatranja). Realan `word-freq-bridge` worktree: `uncovered_lines` sad tešnji, precizniji skup (bez praznih linija unutar `main()` tela) — ista suštinska poruka (CLI omotač nepokriven), ali bez lažnog šuma.
- **B5 fix potvrđen**: simulacija pada `--cov` flegova (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`) → posle uspešnog recovery-ja na goli `pytest -q`, izlaz sad ispravno `"layer_failed": ""` (ranije ostajalo `"unit_tests"` uprkos `deterministic_status: PASS`).
- **Regresija bez promena**: real `word-freq-bridge` (i dalje PLAUSIBLE preko merene pokrivenosti), `divide-repo` (i dalje PLAUSIBLE), orphan `cirilica-konverter` worktree (i dalje CONFIRMED preko fallback heuristike, bez pada procesa) — svi ponovo testirani posle ispravki, identičan ishod kao pre (osim preciznijih `uncovered_lines` gde je B4 primenjiv).

### Zaključak runde review-a

Stavka #3 se sada smatra završenom sa potvrđenom nezavisnom proverom. `Testament.java`-tipa rub-slučaj klasifikacije (dokumentovano ranije, van Python domena) ostaje svesno neispravljen. `coverage_check.py` i `checker-verify.sh` na Mac-u su ažurni sa svim B2–B5 ispravkama; **distributivni `.skill` fajl i dalje čeka zajedničko pakovanje na kraju**.
