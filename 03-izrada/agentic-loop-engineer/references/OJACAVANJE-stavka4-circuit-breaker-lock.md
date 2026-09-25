# Ojačavanje — Stavka #4: file-lock za `circuit_breaker.py` (loop_state.json)

*16. septembar 2026.*

## Polazna tačka

Stavka #4 (poslednja u dogovorenom redosledu 1→5→2→3→4) je opisana kao: "`circuit_breaker.py`/`registry_write.py` nemaju file-lock ako se ikad doda drugi pisac u `loop_state.json` (trenutno je to bezopasno jer je dizajn jedan-proces-po-worktree-u)".

Provera koda je pokazala da je `registry_write.py` (koji piše u DRUGI, deljeni fajl — `registry.json`, koji prati sve aktivne worktree-ove) **već ispravljen u ranijoj rundi** (treći krug provere / audit) — koristi `fcntl.flock()` ekskluzivni lock kroz celu read-modify-write kritičnu sekciju, dokumentovano u sopstvenom docstring-u ("30 paralelnih pisaca, 0 gubitka posle ispravke"). Sanity-test ovom prilikom (20 konkurentnih upisa) potvrdio je da i dalje radi ispravno — 20/20 zadataka upisano.

**Stvaran cilj stavke #4 je bio `circuit_breaker.py`**, koji piše u `loop_state.json` (per-worktree stanje petlje: broj iteracija, istorija grešaka, istorija napretka) — taj fajl NIJE imao nikakvu zaštitu (obično `load_state()`/`save_state()`, bez `fcntl` ili bilo kakvog compare-and-swap).

## Baseline — dokazano, ne pretpostavljeno

20 KONKURENTNIH poziva `circuit_breaker.py` na isti, prazan `loop_state.json` (svaki sa jedinstvenim `--error-signature`/`--lines-changed`):

```
iteration_count: 11 (očekivano 20)
error_signatures len: 11 (očekivano 20)
lines_changed_history len: 11 (očekivano 20)
```

**9 od 20 (45%) upisa izgubljeno** — klasična lost-update rasa: svaki proces učita CEO state dict, izmeni svoju lokalnu kopiju, i upiše NAZAD CEO dict — poslednji koji upiše potpuno prepiše sve izmene svih ostalih procesa koji su učitali stanje PRE tog upisa, ne samo jedno polje.

Ovo je **ozbiljnije** od `registry.json` slučaja, jer je `circuit_breaker.py` SAMA bezbednosna ograda sistema (Hard Ceiling na broj iteracija/wall-clock, "repeated error"/"no progress" trip). Izgubljeni upisi bi mogli TIHO onesposobiti baš tu ogradu:
- Potcenjen `iteration_count` → Hard Ceiling nikad ne okine, iako je stvarno izvršeno više iteracija nego što je zabeleženo.
- Izgubljeni unosi u `error_signatures`/`lines_changed_history` → "repeated error"/"no progress" trip nikad ne okine, iako se greška/stagnacija stvarno ponavljala.

I dalje važi: trenutni dizajn je jedan-proces-po-worktree-u, pa je ovo preventivna ispravka za hipotetički budući scenario (npr. supervizor/monitoring proces koji bi takođe pisao, ili bag koji duplira poziv), ne aktivan bag danas.

## Ispravka

Primenjen **isti, već proveren obrazac** kao `registry_write.py` (namerno, ne izmišljen novi mehanizam): `fcntl.flock()` ekskluzivni lock na posebnom `loop_state.json.lock` fajlu, drži se kroz CELU read-modify-write kritičnu sekciju (od `load_state()` do `save_state()`/`os.rename()`).

Konkretno:
- Cela postojeća logika (`main()`-ovo telo) premeštena je nepromenjena u novu `_run(args) -> int` funkciju.
- Novi `main()`: parsira argumente, kreira `.lock` fajl pored state fajla (`os.makedirs` odbrambeno pre), drži `fcntl.flock(lockf, fcntl.LOCK_EX)` kroz `_run(args)` poziv (`try`/`finally` sa `LOCK_UN`), vraća njegov exit kod.
- `save_state()` dodatno dobija PID-sufiks na privremenom fajlu (`{path}.tmp.{os.getpid()}` umesto `{path}.tmp`) — nije striktno neophodno sad kad je pristup serijalizovan lock-om, ali je jeftina odbrambena doslednost sa već proverenim `registry_write.py` obrascem.
- Nijedna postojeća grana logike (Hard Ceiling, clock skew, repeated error, no progress, itd.) nije menjana — samo premeštena unutar zaštićene kritične sekcije.

## Retest (na pravom Mac-u)

- **Isti 20-konkurentnih-poziva test, sa ispravkom**: `iteration_count: 20/20`, `error_signatures len: 20/20`, `lines_changed_history len: 20/20`, svi potpisi jedinstveni (nema duplikata/gubitka). Nema zaostalih `.tmp.*` fajlova (svi ispravno preimenovani).
- **Stres test, 50 konkurentnih poziva**: 20/20 → 50/50, ukupno vreme 0.385s, bez grešaka u ijednom pojedinačnom log fajlu. Nema deadlock/performans problema.
- **Puna regresija, OLD-vs-NEW skripta, svih 9 grana ponašanja** (sekvencijalno, jedan poziv): CONTINUE, PASS/model-based exit, hard ceiling iteracije, hard ceiling wall-clock, `state_file_unreadable`, `state_missing_fields`, clock skew, repeated error (3 ponovljene), no progress (3 zaredom ~0 izmena) — **svi identičan izlaz i exit kod, OLD i NEW**, bez ijedne razlike.
- **Sanity na pravom worktree-u**: kopija stvarnog `word-freq-bridge/.agent/loop_state.json`, pozvano sa `--verify-status PASS` → ispravan `STOP`/`verify_passed`, `iteration_count` ispravno inkrementiran, `status: completed`.
- **`registry_write.py` sanity** (postojeća, ranije ispravljena zaštita): 20 konkurentnih upisa na `registry.json` → 20/20 task-ova upisano, bez gubitka — potvrđeno da ranija ispravka i dalje ispravno radi.

## Šta ova ispravka namerno ne rešava

- `fcntl.flock` je POSIX-specifičan (Linux/macOS) — ne radi na Windows-u. Dovoljno za ovaj kontekst (macOS/Linux dev mašine), isti kompromis kao već prihvaćen u `registry_write.py`.
- Lock fajl (`loop_state.json.lock`) se ne briše nikad — trajno ostaje pored state fajla. Ovo je standardan obrazac (isto kao `registry.json.lock`), bezopasno, ne raste u veličini.
- Ne rešava scenario u kom bi DVA RAZLIČITA worktree-a nekako delila isti `loop_state.json` (dizajn to i dalje sprečava na drugom nivou — svaki worktree ima sopstveni `.agent/` direktorijum).

## Fajlovi

- `agentic-loop-engineer/scripts/circuit_breaker.py` — izmenjen. Stara verzija sačuvana kao `circuit_breaker.py.pre-stavka4-backup` na Mac-u.
- `agentic-loop-engineer/scripts/registry_write.py` — nepromenjen (već ispravan iz ranije runde), samo re-verifikovan.

**Distributivni `.skill` fajl još nije ažuriran** — ovo je bila POSLEDNJA stavka u dogovorenom redosledu (1→5→2→3→4); pakovanje sledi kao poseban korak.

## Runda review — nezavisan adversarijalan review (16. sept, isti dan)

Po ustaljenom obrascu, spawn-ovan je svež subagent da nezavisno proveri gorenavedene tvrdnje. **Glavni mehanizam potvrđen ispravan** — baseline rasa (10-50% gubitka, tajming-zavisno), retest (20/20, 50/50 bez gubitka), regresija (svih 9 grana ponašanja bit-za-bit identično OLD/NEW), i `registry_write.py` sanity — sve nezavisno reprodukovano preko `device_bash`-a, uz dodatnih 170+ konkurentnih poziva kroz više rundi radi hvatanja retkih tajming-zavisnih problema (nijedan nađen).

Review je aktivno tražio NOVE rizike koje je SAMO dodavanje `fcntl.flock`-a moglo uneti (pre ispravke nije postojao nikakav lock, pa nijedan lock-specifičan rizik nije mogao ni postojati) i našao:

- **H3 (potvrđen, stvaran bag)** — otvaranje `.lock` fajla nije bilo ničim zaštićeno: ako `{state}.lock` VEĆ POSTOJI kao DIREKTORIJUM (ili je nedostupan iz nekog drugog OSError razloga), skripta je bacala GOLI Python traceback (`IsADirectoryError`) umesto strukturiranog STOP JSON-a — sa pogrešnim exit kodom 1 koji bi pozivalac mogao protumačiti kao Hard Ceiling, ne kao crash.
- **H1 (legitiman, nov arhitektonski rizik, ne aktivan bag)** — `fcntl.flock(lockf, fcntl.LOCK_EX)` bez `LOCK_NB`/timeout-a blokira NEODREĐENO. Pre ispravke nijedan lock nije postojao, pa zaglavljen proces NIKAD nije mogao blokirati drugi — sad MOŽE (hipotetički budući drugi pisac koji ostane živ ali zaglavljen, ne ubijen — `kill -9` slučaj je testiran i OS ispravno automatski oslobađa `flock`, ali "živ i zaglavljen" ostaje rizik). U tenziji sa filozofijom istog fajla ("STOP je bezbedniji default od tihog visenja bez nadzora").
- **H5 provera** (da li je `$HOME/mnt/loops` neki mrežni/FUSE mount na kom je `flock` poznato nepouzdan) — review je testirao SAMO na `/tmp` (lokalni ext4), ne na stvarnoj `mnt/loops` putanji, i flagovao ovo kao ograničenje. Ja sam to naknadno zatvorio: isti 20-konkurentnih-poziva test pokrenut DIREKTNO na `$HOME/mnt/loops/tmp-stavka4-fstest` (stvarni bridge kroz koji prave worktree-ove idu) → 20/20, bez gubitka, bez grešaka. `flock` je potvrđeno pouzdan na ovoj konkretnoj putanji za ovo okruženje.
- Ostale hipoteze (H2 - truncate interferencija, H4 - tačnost per-process izlaza pod konkurencijom) - **WRONG/odbačene**, aktivno testirano i nije nađen problem.
- Dodatni, van-opsega nalaz: neuhvaćen tip-greška u state fajlu (`max_iterations` kao string) daje identičan (neuhvaćen, ružan) traceback i u OLD i u NEW skripti — pre-postojeća rupa, ne uvedena ovom ispravkom, van opsega stavke #4.

### Ispravke (H1, H3)

- **H3**: `os.makedirs`/`open(lock_path, "w")` sad unutar `try/except OSError`, vraća `_stop_json("lock_unavailable", detail=...)` (isti STOP+JSON+escalate obrazac kao ostale greške), exit 2.
- **H1**: zamenjen blokirajući `fcntl.flock(lockf, fcntl.LOCK_EX)` petljom koja pokušava `LOCK_EX | LOCK_NB` uz kratko spavanje (0.1s) do `LOCK_TIMEOUT_SEC = 30`; ako lock nikad ne oslobodi u tom roku, vraća `_stop_json("lock_timeout", timeout_sec=30)` umesto večnog čekanja.

### Retest posle H1/H3 ispravki (na pravom Mac-u)

- **H3 fix potvrđen**: lock fajl kao direktorijum → `{"decision": "STOP", "reason": "lock_unavailable", "escalate_to_human": true, "detail": "[Errno 21] Is a directory: ..."}`, exit 2 — čist, strukturiran izlaz umesto traceback-a.
- **H1 fix potvrđen, dva scenarija**: (a) drugi proces drži lock 5s (kraće od 30s timeout-a) → poziv čeka ~4.6s pa ispravno nastavlja i vraća tačan rezultat; (b) drugi proces drži lock 40s (DUŽE od 30s timeout-a) → poziv čeka tačno ~30.06s pa vraća `{"decision": "STOP", "reason": "lock_timeout", "escalate_to_human": true, "timeout_sec": 30}`, exit 2 — potvrđeno da VIŠE NEMA večnog čekanja.
- **Puna regresija ponovljena**: 20 konkurentnih poziva (20/20, bez gubitka, bez traceback-ova), svih 9 grana ponašanja (CONTINUE/PASS/hard-ceiling-iteracije/hard-ceiling-wallclock/missing-fields/clock-skew/invalid-started-at) — OLD i NEW i dalje bit-za-bit identični.

### Zaključak runde review-a

Stavka #4 se sada smatra završenom sa potvrđenom nezavisnom proverom, uključujući ispravku oba nalaza (H1, H3) i zatvaranje H5 provere na stvarnoj putanji. Ovo je bila poslednja stavka u dogovorenom redosledu — **sledi zajedničko pakovanje `.skill` fajla (#1, #5, #2, #3, #4)**.
