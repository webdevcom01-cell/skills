# Why moved

This was the entire contents of `_inbox/` (top-level, not a `_review*` subfolder —
those were handled separately in commit `cc31134`).

Every file checked individually before moving:
- `PATCH-skill-creator-pro.md` — the patch it describes was already applied verbatim
  in commit `fead825` (diffed the two texts, byte-identical after formatting).
- `evals.json` (4 cases), `evals-v5.json` (5 cases, older wording) — earlier drafts
  of skill-distiller's eval suite, both superseded by the version now committed at
  `standalone/skill-distiller/evals/evals.json`.
- `evals-v3fix.json` — byte-identical (sha256 match) to the already-committed
  `standalone/skill-distiller/evals/evals.json`. Pure duplicate.
- `skill-distiller.skill` (v1.0.0), `skill-distiller-v1.1.0.skill`,
  `skill-distiller-v1.3.0.skill` — packaged `.skill` zip archives of the exact same
  three superseded skill-distiller versions (families D, B, C) already moved to
  `_to_delete/` as raw directories in commit `cc31134`. Same content, just zipped.
- `skill-distiller-v1.4.0.skill` — packaged archive of the canonical version, which
  is already committed as `standalone/skill-distiller`.

Nothing here is new content. Canonical copy retained: `standalone/skill-distiller`.
