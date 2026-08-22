# Eval set: safe-agent-builder

## Zašto ovaj skill i zašto sada

Ovo je **prvi eval set** za `safe-agent-builder`, i ranija analiza cele biblioteke ga je
eksplicitno označila kao prioritet za fazu 03: skill ima "safe" u imenu, tvrdi da gradi
deterministički bezbednosni gate (validator + condition + fail-closed grananje) za AgentStack
agente, a do sada nije imao nijedan eval koji bi dokazao da te provere zaista rade onako kako
SKILL.md tvrdi. Skill koji obećava bezbednost bez ijednog testa te bezbednosti je tačno onaj tip
rizika koji eval setovi treba da hvataju prvi — otud prioritet u odnosu na ostalih pet skillova iz
faze 03.

## Šta set testira

Svih 6 slučajeva su **hipotetički, samostalni scenariji rezonovanja** (bez pristupa fajlovima,
konverzaciji ili spoljnom stanju) koji proveravaju da li agent tačno primenjuje pravila iz
`SKILL.md` (i parametrizovanu validator šablonu iz `references/flow-templates.md`, na koju
`SKILL.md` eksplicitno upućuje u koracima 2–3). Prioritet je dat scenarijima gde bi **pogrešan
zaključak agenta doveo do lažnog osećaja bezbednosti** — agent kaže "bezbedno" ili "PASS" kad
pravila, doslovno primenjena, kažu suprotno:

1. **Eval 1** — Pravilo #2 ("every branch ends in a message node"): PASS grana koja se završava na
   function čvoru (pass-emitter) umesto na message čvoru tiho propušta sirov, nevalidiran izlaz
   procesora — flow *izgleda* kompletan (ima validator i gate), ali nije.
2. **Eval 2** — Pravilo #3 (guard the input): validator koji proverava format/zabranjene
   fraze/statistike ali NE proverava prazno/N/A osnovno polje propušta fabrikovanu temu — ovo je
   doslovno primer "Hook Writer" scenarija kojim sam SKILL.md otvara obrazloženje skilla.
3. **Eval 3** — Pravilo #4 (fail closed): downstream `call_agent` povezan pre/paralelno sa gate-om
   znači da BLOCKED verdikt stiže prekasno da bilo šta spreči.
4. **Eval 4** — detalj Pravila #3: input-guard sa egzaktnim poređenjem prema kratkoj listi
   ('n/a'/'na'/'none'/'unknown') ne hvata sinonime poput "not applicable" — OR-uslov sa četiri
   grane koji izgleda sveobuhvatno, a nije.
5. **Eval 5** — najfiniji i najvažniji slučaj: fabrikovana statistika koja ne prati poreklo do
   ulaza je u podrazumevanoj šablon-validaciji `severity:"warning"`, ne `"error"` — gate je vraća
   kao PASS. Direktno testira da agent ne preuveličava šta gate garantuje.
6. **Eval 6** — kontrast prema Evalu 5: pogrešan broj stavki (numerički prag, `items.length !==
   EXPECTED_COUNT`) JESTE blokirajuća `"error"` provera — agent mora razlikovati šta zaista
   blokira od onoga što samo upozorava.

## Šta set namerno NE testira

Ne testira mehaničke/proceduralne korake skilla (redosled MCP poziva, tačan REST kontrakt za evale
iz `references/evals.md`, KB wiring, `as_inspect_flow` backup disciplinu) niti trigering opisa
skilla. Ovo su validni sledeći kandidati, ali nisu bezbednosno-kritični u istom smislu — set se
namerno fokusira na "da li agent ispravno rezonuje o tome kada je flow zaista bezbedan", ne na "da
li zna redosled alata".

## Format

Isti format kao `skill-creator-pro/evals/evals.json`: svaki slučaj ima `id`, samostalan `prompt`
(hipotetički scenario rešiv čistim rezonovanjem), `expected_output` (tačan zaključak + referenca na
konkretno pravilo iz SKILL.md) i `expectations` (lista konkretnih, proverljivih tvrdnji koje grader
može da potvrdi/opovrgne u odgovoru agenta).

## Ograničenje i sledeći korak

Ovo su rezonovanje-evali (agent nema pristup pravom AgentStack flow-u), ne end-to-end testovi nad
stvarno skalfoldovanim agentom. Sledeći korak je end-to-end eval koji stvarno pokreće
`safe-agent-builder` na test-specifikaciji, gradi flow preko MCP alata, i proverava rezultat kroz
`as_inspect_flow`/smoke test — čime bi se zatvorila razlika između "agent zna pravilo" i "agent ga
stvarno primenjuje u alatu".
