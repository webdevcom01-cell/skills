# Prvi živi pilot - nalazi sa pravog uređaja (van cloud sandbox-a)

**Kontekst:** posle tri runde audita/verifikacije (sve rađene u cloud sandbox-u,
protiv sintetički napravljenih stanja), odlučeno je da se pre paketovanja
skill-a odradi pravi pilot. Nije postojao pripremljen produkcioni repo - samo
"loops" folder je bio povezan - pa je pilot urađen kao jednokratan,
disposable git repo (`sandbox-pilot-repo`) UNUTAR istog povezanog foldera,
na PRAVOM macOS uređaju (ne cloud kontejneru).

Ovo je prva provera koja je pokrenula CEO redosled (spawn → Maker izmena →
commit → checker-verify → prepare-checker-bundle) na pravom git repo-u,
umesto testiranja svake skripte pojedinačno. Upravo taj pun redosled je
otkrio 3 nova buga koja tri prethodne runde nisu mogle da vide.

---

## A. Granica ovog pilota - šta NIJE moglo biti testirano

Uređaj ima `claude` CLI na `/opt/cowork/claude-bin/claude`, ali je namerno
onemogućen u ovom Cowork bridge okruženju:

```
$ claude --version
claude: only `claude -p "<prompt>"` is supported in this environment
$ claude -p "say hello"
claude: claude is not enabled in this environment
```

Posledica: **ne postoji način da se odavde pokrene stvaran, živ Claude Code
proces koji čita `.claude/settings.json` i sam pozove `guardrail_check.py`
kao hook.** Sve što je ispod opisano kao "guardrail testiran uživo" znači:
skripta je pozvana sa sintetičkim ali REALNO-oblikovanim PreToolUse JSON-om,
na pravom uređaju, u pravom worktree-u - dokazuje da SKRIPTA radi ispravno,
ne da Claude Code STVARNO poziva tu skriptu u ovom okruženju.

**Ovo ne menja preporuku iz prethodne runde - naprotiv, pojačava je:** SKILL.md
sekcija 7 već traži da se pre prve prave upotrebe pokrene "Verifikacija
guardrails-a" komanda u TVOM stvarnom Claude Code terminalu (van Cowork-a,
gde `claude` CLI stvarno radi). To ostaje obavezan korak - ovaj pilot ga čini
važnijim, ne manje važnim, jer je sada potvrđeno da Cowork bridge okruženje
ne može da ga zameni.

---

## B. Šta JESTE testirano uživo, i prošlo

Sve dole na pravom uređaju (macOS, git 2.34.1, python 3.10.12, node v22.23.2,
uv), unutar `sandbox-pilot-repo` (mala Python biblioteka sa namernim bagom).

1. **`spawn-worktree-agent.sh`** - kreirao worktree, granu, `.agent/` strukturu,
   `uv sync` venv, i upisao u registry - sve na pravom fajl-sistemu, bez greške.
2. **`guardrail_check.py`** - 6 slučajeva (git force-push u jednoj liniji, isti
   force-push razbijen bash line-continuation-om radi DOTALL provere, `DROP
   TABLE` kao `block`, `mcp__Gmail__send_message` kao `require_human` po
   `tool_name`, malformisan `tool_input` kao string umesto dict, i bezopasna
   komanda kao kontrola) - svih 6 vratilo tačno očekivan verdikt.
3. **`approve.sh` ceo životni ciklus** - pending → covek odobrava → jednokratno
   `allow` → isti token ponovo traži odobrenje (ispravno potrošen).
4. **`registry_write.py` konkurentnost na macOS** - 40 paralelnih pisaca, DVA
   puta (jednom na lokalnom disku VM-a, jednom UNUTAR bridge-ovanog mnt/loops
   foldera koji je stvaran kanal ka disku korisnika) - 40/40 sačuvano oba puta.
   Ovo je prva potvrda da `fcntl.flock()` radi ispravno i preko ovog
   specifičnog bridge mehanizma, ne samo na Linux cloud sandbox disku gde je
   prvobitno testirano.
5. **`circuit_breaker.py`** - PASS put (verify_status PASS → STOP verify_passed,
   exit 3, state ispravno ažuriran).
6. **`prepare-checker-bundle.sh`** - posle ispravki iz sekcije C, tri puta
   zaredom na tri različita mini-zadatka - bundle sadrži TAČNO ono što treba,
   ništa više.

---

## C. Novi nalazi - bugovi koje su prethodne 3 runde propustile

Zajednička nit: sve tri prethodne runde su testirale svaku skriptu POJEDINAČNO,
sa ručno pripremljenim stanjem. Nijedna nije pokrenula PRAVI redosled
(spawn → izmeni kod → komituj → verify → bundle) na pravom git repo-u. Ovaj
pilot je prvi put to uradio, i to je otkrilo probleme koji se javljaju samo
na spoju koraka.

### C.1 [VISOKO] `checker-verify.sh` je lažno prijavljivao "testovi padaju" kad alat nije bio na PATH-u

`checker-verify.sh` je zvao goli `pytest -q` / `ruff check .` / `mypy .`,
pretpostavljajući da su na PATH-u. Na pravom uređaju, `pip install pytest`
je instalirao pytest u direktorijum koji NIJE na PATH-u (standardna pip
poruka upozorenja), i bare `pytest -q` je pukao sa `command not found` -
skripta je to tiho prijavila kao `"unit_tests:FAIL"`, neodvojivo od
stvarnog pada testova. Isti rizik postoji za svaki `uv`-upravljan Python
projekat gde alat nije deklarisan kao dependency.

**Zašto je ovo opasno:** Checker sloj postoji da bude objektivna istina.
Lažan "testovi padaju" bi naveo agenta da "popravlja" kod koji radi ispravno,
ili - gore - da lažni FAIL blokira validnu izmenu bez ijednog stvarnog razloga.

**Ispravka:** nova `run_py_tool()` funkcija pokušava redom (1) `uv run <alat>`
ako `uv` postoji i projekat ima `pyproject.toml`, (2) ako TAJ pokušaj
propadne SPECIFIČNO zato što alat nije deklarisan dependency (prepoznato po
poruci u izlazu, ne po golom exit kodu), `python3 -m <alat>` kao fallback,
(3) bare alat kao poslednji pokušaj. Retestirano: `unit_tests:PASS` sa
istim environment-om koji je pre ispravke davao lažan FAIL.

### C.2 [SREDNJE, regresija unutar iste ispravke] Prvi pokušaj C.1 je lažno pokretao lint na projektima koji ruff/mypy uopšte ne koriste

Prva verzija ispravke je koristila `command -v uv` kao (delimičan) uslov za
"da li da pokušam lint" - pogrešno, jer `uv` biti prisutan ne znači da OVAJ
projekat koristi `ruff`/`mypy`. Rezultat: sandbox projekat koji ruff/mypy
nikad ne pominje je dobio lažan `"lint:FAIL"` čim je `uv` prisutan na mašini.

**Ispravka:** `ruff_in_use()`/`mypy_in_use()` proveravaju stvaran trag upotrebe
(alat na PATH-u, uvoziv iz `python3`, ili pomenut u `pyproject.toml`), ne
samo prisustvo `uv`-a. Retestirano: lint/typecheck se sada ispravno
preskaču kad projekat te alate ne koristi, i dalje se pokreću ispravno kad
ih koristi (`uv run` put testiran indirektno kroz isti mehanizam za pytest).

Ovo je još jedna potvrda pouke iz treće runde (C.2 u `VERIFIKACIJA-treci-krug.md`):
čak i ispravka napravljena tokom rigorozne provere može uneti novu grešku -
razlog više da se svaka ispravka odmah retestira, ne samo pročita.

### C.3 [KRITIČNO - probija Domen 2 izolaciju kroz sporedna vrata] `prepare-checker-bundle.sh` i necommit-ovan `.agent/` zajedno poništavaju Maker-Checker izolaciju

Dva povezana problema, otkrivena tek kad je pun ciklus pokrenut na pravom repo-u:

**C.3.a** `prepare-checker-bundle.sh` je računao `git diff BASE...HEAD`
(tri tačke, dva ref-a) - ovo poredi SAMO komitovanu istoriju. Maker koji
napravi izmenu ali je ne komituje odmah (sasvim realan tok - mnogi agenti
komituju tek na kraju iteracije ili tek posle Checker odobrenja) dobija
POTPUNO PRAZAN `diff.patch`, dok `verify_result.json` istovremeno pokazuje
PASS (testovi su pokrenuti direktno protiv radnog direktorijuma, ne protiv
commit-a). Checker bi video "nema izmena, ali testovi prolaze".

**C.3.b - ozbiljnije:** ništa u paketu nije sprečavalo `.agent/` (scratchpad,
task_log, approvals, checker_bundle) da bude komitovano na agent granu -
sasvim realno sa `git add -A`. Kad se to desi, `git diff BASE...HEAD` (posle
ispravke C.3.a, `git diff BASE`) POKAZUJE `scratchpad.md`/`task_log.md` KAO
DEO `diff.patch`-a - iako ih `prepare-checker-bundle.sh` namerno ne kopira
direktno u bundle. Ovo TIHO PONIŠTAVA celu Domen 2 kontekst-izolaciju kroz
drugi kanal: Checker koji čita `diff.patch` bi video tačno ono što je
izolacija trebalo da sakrije. Ovo je potvrđeno direktnim testom - komitovan
`.agent/` je zaista završio u `diff.patch`-u pre ispravke.

**Ispravka (dva dela):**
1. `git diff BASE...HEAD` → `git diff BASE` (jedan ref umesto opsega) - hvata
   SVE izmene u odnosu na base granu, komitovane i nekomitovane, bez
   pretpostavke o tome kada Maker komituje. Dodato i upozorenje ako je
   rezultujući `diff.patch` prazan (umesto da se to tiho prihvati kao
   normalan slučaj).
2. `spawn-worktree-agent.sh` sada, odmah pri kreiranju `.agent/` direktorijuma,
   upisuje `.agent/` (i, kao dodatnu higijenu, `__pycache__/`, `*.pyc`,
   `.venv/`, `node_modules/`) u `.git/info/exclude` (deljen između svih
   worktree-ova istog repo-a, ne dira korisnikov pravi `.gitignore`) - tako
   da `.agent/` NIKAD ne može da postane trag-ovan/komitovan fajl, bez obzira
   šta Maker radi.

**Retestirano triput** (tri odvojena mini-zadatka, sveži worktree svaki put):
- Bez ispravke: `.agent/` sadržaj (uključujući scratchpad.md, approvals,
  pending_human_approval JSON-ove) i `__pycache__` binarni fajlovi su
  završili u commit-u i u `diff.patch`-u.
- Posle ispravke: `git show --stat HEAD` i finalni `diff.patch` sadrže SAMO
  stvarnu izmenu koda i testova (plus legitiman `uv.lock`) - nula `.agent/`
  putanja, nula `__pycache__` fajlova, u sva tri ponovljena testa.

---

## D. Operativna napomena (bridge mehanika, ne bug u paketu)

Jednom tokom pilota, `device_commit_files` je vratio `"written"` uspeh, ali
je NAREDNI `device_bash` poziv (md5 provera) pročitao STARI sadržaj fajla -
drugi identičan poziv `device_commit_files` je odmah posle toga ispravno
propagirao izmenu. Ovo je infrastrukturna osobina bridge-a (verovatno kratko
kašnjenje propagacije), ne bug u `agentic-loop-engineer-v2` paketu. Praktična
pouka: kad se fajl menja preko device bridge-a više puta zaredom, uvek
verifikovati sadržaj (md5 ili direktan `sed`/`cat`) POSLE svakog
`device_commit_files`, pre nego što se sledeći korak osloni na tu izmenu -
tačno ono što je ovaj pilot radio, i zbog čega je problem odmah uočen umesto
da tiho prođe.

---

## E. Zaključak i preporuka

Pilot je potvrdio da sistem radi ispravno na PRAVOM uređaju za sve delove
osim same Claude Code hook-dispatch mehanike (koja zahteva `claude` CLI koji
ovaj Cowork bridge namerno onemogućava). Usput je pronašao i ispravio 3 nova
buga (jedan kritičan - C.3, probijanje Domen 2 izolacije) koja tri prethodne
audit runde nisu mogle otkriti, jer nijedna nije pokrenula pun redosled
koraka na pravom git repo-u - samo pojedinačne skripte, izolovano.

**Preporuka:**
1. Ovaj paket je sada spreman za sledeći korak (paketovanje u portabilan
   skill preko `package_skill.py`) - sa jednim OBAVEZNIM uslovom pre prve
   prave upotrebe na stvarnom projektu:
2. Pokreni "Verifikacija guardrails-a" komandu iz `SKILL.md` sekcije 7 u
   SVOM stvarnom Claude Code terminalu (ne u ovom Cowork bridge-u) - ovo je
   jedini način da se potvrdi da `.claude/settings.json` zaista navodi tvoju
   instalaciju Claude Code-a da pozove `guardrail_check.py` PRE svakog alata,
   što ovaj pilot nije mogao da proveri.
3. `sandbox-pilot-repo` folder (i `worktrees/` pored njega) su potpuno
   disposable - bezbedno ih je obrisati kad završiš pregled ovog izveštaja.
