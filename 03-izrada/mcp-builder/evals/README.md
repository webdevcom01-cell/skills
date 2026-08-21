# Evals for mcp-builder

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Faza 03 (Izrada) ima 6
skillova, i pre ovog seta nijedan od njih nije imao svoj eval — nakon što je Faza 04
(Test/QA) upravo dovršena sa 7/7 skillova pokrivenih evalima, ovo je prvi korak u
prelasku na Fazu 03.

## Šta ovaj set testira, i šta namerno ne testira

`mcp-builder` je proceduralni vodič u četiri faze (Research & Planning →
Implementation → Review & Test → Create Evaluations) za pravljenje MCP servera, i u
produkciji se oslanja na živo spoljašnje stanje koje iz ove sesije nije dostupno:
`WebFetch` poziva na `modelcontextprotocol.io` i na `raw.githubusercontent.com` za
TypeScript/Python SDK README fajlove (sekcije 1.2–1.3), stvarno pisanje i kompajliranje
koda protiv `reference/node_mcp_server.md` i `reference/python_mcp_server.md`, i
pokretanje MCP Inspector-a nad stvarno implementiranim serverom (sekcija 3.2). Ovaj set
ništa od toga ne pokreće i ne pretpostavlja pristup internetu, konkretnom API-ju servisa
koji se integriše, niti sadržaju `reference/` fajlova — fokus je isključivo na SKILL.md
telu, kako je i traženo.

Umesto toga, set testira sloj koji je nezavisan od žive infrastrukture, a podjednako
lako pogrešiti: dat konkretan hipotetički scenario (stanje implementacije, broj
napisanih pitanja, sadržaj jednog predloženog eval pitanja, tip servera koji se gradi),
da li agent ispravno primenjuje eksplicitna pravila i pragove koje SKILL.md sam
navodi za Fazu 4 (Create Evaluations) i za izbor transporta u Fazi 1.3. Namerno se NE
testira subjektivniji deo procesa — da li je neko pitanje dovoljno "kompleksno" ili
"realistično" (4.3), pošto to zahteva stvaran uvid u pravu API domenu, kao ni sadržaj
`reference/mcp_best_practices.md` (imenovanje alata, paginacija, JSON vs. Markdown
odluke) koji SKILL.md samo referencira kao poseban fajl, a ne razrađuje u svom telu.

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi kao lako pogrešiti:

1. **Numerički prag u 4.2** — sekcija se doslovno zove "Create **10** Evaluation
   Questions"; 6 kvalitetnih pitanja ne zadovoljava zahtev jer je broj nezavisan uslov
   od kvaliteta.
2. **OR/AND grana pri izboru transporta (1.3)** — "Streamable HTTP for remote
   servers... stdio for local servers" su dve nezavisne grane; lako se generalizuje
   Streamable HTTP kao univerzalno "preporučen" i previdi da lokalni server ide na
   stdio granu.
3. **Redosled koraka u 4.2 koji se lako preskoči** — Tool Inspection → Content
   Exploration → Question Generation → Answer Verification; pisanje odgovora iz
   opšteg znanja bez stvarnog rešavanja pitanja preskače poslednji, eksplicitno
   propisani korak.
4. **Edge case: Read-only zahtev iz 4.3** — evaluaciono pitanje mora zahtevati samo
   nedestruktivne operacije; realizam i kompleksnost pitanja ne kompenzuju kršenje
   ovog nezavisnog uslova.
5. **Razlika između sličnih stanja: Verifiable iz 4.3** — odgovor mora biti jedan
   jasan string proveriv poređenjem; otvorena lista sa dozvoljenim redosledom/
   podskupom to narušava, iako "izgleda" kao ispravan odgovor.
6. **Eksplicitan format u 4.4** — propisan je XML sa tačno određenim tagovima
   (`<evaluation><qa_pair><question>/<answer></qa_pair></evaluation>`); JSON sa
   drugačijim imenima polja krši i tip fajla i imena tagova, dva nezavisna problema.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`,
`prompt` (konkretan hipotetički scenario sa svim potrebnim brojevima/stanjima već
datim u tekstu, rešiv čistim rezonovanjem iz pravila u SKILL.md — bez pristupa
razgovoru, fajlovima sa diska ili spoljnom stanju), `expected_output` (tačan zaključak
i konkretna sekcija/pravilo iz SKILL.md na koje se oslanja), i `expectations`
(konkretne, proverljive tvrdnje koje grejder može da potvrdi ili ospori, ne opšti
utisci o kvalitetu odgovora).

## Ograničenje i sledeći korak

Ovo je "logic-only" sloj — testira da li agent ispravno primenjuje eksplicitne pragove,
grane i redosled koraka iz SKILL.md kad mu se da gotov hipotetički scenario, ne testira
da li agent stvarno ume da sprovede Fazu 1–3 (WebFetch dokumentacije, pisanje i
kompajliranje funkcionalnog TypeScript/Python MCP servera, pokretanje MCP Inspector-a)
ili da generiše svih 10 pitanja sa stvarno tačnim, verifikovanim odgovorima protiv
prave eksterne API integracije. Kad bude dostupan test setup sa konkretnim ciljnim
API-jem (npr. sandbox REST servis sa poznatim podacima) protiv kog agent može stvarno
da izgradi i evaluira MCP server, set treba proširiti pravim end-to-end slučajevima
koji proveravaju i kvalitet generisanog koda i stvarnu tačnost odgovora na 10
pitanja — ovih 6 slučajeva je početna, jeftina provera razumevanja pravila, ne
konačna provera skilla.
