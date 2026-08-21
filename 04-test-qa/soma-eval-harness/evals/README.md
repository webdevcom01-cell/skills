# Evals for soma-eval-harness

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Avgust 2026 quality audit je
pokazao da nijedan od 7 skillova u fazi 04 (Test/QA) nema svoj eval — uključujući ovaj
skill, čiji je posao da gradi eval-ove za druge SOMA agente.

## Šta ovaj set testira, i šta namerno ne testira

U produkciji `soma-eval-harness` poziva prave SOMA agente (`as_chat_with_agent`) i čita
živ Obsidian vault (`agents/*/evo-log.md`). Ovaj eval set ne pokreće taj pravi pipeline —
nemamo pristup korisnikovom živom SOMA vault-u iz ove sesije. Umesto toga testira deo
koji je podjednako kritičan a potpuno nezavisan od žive infrastrukture: da li agent, kad
mu se da konkretan hipotetički ishod grejdera (G1–G4, M1, M2, cr_flag, itd.), ispravno
primenjuje sopstvena pravila iz SKILL.md da izračuna `observed_grade`, `trial_correct`,
`valid_trials`, `consistency` i lifecycle odluke (graduation/regression).

Svih 6 slučajeva cilja pravilo koje SKILL.md sam eksplicitno označava kao lako za
pogrešiti — nisu izmišljene situacije, nego direktni citati iz teksta skilla:

1. Polaritet ishoda kod guardrail zadatka (Hard rule #11) — FAIL koji je *ispravan* je
   uspeh, ne neuspeh. Ovo je najverovatnija greška: naivna implementacija tretira svaki
   `observed_grade = FAIL` kao lošu vest bez provere `expected_grade`.
2. Isključivanje TIMEOUT/ERROR iz `valid_trials` i MIN VALIDITY prag (< 3 → INCONCLUSIVE).
3. `G3 = WARN` mora da eskalira na H1 — ne sme se rešiti direktno iz G/M gradera.
4. Graduation zahteva 3 UZASTOPNA run-a, ne jedan — lako se preskoči pri prvom čitanju.
5. Regression pravilo ima DVA nezavisna uslova ("drops ≥ 2 trials OR crosses a band
   boundary downward") — pad od samo 1 trial-a (5/5 → 4/5) i dalje je regresija jer
   prelazi granicu banda, što se lako previdi ako se čita samo prvi uslov.
6. M1 retry na graničnom skoru uzima NIŽI rezultat, ne prvi ni prosek.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(konkretan hipotetički scenario, odgovoriv bez pristupa spoljnom stanju ili istoriji
razgovora — isti princip kao "queries must satisfy" pravilo u
`skill-creator-pro/evals/README.md`), `expected_output`, i `expectations` (konkretne,
proverljive tvrdnje, ne opšti utisci).

## Ograničenje

Ovo je "logic-only" sloj — testira razumevanje pravila, ne stvarno izvršavanje pipeline-a.
Nije zamena za pravi end-to-end eval protiv živog SOMA vault-a (onako kako
`system-teardown/evals/` ima stvarne izvršene run-ove sa `grades.tsv`). Kad bude vremena/
budžeta za to, ovaj set treba proširiti pravim `as_chat_with_agent` run-ovima protiv
stvarnih TI/HW/CR agenata — ovih 6 slučajeva je početna, jeftina provera razumevanja
pravila, ne konačna provera skilla.
