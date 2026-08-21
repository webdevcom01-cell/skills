# Eval set — soma-score-analyzer

## (a) Prvi eval set za ovaj skill

Ovo je prvi eval set za `soma-score-analyzer` i uopšte prvi eval bilo kog skilla u fazi
"06-rad-odrzavanje" (13 skillova, dosad nijedan sa evalom). Sadrži 6 slučajeva u
`evals.json`, u istom formatu koji koristi `skill-creator-pro/evals/evals.json` (`skill_name`,
niz `evals` sa `id`, `prompt`, `expected_output`, `expectations`).

## (b) Šta testira, šta ne testira, i zašto

Svi slučajevi testiraju čisto rezonovanje nad pravilima eksplicitno navedenim u SKILL.md —
posebno sekciju "Hard rules — zero hallucination" i korake koji sadrže brojčane pragove,
grananja ili lako-preskočiv redosled. Nijedan scenario ne pretpostavlja pristup stvarnom
Obsidian vault-u, KB-u ili agent-studio-db okruženju — svaki je samostalna hipoteza sa
konkretnim brojevima/stanjem, rešiva bez ičega van teksta prompta.

Eval set NE testira: (1) samu mehaniku poziva alata (`obsidian_read_note` parametre,
`as_search_knowledge_base` sintaksu) — to je integracioni test, ne rezonovanje o pravilima;
(2) Appendix A (scaffolding trajnog SA agenta) — to je opciona, irreverzibilna grana koja
zahteva eksplicitan zahtev korisnika i drugačiji tip verifikacije (dry_run, node/edge counts);
(3) Step 0.5 regression-check klasifikaciju (`regression` vs `flaky` vs `by_design`) — nije
uključena jer zahteva poređenje dva ai_response prompta koje agent ne može hipotetički
simulirati bez konkretnog teksta prompta, pa bi eval bio neproverljiv čistim rezonovanjem.
Ovo su prirodni sledeći kandidati za budući eval set, ne propust ovog.

## (c) Koje pravilo svaki slučaj cilja

1. **Winners-log prag je per-platform ≥17/20** (Hard rule 3) — testira da agent ne upiše
   samo "pobedničku" platformu nego SVE platforme ≥17, uključujući granični slučaj tačno 17.
2. **Zabrana izmišljanja rubrike** (Hard rule 1, Step 1 STOP uslov) — testira da agent stane
   i pita korisnika kad KB pretrage ne vrate upotrebljivu rubriku, umesto da skorira "na oko".
3. **Skorovanje samo stvarnog sadržaja / MISSING platforma** (Hard rule 2) — testira da
   nedostajuća platforma bude označena MISSING, ne procenjena, i da automatski ne kvalifikuje
   za winners-log.
4. **Append, nikad overwrite; supersede kao default** (Hard rule 5, Step 5b) — testira da
   agent doda novu liniju sa "supersedes UNSCORED entry" umesto da prepiše postojeću liniju
   bez eksplicitnog zahteva korisnika.
5. **Paginacija i backup pre replace-a** (Step 5b, detaljna procedura) — testira da agent
   prepozna da je jedan `obsidian_read_note` poziv nedovoljan (has_more/total_lines), da
   sabere sve stranice, proveri broj linija i napravi `.bak` pre pisanja — čak i kad je
   korisnik već eksplicitno odobrio replace.
6. **SINGLE_HOOK_BUG flag** (Step 4) — testira prepoznavanje edge case-a (identičan hook na
   svih pet platformi) i da flag ne potisne niti se pomeša sa nezavisnim ≥17 pragom za
   winners-log.

## (d) Format

Isti format kao `skill-creator-pro/evals/evals.json`: top-level `skill_name` i `evals` niz;
svaki slučaj ima `id` (broj), `prompt` (samostalan hipotetički scenario), `expected_output`
(tačan zaključak + pravilo iz SKILL.md na koje se oslanja) i `expectations` (lista konkretnih,
proverljivih tvrdnji — pogodnih za ručnu ili LLM-as-judge proveru).

## (e) Ograničenje i sledeći korak

Ovaj set proverava samo rezonovanje o pravilima (tekstualne odluke), ne i stvarno izvršavanje
alata — pravi test bi zahtevao da agent zaista pozove `as_search_knowledge_base`,
`obsidian_read_note/update_note` itd. nad simuliranim ili pravim KB/vault stanjem i da se
provere `expectations` nad stvarnim tool-call transkriptom (kao što `skill-creator-pro` primer
proverava `benchmark.json`/`grading.json` sadržaj). Sledeći korak je ili (1) dodati "izvršne"
eval slučajeve sa fixture Obsidian notama i mock KB odgovorima, ili (2) pokriti Step 0.5
regression-check i Appendix A granu posebnim setom čim se za njih definišu konkretni
ulazni fixture-i (npr. stvarni ai_response prompt tekstovi za HW/CR).
