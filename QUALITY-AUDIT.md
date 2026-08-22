# Provera kvaliteta skill biblioteke

Datum: 21. avgust 2026. — **osveženo dvaput** (izvorna verzija napisana ranije istog dana je
zastarela za par sati; brojevi ispod su dodatno osveženi 22. avgust 2026. posle uklanjanja 4
skilla i dodavanja 1 novog — vidi drugu napomenu o osvežavanju ispod).
Obim: 50 skillova, organizovanih u 8 faza pipeline-a `ideja → projekat → gotovo rešenje` u
repozitorijumu `skills` (radno stablo posle commit-a `eafe7fc`, grana `main`).

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

## Napomena o osvežavanju (22. avgust 2026.)

Broj skillova se promenio sa 53 na 50, commit-om `eafe7fc`, u sklopu plana unapređenja repoa:
`docx`, `pdf`, `pptx` i `xlsx` su uklonjeni iz `plugin/skills/` (i iz odgovarajućeg faznog foldera
`07-izlazni-formati/`) jer su nosili Anthropic-ovu "Services only" licencu koja zabranjuje
redistribuciju van Claude servisa — nisu smeli da postoje u paketu namenjenom deljenju trećim
licima. Istim commit-om je dodat `plugin-sync` (faza 06) kao novi tracked skill (SKILL.md +
`scripts/package_plugin.py` + `scripts/sync_plugin.py`), koji za sada nema `evals/`. Neto promena:
−4 (docx/pdf/pptx/xlsx) +1 (plugin-sync) = −3, sa 53 na 50.

Svi brojevi u ovom fajlu ispod ove napomene su ponovo izmereni direktno iz `01-08/*/` posle ove
izmene, istim postupkom kao u prethodnom osvežavanju (provera prisustva `evals/`/`tests/`/
`references/`/`scripts/` po folderu, ne pretpostavka iz starih brojeva).

## Ukupna slika

Od 50 skillova:

| Metrika | Broj | % |
|---|---|---|
| Imaju `evals/` folder | 47 | 94% |
| Imaju `scripts/` folder (izvršni kod) | 11 | 22% |
| Imaju `references/` folder | 12 | 24% |
| Imaju `tests/` folder | 2 | 4% |
| Samo SKILL.md, bez ijednog pratećeg foldera | 2 | 4% |

`evals/` pokrivenost ostaje visoka (94%, blago niža u apsolutnom procentu nego pre — 51/53=96% →
47/50=94% — ali to je posledica manjeg imenioca i jednog novog skilla bez evals-a, ne regresije
kod postojećih: sva 47 koja su ranije imala evals/ i dalje ga imaju). Tri skilla sada nemaju
`evals/`: `morning` i `tender-projekat` (isto kao ranije), plus novi `plugin-sync` (dodat ovim
commit-om, evals folder još ne postoji za njega — vidi sekciju ispod).

`tests/` ostaje nisko (4%, isti apsolutni broj kao pre — 2/53 → 2/50 — jer nijedan od uklonjenih
ili dodatih skillova nije imao/dobio `tests/`). Da neki skill ima `scripts/` a nema `tests/` za
njih (9 od 11 skillova sa scripts-om nema tests/) samo po sebi nije alarm — mnogi od tih skripti
su jednostavni generatori dokumenata gde se ispravnost lakše proverava pokretanjem nego formalnim
testom — ali vredi imati na umu za skripte sa stvarnom logikom (npr. `validate_library.py` u
`geo-prompt-library`, `package_skill.py` u `skill-creator-pro`, i sad i `package_plugin.py`/
`sync_plugin.py` u novom `plugin-sync`-u, koji direktno menja `.plugin` pakete).

## Šta je i dalje otvoreno: `morning`, `tender-projekat` — i sad `plugin-sync`

`morning` i `tender-projekat` ostaju jedina dva skilla u celoj biblioteci bez ikakve prateće
infrastrukture — ni `evals/`, ni `references/`, ni `scripts/`. Nije nužno greška (oba su kraća,
ponašanje-usmerena skilla, ne skripte), ali su izuzetak, ne pravilo, pa vredi svesno odlučiti da
li im treba bar minimalan eval pre nego što se na njih osloniš u produkciji (`tender-projekat`
posebno, pošto sam njegov opis kaže da "nosi disciplinu koja je uhvatila svaku pravu grešku do
sada" — ta disciplina zaslužuje proveru da zaista radi, a ne samo da je opisana).

`plugin-sync` je druga vrsta slučaja: ima `scripts/` (dve skripte koje pakuju i sinhronizuju sam
plugin), ali nema `evals/` — a upravo ta vrsta gap-a (novi skript sa stvarnom logikom bez ikakve
provere) je tačno ono što bi budući `skill-lint`/`skill-catalog-sync` alat (predložen u planu
unapređenja) trebalo automatski da uhvati čim se doda. Vredi mu dodati bar osnovni eval pre nego
što se dalje oslanja na njega za pakovanje distributable `.plugin` fajla.

## Pregled po fazama

| Faza | Skillova | Sa evals/ | Sa tests/ | Sa references/ | Sa scripts/ | Samo SKILL.md |
|---|---|---|---|---|---|---|
| 01 — Ideja/validacija | 5 | 5 | 0 | 3 | 0 | 0 |
| 02 — Dizajn/arhitektura | 3 | 3 | 1 | 2 | 1 | 0 |
| 03 — Izrada | 6 | 6 | 1 | 2 | 3 | 0 |
| 04 — Test/QA | 7 | 7 | 0 | 0 | 0 | 0 |
| 05 — Isporuka klijentu | 4 | 4 | 0 | 3 | 3 | 0 |
| 06 — Rad i održavanje | 14 | 13 | 0 | 1 | 2 | 0 |
| 07 — Izlazni formati | 8 | 8 | 0 | 0 | 1 | 0 |
| 08 — Drugi projekti | 3 | 1 | 0 | 1 | 1 | 2 |

Faza 06 je porasla sa 13 na 14 skillova (dodat `plugin-sync`, bez evals-a — zato kolona "Sa
evals/" ostaje 13 iako je "Skillova" poraslo). Faza 07 je pala sa 12 na 8 (uklonjeni `docx`,
`pdf`, `pptx`, `xlsx`) — preostalih 8 i dalje svi imaju `evals/`. Faza 08 je i dalje jedina sa
"samo SKILL.md" skillovima (`morning`, `tender-projekat`) — vidi sekciju iznad. Sve ostale faze
imaju evals pokrivenost 100%.

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

## Preporuke, po prioritetu (osveženo 22. avgust 2026.)

Prioriteti iz prethodne verzije (popuni fazu 04, popuni `safe-agent-builder`, popuni fazu 06) su
**ispunjeni** — sve sada imaju evals (izuzev novog `plugin-sync`-a, vidi tačku 1 ispod). Novi
prioriteti, na osnovu trenutnog stanja:

1. **`morning`, `tender-projekat` i sad `plugin-sync`** — tri skilla bez ikakve/dovoljne provere.
   `tender-projekat` posebno, jer eksplicitno tvrdi da čuva "disciplinu koja je uhvatila svaku
   pravu grešku" — ta tvrdnja zaslužuje bar jedan eval scenario koji je dokazuje. `plugin-sync`
   je najhitniji od ova tri jer njegove skripte direktno pakuju i menjaju distributable `.plugin`
   fajl koji se deli sa drugima — greška tu ima najveći domet.
2. **`tests/` pokrivenost ostaje na 2/50.** Za skillove sa netrivijalnom izvršnom logikom u
   `scripts/` (npr. `validate_library.py` u `geo-prompt-library`, `package_skill.py` u
   `skill-creator-pro`, `package_plugin.py`/`sync_plugin.py` u `plugin-sync`, ili bilo koji budući
   skript koji menja podatke/fajlove) razmisliti da li im treba pravi unit test uz eval — evals
   proverava ponašanje agenta, tests proverava da kod sam po sebi radi ispravno na ivičnim
   slučajevima.
3. **Redovnije osvežavanje ovog izveštaja.** Ovaj repo se menja brzo — vredi ga ponovo pokrenuti
   posle svake veće serije izmena kataloga skillova (dodavanje/uklanjanje), umesto da se izveštaj
   piše jednom i ostavi da zastari, kao što se dogodilo i ovog puta (od 21. do 22. avgusta broj
   skillova se promenio, a izveštaj je to prijavio tek naknadno).

## Ograničenje ovog izveštaja

Ovo je snapshot na osnovu strukture foldera (broj fajlova, prisustvo `evals/`/`tests/`/`references/`/`scripts/`), ne čitanje svakog SKILL.md teksta reč po reč. Moguće je da neki "tanak" skill (samo SKILL.md) ipak sadrži jasna pravila i primere unutar samog teksta koja ga čine dovoljno pouzdanim bez posebnog eval foldera — ova analiza to ne razlikuje. Takođe ne meri da li su postojeći `evals/` folderi sadržajni (koliko test-scenarija, da li zaista pokrivaju granične slučajeve) — samo da li folder postoji. Za skillove koje označiš kao prioritet, sledeći korak bi bio da pročitamo taj konkretan `evals/` sadržaj zajedno i odlučimo da li je dovoljan.
