# Evals for agent-scaffolder

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Faza 03-izrada ima 6 skillova;
ovo je prvi od njih koji dobija svoj eval set, nakon što je faza 04 (Test/QA) završena
sa 7/7 skillova pokrivenih.

## Šta ovaj set testira, i šta namerno ne testira

`agent-scaffolder` je dug, deveto-koračni skill (STEP 0–9) koji u produkciji poziva
stvaran niz MCP alata nad živim AgentStack sistemom i Obsidian trezorom: `as_create_agent`,
`as_inspect_flow`, `as_update_flow`, `as_list_knowledge_bases`, `as_add_kb_text`,
`as_patch_node_field`, `as_get_kb_embedding_status`, `as_chat_with_agent`, plus
`obsidian_create_note` / `obsidian_read_note` / `obsidian_update_note`. Ova sesija nema
pristup toj infrastrukturi — nema pravog AgentStack naloga niti pravog trezora nad kojim bi
se skill mogao stvarno pokrenuti od početka do kraja.

Zato ovaj set NE testira: da li se agent zaista završava sa validnim `agentId`-jem, da li
`as_update_flow` u praksi stvarno prihvata izgrađeni JSON, tačan ASCII format STEP 9
izveštaja, TaskCreate listu iz STEP 0, redosled paralelnih poziva, niti stvarno ponašanje
`as_get_kb_embedding_status` pollinga (20s x 5 pokušaja). Sve to zahteva pravi, pokrenut
skill sa MCP pristupom pravom AgentStack + Obsidian sistemu.

Umesto toga, set testira sloj koji je nezavisan od žive infrastrukture a podjednako
kritičan za ispravnost: kad se agentu opiše konkretno hipotetičko stanje (npr. jedan
odgovor na AskUserQuestion, jedan broj node-ova, jedan broj unosa u evo-log-u), da li on
ispravno primenjuje sopstvena eksplicitna pravila iz SKILL.md — bez pristupa razgovoru,
fajlovima na disku ili spoljnom stanju, čisto rezonovanjem iz teksta pravila.

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi, ne izmišljenu situaciju:

1. **Temperatura — AND uslov** (STEP 1b tabela): red "Research → 0.3" zahteva I šaru u
   imenu ("monitor" itd.) I Q3=Yes zajedno — lako se pogrešno primeni samo na osnovu imena,
   ignorišući da je web search isključen.
2. **Downstream resolucija — OR uslov** (STEP 1c): "Only if Q1 = 'Sends output' OR 'Middle
   link'" — dve nezavisne grane; lako se zaboravi da "Middle link" samostalno okida korak,
   ne samo "Sends output".
3. **BINDING RULE** (STEP 5b): `call_agent.inputVariable` mora biti jednako
   `extractor.outputVariable` — "never change one without changing the other" — klasična
   greška je promeniti samo jednu stranu veze.
4. **Obavezan dry-run bez izuzetka za "male" izmene** (STEP 5d, v2.1 promena): `as_update_flow`
   nema undo i zamenjuje CEO flow; pravilo ne pravi razliku između "male" i "velike" izmene.
5. **Verifikacija broja edge-ova** (STEP 5e): "Edge count = node count - 1 (linear chain)" —
   lako se pomeša sa "edge count = node count" kad se node-ovi prosto prebroje.
6. **Prag topK "20+"** (agent-card / DESIGN_SPEC resursna tabela): "20+" znači "20 ili više",
   ne "više od 20" — granični slučaj tačno na 20. unosu, dodatno otežan time što STEP 9
   koristi blažu formulaciju "exceeds 20" koja bi doslovno značila drugačije.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(konkretan hipotetički scenario sa svim potrebnim brojevima/stanjima već datim u tekstu,
rešiv čistim rezonovanjem bez pristupa razgovoru, fajlovima ili spoljnom stanju),
`expected_output` (tačan zaključak i pravilo iz SKILL.md na koje se oslanja, sa objašnjenjem
zašto), i `expectations` (konkretne, proverljive tvrdnje koje grejder može da potvrdi ili
ospori, ne opšti utisci o kvalitetu odgovora).

## Ograničenje i sledeći korak

Ovo je "logic-only" sloj — testira da li agent ispravno primenjuje pravila odlučivanja,
uslove i pragove kad mu se daju gotovi hipotetički ulazi, ne testira stvarno izvršavanje
devet koraka skilla nad pravim AgentStack + Obsidian sistemom (pravo kreiranje agenta,
pravo pisanje flow-a, pravo seedovanje KB-a, pravi smoke test). Kad bude dostupna sandbox
instanca AgentStack-a i test-trezor u Obsidian-u, ovaj set treba proširiti pravim end-to-end
run-om koji bi proverio i tačan format STEP 9 izveštaja, stvaran redosled/broj MCP poziva,
i ponašanje pri stvarnom `as_update_flow` ili embedding failure-u iz Error Handling Reference
tabele. Ovih 6 slučajeva je početna, jeftina provera razumevanja pravila — ne konačna
provera skilla.
