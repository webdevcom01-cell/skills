# Evals for agent-health-check

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Faza 04 (Test/QA) ima 7 skillova
od kojih trenutno nijedan nema svoj eval — ovaj set je drugi u nizu (posle
`soma-eval-harness`) koji to popravlja.

## Šta ovaj set testira, i šta namerno ne testira

U produkciji `agent-health-check` izvršava dve faze stvarnih MCP poziva nad živim Agent
Studio sistemom: Phase 1 su tri globalna poziva (`as_find_broken_flows`,
`as_diagnose_models`, `as_list_agents`) nad svih 55 agenata, a Phase 2 su sekvencijalni
per-agent pozivi (`as_inspect_flow`, `as_list_knowledge_bases`) nad listom produkcijskih
agenata. Ovaj eval set NE poziva nijedan od tih alata i ne pretpostavlja pristup živom
AgentStack sistemu — iz ove sesije nemamo tu infrastrukturu. Umesto toga testira sloj koji
je nezavisan od žive infrastrukture, a podjednako kritičan: kad se agentu da konkretan
hipotetički rezultat tih poziva (npr. jedan `severity` string, jedan `embeddingStatus`,
jedan broj provera), da li on ispravno primenjuje sopstvena pravila iz SKILL.md da
klasifikuje CRITICAL vs WARNING, izračuna score, i generiše ispravan tekst fix-a.

Namerno se NE testira: tačan format finalnog izveštaja iz STEP 6 (ASCII separator linije,
emoji, redosled sekcija), korišćenje TaskCreate liste iz STEP 0, efikasnost poziva (da li
je agent stvarno pozvao tačno 3 globalna poziva paralelno umesto sekvencijalno), niti
ponašanje pri stvarnom tool-call failure-u opisanom u Constraint #4. Sve to zahteva
stvaran, pokrenut skill sa MCP pristupom Agent Studio bazi — nešto što ovde nije dostupno.

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi kao potvrđenu činjenicu ili
tvrdo pravilo — nisu izmišljene situacije:

1. D0 severity mapiranje: jedina potvrđena WARNING vrednost je doslovno `"WARN"`; svaka
   druga vrednost (npr. `"ERROR"`) mora se konzervativno tretirati kao CRITICAL — lako se
   pogrešno pretpostavi da su slične vrednosti "isto".
2. Tabela `embeddingStatus` → severity: `processing` i `partial_failure` su WARNING (sa
   različitim obaveznim detaljima — retry napomena vs. `statusBreakdown`), dok je `failed`
   CRITICAL — lako se pomešaju jer sve tri zvuče "loše".
3. `count: 0` (agent nema KB) NIJE automatski CRITICAL — to je AND uslov sa Dimenzijom B:
   CRITICAL je samo ako flow agenta i inače ima `kb_search` node. Ovo je dvo-granski uslov
   koji je najlakše preskočiti.
4. Scoring granica: score tačno 70 spada u DEGRADED (70–89), ne u AT RISK (50–69) — susedne
   kategorije se lako pomešaju na samoj granici.
5. Scope override: kad korisnik ograniči proveru na jednog agenta, to ograničava SAMO
   Phase 2 (i posledično koji agent prolazi Memory Wiring/KB proveru) — Phase 1, uključujući
   Dimenziju F (duplikati imena), i dalje pokriva SVE agente u sistemu.
6. Zabrana izmišljanja podataka: kad `as_list_knowledge_bases` ne vrati nijednu KB, fix tekst
   mora biti tačno propisana rečenica ("Manual fix required..."), nikad izmišljen
   `knowledgeBaseId` ubačen u `as_patch_node_field` komandu.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(konkretan hipotetički scenario sa svim potrebnim brojevima/stanjima već datim u tekstu,
rešiv čistim rezonovanjem bez pristupa razgovoru, fajlovima ili spoljnom stanju),
`expected_output` (tačan zaključak i pravilo iz SKILL.md na koje se oslanja), i
`expectations` (konkretne, proverljive tvrdnje koje grejder može da potvrdi ili ospori, ne
opšti utisci o kvalitetu odgovora).

## Ograničenje

Ovo je "logic-only" sloj — testira da li agent ispravno primenjuje pravila klasifikacije i
scoring-a kad mu se daju gotovi ulazni podaci, ne testira stvarno izvršavanje dve faze MCP
poziva nad pravim Agent Studio sistemom. Nije zamena za pravi end-to-end eval koji bi
pokrenuo skill protiv sandbox AgentStack instance sa namerno zasejanim pokvarenim flow-ovima,
praznim KB-ovima i duplim imenima agenata, i proverio i tačan format STEP 6 izveštaja i
stvarni broj/redosled MCP poziva. Kad bude dostupna takva sandbox instanca, ovaj set treba
proširiti pravim run-ovima — ovih 6 slučajeva je početna, jeftina provera razumevanja
pravila, ne konačna provera skilla.
