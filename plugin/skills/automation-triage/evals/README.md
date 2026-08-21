# Eval set za automation-triage

Ovo je prvi eval set za skill `automation-triage`, deo faze 06-rad-održavanje — koja trenutno, od 13 skillova, nema nijedan drugi eval set. Cilj nije pokriti ceo skill, već napraviti čvrst temelj: šest slučajeva koji svaki cilja jedno eksplicitno, lako-pogrešivo pravilo iz `SKILL.md` i njegovih `references/` fajlova, izraženo kao samostalan hipotetički scenario rešiv čistim rezonovanjem, bez pristupa disku, skriptama ili prethodnom razgovoru.

## Šta testira, i koje pravilo cilja svaki slučaj

1. **Sito sme samo DROP/ADVANCE, nikad verdikt** (Korak 2: *"The sieve may only DROP or ADVANCE. It may never reach a verdict."*). Testira da agent ne "presudi" REFUSE iz četiri polja prvog prolaza, čak i kad signal deluje alarmantno, i da primeni jedini uslov za DROP: `frequency-band == "rarely"`.
2. **`data-access == 0` bezuslovno vodi ka REFUSE** (dimensions.md: *"Score 0 honestly. It is a REFUSE."*). Testira da nizak error-cost ne "spasava" zadatak — ovo je prva provera u lancu i ne zavisi od drugih polja.
3. **`error-cost == high` I `verifiability == 0` istovremeno → REFUSE bez obzira na volumen** (dimensions.md, citat: *"high with verifiability 0 is a REFUSE regardless of volume"*). Testira da agent prepozna nezavisnu AND-granu i ne dozvoli velikom volumenu (300h) da nadjača pravilo.
4. **Verifiability se boduje prema onome što zadatak proizvodi DANAS, ne prema budućem sistemu** (dimensions.md, "The trap", uz doslovan primer *"the output looks right — that is a 1"*). Testira precenjivanje ocene 3 zato što bi izlaz *mogao* biti strukturiran kad bi se agent drugačije izgradio.
5. **Fragilnost se proverava u OBA smera (0.5× i 2×), ne samo u jednom** (Korak 5, i logika u `score_task.py`). Najkompleksniji slučaj — sadrži pun numerički primer da agent mora izračunati oba scenarija i otkriti da provera samo jednog smera (2×) daje lažan osećaj sigurnosti.
6. **Nedostajuće polje postaje `NOT MEASURED` i vodi ka WATCH, nikad se ne popunjava procenom** ("Two rules that govern everything": *"it does not get a plausible number"*). Testira da odlične ostale dimenzije ne nadjačaju ovo pravilo kad je volumen nepoznat.

## Šta NE testira, i zašto

Set namerno ne pokriva: format tri izlazna dokumenta, kategorije grešaka `check_triage.py` (FORBIDDEN, NAMED_PERSON...), pravilo o 3-7 zadataka za predaju, zabranu prenosa sati u handoff, ili zabranu wildcard karaktera u imenu zadatka. Ovi su podjednako eksplicitni, ali ili zahtevaju proveru generisanog dokumenta (teže se svode na čist "prompt → rezonovanje" oblik), ili se suštinski preklapaju sa principom koji slučaj 6 već pokriva ("ne izmišljaj/ne otkrivaj ono što ti nije rečeno" — npr. "roles never names"). Ostavljeno je za sledeću iteraciju, radije nego forsirano ugurano ovde sa slabijom utemeljenošću.

## Format

Prati format `skill-creator-pro/evals/evals.json`: `skill_name`, niz `evals` sa `id`, `prompt`, `expected_output` (zaključak sa razlogom i referencom na pravilo), `expectations` (3-5 proverljivih tvrdnji po slučaju).

## Ograničenje i sledeći korak

Ovi slučajevi proveravaju samo *rezonovanje* o pravilima — nijedan ne pokreće stvarno `scripts/score_task.py` ili `screen_task.py`, niti proverava da agent zaista poziva te skripte umesto da "u glavi" računa verdikt (a SKILL.md je eksplicitan: "the arithmetic must not be yours"). Sledeći korak je drugi sloj evala koji proverava izvršenje skripti sa ispravnim argumentima — to zahteva izvršno okruženje sa pristupom `scripts/`, van okvira ovog prvog, čisto rezonskog seta.
