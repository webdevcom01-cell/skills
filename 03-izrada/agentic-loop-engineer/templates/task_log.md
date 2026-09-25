---
task_id: "<popuni pri kreiranju>"
version: 1
description: "Append-only log svih iteracija - ULAZ za Dreaming (out-of-band) proces"
---

<!--
  Ovaj fajl JESTE deljen resurs kada više agenata piše u zajednički log
  (npr. centralni dashboard umesto po-worktree loga). Ako je centralizovan,
  SVAKI upis mora ići kroz compare-and-swap (vidi registry_write.py obrazac)
  - pročitaj version, pripremi izmenu, proveri da se version nije promenio,
  atomično upiši (write .tmp + rename), inače reload+retry.

  Ako je log po-worktree (preporučeno za v1 - jednostavnije), nema
  konkurentnog pristupa i version polje služi samo za audit trag.
-->

## Iteracija 1
- timestamp:
- verify_verdict: (PASS/FAIL/NO_APPLICABLE_CHECKS)
- max_confidence: (CONFIRMED/PLAUSIBLE/NONE)
- error_signature (ako FAIL):
- lines_changed:
- circuit_breaker_decision: (CONTINUE/STOP)
- napomena:

## Iteracija 2
...

<!--
  DREAMING PROCES (out-of-band, periodičan): čita sve task_log.md fajlove
  iz proteklog perioda, traži ponavljajuće error_signature obrasce kroz
  VIŠE različitih task-ova (ne samo unutar jednog), i predlaže patch za
  SKILL.md ili guardrails.yaml. Predlog ide čoveku na odobrenje - dreaming
  proces NIKAD sam ne commit-uje promenu pravila sistema.
  Ovo mapira na tvoj postojeći `instincts-updater` skill - koristi njega
  kao izvršioca ovog koraka umesto novog alata.
-->
