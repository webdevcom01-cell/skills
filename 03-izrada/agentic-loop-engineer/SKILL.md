---
name: agentic-loop-engineer
description: Production skill za dizajn, izvršavanje i upravljanje self-prompting autonomnim agent petljama, sa izvršivim skriptama za worktree izolaciju, maker-checker verifikaciju, circuit breaker i human-in-the-loop ograde. v2 - zatvara gap-ove iz v1 concept checklist-e.
---

# Agentic Loop Engineering System (v2)

Ovo NIJE samo checklist principa (to je bio v1) - ovo je skill koji upućuje
na izvršive skripte u `scripts/`, konfiguraciju u `config/` i šablone u
`templates/`. Detaljno obrazloženje SVAKE odluke ispod je u
`references/deep-analysis.md` - učitaj ga samo kad ti treba obrazloženje,
ne za svako pokretanje (progressive disclosure).

## 0. Kad koristiti ovaj skill
Kad pokrećeš zadatak koji zahteva više od jedne Think→Act→Observe→Verify
iteracije bez stalnog ljudskog nadzora nad svakim korakom - bilo jedan
agent u worktree-u, bilo više paralelnih agenata.

**Ne koristi ovo** za jednokratne izmene koje ti sam radiš u glavnoj sesiji
- overhead orkestracije se isplati tek kad zadatak ima realnu šansu da
traje više iteracija ili da se paralelizuje.

## 1. Pre svakog pokretanja - Pre-Flight Checklist
1. [ ] Definisan **jedan** konkretan cilj po task-u, sa determinističkim
       acceptance criteria (ne "poboljšaj X", nego "test suite Y prolazi I
       Z je implementirano").
2. [ ] `hooks/settings.snippet.json` je ubačen u `.claude/settings.json` u
       worktree-u (PreToolUse hook -> `scripts/guardrail_check.py`) - ovo
       je jedini korak koji nikad ne preskačeš, čak ni za "brz test". Bez
       ovog hook-a, `config/guardrails.yaml` je samo dokumentacija, ne
       zaštita - proveri da hook stvarno okida (vidi "Verifikacija
       guardrails-a" ispod) pre nego što pustiš agenta da radi bez nadzora.
3. [ ] Hard Ceiling brojevi eksplicitno postavljeni (`max_iterations`,
       `max_wall_clock_sec`) - default u `spawn-worktree-agent.sh` je
       namerno konzervativan (5 iteracija / 30 min), podigni tek posle
       dokazane stabilnosti.
4. [ ] Odlučeno KO/ŠTA radi Checker korak (svež subagent/proces, nikad isti
       kontekst kao Maker).
5. [ ] Ako `task_spec.md`/`plan.md` imenuje konkretan CLI alat/ORM/build-tool sa
       SOPSTVENIM mrežnim zahtevima mimo standardnog paket-registry-ja (npr.
       Prisma, Playwright, native build alati) — taj alat je STVARNO pokrenut
       (smoke-test komanda, npr. `npx <alat> --version`) u ISTOM okruženju gde
       će Maker raditi, PRE spawn-a. "npm install je prošao" ne dokazuje da će
       alat raditi - proveren, stvaran slučaj: Prisma CLI puca na svakom pozivu
       (uklj. `-v`) jer preuzima native binarni fajl sa drugog hosta od npm
       registry-ja, koji može biti blokiran network politikom dok je sam
       registry dostupan.
6. [ ] Pre PRVOG commit-a baznog repoa (pre `spawn-worktree-agent.sh`), proveri
       da `.agent/` (i bilo šta iz ranijeg ručnog testiranja guardrail/checker
       skripti u tom folderu) NIJE već tu ili je u `.gitignore` - `.git/info/exclude`
       zaštita koju ova skripta pravi PO WORKTREE-U ne pokriva sadržaj koji je
       već ušao u bazni commit pre nego što je worktree i napravljen.

## 2. Worktree izolacija
Koristi `scripts/spawn-worktree-agent.sh <task-id> <base-branch> <prompt-file> [max-iterations]`.

Pravila koja skripta sprovodi:
- Jedinstveno ime grane po task-u i timestamp-u (nikad dupli checkout iste grane).
- Zavisnosti (node_modules/venv) se instaliraju PO worktree-u - koristi
  pnpm/uv sa shared cache-om da to ne bude sporo.
- Cleanup: `git worktree remove <path>` posle merge-a ili discard-a.
  Worktree stariji od 24h bez aktivnosti u `.agent/loop_state.json` se
  smatra napuštenim - proveri i obriši ručno dok ne automatizuješ.
- Agent NIKAD ne radi `git merge`/`git push` na zaštićenu granu sam
  (to je guardrails.yaml `require_human` akcija) - agent priprema
  patch/PR, Checker validira, čovek (ili odvojen merge-bot proces) merguje.

## 3. Think → Act → Observe → Verify → Repeat
- **Think**: plan za iteraciju, upisan u `templates/scratchpad.md` PRE
  bilo kog tool poziva.
- **Act**: jedan atomičan tool poziv, proveren protiv `guardrails.yaml`.
- **Observe**: sirov rezultat (stdout/stderr/diff), bez interpretacije.
- **Verify**: pokreni `scripts/checker-verify.sh <worktree-dir>` - OVO JE
  POSEBAN KORAK, nikad se ne meša sa Observe. Vraća deterministički
  verdikt (PASS/FAIL/NO_APPLICABLE_CHECKS) + max_confidence
  (CONFIRMED/PLAUSIBLE/NONE).
- **Repeat**: pozovi `scripts/circuit_breaker.py` sa rezultatom Verify
  koraka - ON odlučuje CONTINUE ili STOP, ne agent sam.

## 4. Maker-Checker izolacija
- Maker radi u worktree-u, produkuje diff + kratak izveštaj.
- Pokreni `scripts/prepare-checker-bundle.sh <worktree-dir> <base-branch>` -
  ovo FIZIČKI izoluje šta Checker vidi (poseban direktorijum sa samo
  task_spec.md, diff.patch, verify_result.json), umesto da izolacija
  zavisi od toga da se neko seti da ne pokaže Checker-u scratchpad.md.
- Checker se pokreće u **potpuno svežem kontekstu** (nov subagent/proces,
  cwd = bundle direktorijum) - nikad Maker-ovo rezonovanje ni istoriju
  pokušaja.
- Verdikt ima dva nivoa: `CONFIRMED` (deterministički dokazano - test/lint
  prošao I diff pokriven) vs `PLAUSIBLE` (izgleda ispravno, nema
  determinističkog dokaza). Koristi isti `CONFIRMED/PLAUSIBLE` obrazac kao
  `adversarial-verify` skill - ne izmišljaj novu šemu.
- Ako Maker menja logiku bez odgovarajućih test izmena, max verdikt je
  automatski `PLAUSIBLE`, nikad `CONFIRMED` (sprovodi `checker-verify.sh`).
- Ako nema primenljive determinističke provere (`NO_APPLICABLE_CHECKS`,
  exit 2) - to je automatski signal za human review, ne tih `PASS`.

## 5. Dual Stopping Conditions
- **Model-based exit**: Verify PASS + svi acceptance criteria iz
  scratchpad checklist-e otkačkirani.
- **Hard Ceiling** (van modelovog domašaja, sprovodi `circuit_breaker.py`):
  `max_iterations`, `max_wall_clock_sec`, i token budžet (za AgentStack
  agente koristi postojeći `as_set_agent_budget`/`as_get_agent_budget`; za
  Claude-Code-native/"Nivo A" agente prati `usage` polje iz session loga
  ručno dok se ne izgradi automatizacija).
- **Circuit breaker za ponovljenu grešku**: ista `error_signature` 3 puta
  zaredom → STOP + eskalacija čoveku, sa punim kontekstom prethodnih
  pokušaja.
- **Circuit breaker za nula-napredak**: 3 iteracije zaredom sa ≤2
  izmenjene linije dok je Verify i dalje FAIL → STOP + eskalacija.
- Ako se ovo koristi kao AgentStack heartbeat/autonomous orchestrator
  (bez čoveka po ciklusu) - dodaj i **stage-gate limit** (broj faza koje
  smeju proći bez ljudske potvrde) kao dodatni wrapper oko heartbeat-a;
  AgentStack heartbeat mehanizam sam po sebi to ne sprovodi.

## 6. Memory Engineering & Konkurentnost
- In-band memorija: `templates/scratchpad.md` (radni plan, kratak, čita se
  u celosti) i `templates/task_log.md` (append-only istorija iteracija).
- Progressive disclosure: ovaj SKILL.md ostaje kratak; detaljno
  obrazloženje ide u `references/deep-analysis.md`, učitava se na zahtev.
- Zaštita deljenih fajlova (SAMO registry.json / centralizovan task_log ako
  ga koristiš; worktree fajlovi su već izolovani i ne trebaju ovo):
  `scripts/registry_write.py` koristi `fcntl.flock` ekskluzivni lock oko
  cele read-modify-write sekcije. **Ispravka posle trećeg kruga provere:**
  originalna verzija je tvrdila "optimistic concurrency" (hash-proveri-pa-
  upiši), ali je to bio neispravan TOCTOU obrazac - nezavisan test sa 30-40
  paralelnih pisaca je pokazao gubitak 25-80% upisa. Sa `flock`-om, isti test
  (40 paralelnih pisaca) čuva svih 40 bez gubitka - videti
  `references/AUDIT-nalaz.md`. Ne veruj "zvuči sofisticirano" opisu bez testa.
- Out-of-band "Dreaming": periodičan (scheduled task, ne in-process cron)
  batch review `task_log.md` fajlova preko više task-ova, traži
  ponavljajuće error obrasce, predlaže patch za SKILL.md/guardrails.yaml.
  Predlog ide čoveku na odobrenje - koristi postojeći `instincts-updater`
  skill za ovaj korak, ne grade novi alat.

## 7. Human-in-the-Loop Guardrails
Puna, pattern-based lista je u `config/guardrails.yaml` (baza podataka,
git force/merge na zaštićene grane, produkcioni deploy - i preko bash-a i
preko MCP alata kao Railway/Gmail, `rm -rf`, rotacija kredencijala).
**Sprovedena je stvarnim Claude Code PreToolUse hook-om** (`scripts/guardrail_check.py`,
ožičen preko `hooks/settings.snippet.json`), ne samo tekstom u ovom fajlu:
- Hook proverava SVAKI tool poziv (Bash I MCP alate) pre izvršenja - nikad
  oslonjeno na to da agent sam prepozna rizik.
- Dve akcije: `block` (nikad se ne odobrava kroz agenta - čovek izvršava
  ručno, van petlje) i `require_human` (hook uvek vrati "deny" + upiše
  pending zapis; čovek pregleda i pokreće `scripts/approve.sh <worktree> <token>`
  što daje JEDNOKRATNU dozvolu za tačno tu komandu - agent mora ponovo
  poslati identičnu akciju, ne dobija blanket dozvolu za tip komande).
- **Zašto ne koristimo `permissionDecision: "ask"`** (koji zvanično postoji,
  vidi `references/AUDIT-nalaz.md` treći krug): u headless/autonomnoj sesiji
  (`claude -p`, tačno naš ciljani slučaj) Anthropic-ova dokumentacija
  eksplicitno kaže da "ask" nema kome da postavi pitanje pa se proces gasi -
  gubi se mogućnost nastavka. `deny + pending-approval + approve.sh` radi
  identično u interaktivnoj i headless sesiji i dozvoljava asinhroni
  nastavak. Ako UVEK radiš interaktivno, `"ask"` je jednostavnija alternativa.
- Fail-safe: ako `guardrails.yaml` ne može da se učita, nedostaje PyYAML,
  ili se desi BILO KOJA neočekivana greška pri obradi pojedinačnog tool
  poziva (npr. neispravan regex, neočekivan oblik `tool_input`), hook je
  fail-closed (blokira taj poziv) umesto fail-open.
- **Poznato ograničenje (disclosure, ne propust):** regex/pattern provera
  na tekstu komande je nužna ali ne dovoljna odbrana (zaobilazi se alias-om,
  env-var indirekcijom, obfuskacijom). Zato MORAJU postojati i nezavisni
  slojevi: git branch protection na remote-u za zaštićene grane, i
  least-privilege/scope-ovani API ključevi za MCP konektore, tako da agent
  fizički ne poseduje kredencijal koji može da dotakne produkciju.

### Verifikacija guardrails-a (uradi PRE prvog pravog pokretanja)
```
echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"},"cwd":"'$(pwd)'"}' \
  | python3 scripts/guardrail_check.py
```
Očekivano: JSON sa `"permissionDecision": "deny"` i upisan fajl u
`.agent/pending_human_approval/`. Ako to ne vidiš, hook nije ožičen
ispravno - NE nastavljaj dok se ovo ne popravi.

## 8. Prvi prototip - redosled
1. Jedan zadatak, jedan agent, bez paralelizma.
2. `guardrails.yaml` provera aktivna od prve komande.
3. Hard Ceiling = 5 iteracija za prvi test.
4. `checker-verify.sh` kao odvojen proces posle svake iteracije.
5. Ručno simuliraj konflikt na deljenom fajlu da potvrdiš da
   `registry_write.py` detektuje i retry-uje.
6. Tek posle 3-5 uspešnih realnih zadataka → drugi paralelni worktree.
7. Tek posle stabilnog paralelizma → AgentStack heartbeat integracija sa
   stage-gate limitom.

## Reference fajlovi
- `references/deep-analysis.md` - puno obrazloženje svake odluke iznad
  (učitaj samo kad ti treba "zašto", ne za rutinsko pokretanje)
- `references/AUDIT-nalaz.md` - drugi krug provere (posle v2): pronađeni
  bagovi, standardi protiv kojih je verifikovano (sa izvorima), i svesno
  prihvaćeni preostali rizici
- `references/VERIFIKACIJA-treci-krug.md` - treći krug: NEZAVISNA verifikacija
  (poseban subagent + moja sopstvena odvojena reprodukcija) svake tehničke
  tvrdnje, uključujući ispravku jedne pogrešne tvrdnje iz drugog kruga
  (permissionDecision "ask" ipak postoji) i dve dodatne stvarne greške u
  kodu (registry_write.py konkurentnost, regex bypass preko više redova)
- `references/PRVI-ZIVI-PILOT.md` - **NAJAŽURNIJI izveštaj, pročitaj ga pre
  prve produkcione upotrebe.** Prvi pilot na PRAVOM uređaju (ne cloud
  sandbox), sa punim redosledom koraka (spawn → izmena → commit → verify →
  bundle) na pravom git repo-u - otkrio 3 nova buga koja tri prethodne runde
  (sve rađene izolovano, po skripti) nisu mogla da vide, uključujući jedan
  kritičan (necommit-ovan `.agent/` je mogao da probije Domen 2 Maker-Checker
  izolaciju kroz `diff.patch`). Takođe eksplicitno dokumentuje šta OVAJ tip
  pilota NE može da dokaže (stvarna Claude Code hook-dispatch mehanika) i
  zašto "Verifikacija guardrails-a" ispod ostaje obavezan korak.
- `references/OJACAVANJE-runda1-paralelizam.md` - stavka #1 ojačavanja
  (pravi paralelizam, nikad ranije testiran): konkurentan spawn istog
  task-id-a mogao je korumpirati/izgubiti fajlove pobedničkog worktree-a,
  ne samo ostaviti siroče; ispravljeno atomičnom mkdir-lock rezervacijom
  task-id-a, uključujući PID/vreme-svesnu detekciju zaglavljenog claim-a
- `references/OJACAVANJE-runda2-sdd-most.md` - stavka #5 ojačavanja (most
  sdd-workflow → agentic-loop-engineer, nikad ranije testiran): Maker
  strana radi preko tankog task_spec.md pointera; Checker strana je imala
  pravi bag (bundle nije sadržao specs/ na koje task_spec.md upućuje) -
  ispravljeno, uz dva dodatna nalaza u samoj ispravci (curenje specs/ za
  nepovezane feature-e, cp -R ne prati symlink)
- `references/OJACAVANJE-stavka2-guardrail-indirekcija.md` - stavka #2
  ojačavanja (regex guardrail bypass): alias/env-var indirekcija, eval+base64,
  $IFS/backslash whitespace trikovi - svih 6 varijanti dokazano zaobilazilo
  originalni regex, ispravljeno normalizacijom + indirection-primitive
  pravilima + cross-call var/alias pamćenjem; nezavisan review našao
  kritičan bag (odbijena komanda je svejedno trovala state) i bag dubine
  lanca dodela, oba ispravljena
- `references/OJACAVANJE-stavka3-checker-coverage.md` - stavka #3
  ojačavanja (checker-verify.sh heuristika): otkriven ozbiljniji,
  ranije nedokumentovan bag (git diff HEAD slep na progresivno komitovan
  rad), bag klasifikacije fajlova, i dodat nov, jači signal (merena
  pokrivenost linija za Python preko coverage_check.py); nezavisan review
  našao i ispravio 4 nova baga u samoj ispravci (najozbiljniji: pokrivenost
  potpuno slomljena za ćirilična imena fajlova)
- `references/OJACAVANJE-stavka4-circuit-breaker-lock.md` - stavka #4
  ojačavanja (poslednja u redosledu): circuit_breaker.py nije imao nikakvu
  zaštitu za loop_state.json, baseline dokazao gubitak upisa pod
  konkurencijom (45%); ispravljeno istim fcntl.flock obrascem kao već
  proveren registry_write.py; nezavisan review našao i ispravio 2 nalaza u
  samoj lock-ispravci (direktorijum kao lock fajl rušio skriptu;
  beskonačno blokirajući lock bez timeout-a)
- `references/OJACAVANJE-runda6-portable-repo-transfer-fix.md` - stavka #6
  ojačavanja: `scripts/portable-repo-transfer.sh` (git bundle export/import,
  dodat da reši worktree-`.git`-je-pokazivač problem iz DEPLOY runde 8) je u
  produkcionoj upotrebi (QR Kod Menadžer pilot, rundе 10-11) tri puta uživo
  pogodio isti bag - `git bundle verify` puca kad se skript pozove iz foldera
  koji sam po sebi nije git repo, čak i kad je bundle potpuno ispravan; i
  `import` podkomanda nije imala način da prenese NOVE komite u repo koji već
  postoji (samo fresh `git clone` u nepostojeći folder), pa se drugi/treći
  krug promena ručno zaobilazio preko `git fetch`+`merge --ff-only`. Oba
  ispravljena: `bundle_verify_anywhere()` proverava integritet preko
  jednokratnog scratch repoa (cwd-nezavisno), i nova `sync` podkomanda
  automatizuje inkrementalni fetch+ff-only-merge (sa jedinstvenim privremenim
  ref-om, garantovano obrisanim i na uspeh i na neuspeh; ff-only odbijen =
  ciljni repo netaknut, bez rebase/force). Dokazano uživo: export/import iz
  namerno ne-git cwd-a (ranije bi pucalo), sync sa auto-detekcijom grane,
  i sync koji čisto odbija na pravoj divergenciji (ciljni repo dobio lokalni
  commit koji bundle nema) - ciljni repo posle odbijenog sync-a bit-za-bit
  nepromenjen, privremeni ref obrisan.
- `scripts/` - izvršive skripte (worktree, checker, circuit breaker,
  registry, guardrail_check, approve, portable-repo-transfer)
- `config/guardrails.yaml` - destruktivne akcije (pravila)
- `hooks/settings.snippet.json` - wiring guardrail_check.py kao pravi
  Claude Code PreToolUse hook
- `templates/` - scratchpad.md, task_log.md
