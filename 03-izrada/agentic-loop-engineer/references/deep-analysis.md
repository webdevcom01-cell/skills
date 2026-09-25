# Duboka analiza: Agentic Loop Engineering sistem

**Status:** Pre-implementaciona analiza (v1 SKILL.md je koncept/checklist, ne izvršni sistem)
**Kontekst:** Ovo direktno nastavlja tvoj "Nivo A" agent rad (Claude-Code-native agent, bez API ključa, radi kroz Claude Code sesiju) i pokriva gap koji je enterprise-agent-readiness skill ostavio otvoren — taj skill trenutno zna da procenjuje samo AgentStack `as_*` agente, ne i ovaj tip petlje.

---

## 0. Opšta ocena polaznog SKILL.md

Dokument koji si poslao je **checklist/mentalni model**, ne sistem. To nije loše — SKILL.md fajlovi i treba da budu kratki i da upućuju na reference — ali trenutno nema nijedne konkretne komande, fajl-formata, threshold vrednosti ili API poziva. Svaka stavka je imenovana ("Worktrees izoluju agente", "Hard Ceiling postoji") ali nijedna nije definisana do nivoa da je možeš pokrenuti. Ispod je analiza po sve tražena 4 domena, plus konsolidovan gap-registar i prototip.

---

## 1. Architecture & Worktree Isolation

### Šta v1 kaže
"Worktrees izoluju svakog paralelnog agenta u svoj Git worktree/working directory da spreči file lock kolizije." Cilj je tačan, mehanizam nije specificiran.

### Tehnička analiza

**Git worktree osnove koje moraš rešiti eksplicitno:**

- Jedan `git worktree add ../wt/<task-id> -b agent/<task-id> <base-branch>` po agentu. Svaki worktree ima svoj `.git` pointer fajl (ne pun repo), pa je jeftino kreirati i brisati, ali **deli isti `.git/objects`** — konflikti se ne dešavaju na nivou objekata, samo na nivou radnih fajlova, što je tačno ono što želiš.
- **Problem koji v1 ne pominje:** dva worktree-a ne mogu imati checked-out istu granu istovremeno (`fatal: '<branch>' is already checked out`). Orkestrator MORA generisati jedinstveno ime grane po task-u (`agent/<task-id>-<timestamp>`), nikad da agent radi direktno na `main`/`develop`.
- **node_modules / venv problem:** svaki worktree je pun radni direktorijum — ako imaš Node/Python projekat, svaki paralelni agent treba svoju instalaciju zavisnosti, što je sporo i troši disk. Rešenje: `pnpm` sa shared store (`pnpm install` je jeftin po worktree-u jer linkuje iz globalnog cache-a), ili `uv`/`virtualenv` sa shared pip cache. Ovo MORA biti u pre-flight koraku orkestracije, inače prvi paralelni test će biti 10x sporiji nego što očekuješ.
- **Port konflikti:** ako agent pokreće dev server ili test runner koji binduje port, dva paralelna worktree-a će se sudariti na istom portu. Treba dodeliti port range po task-id-u (npr. `base_port + (hash(task_id) % 100)`).
- **Cleanup je obavezan korak, ne opcija:** `git worktree remove` posle merge-a ili discard-a; zaboravljeni worktree-ovi se akumuliraju i `git worktree list` postaje nečitljiv, a disk se puni. Treba TTL politika (npr. auto-prune worktree-ova stariji od 24h bez aktivnosti).
- **Merge strategija nije definisana u v1** — ko i kako vraća rezultat u glavnu granu? Predlog: agent nikad ne radi `git merge`/`git push` na zaštićenu granu sam (to je destruktivna akcija — vidi Domen 5); agent otvara PR/napravi patch, Checker validira, **čovek ili checker-only-merge bot** izvršava merge.

### Think → Act → Observe → Verify → Repeat ciklus — konkretna definicija

U v1 ovo je samo imenovano. Evo mapiranja na stvarni Claude Code / agentic okvir:

| Faza | Šta se konkretno dešava | Artefakt |
|---|---|---|
| **Think** | Model eksplicitno piše plan pre alata (u ovoj sesiji: `<thinking>` blok ili reasoning pre tool_use) | zapis u `scratchpad.md` — "Plan za iteraciju N" |
| **Act** | Jedan atomičan tool call (edit, bash, test run) — NE serija nepregledanih poziva | tool_use log |
| **Observe** | Sirovi rezultat alata (stdout/stderr/diff) se čita bez interpretacije | tool_result |
| **Verify** | **Deterministički** korak — lint/test/typecheck/schema (vidi Domen 2). Ovo je faza koja u v1 fali kao eksplicitan, obavezan checkpoint — bez nje "Verify" se stopi sa "Observe" i model samo *tvrdi* da je uspeo | exit code + strukturisan JSON verdict |
| **Repeat** | Nova iteracija SAMO ako Verify=FAIL i nismo dostigli Hard Ceiling (Domen 3) | inkrement `iteration_count` u `loop_state.json` |

Ključna praznina: v1 ne razdvaja "Observe" od "Verify" kao odvojene korake. Ako ih spojiš, dobijaš klasičan "agent kaže da je gotovo jer je pročitao svoj sopstveni output i poverovao mu" — ovo je tačno mehanizam Verification Gap-a iz Domena 2.

---

## 2. Maker-Checker Split & Objective Verification

### Šta v1 kaže
"Maker NIKAD ne evaluira sopstveni output; Checker validira protiv specifikacije." Princip je ispravan, ali v1 ne kaže **kako** se ta izolacija tehnički sprovodi.

### Tehnička analiza

**Razdvajanje mora biti na nivou konteksta, ne uloge.** Ako isti chat/context window prvo "piše kod kao Maker" pa onda "prekopira šešir i kaže da je sad Checker", to nije razdvajanje — model i dalje ima pristup svom prethodnom rezonovanju i racionalizaciji, i statistički će potvrditi sopstveni rad (confirmation bias je jednako prisutan kod LLM-a kao i kod ljudi koji recenziraju svoj kod). Ovo je tačno "Verification Gap" koji pominješ.

**Ispravna implementacija (i ono što već koristiš u drugim skillovima, npr. `adversarial-verify`):**
1. Maker radi u svom worktree-u/kontekstu i produkuje diff + kratak "šta sam uradio" izveštaj.
2. Checker se pokreće kao **potpuno svež subagent/sesija** (Task/Agent tool sa novim kontekstom, ili čak novi `claude -p` proces) kome se daje SAMO: (a) originalna specifikacija/zahtev, (b) git diff, (c) rezultati determinističkih provera. Checker-u se namerno NE prosleđuje Maker-ovo rezonovanje ni njegov "success narrative" — to je ono što sprečava rubber-stamping.
3. Checker vraća strukturisan verdikt sa dva nivoa poverenja, ne binarni "OK/nije OK": `CONFIRMED` (deterministički dokazano — test/lint prošao i logika proverena čitanjem diff-a) vs `PLAUSIBLE` (izgleda ispravno, ali nema determinističkog dokaza — npr. ponašanje koje se ne može automatski testirati). Ovo mapira tačno na tvoj postojeći `adversarial-verify` i `ReportFindings` obrazac (`verdict: CONFIRMED|PLAUSIBLE`) — **iskoristi tu istu šemu ovde umesto da izmišljaš novu.**

**Deterministički slojevi provere (redosled, od jeftinijeg ka skupljem):**
1. **Sintaksa/format** — linter (eslint/ruff/gofmt), pre bilo čega drugog (sekunde).
2. **Tipovi** — `tsc --noEmit`, `mypy`, itd. (sekunde do desetine sekundi).
3. **Unit testovi** — postojeći + novi testovi koje je Maker OBAVEZAN da doda za svaku promenu ponašanja. Ako Maker ne doda test, Checker automatski vraća `PLAUSIBLE` maksimalno, nikad `CONFIRMED`.
4. **Schema/contract validacija** — za API promene: zod/pydantic šema, OpenAPI diff, DB migration dry-run.
5. **Integration/E2E** — najskuplje, pokreće se samo ako prethodni slojevi prođu.

**Gap u v1 koji je ozbiljan:** ne postoji pravilo šta se dešava kada NEMA determinističkog testa za dati zadatak (npr. "poboljšaj copy na landing page-u", "restrukturiraj scratchpad format"). Za takve zadatke, Checker MORA eksplicitno reći "nema determinističkog kriterijuma, verdikt je subjektivan" i to se tretira kao automatski razlog za dodatni human-in-the-loop review, a ne za tihi `CONFIRMED`.

---

## 3. Dual Stopping Conditions & Circuit Breakers

### Šta v1 kaže
Model-based exit (`/goal`) + Hard Ceiling (max broj pokušaja/token trošak). Princip tačan, brojevi i mehanizam beskonačne petlje nisu definisani.

### Tehnička analiza

**Dva nezavisna limita, oba moraju biti tvrdo kodirana (ne "sugerisana" modelu):**

1. **Model-based exit** — agent sam proglašava završetak kada su ispunjeni eksplicitni, unapred definisani acceptance criteria (ne "mislim da je gotovo" nego "test suite X prolazi I diff pokriva sve stavke iz spec.md checklist-e"). Ovo se implementira kao poslednji korak u Verify fazi, ne kao posebna komanda koju agent sam odlučuje da pozove.
2. **Hard Ceiling** — MORA biti van modelovog domašaja, tj. proverava ga orkestrator (spoljni skript), ne sam agent, jer agent koji je zapao u petlju neće pouzdano "primetiti" da je premašio limit. Tri nezavisne ograde, sve istovremeno:
   - `MAX_ITERATIONS` (npr. 10 Think→Act→Verify ciklusa po zadatku)
   - `MAX_WALL_CLOCK` (npr. 30 min po zadatku) — hvata slučaj kad je svaka iteracija "validna" ali ih ima previše
   - `MAX_TOKEN_BUDGET` / trošak — ako agent radi kroz tvoj AgentStack, ovo već imaš gotovo (`as_set_agent_budget`/`as_get_agent_budget`); za Claude-Code-native (Nivo A) agenta ovo ne postoji nativno i moraš ga graditi ručno praćenjem `usage` polja iz session loga.

**Beskonačna refleksija / ponavljanje grešaka — ovo v1 uopšte ne rešava, a to je najčešći stvarni failure mode.** Konkretan mehanizam (circuit breaker):
- Posle svakog Verify FAIL-a, izračunaj **potpis greške** = hash(tip_greske + fajl + poruka_normalizovana). Čuvaj poslednjih N potpisa u `loop_state.json`.
- Ako se **isti potpis** pojavi ≥3 puta zaredom → **trip breaker**: prekini petlju, ne pokušavaj ponovo, upiši `BLOCKED: repeated_error` i eskaliraj čoveku sa punim kontekstom (koje 3 pokušaja, koje greške, šta je probano).
- Ako se broj IZMENJENIH linija po iteraciji približava nuli dok je Verify i dalje FAIL (agent "kruži" bez napretka) → isti trip, drugi razlog (`no_progress`).
- Ovo je suštinski Circuit Breaker pattern iz SRE prakse, primenjen na agent loop — half-open stanje (jedan probni pokušaj posle pauze) je opciono za v2, za v1 prototip dovoljan je prost "otvoren = stani".

**Šta v1 ne pominje, a bitno je za tvoj slučaj:** ako ovo ikad radi u AgentStack-u kao heartbeat/autonomous orchestrator (tvoja pending stavka "Autonomous orchestrator variant... heartbeat running stage-gate phases without a human"), Hard Ceiling mora uključivati i **stage-gate limit** — koliko faza sme da prođe bez ljudskog potvrđivanja pre nego što se heartbeat sam pauzira. Trenutni AgentStack heartbeat (`as_set_heartbeat_schedule`/`as_set_heartbeat_context`) nema, koliko vidim iz dostupnih alata, ugrađen concept "broj neintervenisanih ciklusa" — to treba dodati kao wrapper logiku, ne osloniti se da heartbeat sistem to radi sam.

---

## 4. Memory Engineering & Optimistic Concurrency

### Šta v1 kaže
In-band memorija (scratchpad.md, task_log.md, grep/bash), optimistic concurrency preko hash-a, i "Dreaming" batch proces za čišćenje. Koncepti su tačni, ali nema formata fajlova ni algoritma za concurrency.

### Tehnička analiza

**Progressive Disclosure — ovo već radi tačno po ovom principu u pravom Claude Code SKILL sistemu:** frontmatter (`name`/`description`) se učitava uvek, telo skill-a se učitava tek kad je relevantno, reference fajlovi se učitavaju tek na eksplicitan zahtev. v1 SKILL.md ispravno imenuje princip, ali ga ne primenjuje na sebe — ceo v1 fajl je "pun tekst" bez razdvajanja na frontmatter-summary vs. detaljne reference fajlove. **Praktična posledica:** kad ovaj skill naraste (a hoće, čim dodaš worktree skripte, checker šablone, guardrails listu), sve to treba da bude u `references/*.md` fajlovima na koje SKILL.md upućuje, ne u samom SKILL.md — tačno po tvom postojećem skills-workflow obrascu (PATCH.md → reference fajlovi → SKILL.md → `package_skill.py` validacija).

**Optimistic concurrency — konkretan algoritam (compare-and-swap):**
```
1. read_version = hash(file_content) ILI eksplicitno version polje (npr. "version: 7" u frontmatter-u)
2. agent priprema izmenu lokalno (ne piše odmah)
3. pre upisa: re-read fajl, uporedi trenutni hash sa read_version
4. ako se poklapa → atomičan upis (write to .tmp + rename, NIKAD direktan overwrite - rename je atomičan na POSIX fs)
5. ako se NE poklapa → neko drugi je upisao u međuvremenu → reload, merge (ili re-queue), retry
```
Ovo je doslovno isti obrazac koji ova sesija koristi za `if_version` na Artifact DB i memory alatima koje ti sad koristim — dokazano radi za tačno ovaj problem (više paralelnih pisaca u jedan shared resurs) i predlažem da ga kopiraš 1:1 umesto da izmišljaš novi mehanizam.

**Multi-agent flotila — gde konflikt STVARNO nastaje:** ako je worktree izolacija urađena kako treba (Domen 1), agenti NE dele radne fajlove — svaki radi u svom direktorijumu. Konflikt nastaje samo na **deljenom orkestracionom stanju**: `registry.json` (lista aktivnih task-ova), zajednički `task_log.md` ili dashboard fajl. Za te specifične fajlove treba compare-and-swap iznad; za same worktree fajlove concurrency zaštita nije ni potrebna jer je izolacija već rešila problem na nivou fajl-sistema — v1 ovo meša u jedan pasus, što zamagljuje da su to dva različita problema sa dva različita rešenja.

**"Dreaming" out-of-band proces — konkretizacija:**
- Ovo se implementira kao **scheduled task** (ne lokalni cron — u ovoj vrsti sesije koristi se pravi scheduled-task mehanizam, ne in-process cron, jer in-process ne preživi restart sesije), koji periodično (npr. nedeljno) pokreće batch review svih `task_log.md` fajlova iz protekle nedelje.
- Output dreaming procesa ide u DVA mesta: (a) predlog patch-a za sam skill (mapira se direktno na tvoj `instincts-updater` skill — to je alat koji već imaš za tačno ovaj posao, nema potrebe da ga duplираš), (b) arhiviranje/kompresija starih task_log unosa da se in-band memorija ne naduva unedogled.
- v1 ne kaže KO odobrava promene koje dreaming proces predlaže — po principu iz Domena 5, promena pravila samog sistema (SKILL.md) treba da prođe kroz čoveka pre commit-a, dreaming proces predlaže patch, ne merguje ga sam.

---

## 5. Human-in-the-Loop Guardrails

### Šta v1 kaže
Nabraja kategorije (brisanje baze, javne poruke, produkcijski merge) ali ne daje mehanizam detekcije ni potpunu listu.

### Tehnička analiza

**Detekcija mora biti pattern-based na nivou orkestratora, ne "agent treba da zna da pita".** Model koji je usred izvršavanja zadatka statistički ima tendenciju da nastavi izvršavanje (to je doslovno cilj njegovog treninga — biti helpful i završiti zadatak). Osloniti se na to da će "setiti se" da stane pred rizičnom akcijom je slaba ograda. Umesto toga:
- Pre svakog `bash`/tool poziva, orkestrator (ili pre-tool-use hook, ako radiš u pravom Claude Code okruženju) proverava komandu protiv **explicit deny/confirm liste** (regex pattern match), ne protiv modelovog rasuđivanja.

**Konkretna, kompletnija lista destruktivnih/nepovratnih akcija (v1 lista je nepotpuna — dodato ono što fali):**

| Kategorija | Primeri | Zašto je nepovratno |
|---|---|---|
| Baza podataka | `DROP TABLE`, `TRUNCATE`, `DELETE FROM ... ` bez `WHERE`, migracije koje menjaju produkcionu šemu | Gubitak podataka, često bez backup-a u trenutku izvršenja |
| Git / kod | `push --force` (posebno na `main`/`master`), merge/rebase na zaštićenu granu, `git reset --hard` na deljenoj grani | Prepisuje istoriju za sve saradnike |
| Deploy | Deploy na produkcioni Railway environment, promena env varijabli u produkciji (`set-variables` na prod) | Direktno utiče na žive korisnike |
| Komunikacija | Slanje email-a, Slack poruka, bilo koje eksterne poruke ka trećim licima | Ne može se "povući" pošto je pročitano |
| Novac | Bilo koji payment/billing API poziv, promena cena, refund | Finansijska šteta |
| Fajl sistem | `rm -rf` van worktree granice, brisanje fajlova van scratch prostora | Gubitak rada koji nije bio pod git kontrolom |
| Bezbednost | Rotacija/brisanje API ključeva, promena permisija/rola korisnika | Može zaključati pristup ili otvoriti rupu |

- v1 ne kaže **šta agent radi dok čeka odobrenje** — ispravno ponašanje: agent PRIPREMI akciju (napiše tačnu komandu/diff koja bi se izvršila), STANE, i eksplicitno traži potvrdu sa punim opisom posledice ("Ovo će obrisati 40,000 redova iz tabele `orders` bez mogućnosti povratka. Nastaviti?") — nikad tiho "planiram da nastavim ako ne čujem ništa za 30s".
- **Fail-safe default:** ako orkestrator ne može sa sigurnošću da klasifikuje akciju (regex ne pokriva slučaj), default je STOP i pitaj, ne "verovatno je bezbedno, nastavi".

---

## 6. Konsolidovana lista nedostataka (prioritizovano po riziku)

1. **[KRITIČNO]** Nema mehanizma detekcije destruktivnih akcija van modelovog rasuđivanja (Domen 5) — bez ovoga, sve ostalo je kozmetika, jer jedan loš `rm -rf` ili `push --force` uništava poverenje u ceo sistem.
2. **[KRITIČNO]** Maker-Checker nije definisan kao izolacija konteksta, samo kao izolacija uloge — trenutna formulacija ne sprečava Verification Gap, samo ga imenuje.
3. **[VISOKO]** Nema circuit breaker algoritma za ponovljene greške/beskonačnu refleksiju — najčešći stvarni failure mode agentskih petlji, a v1 ga uopšte ne adresira konkretno.
4. **[VISOKO]** Hard Ceiling nije specificiran brojevima niti mestom izvršenja (mora biti van agenta, u orkestratoru) — kao tekst je dekorativan.
5. **[SREDNJE]** Worktree lifecycle (imenovanje grana, cleanup/TTL, merge strategija, port/dependency konflikti) nije definisan — radiće za prvi test, pući će posle par dana paralelnog rada.
6. **[SREDNJE]** Optimistic concurrency nema konkretan algoritam ni razliku između "izolovanih" (worktree) i "deljenih" (registry/log) fajlova.
7. **[SREDNJE]** Nema definisanog šta se dešava kad ne postoji deterministički test za zadatak — tiho pada na subjektivnu ocenu bez signalizacije.
8. **[NISKO]** "Dreaming" proces nema vlasnika odobrenja promena i nema jasnu vezu ka postojećem `instincts-updater` skillu — rizik dupliranja alata.
9. **[NISKO]** Sam SKILL.md ne primenjuje sopstveni "Progressive Disclosure" princip (nema `references/` strukturu).

---

## 7. Plan implementacije prvog prototipa

Cilj prve iteracije: **jedan zadatak, jedan agent, potpuna petlja end-to-end** — bez paralelizma za sada (paralelizam dodaješ tek kad je single-agent petlja dokazano stabilna; paralelizam preko nestabilne petlje samo umnožava haos N puta).

**Koraci:**
1. Postaviti `guardrails.yaml` i uključiti proveru PRE bilo kog bash poziva (čak i u single-agent modu — ovo je najjeftinija i najvažnija zaštita).
2. Pokrenuti jedan zadatak u worktree-u sa `spawn-worktree-agent.sh`, sa Hard Ceiling = 5 iteracija za prvi test (namerno nisko, da vidiš kako se ponaša circuit breaker pre nego što mu veruješ sa 15).
3. Nakon svake iteracije, pozvati `checker-verify.sh` kao **odvojen proces** (ne isti kontekst) — za v1 test dovoljno je da to bude čak i ti ručno, dok validiraš da li skripta daje smislen verdikt.
4. Voditi `task_log.md` sa version poljem, testirati compare-and-swap ručno tako što "simuliraš" drugog pisca (izmeniš fajl dok skripta radi) i proveriš da li detektuje konflikt.
5. Tek kad ovih 4 koraka rade pouzdano na 3-5 realnih zadataka → dodati drugi paralelni worktree i testirati port/dependency izolaciju.
6. Tek kad paralelizam radi → povezati sa AgentStack heartbeat-om za autonomni mod (tvoja pending stavka), sa stage-gate limitom kao dodatnim Hard Ceiling slojem.

Prateći fajlovi (isporučeni uz ovu analizu):
- `agentic-loop-engineer-v2/SKILL.md` — ažurirana verzija skill-a koja zatvara gap-ove 1, 2, 3, 4, 7, 9
- `agentic-loop-engineer-v2/scripts/spawn-worktree-agent.sh` — worktree orchestration
- `agentic-loop-engineer-v2/scripts/checker-verify.sh` — deterministički + CONFIRMED/PLAUSIBLE sloj
- `agentic-loop-engineer-v2/scripts/circuit_breaker.py` — potpis grešaka + trip logika
- `agentic-loop-engineer-v2/config/guardrails.yaml` — destruktivne akcije, pattern-based
- `agentic-loop-engineer-v2/templates/scratchpad.md`, `task_log.md` — in-band memorija sa version poljem

**Napomena o obimu:** ovo je prototip za validaciju koncepta, ne produkcioni sistem. Sve numeričke vrednosti (5 iteracija, 3 ponovljene greške, 30 min wall clock) su početne pretpostavke — podesi ih nakon prvih par realnih pokretanja, ne pre.
