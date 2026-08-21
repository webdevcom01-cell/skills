# Provera kvaliteta skill biblioteke

Datum: 21. avgust 2026. — **osveženo** (originalna verzija napisana ranije istog dana je zastarela
za par sati; vidi napomenu ispod).
Obim: 53 skilla, organizovana u 8 faza pipeline-a `ideja → projekat → gotovo rešenje` u repozitorijumu
`skills` (radno stablo posle commit-a `e18b322`, grana `main`).

Ovaj izveštaj ne ocenjuje da li je sadržaj svakog SKILL.md dobro napisan (za to bi trebalo pročitati svaki tekst pojedinačno) — meri **strukturnu zrelost**: da li skill ima samo jedan prozni fajl, ili i prateću infrastrukturu (`references/` za dodatnu dokumentaciju, `scripts/` za izvršni kod, `evals/` i `tests/` za proveru da li skill zapravo radi ono što tvrdi da radi). Ta struktura je dobar pokazatelj pouzdanosti — SKILL.md može da *opiše* dobro ponašanje, ali samo `evals/`/`tests/` dokazuju da se ono zaista dešava.

## Napomena o osvežavanju (21. avgust 2026.)

Prethodna verzija ovog izveštaja (commit `b9a2e6d`) je javljala da samo 5/53 skilla imaju `evals/`
folder (9%) i da je faza 04 (Test/QA) strukturno najslabija — nijedan od njenih 7 skillova nije
imao evals. Direktna provera fajl-sistema danas pokazuje da je to odavno ispravljeno: **51/53
skillova sada ima `evals/`**, uključujući svih 7 iz faze 04. Serija commit-ova istog dana
(`9ce0b61` "Dodaj eval setove za fazu 07", `832d768` "evals-faza-02-dizajn", i dr.) je pretekla
izveštaj pre nego što je iko stigao da ga pročita. Ovo osvežavanje postoji da se to ne ponovi bez
primetbe — brojevi ispod su izmereni direktno iz `01-08/*/`.

Uz osvežavanje brojeva, popravljena su i dva `SKILL.md` fajla sa CRLF završecima linija
(`algorithmic-art`, `canvas-design`, i njihove kopije u `plugin/skills/`) — normalizovani na LF
kao i ostatak repoa.

## Ukupna slika

Od 53 skilla:

| Metrika | Broj | % |
|---|---|---|
| Imaju `evals/` folder | 51 | 96% |
| Imaju `scripts/` folder (izvršni kod) | 14 | 26% |
| Imaju `references/` folder | 12 | 23% |
| Imaju `tests/` folder | 2 | 4% |
| Samo SKILL.md, bez ijednog pratećeg foldera | 2 | 4% |

Slika se potpuno promenila u odnosu na prethodnu verziju ovog izveštaja: umesto "skoro polovina
biblioteke se oslanja isključivo na prozni opis", sada je to samo 2 skilla. `evals/` pokrivenost
je gotovo univerzalna. Ono što OSTAJE nisko — i vredi pratiti dalje — je `tests/` (4%): `evals/`
grubo proverava da li se agent/skill ponaša kako treba na primerima, dok `tests/` obično
proverava deterministički kod (skripte, funkcije). Da neki skill ima `scripts/` a nema `tests/`
za njih (12 od 14 skillova sa scripts-om nema tests/) samo po sebi nije alarm — mnogi od tih
skripti su jednostavni generatori dokumenata gde se ispravnost lakše proverava pokretanjem nego
formalnim testom — ali vredi imati na umu za skripte sa stvarnom logikom (npr. `validate_library.py`
u `geo-prompt-library`, `package_skill.py` u `skill-creator-pro`).

## Šta je i dalje otvoreno: `morning` i `tender-projekat`

Ovo su sada JEDINA dva skilla u celoj biblioteci bez ikakve prateće infrastrukture — ni `evals/`,
ni `references/`, ni `scripts/`. Nije nužno greška (oba su kraća, ponašanje-usmerena skilla, ne
skripte), ali su sad izuzetak, ne pravilo, pa vredi svesno odlučiti da li im treba bar minimalan
eval pre nego što se na njih osloniš u produkciji (`tender-projekat` posebno, pošto sam njegov
opis kaže da "nosi disciplinu koja je uhvatila svaku pravu grešku do sada" — ta disciplina zaslužuje
proveru da zaista radi, a ne samo da je opisana).

## Pregled po fazama

| Faza | Skillova | Sa evals/ | Sa tests/ | Sa references/ | Sa scripts/ | Samo SKILL.md |
|---|---|---|---|---|---|---|
| 01 — Ideja/validacija | 5 | 5 | 0 | 3 | 0 | 0 |
| 02 — Dizajn/arhitektura | 3 | 3 | 1 | 2 | 1 | 0 |
| 03 — Izrada | 6 | 6 | 1 | 2 | 3 | 0 |
| 04 — Test/QA | 7 | 7 | 0 | 0 | 0 | 0 |
| 05 — Isporuka klijentu | 4 | 4 | 0 | 3 | 3 | 0 |
| 06 — Rad i održavanje | 13 | 13 | 0 | 1 | 1 | 0 |
| 07 — Izlazni formati | 12 | 12 | 0 | 0 | 5 | 0 |
| 08 — Drugi projekti | 3 | 1 | 0 | 1 | 1 | 2 |

Faza 08 je sad jedina sa "samo SKILL.md" skillovima (`morning`, `tender-projekat`) — vidi sekciju
iznad. Sve ostale faze imaju evals pokrivenost 100%.

## Skillovi koji su najbolje strukturirani (uzor za ostale)

I dalje važi iz prethodne verzije — ovih pet imaju punu ili gotovo punu infrastrukturu i mogu
poslužiti kao interni šablon:

- `skill-creator-pro` (03-izrada) — evals, references, scripts (+ eval-viewer, agents, assets).
- `geo-prompt-library` (08-drugi-projekti) — evals, references, scripts, fixtures, assets —
  najkompletniji skill u celoj biblioteci (44 fajla).
- `system-teardown` (02-dizajn) — evals, references, assets.
- `prompt-engineer-pro` (02-dizajn) — evals, tests, references, scripts — jedan od samo dva
  skilla sa i evals i tests folderom.
- `rls-rollout` (03-izrada) — evals, tests, scripts, templates, reference — drugi od dva
  skilla sa tests folderom; jedini sa `allowed-tools` ograničenim na (Read, Glob, Grep, Bash)
  i `disable-model-invocation: true` (mora se pozvati eksplicitno, ne trigeruje se sam).
- `team-enablement-program` (05-isporuka) — evals, references, scripts.

## Preporuke, po prioritetu (osveženo)

Prioriteti iz prethodne verzije (popuni fazu 04, popuni `safe-agent-builder`, popuni fazu 06) su
**ispunjeni** — sve sada imaju evals. Novi prioriteti, na osnovu trenutnog stanja:

1. **`morning` i `tender-projekat`** — jedina dva skilla bez ikakve provere. `tender-projekat`
   posebno, jer eksplicitno tvrdi da čuva "disciplinu koja je uhvatila svaku pravu grešku" — ta
   tvrdnja zaslužuje bar jedan eval scenario koji je dokazuje.
2. **`tests/` pokrivenost ostaje na 2/53.** Za skillove sa netrivijalnom izvršnom logikom u
   `scripts/` (npr. `validate_library.py` u `geo-prompt-library`, `package_skill.py` u
   `skill-creator-pro`, ili bilo koji budući skript koji menja podatke/fajlove) razmisliti da li
   im treba pravi unit test uz eval — evals proverava ponašanje agenta, tests proverava da kod
   sam po sebi radi ispravno na ivičnim slučajevima.
3. **Redovnije osvežavanje ovog izveštaja.** Ovaj repo se menja brzo (25 commit-ova u jednom danu
   pri prošlom pregledu) — vredi ga ponovo pokrenuti posle svake veće serije evals-commit-ova,
   umesto da se izveštaj piše jednom i ostavi da zastari na par sati.

## Ograničenje ovog izveštaja

Ovo je snapshot na osnovu strukture foldera (broj fajlova, prisustvo `evals/`/`tests/`/`references/`/`scripts/`), ne čitanje svakog SKILL.md teksta reč po reč. Moguće je da neki "tanak" skill (samo SKILL.md) ipak sadrži jasna pravila i primere unutar samog teksta koja ga čine dovoljno pouzdanim bez posebnog eval foldera — ova analiza to ne razlikuje. Takođe ne meri da li su postojeći `evals/` folderi sadržajni (koliko test-scenarija, da li zaista pokrivaju granične slučajeve) — samo da li folder postoji. Za skillove koje označiš kao prioritet, sledeći korak bi bio da pročitamo taj konkretan `evals/` sadržaj zajedno i odlučimo da li je dovoljan.
