# Evals for soma-model-preflight

Prvi eval set za ovaj skill otkad je uveden u biblioteku. `soma-model-preflight` je jedan
od 7 skillova u fazi 04 (Test/QA) koji do sada nije imao nijedan eval, iako mu je posao
da spreči tihe (silent) runtime otkaze — tačno onu vrstu greške koju je teško uočiti bez
sistematske provere.

## Šta ovaj set testira, i šta namerno ne testira

U produkciji `soma-model-preflight` poziva prave alate nad živim AgentStack sistemom:
`as_diagnose_models` (čita stvarno stanje API ključeva na serveru), `as_get_agent`
(čita stvarnu konfiguraciju agenta i njegovih node-ova) i `as_update_agent_model` /
`as_patch_node_field` (menjaju stvarno stanje agenta). Ovaj eval set ne poziva te alate
i ne pretpostavlja pristup ičijem živom AgentStack serveru ili konkretnim agentima —
nemamo tu infrastrukturu iz ove sesije. Umesto toga testira sloj koji je podjednako
kritičan a potpuno nezavisan od žive infrastrukture: kad se agentu da konkretan
hipotetički rezultat provere ključeva i konfiguracije agenta/node-ova, da li on ispravno
primenjuje sopstvena pravila iz SKILL.md da odluči šta JE i šta NIJE bezbedno, i koji
fallback (ako ijedan) treba predložiti.

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi u sekciji "Hard rules"
ili u koracima workflow-a, ne izmišljenu situaciju:

1. Hard rule #2 — proveriti node models pojedinačno, ne samo agent-level model (agent
   može izgledati OK na nivou, a jedan node ipak koristi model bez ključa).
2. Hard rule #5 — kad NIJEDAN ključ nije podešen (uključujući OPENAI_API_KEY), čak ni
   default fallback gpt-4.1-mini nije "sane" — mora se STATI, ne predložiti fallback.
3. Hard rule #1 — live provera uvek ima prednost nad snapshot-om zapisanim u SKILL.md;
   ako se ključevi promene, odluka prati live podatke.
4. Hard rule #3 — nikad ne primeniti `as_update_agent_model` bez eksplicitne potvrde
   korisnika, čak ni kad korisnik traži samo "proveru".
5. Napomena uz STEP 4 — prazan prompt na node-u je odvojen bug; zamena modela ga ne
   rešava i mora se posebno flagovati.
6. STEP 3, druga stavka — kad agent već ima radni OpenAI node, fallback treba da prati
   TAJ model radi konzistentnosti, a ne mehanički generički default gpt-4.1-mini.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(konkretan hipotetički scenario sa svim potrebnim brojevima/stanjima, rešiv čistim
rezonovanjem bez pristupa spoljnom stanju, fajlovima ili istoriji razgovora), `expected_output`
(tačan zaključak i pravilo iz SKILL.md na koje se oslanja) i `expectations` (konkretne,
proverljive tvrdnje o tome šta agent mora i ne sme reći, a ne opšti utisci).

## Ograničenje

Ovo je "logic-only" sloj — testira da li agent ispravno *rezonuje* nad pravilima, ne da
li stvarno ispravno poziva `as_diagnose_models` / `as_get_agent` / `as_update_agent_model`
nad pravim AgentStack serverom ili da li tačno parsira njihov stvarni JSON izlaz. Nije
zamena za pravi end-to-end eval protiv žive instance sa stvarnim agentima i stvarnim
API ključevima. Sledeći korak, kad bude dostupan pristup živom AgentStack okruženju: dodati
run-ove koji stvarno pozivaju `as_diagnose_models` nad test agentom sa namerno lošom
konfiguracijom (npr. klon ETL Pipeline Architect-a) i provere da li se predloženi fallback
zaista primenjuje i verifikuje kroz pravi `as_update_agent_model` poziv.
