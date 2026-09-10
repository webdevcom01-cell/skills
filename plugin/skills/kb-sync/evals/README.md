# kb-sync — eval set

Ovo je prvi eval set za skill `kb-sync` (faza `06-rad-odrzavanje`). Faza ima 13 skillova i do sada nijedan nije imao svoj eval set — ovaj fajl pokriva `kb-sync`, skill koji sinhronizuje Obsidian vault fajlove sa Agent Studio knowledge base-ovima kroz True-Sync obrazac (ADD novo → sačekaj READY → DELETE staro).

## Šta testira

Šest slučajeva, svaki cilja jedno eksplicitno pravilo iz `SKILL.md` koje je lako pogrešiti jer zahteva pamćenje uslova sa dve nezavisne grane (AND/OR) ili redosleda koraka:

1. **DELETE gate je fail-closed, ali ne blokira ADD** (Step 5.0). ADD je nedestruktivan i izvršava se bez obzira na odobrenje; DELETE se gejtuje i, bez eksplicitnog "da/obriši/yes", preskače se za sve u tom run-u i prijavljuje kao WARNING — ne tiho izostavlja, niti zaustavlja ceo sync.
2. **`contentHash == null` → CHANGED, ne SKIPPED** (Step 5d, Case B). Kontraintuitivno: nedostatak podatka za poređenje intuitivno vodi ka "preskoči", ali skill eksplicitno traži suprotno.
3. **`status != READY` → ne diraj fajl uopšte** (Step 5d, Case C). Ni ADD ni DELETE dok je izvor PENDING/PROCESSING/FAILED — samo WARNING i nastavak dalje.
4. **Legacy naming mismatch → samo ADD, nikad automatski DELETE** (Step 4 napomena). Kad lookup po imenu ne nađe izvor zbog stare konvencije, tretira se kao Case A (nov fajl); stari izvor ostaje duplikat za ručno čišćenje.
5. **Redosled ADD→wait→DELETE, nikad DELETE→ADD** (Step 5f, Constraint #2). Test nudi naizgled razuman argument ("izbegni privremeni duplikat") da proveri da li agent popušta i krši redosled koji sprečava gap u KB-u.
6. **Zabrana `as_search_knowledge_base` za change detection** (Constraint #3). Proverava da agent razlikuje chunk-level od document-level hash-a i insistira na HTTP GET `contentHash` polju.

## Šta NE testira i zašto

Set namerno ne pokriva format bash `curl` komandi, tajming 7-sekundnog rate-limit bafera, 429 retry logiku niti Step 0 (TaskCreate listu) — to su operativni detalji koji zavise od izvršnog okruženja (stvarni HTTP pozivi, stvaran vault), a ne od rezonovanja o pravilima. Fokus je na odlukama na račvanjima logike (grane, redosled, edge case-ovi), jer je tu najveći rizik od tihog gubitka ili duplikacije podataka — što je i traženi fokus zadatka.

## Format

Prati format `skill-creator-pro/evals/evals.json`: top-level `skill_name` i `evals` niz; svaki slučaj ima `id`, `prompt` (samostalan hipotetički scenario, bez reference na spoljni kontekst), `expected_output` (zaključak i obrazloženje sa referencom na pravilo/korak iz SKILL.md) i `expectations` (4–5 konkretnih, proverljivih tvrdnji o tome šta odgovor mora i ne sme sadržati).

## Ograničenje i sledeći korak

Ovo su rezonovanje-evali — proveravaju da li agent ispravno primenjuje pravila na opisano stanje — ne end-to-end izvršni evali koji bi pokretali stvarni MCP/curl tok. Sledeći korak: izvršni eval (mock HTTP server + mock Obsidian vault) koji proverava da agent zaista poziva alate ispravnim redosledom i produkuje tačan izveštaj (ADDED/UPDATED/SKIPPED/WARNINGS/ERRORS), ne samo da o tome ispravno rezonuje.
