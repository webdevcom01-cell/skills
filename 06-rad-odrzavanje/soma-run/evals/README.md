# Evals for soma-run

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Faza `06-rad-odrzavanje` ima 13
skillova i nijedan do sada nema svoj eval — `soma-run` je prvi, namerno izabran jer je
najveći i najkritičniji skill u fazi: pravi agent harness koji pokreće produkcioni SOMA
pipeline (TI → HW → CR) i piše direktno u produkcione evo-logove i winners-log u
Obsidian-u. Greška ovde ne ostaje lokalna — loguje se pogrešan set hookova, duplira se rad
agenata, ili se propušta korak koji baš to sprečava. SKILL.md (~790 linija) dokumentuje
aktivan arhitektonski konflikt (TI interno lanči HW i CR server-side, pa spoljno
pokretanje FULL scope-a izvršava HW dvaput i CR triput) plus izmerenu retry-storm grešku
klijenta — oba su razlog zašto skill ima toliko eksplicitnih hard rules i fail-closed
gate-ova koje je lako pogrešno primeniti.

## Šta ovaj set testira, i šta namerno ne testira

`soma-run` u produkciji zove `as_chat_with_agent` na pravim SOMA agentima (Trend
Intelligence, Hook Writer, Content Repurposer), poll-uje `as_get_recent_executions` i
`as_list_agent_calls`, i piše preko `obsidian_read_note`/`obsidian_update_note` u prave
evo-log i winners-log fajlove. Nijedan od ovih alata i nijedno od tog stanja nije dostupno
iz ove sesije, pa set ne pokreće nijedan stvaran pipeline run end-to-end i ne proverava da
li agent stvarno ume da parsira sirov TI/HW/CR tekst iz prakse.

Umesto toga, svih 7 slučajeva testira da li agent — kad mu se da konkretno, samostalno
hipotetičko stanje (poruka korisnika, izvučene vrednosti, ili sadržaj agent outputa) —
ispravno primenjuje pravila iz SKILL.md bez pristupa razgovoru, disku ili live
infrastrukturi. Svaki prompt je rešiv čistim rezonovanjem iz teksta skilla.

## Koje pravilo svaki slučaj cilja

1. **STEP 1, scope gate za FULL/TI+HW** — eksplicitan zahtev za "full pipeline" se NE
   pokreće odmah; mora se postaviti upozorenje i sačekati eksplicitno "da"/"yes". Gate je
   fail-closed — sama formulacija zahteva korisnika nije potvrda.
2. **STEP 1, default scope + STEP 5/6/7/8 skip uslovi** — kad scope nije naveden, default
   je "TI", ali to znači da OVAJ poziv skilla eksplicitno preskače HW, CR, quality gate i
   sve povezano logovanje (gated na "pipeline_scope=='TI'" / "HW was not run"), čak i kad
   server-side lanac interno završi ceo TI→HW→CR tok.
3. **STEP 4c, fire-and-poll na TI timeout** — timeout na 60s nije failure; poruka se NIKAD
   ne šalje ponovo (drugi send = drugi pun server-side lanac); pravilan odgovor je čekanje
   ~120s pa poll `as_get_recent_executions`.
4. **Hard rule + STEP 4g** — `{ti_handoff}` mora sadržati kompletan verbatim `{ti_output}`
   u `<<SOMA_CONTEXT_START>>` bloku; slanje samo strukturisanog header-a (čak i kad su svi
   ključni podaci već izvučeni) je eksplicitno zabranjeno.
5. **STEP 4f, quality_score prag** — numerička granica `≥0.33` odvaja WARN od ABORT-a;
   1/3 ≈ 0.33 je WARN (pipeline nastavlja sa "not found" za nedostajuće elemente), ne
   ABORT (rezervisan striktno za 0.0).
6. **STEP 8a + Constraints Summary, winners-log prag** — "Score ≥ 17/20 per platform — not
   just the overall winner"; svaka platforma se proverava nezavisno, ne samo ona sa
   najvišim skorom.
7. **STEP 6e, CR flag AND-uslov** — UNSCORED + `quality_flags: []` pronađeno → "none", ali
   UNSCORED + `quality_flags` uopšte nije pronađeno → "WARN". Odsustvo pominjanja nije isto
   što i eksplicitna prazna lista.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(samostalan hipotetički scenario, rešiv čistim rezonovanjem iz pravila u SKILL.md — bez
pretpostavke da agent ima pristup ovom razgovoru, fajlovima na disku ili live SOMA/Obsidian
infrastrukturi), `expected_output` (tačan zaključak i zašto, sa direktnim pozivanjem na
konkretnu sekciju/pravilo iz SKILL.md), i `expectations` (konkretne, proverljive tvrdnje o
tome šta agent mora — ili izričito ne sme — da kaže ili uradi).

## Ograničenje / sledeći korak

Ovo je "logic-only" sloj — proverava da li agent ispravno primenjuje eksplicitna pravila
kad mu se da gotovo, jasno stanje, ne da li ume da to stanje sam proizvede iz pravog
SOMA/Agent Studio okruženja. Konkretno ne testira: parsiranje neuređenog, prirodnog
TI/HW/CR teksta radi ekstrakcije `{ti_trend}`/`{ti_confidence}`/`{ti_angle}`/skorova; da li
`as_list_agent_calls` provera izvora (STEP 4c-bis) stvarno hvata pogrešan URL u praksi; da
li retry-storm dedup (STEP 4c) ispravno radi kad `as_get_recent_executions` vrati tri i
više novih execution-a sa realnim `startedAt` vrednostima; i da li evo-log/winners-log
upisi zaista poštuju read-before-write nad pravim Obsidian notes. Kad bude dostupan pristup
test SOMA/Agent Studio i Obsidian instanci, set treba proširiti stvarnim run-ovima kroz sve
tri faze — ovih 7 slučajeva je jeftina početna provera razumevanja pravila, ne zamena za to.
