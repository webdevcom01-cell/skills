---
task_id: "<popuni pri kreiranju>"
version: 1
last_updated: "<ISO timestamp>"
description: "Radna memorija za tekući task - Think faza svake iteracije ide ovde PRE Act-a"
---

<!--
  PROGRESSIVE DISCLOSURE napomena: ovaj fajl je namenjen da bude KRATAK
  i da se čita u celosti svaki put (radna memorija). Detaljna dokumentacija,
  arhivirani task_log unosi ili reference materijali NE idu ovde - idu u
  references/ i učitavaju se samo na eksplicitan zahtev.

  OPTIMISTIC CONCURRENCY: ovaj fajl je u worktree-u pojedinačnog agenta,
  pa nema konkurentnog pristupa - version polje je i dalje tu radi
  konzistentnosti sa deljenim fajlovima (task_log.md, registry.json) i radi
  lakšeg auditovanja istorije izmena.
-->

## Cilj zadatka (kopija iz task_spec.md, ne menjati)
<popuni>

## Acceptance criteria (deterministički, checklist)
- [ ] <kriterijum 1 - npr. "test suite X prolazi">
- [ ] <kriterijum 2>

## Iteracija N - Think
- Šta je stanje posle prethodnog Verify koraka:
- Plan za ovu iteraciju (1 atomična izmena, ne serija nepovezanih):
- Očekivani rezultat Verify koraka:

## Iteracija N - Observe (sirovi rezultat, bez interpretacije)
```
<stdout/stderr/diff summary>
```

## Iteracija N - Verify (iz checker-verify.sh, ne subjektivna ocena)
- deterministic_status:
- max_confidence:
- Napomena ako je NO_APPLICABLE_CHECKS ili PLAUSIBLE:

## Istorija odluka (append-only, ne brisati prethodne)
- <iteracija broj> - <kratak zaključak>
