# evals: agent-dependency-mapper

Ovo je prvi eval set za skill `agent-dependency-mapper` (faza 06-rad-odrzavanje).
Faza trenutno ima 13 skillova bez ijednog eval-a — ovo je prvi korak ka
pokrivanju.

## Šta testira

Pet slučajeva, svaki utemeljen na konkretnom, eksplicitnom pravilu iz
`SKILL.md` (sekcije "Hard rules" i "Workflow"), a ne na izmišljenim
scenarijima:

1. **Orphan/empty-shell vs. standalone leaf** — SKILL.md eksplicitno traži da
   se razlikuju dva slična, ali suprotna zaključka: `in=0 AND out=0 AND
   empty flow` (kandidat za brisanje) naspram `in=0, out=0, ali radni
   flow koji samo ne zove druge agente` (normalno, NIJE kandidat). Ovo je
   klasična "lako pomešati" zamka jer prva dva uslova izgledaju identično.
2. **`hasFlow=false` → nema izlaznih grana** — Hard rules eksplicitno kažu da
   se u tom slučaju out-edges *infereiraju*, a agent se markira "no flow" —
   test proverava da se `as_inspect_flow` ne poziva nepotrebno.
3. **Static vs. runtime neslaganje i obavezno labelovanje izvora** — pravilo
   "ako se static i runtime ne slažu, prikaži OBA sa labelama — ne biraj
   ćutke" plus anti-halucinacijsko pravilo "svaka grana mora imati source".
   Test proverava da se dve različite grane ne stope pogrešno u `both`.
4. **READ-ONLY hard rule** — skill sme samo da *lista* kandidate za brisanje;
   čovek odlučuje i deluje. Test simulira eksplicitan zahtev korisnika da
   agent sam obriše orphan agente, i proverava da odgovor odbija to i ne
   poziva mutation alate.
5. **Dangling edge cross-check** — kada static grana pokazuje na
   `targetAgentId` koji više ne postoji u `as_list_agents`, mora se
   obeležiti `dangling`, ne tiho izostaviti ili pogrešno preusmeriti.

## Šta NE testira i zašto

Ne testira se sam mehanički proces pozivanja alata (`as_list_agents`,
`as_inspect_flow`, `as_list_agent_calls`) niti tačan format izveštaja iz
`reference/dependency-mapping.md`, jer ovaj eval set namerno ostaje na nivou
SKILL.md pravila koja je čitalac mogao proveriti bez pristupa referentnom
fajlu. Takođe se ne testira limit od 100 runtime poziva (`Notes` sekcija)
posebnim slučajem — smatran je manje podložnim pogrešnom tumačenju od
gornjih pet, pa je ostavljen za sledeću iteraciju.

## Format i ograničenje

Format prati `skill-creator-pro/evals/evals.json`: `skill_name`, niz `evals`
sa `id`, `prompt`, `expected_output`, `expectations`. Pošto skill u produkciji
zavisi od žive Agent Studio MCP konekcije (`as_*` alati) kojoj ovde nema
pristupa, svaki `prompt` je samostalan hipotetički scenario — sadrži
dovoljno "izmišljenih" ali eksplicitnih podataka (in/out-degree, hasFlow,
targetAgentId, itd.) da se ispravan zaključak izvede čistim rezonovanjem iz
teksta SKILL.md, bez ikakvog spoljnog stanja.

## Sledeći korak

Dodati eval za `reference/dependency-mapping.md` (algoritam, template,
verifikacionu listu) kada bude dostupan za čitanje, i eval za SPOF rangiranje
i cycle/self-loop `visited` set pravilo koje SKILL.md pominje u koraku 4.
