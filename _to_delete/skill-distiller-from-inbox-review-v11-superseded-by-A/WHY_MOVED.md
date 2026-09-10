# Why moved

This was Family B (`_inbox/_review_v11`), `skill-distiller` version `1.1.0`.

Diffed against the canonical `standalone/skill-distiller` (Family A, version `1.4.0`):
this version is missing the entire mechanical verbatim-copy check step (calling
`scripts/check_verbatim_overlap.py`), which A's own changelog text says was added
after a real distillation run reproduced up to 29 consecutive words of source text
nearly verbatim while self-reporting that it hadn't — self-assessment alone wasn't
reliable enough. Running this version instead of A would silently drop that safety
check. Canonical copy retained: `standalone/skill-distiller`.
