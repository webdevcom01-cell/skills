# Evals for enterprise-agent-readiness

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Avgust 2026 quality audit je
pokazao da nijedan od 7 skillova u fazi 04 (Test/QA) nema svoj eval — uključujući ovaj
skill, čiji je posao da izda produkciono sign-off za DRUGE Agent Studio agente.

## Šta ovaj set testira, i šta namerno ne testira

U produkciji `enterprise-agent-readiness` radi niz živih MCP poziva (`as_inspect_flow`,
`as_find_broken_flows`, `as_diagnose_models`, `as_list_evals`, `as_get_agent_budget`,
`as_list_agent_calls`...) nad stvarnim agentom u Agent Studio-u, a rezultat upisuje u
Obsidian sign-off fajl. Ovaj eval set NE pokreće taj pravi pipeline — nemamo pristup
korisnikovom živom Agent Studio-u ni Obsidian vault-u iz ove sesije, pa ne možemo
proveriti da li agent stvarno ume da pozove `as_inspect_flow` i pravilno protumači
prave nodes/edges, niti da li stvarno piše sign-off notu na disk. Umesto toga, set
testira deo koji je i dalje kritičan a potpuno nezavisan od žive infrastrukture: kad se
agentu da konkretan, već-gotov hipotetički nalaz (rezultat audita, stanje jednog čvora,
opis dva paralelna scenarija), da li on ispravno primenjuje SOPSTVENA pravila iz
SKILL.md da izvede verdikt, klasifikuje REQ vs ⚠️, i odredi ispravan redosled radnji.
Ovo je "logic-only" sloj — proverava razumevanje pravila, ne izvršavanje audita.

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi kao lako za pogrešiti:

1. **STEP 3 verdikt** — "All REQ green ⇒ Enterprise-grade. Any REQ ❌ ⇒ Needs work" je
   AND uslov: jedna crvena REQ stavka obara ceo verdikt bez obzira koliko je ostalih
   REQ stavki zeleno; nema "skoro spreman" srednje stanje.
2. **B7 "who guards the guards"** — uslovni REQ koji važi samo za deterministic
   gate/validator/security agente; SKILL.md eksplicitno imenuje najčešći promašaj
   ("building the gate but never eval-gating the gate") i odbacuje izgovor da
   deterministički agent ne treba eval.
3. **C6 dva nezavisna uslova** — ispravna `{{var}}` interpolacija NE garantuje prolaz;
   `onError:"continue"` koji tiho propušta grešku je odvojen, nezavisan uslov koji sam
   po sebi obara C6.
4. **F4 HOTL vs HITL granica** — autonomni predlog koji NE upravlja runtime-om je OK
   uz memory-integrity gate (HOTL); ali svaki upis koji STVARNO upravlja runtime-om
   (KB koji čita `kb_search`, prompt, flow) zahteva ljudsko odobrenje + canary +
   auto-rollback (HITL) — dva slična scenarija koja se lako pomešaju.
5. **Edge case eskalacije** — kod autonomnog/scheduled agenta, E2 (budžet) i G3
   (schedule health) prelaze iz "nije REQ" u REQ; čitanje samo osnovne A-H tabele bez
   primene edge-case sekcije daje pogrešan (blaži) zaključak.
6. **STEP 5 obavezan redosled** — snapshot → (hermetički test ako je funkcija) →
   dry_run:true → dry_run:false → smoke, bez izuzetka za "trivijalne" izmene; tekst
   eksplicitno kaže "Never apply a behavior-changing fix without steps 1–5".

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(konkretan hipotetički scenario sa svim brojevima/stanjima potrebnim da se zadatak
nedvosmisleno reši — odgovoriv bez pristupa ovom razgovoru, fajlovima na disku ili
spoljnom stanju), `expected_output` (tačan zaključak i zašto, sa referencom na
konkretno pravilo iz SKILL.md), i `expectations` (konkretne, proverljive tvrdnje o
tome šta agentov odgovor mora i ne sme da sadrži — ne opšti utisci).

## Ograničenje

Ovo je "logic-only" sloj — testira da li agent ispravno primenjuje pravila kad mu se
da gotov nalaz, ne da li ume da PRIBAVI taj nalaz kroz prave `as_*` MCP pozive nad
živim agentom, niti da li stvarno piše sign-off notu u Obsidian. Nije zamena za pravi
end-to-end eval koji auditira stvaran Agent Studio agent i proverava da je sign-off
fajl zaista napisan. Kad bude vremena/budžeta za to, ovaj set treba proširiti pravim
run-ovima nad test-agentima u Agent Studio-u (uključujući namerno "loš" agent sa
poznatim gapovima, da se proveri da audit stvarno pronalazi te gapove) — ovih 6
slučajeva je početna, jeftina provera razumevanja pravila, ne konačna provera skilla.
