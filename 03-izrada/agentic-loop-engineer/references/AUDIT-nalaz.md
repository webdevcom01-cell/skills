# Audit nalaz — drugi krug provere (posle v2 paketa)

**Cilj ove provere:** ne ponoviti analizu, nego proveriti da li ono što je
ISPORUČENO u v2 paketu (SKILL.md + skripte + config) stvarno radi kako piše,
da li je usklađeno sa zvaničnim Claude Code standardima, i da li postoji
nešto ozbiljno izostavljeno pre nego što se bilo šta pokrene bez nadzora.

Metodologija: (1) provera frontmatter/hook formata protiv zvanične
dokumentacije (code.claude.com), (2) linija-po-liniju čitanje svake
isporučene skripte tražeći konkretne bagove, (3) funkcionalno testiranje
svakog nalaza pre i posle ispravke, ne samo statička analiza.

---

## A. Provera protiv zvaničnih standarda

| Standard | Provereno protiv | Rezultat |
|---|---|---|
| SKILL.md frontmatter polja | [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) | `name` + `description` su validna, opciona polja; oba su ispod 1536 karaktera. Usklađeno. |
| PreToolUse hook JSON ulaz/izlaz | [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) | v1 audit paketa NIJE imao nijednu skriptu koja implementira hook — samo YAML dokumentaciju. Ovo je bio najveći nalaz (vidi B.1). Implementirano po tačnoj šemi (`tool_name`, `tool_input.command`, `hookSpecificOutput.permissionDecision`). |
| `permissionDecision` dozvoljene vrednosti | isto (eksplicitno potvrđeno upitom) | Samo `allow` / `deny` / izostavljeno — **NEMA** `ask` vrednosti. Ovo je promenilo dizajn: "require_human" ne može biti "postavi pitanje i sačekaj" na nivou hook-a, mora biti "deny + upiši pending zapis + čovek ručno pokreće jednokratno odobrenje". Implementirano tako (vidi B.1). |
| Matcher sintaksa za "svi alati" | isto | `"*"`, `""` ili izostavljen matcher — sve tri hvataju sve alate, uključujući MCP pozive. Jedan hook pokriva i Bash i MCP (potvrđeno). |

**Zašto je ovo bilo bitno proveriti, ne pretpostaviti:** da sam pretpostavio da postoji `permissionDecision: "ask"` (uobičajena pretpostavka, postoji u nekim starijim/trećim izvorima), ceo guardrails mehanizam bi bio dizajniran oko nepostojeće funkcije i tiho ne bi radio kad zatreba.

---

## B. Pronađeni bagovi (svi ispravljeni i retestirani)

### B.1 [KRITIČNO] Guardrails.yaml nije imao nikakvu enforcement skriptu
**Nalaz:** v1 audit paketa je imao `config/guardrails.yaml` sa pravilima i tvrdnju u SKILL.md "orkestrator proverava svaku komandu protiv njega" — ali nijedna skripta u paketu to nije radila. Bio je to dokument o nameri, ne zaštita.

**Ispravka:** Napisan `scripts/guardrail_check.py` kao pravi Claude Code PreToolUse hook (šema potvrđena, vidi A), ožičen preko `hooks/settings.snippet.json`. Dodat `scripts/approve.sh` za jednokratno ljudsko odobrenje (compare-and-swap-style token, ne blanket dozvola). Guardrails.yaml prepravljen da pokriva i MCP alate (scope: tool_name / any), ne samo bash stringove — v1 pravila su hvatala samo CLI komande, ne i direktne MCP pozive (npr. Railway `set-variables` preko MCP-a, ne preko CLI-ja).

**Test dokaz:** 8 scenarija testirano uživo (harmless komanda prolazi bez odluke; `git push --force` → deny + pending zapis; `approve.sh` → jednokratni token; ista komanda drugi put → allow; treći put → deny opet jer je token potrošen; `DROP TABLE` → block bez mogućnosti resume-a; `mcp__Gmail__send_message` → deny po tool_name; Railway MCP `set-variables` sa `"production"` u argumentima → deny po any-scope pravilu). Svi prošli kako je specificirano.

### B.2 [VISOKO] Pogrešan izračun wall-clock vremena (vremenska zona)
**Nalaz:** `circuit_breaker.py` je parsirao `started_at` (UTC, generisan sa `date -u`) sa `time.strptime()` pa ga konvertovao u epoch sa `time.mktime()`. `time.mktime()` tretira `struct_time` kao **lokalno** vreme, ne UTC. Na bilo kojoj mašini van UTC+0 — uključujući Europe/Podgorica (UTC+2) — ovo bi pomerilo izračunati "elapsed" za tačno tu vremensku razliku, i to u zabludu koja se kompenzuje sama sa sobom pogrešno kad je razlika pozitivna (istočno od UTC): "elapsed" bi bio precenjen za razliku, i wall-clock circuit breaker bi okidao PRERANO, i to nasumično u zavisnosti od DST perioda.

**Ispravka:** zamenjeno sa `calendar.timegm()`, koji tretira `struct_time` eksplicitno kao UTC.

**Test dokaz:** Test pokrenut sa `TZ=Europe/Podgorica`, `started_at` postavljen na "sada" (UTC), 2 sekunde pauze, `max_wall_clock_sec=5` → ispravno vraća `CONTINUE` (elapsed ≈ 2s, ne lažnih ~2h+2s koje bi dao stari kod).

### B.3 [SREDNJE] Path traversal kroz task-id
**Nalaz:** `spawn-worktree-agent.sh` je koristio `TASK_ID` direktno u konstrukciji putanje (`WT_DIR="${WT_ROOT}/${TASK_ID}"`) bez validacije. Task-id kao `../../evil` bi omogućio kreiranje/brisanje van namenjenog `worktrees/` direktorijuma.

**Ispravka:** dodata eksplicitna regex validacija (`^[a-zA-Z0-9_-]+$`) pre bilo kakve upotrebe, plus validacija da su `max-iterations`/`max-wall-clock-sec` pozitivni celi brojevi (sprečava nevalidan JSON u `loop_state.json` koji bi pukao `circuit_breaker.py` kasnije).

**Test dokaz:** `../../evil` odbijen sa jasnom porukom; `abc` kao max-iterations odbijen.

### B.4 [SREDNJE] Nema cleanup-a na pad usred kreiranja worktree-a
**Nalaz:** ako `git worktree add` uspe ali neki kasniji korak (instalacija zavisnosti, upis u registry) pukne, ostaje "napola" worktree i grana koja blokira ponovni pokušaj sa istim task-id-om i zbunjuje `git worktree list`.

**Ispravka:** dodat `trap ... ERR` koji čisti worktree i granu ako bilo koji korak pukne pre finalnog uspeha; `CLEANUP_NEEDED` flag se gasi tek na samom kraju.

**Test dokaz:** simuliran pad u koraku instalacije zavisnosti (neispravan `pyproject.toml`) → trap je obrisao worktree i granu, `git worktree list` posle pada pokazuje čist repo.

---

## C. Ojačano (nije bio "bag", ali je bilo samo opisano, sada je sprovedeno kodom)

**Maker-Checker fizička izolacija (Domen 2):** originalni v2 je opisivao izolaciju konteksta tekstualno u SKILL.md, oslanjajući se na to da će neko "znati" da Checker-u ne pokaže scratchpad.md. Dodat `scripts/prepare-checker-bundle.sh` koji fizički kopira SAMO `task_spec.md` + `diff.patch` + `verify_result.json` u poseban direktorijum — izolacija je sada posledica strukture fajlova, ne discipline. Testirano funkcionalno.

---

## D. Svesno prihvaćeni preostali rizici (disclosure, ne propust)

Ovo NISU stvari koje su "zaboravljene" — namerno su van obima v1 prototipa, navedeno eksplicitno da ne bi bile pogrešno protumačene kao rešene:

1. **Regex guardrails se mogu zaobići** (alias, `eval`, env-var indirekcija, base64 obfuskacija komande). Rečeno eksplicitno u `guardrails.yaml` i SKILL.md — potreban je drugi nezavisni sloj (git branch protection na remote-u, scope-ovani/least-privilege API ključevi za MCP konektore) van ovog paketa.
2. **`checker-verify.sh` heuristika "logika promenjena bez testa"** je gruba (proverava da li je BILO KOJI test fajl dotaknut, ne da li taj test stvarno pokriva promenu). Dovoljno za v1 da spreči najočigledniji slučaj (nula test izmena), ali ne zamenjuje ljudski review test kvaliteta.
3. **Hook API se menja između verzija Claude Code-a.** Šema u `hooks/settings.snippet.json` i `guardrail_check.py` je potvrđena protiv dokumentacije u trenutku ovog audita (septembar 2026) — proveri `code.claude.com/docs/en/hooks` ponovo ako se posle nadogradnje Claude Code-a hook prestane okidati kako treba.
4. **`circuit_breaker.py` i `registry_write.py` nemaju eksplicitni file-lock (fcntl)** — oslanjaju se na to da je `loop_state.json` per-worktree (jedan proces odjednom po dizajnu iz Domena 1), a `registry.json` na compare-and-swap retry. Ako se ikad doda drugi pisac u isti `loop_state.json` (npr. paralelni monitoring proces), treba dodati pravi file-lock, ne samo compare-and-swap.
5. **Enterprise-agent-readiness gap ostaje otvoren** — taj skill trenutno audituje samo AgentStack `as_*` agente. Ovaj v2 paket (Claude-Code-native, "Nivo A" tipa) nije pokriven tim auditom; ovaj AUDIT-nalaz.md je ad-hoc zamena za taj konkretan slučaj, ne generalizovano rešenje gap-a.

---

## E. Zaključak

Svih 6 gap-ova iz prve analize (Domen 6 originalnog dokumenta) su ili zatvoreni kodom (worktree lifecycle, memory concurrency, stopping conditions, guardrails enforcement) ili eksplicitno preneti kao poznat, dokumentovan rizik (regex bypass, heuristika za testove). Dodatna 4 bagova pronađena u OVOM krugu (guardrails enforcement gap, UTC bug, path traversal, cleanup na pad) su pronađena čitanjem koda linija-po-liniju i funkcionalnim testiranjem, ne pretpostavkom — i sva 4 su ispravljena i retestirana sa dokazom u ovom fajlu.

**Preporuka:** paket je spreman za Korak 1 iz plana (jedan agent, jedan zadatak, Hard Ceiling = 5, guardrails hook aktivan od prve komande) — pod uslovom da se pre prvog pravog pokretanja izvrši "Verifikacija guardrails-a" komanda iz SKILL.md sekcije 7 i potvrdi da hook stvarno okida u TVOM konkretnom Claude Code okruženju (verzija hook API-ja se menja).
