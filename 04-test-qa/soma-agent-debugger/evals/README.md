# Evals for soma-agent-debugger

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Avgust 2026 quality audit je
pokazao da nijedan od 7 skillova u fazi 04 (Test/QA) nema svoj eval — ovaj skill je drugi
u nizu koji to dobija, posle `soma-eval-harness`.

## Šta ovaj set testira, i šta namerno ne testira

U produkciji `soma-agent-debugger` radi nad živim AgentStack/SOMA stanjem koje ova sesija
nema kako da dohvati: poziva `as_get_agent` i `as_inspect_flow` na pravim agentima, čita
`git log` i stvaran kod u `src/`, izvršava DB upite nad production bazom, i poziva
`as_chat_with_agent` da progura pravi trend kroz pravi pipeline (Mode 4). Nijedan od tih
alata/pristupa nije dostupan iz ove sesije, pa set ne pokreće nijedan od 4 mode-a end-to-end.

Umesto toga testira sloj koji je podjednako kritičan a potpuno nezavisan od žive
infrastrukture: da li agent, kad mu se da konkretan hipotetički nalaz ili stanje, ispravno
primenjuje sopstvena pravila iz SKILL.md — koji izvor je istina kad se dva izvora ne slažu,
kada sme (a kada ne sme) da nastavi na sledeći korak, koji MCP alat je ispravan za koju
izmenu, i gde je granica između dva slična ishoda (npr. "manji" vs "veći" fail).

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi — nisu izmišljene
situacije, nego direktni odrazi teksta skilla:

1. **Hard Rule #3 + Forensic Protocol korak 3** — kad se audit/vault dokument ne slaže sa
   `as_get_agent` live outputom, live pobeđuje, a sporna tvrdnja ide na listu "za
   ispravku", ne u dokaze. Najverovatnija greška: agent tretira stariji/poznatiji izvor
   (audit) kao činjenicu jer "zvuči autoritativno".
2. **STOP point na kraju Mode 1** — "Ne idi na fix bez korisnikove potvrde root cause-a."
   Lako se preskoči kad izveštaj deluje kompletan i ubedljiv.
3. **Mode 3, Critical lessons** — match pool validatora mora da kombinuje SVA relevantna
   polja (title + body + hook), ne samo jedno; provera nad jednim poljem daje false
   negative/positive.
4. **AgentStack MCP napomene** — `as_update_flow` menja ceo flow i nema undo (uvek
   `dry_run` prvo); za jedno polje koristi se `as_patch_node_field`, čiji `field_value`
   nosi broj kao broj, ne kao citirani JSON string.
5. **Mode 4 risk assessment** — razlika između "Mali FAIL → rollback candidate ⚠️" i
   "Veliki FAIL → urgent rollback + debug ❌". Jedan pokvaren pod-check (npr. duplikat) u
   inače prolaznom smoke testu ne sme automatski da eskalira u urgent rollback, niti sme
   da se sakrije pod čist PASS.
6. **"Kada NE koristiti"** — dizajn potpuno novog agenta je eksplicitno van opsega ovog
   skilla; za to postoji `agent-architect`.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(konkretan hipotetički scenario, rešiv čistim rezonovanjem iz pravila u SKILL.md — bez
pristupa razgovoru, fajlovima na disku ili živoj infrastrukturi), `expected_output` (tačan
zaključak i zašto, sa referencom na konkretno pravilo), i `expectations` (konkretne,
proverljive tvrdnje o tome šta agent mora — ili ne sme — da kaže, ne opšti utisci).

## Ograničenje / sledeći korak

Ovo je "logic-only" sloj — testira da li agent ispravno primenjuje pravila kad mu se da
gotovo stanje, ne da li ume da to stanje sam iskopa iz pravog AgentStack-a, git istorije ili
production baze. Konkretno ne testira: da li agent ume da izvrši Forensic Protocol korak-po-
korak nad pravim agentom (Mode 1), da li generisan Claude Code prompt iz Mode 2 zaista prati
šablon i STOP points, da li Mode 3 validator kod koji agent napiše zaista prolazi sopstvene
test case-ove kad se pokrene, i da li Mode 4 smoke test ume da izvede ispravne SQL upite iz
šeme koju je *sam* pročitao (a ne od pretpostavljenih imena kolona). Kad bude dostupan pristup
test AgentStack instanci, set treba proširiti pravim run-ovima kroz sva 4 mode-a — ovih 6
slučajeva je jeftina početna provera razumevanja pravila, ne zamena za to.
