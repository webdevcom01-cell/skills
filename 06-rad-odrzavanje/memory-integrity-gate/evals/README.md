# Evals za memory-integrity-gate

## (a) Zašto je ovo prvi eval set i zašto je prioritet

Faza "06-rad-odrzavanje" ima 13 skillova i do sada nijedan nije imao svoj eval set.
`memory-integrity-gate` je prvi koji ga dobija, i to namerno — ranija analiza cele
biblioteke ga je označila kao VISOK prioritet zajedno sa `soma-memory-fix`, jer ova
dva skilla dodiruju **živu memoriju agenta u produkciji** (winners-log, instincts.md,
KB koju čita `kb_search`). Skill sam sebe opisuje kao "the concrete defense against
OWASP ASI06 (Memory & Context Poisoning)" — ako gate pogrešno propusti nešto što je
trebalo blokirati, ta greška se ne gasi sama od sebe: fabrikovan ili hyped sadržaj
ulazi u naučenu memoriju i **amplifikuje se u svakom budućem run-u** koji tu memoriju
čita. Cena lažnog negativa (propušten poison) je nesrazmerno veća od cene lažnog
pozitiva (karantinovan dobar item, koji čovek može ručno promovisati) — zato evali
namerno testiraju baš granicu "da li bi agent pogrešno zaključio PROMOTE tamo gde
SKILL.md eksplicitno traži QUARANTINE".

## (b) Šta testira / ne testira

Testira se isključivo **rezonovanje o pravilima gate-a** iz teksta SKILL.md — da li
agent, suočen sa konkretnim (izmišljenim ali samodovoljnim) kandidatom i njegovim
source/verifier podacima, ume da primeni deterministička pravila i fail-closed
bias. Ne testira se izvršavanje `mig.code.js` koda (fajl ne postoji u ovoj instalaciji
skilla), ne testira se `as_inspect_flow`/`as_create_agent` orkestracija iz STEP 4-7,
niti UI/deploy mehanika. Svih 6 slučajeva je rešivo čistim rezonovanjem iz pravila
navedenih u SKILL.md, bez pristupa fajlovima, razgovoru ili spoljnom stanju — svaki
prompt nosi kompletan hipotetički payload (title/angle/excerpt, tekst kandidata,
verifier verdict) unutar sebe.

## (c) Koje pravilo svaki slučaj cilja

1. **Grounding samo protiv SOURCE-a, nikad protiv kandidata** (Core principle 2, STEP 2.1)
   — kandidat sa fabrikovanim brojevima koji ne postoje u title/url/angle/excerpt mora
   biti karantinovan i pored VERIFIED skora. SKILL.md ovo naziva "the single most
   common bug"; propust ovde direktno znači promociju izmišljene statistike.
2. **Nezavisna verifikacija je AND uslov na nivou celog batch-a** (STEP 2.5) — jedna
   diskrepanca karantinuje ceo batch, ne samo pogođeni item; selektivna promocija
   "čistih" item-a pored nje je kršenje fail-closed principa.
3. **NO_ANCHOR kao samostalan uslov** (STEP 2.4) — tekst bez ijednog imenovanog tokena
   iz izvora mora u karantin i kad su sve druge provere čiste, jer generička tvrdnja
   bez anchor-a je lako zamenljiva/poisonable.
4. **Fail-closed na neparsibilan input** (STEP 2 "Robust input parsing", Anti-hallucination
   rule 1) — kad ni strip-fences ni ekstrakcija `{...}` supstringa ne uspeju,
   ceo payload ide u QUARANTINE_ALL; ručno "krpljenje" JSON-a mimo determinističke
   funkcije je van dozvoljenog procesa.
5. **HOTL vs HITL po blast-radius-u memorije** (Core principle 5, STEP 5.4) — čist
   gate PROMOTE dovoljan je za auto-promociju u winners-log, ali NIJE dovoljan za
   instincts/KB koje `kb_search` čita u runtime-u; tu treba i canary, i auto-rollback,
   i eksplicitno ljudsko odobrenje.
6. **LOW_SPECIFICITY kao samostalan uslov + ispravan proces za false positive**
   (STEP 2.3, sekcija "Edge cases") — vague-hype fraza karantinuje i kad je sve
   ostalo čisto; a ispravljanje lažnog pozitiva ide preko ručne promocije iz
   karantin loga, nikad preko ad-hoc olabavljivanja pravila bez novog golden
   test slučaja.

Svaki od ovih šest slučajeva cilja tačku u kojoj bi pogrešan zaključak značio da
gate **propusti** nešto što je trebalo blokirati (ili nepotrebno automatizuje upis
koji je trebalo da prođe kroz čoveka) — što je direktno oštećenje integriteta
naučene memorije.

## (d) Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: niz od 6
objekata sa `id`, `prompt` (samostalan hipotetički scenario), `expected_output`
(tačan zaključak + obrazloženje sa referencom na pravilo) i `expectations` (4-5
konkretnih, proverljivih tvrdnji pogodnih za `contains`/checklist stil provere).

## (e) Ograničenje i sledeći korak

Ovaj set testira samo rezonovanje o pravilima, ne i stvarno izvršavanje gate koda
(jer `mig.code.js` nije prisutan u ovoj instalaciji skilla) niti end-to-end deploy
tok (STEP 4-7: `as_create_agent`, dry-run/apply, smoke test). Sledeći korak bi bio
hermetički test set (Node sandbox, golden cases iz STEP 3) koji pokreće stvarnu
gate funkciju kad `mig.code.js` bude prisutan, plus eval koji proverava da je gate-ova
**sopstvena** eval suite (STEP 6, "who guards the guards") zaista povezana sa
`runOnDeploy`.
