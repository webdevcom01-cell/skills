# Evals for soma-agent-cleanup

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Faza "06-rad-održavanje" ima 13
skillova i do sada nijedan nije imao svoj eval — strukturno najslabija faza u celoj
biblioteci. `soma-agent-cleanup` je prvi koji to dobija.

## Šta ovaj set testira, i šta namerno ne testira

U produkciji `soma-agent-cleanup` radi nad živim AgentStack stanjem: poziva `as_list_agents`,
`as_get_recent_executions`, `as_inspect_flow` i `as_list_agent_calls` nad pravim agentima i
flow-ovima, i na kraju `as_delete_agent` sa nepovratnim efektom. Nijedan od tih alata nije
dostupan iz ove sesije, pa set ne pokreće workflow end-to-end i ne proverava da li agent ume
da sam otkrije klastere u pravom radnom prostoru.

Umesto toga testira sloj koji je podjednako kritičan a potpuno nezavisan od žive
infrastrukture: da li agent, kad mu se da konkretno hipotetičko stanje (rezultati alata kao
činjenice u promptu), ispravno primenjuje sopstvena pravila iz SKILL.md — posebno pravila
koja sprečavaju brisanje nečega što ne treba obrisati, jer je ovo skill čija je osnovna
operacija nepovratna (`as_delete_agent`).

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi:

1. **Hard Rule 3 + formula live_score iz Step 3** — flow wiring je autoritativan nad call-log
   recency; duplikat može biti wired `call_agent` target sa nula nedavnih izvršavanja, a
   +100 bonus za wired target nadjačava razliku u broju izvršavanja (×10 po izvršavanju).
   Najverovatnija greška: agent vidi "0 executions, 0 calls" i zaključi da je taj agent mrtav.
2. **Status enum trap iz Step 3** — enum je `PENDING | RUNNING | COMPLETED | FAILED |
   CANCELLED`, nema `SUCCESS`; filter na nepostojeću vrednost tiho vraća prazno i lažno
   nulira usage term za sve kandidate podjednako, umesto da baci grešku.
3. **`as_list_agent_calls` filtrira po imenu, ne po ID-ju (Step 3)** — kad tri duplikata dele
   isto ime, taj alat vraća identičan rezultat za sva tri i ne može da ih razlikuje; per-ID
   signal mora doći iz `as_inspect_flow` skena po `targetAgentId`.
4. **`confirm:true` dry-run zamka (Step 6 + Hard Rule 1)** — poziv bez `confirm` vraća samo
   pregled i ne briše ništa, ali ostatak skilla može lako "prijaviti" brisanje kao završeno
   ako se taj detalj preskoči.
5. **Edge case "dve kopije, dva nezavisna lanca"** — kad su obe kopije aktivno pozivane iz
   različitih flow lanaca bez zajedničkog pozivaoca, to nisu pravi duplikati; skill eksplicitno
   traži da se NE briše nijedna, nego da se divergencija prijavi korisniku.
6. **Step 2 opseg + Step 8 izveštavanje** — singletoni (count=1) su van opsega dedup-klasterovanja;
   `hasFlow:false` agent se samo flaguje kao "possibly abandoned", nikad ne briše na osnovu
   opšteg zahteva za čišćenje duplikata.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(konkretan hipotetički scenario, rešiv čistim rezonovanjem iz pravila u SKILL.md — bez
pristupa razgovoru, fajlovima na disku ili živom AgentStack-u), `expected_output` (tačan
zaključak i zašto, sa referencom na konkretno pravilo/formulu iz skilla), i `expectations`
(konkretne, proverljive tvrdnje o tome šta agent mora — ili ne sme — da kaže, ne opšti
utisci ili "agent je bio pažljiv").

Svaki prompt namerno navodi rezultate alata kao gotove činjenice u tekstu (npr. tačan broj
COMPLETED izvršavanja, tačan `targetAgentId` pronađen u flow skenu) da bi scenario ostao
samostalan i rešiv bez pristupa spoljnom stanju, u skladu sa ograničenjem zadatka.

## Ograničenje / sledeći korak

Ovo je "logic-only" sloj — testira da li agent ispravno primenjuje pravila i formulu
bodovanja kad mu se da već prikupljeno stanje, ne da li ume sâm da izvrši Step 1-8 nad
pravim AgentStack radnim prostorom: da li `as_list_agents(limit:200)` zaista paginira sve
agente, da li flow-sken (Step 4) pokriva baš svaki drugi agent pre nego što se bilo šta
proglasi "nije wired nigde", i da li se STEP 5 plan i STEP 6 potvrda zaista traže po
klasteru u pravoj interakciji, ne samo jednom na početku. Kad bude dostupan pristup test
AgentStack instanci sa namerno zasejanim duplikatima, set treba proširiti pravim run-ovima
kroz sve korake — ovih 6 slučajeva je jeftina početna provera razumevanja pravila o
bezbednom brisanju, ne zamena za to.
