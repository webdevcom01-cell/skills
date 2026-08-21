# Provera kvaliteta skill biblioteke

Datum: 21. avgust 2026.
Obim: 53 skilla, organizovana u 8 faza pipeline-a `ideja → projekat → gotovo rešenje` u repozitorijumu `skills` (commit `b9a2e6d`, grana `main`).

Ovaj izveštaj ne ocenjuje da li je sadržaj svakog SKILL.md dobro napisan (za to bi trebalo pročitati svaki tekst pojedinačno) — meri **strukturnu zrelost**: da li skill ima samo jedan prozni fajl, ili i prateću infrastrukturu (`references/` za dodatnu dokumentaciju, `scripts/` za izvršni kod, `evals/` i `tests/` za proveru da li skill zapravo radi ono što tvrdi da radi). Ta struktura je dobar pokazatelj pouzdanosti — SKILL.md može da *opiše* dobro ponašanje, ali samo `evals/`/`tests/` dokazuju da se ono zaista dešava.

## Ukupna slika

Od 53 skilla:

| Metrika | Broj | % |
|---|---|---|
| Imaju `evals/` folder | 5 | 9% |
| Imaju `tests/` folder | 2 | 4% |
| Samo SKILL.md, bez ijednog pratećeg foldera | 25 | 47% |

Skoro polovina biblioteke se oslanja isključivo na prozni opis u SKILL.md. To samo po sebi nije nužno loše — nekoliko tih fajlova su vrlo opsežni (npr. `soma-run` 4684 reči, `pipeline-debug` 4892 reči) — ali odsustvo `evals/` znači da ne postoji automatska provera da li agent koji koristi taj skill zaista postiže očekivan ishod.

## Najupadljiviji nalaz: faza 04 (Testiranje / QA)

Ironično, faza čija je *svrha* testiranje i QA je strukturno najslabija u celoj biblioteci: svih 7 skillova (`agent-health-check`, `enterprise-agent-readiness`, `pipeline-debug`, `pipeline-input-validator`, `soma-agent-debugger`, `soma-eval-harness`, `soma-model-preflight`) su čisti pojedinačni SKILL.md fajlovi — nijedan nema sopstveni `evals/`, `tests/`, `references/` ili `scripts/`. Čak i `soma-eval-harness`, skill čiji je posao da *gradi* eval harness za druge agente, nema sopstveni eval koji bi dokazao da radi kako treba.

Ovo bi trebalo da bude prioritet broj jedan za popunjavanje.

## Faza sa najviše skillova, a najmanje strukture: 06 (Rad i održavanje)

Ovo je najveća faza (13 od 53 skilla, gotovo četvrtina cele biblioteke), a 10 od 13 (77%) su samo SKILL.md, bez ijednog eval-a u celoj fazi. Ovde žive skillovi koji rade sa живом memorijom i log-ovima nakon lansiranja (`memory-integrity-gate`, `soma-memory-fix`, `kb-sync`, `instincts-updater`...) — greška u ovoj fazi direktno utiče na proizvodni sistem, pa je odsustvo provera ovde rizičnije nego u ranijim fazama gde je greška lakše uočljiva i manje košta.

## Pregled po fazama

| Faza | Skillova | Sa evals/ | Sa tests/ | Samo SKILL.md |
|---|---|---|---|---|
| 01 — Ideja/validacija | 5 | 0 | 0 | 2 |
| 02 — Dizajn/arhitektura | 3 | 2 | 1 | 1 |
| 03 — Izrada | 6 | 1 | 1 | 2 |
| 04 — Test/QA | 7 | 0 | 0 | 7 |
| 05 — Isporuka klijentu | 4 | 1 | 0 | 1 |
| 06 — Rad i održavanje | 13 | 0 | 0 | 10 |
| 07 — Izlazni formati | 12 | 0 | 0 | 1 |
| 08 — Drugi projekti | 3 | 1 | 0 | 1 |

Napomena za fazu 07: većina ovih skillova (`docx`, `pptx`, `pdf`, `xlsx`, `pdf`, `web-artifacts-builder`...) su zreli, mehanički alati za generisanje fajlova, uglavnom sa `scripts/` umesto `evals/` — kod njih odsustvo eval-a je manje hitno, jer se ispravnost lakše proverava direktnim pokretanjem skripte nego kroz formalni eval.

## Skillovi koji su najbolje strukturirani (uzor za ostale)

Pet skillova ima punu ili gotovo punu infrastrukturu (evals + references + scripts, ponekad i tests) i mogu poslužiti kao interni šablon kad se druge faze budu popunjavale:

- `skill-creator-pro` (03-izrada) — 26 fajlova: evals, eval-viewer, references, agents, scripts, assets.
- `geo-prompt-library` (08-drugi-projekti) — 44 fajla: evals, references, scripts, fixtures, assets — najkompletniji skill u celoj biblioteci.
- `system-teardown` (02-dizajn) — 28 fajlova: evals, references, assets.
- `prompt-engineer-pro` (02-dizajn) — 15 fajlova: evals, tests, references, scripts — jedini skill sa i evals i tests folderom.
- `team-enablement-program` (05-isporuka) — evals, references, scripts.

## Preporuke, po prioritetu

1. **Faza 04 (Test/QA) prva.** Dodati bar minimalan `evals/` folder (par test-scenarija sa očekivanim ishodom) za svih 7 skillova, počevši od `soma-eval-harness` i `pipeline-debug` — ovo su skillovi koje ćeš verovatno najviše koristiti kad nešto krene po zlu, pa je najskuplje ako oni sami nisu proverени.
2. **`safe-agent-builder`** (03-izrada) ima "safe" u imenu, a nema nijedan eval koji bi dokazao da bezbednosne provere koje generiše zaista rade. Vredno je popuniti pre nego što se stvarno osloniš na njega u produkciji.
3. **Faza 06, redom po riziku** — prvo `memory-integrity-gate` i `soma-memory-fix` (dodiruju živu memoriju agenta), pa tek onda log/reporting skillove (`winners-log-logger`, `evo-log-writer`) gde je cena greške manja.
4. **Faza 01** (`deep-research`, `roast`) i faza 03 (`agent-scaffolder`, `session-start-hook`) — niži prioritet; ovo su uglavnom skillovi za ranu fazu gde je izlaz "predlog", ne izvršna akcija, pa je rizik od tihog kvara manji.
5. Faza 07 ostaviti kako jeste za sada — mehanički alati, nizak prioritet.

## Ograničenje ovog izveštaja

Ovo je snapshot na osnovu strukture foldera (broj fajlova, prisustvo `evals/`/`tests/`/`references/`/`scripts/`), ne čitanje svakog SKILL.md teksta reč po reč. Moguće je da neki "tanak" skill (samo SKILL.md) ipak sadrži jasna pravila i primere unutar samog teksta koja ga čine dovoljno pouzdanim bez posebnog eval foldera — ova analiza to ne razlikuje. Za skillove koje označiš kao prioritet, sledeći korak bi bio da pročitamo taj konkretan SKILL.md zajedno i odlučimo šta mu tačno nedostaje.
