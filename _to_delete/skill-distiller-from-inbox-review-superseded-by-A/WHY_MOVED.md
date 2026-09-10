# Why moved

This was Family D (`_inbox/_review`), `skill-distiller` version `1.0.0` — the oldest
of the four families found on disk (two other identical copies of this same family
were already sitting in `_to_delete/` from an earlier session).

Diffed against the canonical `standalone/skill-distiller` (Family A, version `1.4.0`):
missing the mechanical verbatim-copy check (same gap as Family B) and also missing
the "fidelity to source" quality check — only 2 of A's 4 advisory quality checks are
present. Confirmed internally consistent (its SKILL.md body never references the
scripts/files it lacks, so it isn't a broken copy, just an earlier one). Canonical
copy retained: `standalone/skill-distiller`.
