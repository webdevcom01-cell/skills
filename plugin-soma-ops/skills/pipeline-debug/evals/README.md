# Evals for pipeline-debug

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Faza 04 (Test/QA) ima 7
skillova, i pre ovog seta nijedan od njih nije imao svoj eval — uključujući
`pipeline-debug`, čiji je posao da dijagnostikuje kvarove u SOMA pipeline-u
(TI → HW → CR → Score Analyzer).

## Šta ovaj set testira, i šta namerno ne testira

U produkciji `pipeline-debug` poziva prave AgentStack MCP alate
(`as_health_check`, `as_get_recent_executions`, `as_find_broken_flows`,
`as_inspect_flow`, `as_list_knowledge_bases`, `as_patch_node_field`) i čita živ
Obsidian vault (`agents/*/evo-log.md`) — i pri primeni popravke stvarno **mutira
produkciju** preko `as_patch_node_field`. Ovaj eval set ne pokreće ništa od toga —
nemamo pristup korisnikovom živom SOMA vault-u ni AgentStack instanci iz ove
sesije, i ne bi bilo odgovorno simulirati poziv koji piše u tuđu produkciju.

Umesto toga, set testira sloj koji je podjednako kritičan a potpuno nezavisan od
žive infrastrukture: dat konkretan hipotetički skup "već pročitanih" nalaza
(status izvršenja, evo-log linije, broj KB-ova, D4/D5 rezultate — tačno onakve
kakve bi vratili gorenavedeni MCP alati), da li agent ispravno primenjuje
sopstvena eksplicitna pravila iz Step 9 (IF-THEN root cause tabela) i Step 10
(uslovi za auto-primenu popravke) da izvede zaključak. Ovo je namerno "logic-only"
sloj — proverava razumevanje pravila, ne stvarno izvršavanje dijagnostike ili
pisanje u produkciju.

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi kao lako za
pogrešiti — nisu izmišljene situacije, nego direktni citati iz teksta skilla:

1. **TIMEOUT prag (RULE M1)** — "duration > 5 min" je striktna nejednakost;
   trajanje od tačno 5:00 ne ispunjava uslov, iako je agent i dalje RUNNING.
2. **QUALITY_DEGRADATION OR uslov sa dve nezavisne grane** — HW grana zahteva
   *uzastopne* UNSCORED unose, CR grana samo traži 2 od poslednjih 5 sa
   QUALITY_VIOLATIONS bez zahteva za uzastopnošću; lako se pogrešno primeni isti
   "consecutive" uslov na obe grane.
3. **RULE C7 (KB_UNWIRED) zahteva kb_count == 1 tačno** — 2 ili više KB-ova čini
   fix "Ambiguous KB", eksplicitno non-trivial po Step 10 i 10c, bez obzira na
   korisničku potvrdu.
4. **Non-trivial lista nadjačava C2/C3 eligibility** — prazan prompt je CRITICAL
   po RULE C2, ali je eksplicitno na Non-trivial listi ("Empty prompt (needs
   human content)") i zato se NIKAD ne auto-primenjuje, čak ni uz potvrdu.
5. **Step 8 eskalacija na DEEP, uslov (b)** — CRASH simptom sa samo WARN nalazima
   mora eskalirati, i eskalacija bezuslovno pokreće D7 čak i kad originalna
   poruka nije sadržala quality trigger reči.
6. **10a Active execution guard nadjačava 10a.5 potvrdu** — RUNNING status agenta
   se proverava neposredno pre patch poziva i preskače popravku bez obzira na to
   što je korisnik već rekao "da".

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`,
`prompt` (konkretan hipotetički scenario sa svim potrebnim brojevima i stanjima,
rešiv čistim rezonovanjem iz pravila u SKILL.md — bez pristupa spoljnom stanju,
konkretnim putanjama sa diska ili istoriji razgovora), `expected_output` (tačan
zaključak i pravilo iz SKILL.md na koje se oslanja), i `expectations` (konkretne,
proverljive tvrdnje o tome šta agent mora i ne sme da zaključi ili uradi).

## Ograničenje

Ovo je "logic-only" sloj — testira da li agent ispravno primenjuje IF-THEN
pravila i uslove za auto-primenu popravke nad *datim* podacima, ne da li ume da
pravilno pozove pravi niz MCP alata (D0–D7 redosled, filtriranje `{debug_scope}`,
parsiranje stvarnog evo-log formata sa pravim graničnim slučajevima) protiv
prave SOMA instance, niti da li `as_patch_node_field` poziv sa pravim
`node_id`/`kb_id` zaista uspeva i prolazi post-patch verifikaciju (Step 10d). Kad
bude dostupan test AgentStack workspace sa kontrolisanim, namerno pokvarenim
SOMA agentima, ovaj set treba proširiti pravim end-to-end run-ovima koji stvarno
pozivaju alate i proveravaju da izveštaj i (potvrđene) popravke odgovaraju
očekivanom stanju — ovih 6 slučajeva je početna, jeftina provera razumevanja
pravila, ne konačna provera skilla.
