# Edge cases

Loaded from `winners-log-logger/SKILL.md` — read when a run hits one of these specific scenarios (decimal score, unrecognized platform, multiple winners in one run, a manually-edited Reference section, a corrupted file missing ## Winners, backdated logging, an edit/delete request). Verbatim from the skill body, moved here only because the combined SKILL.md was approaching the repo's line-count budget.

---

## Edge cases

**Score 17.5 ili decimala:**
Odbij: *"SOMA scoring sistem koristi cele brojeve. Da li misliš 17/20 ili 18/20?"*

**Nepoznata platforma (Threads, Facebook, itd.):**
Pitaj: *"Koja platforma — linkedin, x, youtube, instagram, ili tiktok?"* — ne prihvataj ništa izvan 5 canonical vrednosti.

**Multiple winners u jednom run-u:**
Prikupi podatke za sve, napravi sve replacement-e sekvencijalno. Ne piši za prvog a zanemaruješ drugog.

**Korisnik ručno editovao Reference u Obsidianu:**
Skill vidi Reference ≠ placeholder → neće nuditi update. To je ispravno ponašanje — ručna edita je korisnikova odgovornost.

**Fajl postoji ali nema `## Winners` sekciju (corrupted):**
STOP. *"winners-log.md postoji ali `## Winners` sekcija nije pronađena — fajl je možda oštećen. Proverite ga ručno pre logovanja."*

**Kasno logovanje (juče ili ranije):**
Prihvati korisnikov datum. Normalizuj u YYYY-MM-DD. Logiraj sa tim datumom.

**Korisnik želi da obriše ili ispravi entry:**
Nije podržano ovim skillom. *"Editovanje postojećih entries nije podržano. Otvorite fajl direktno u Obsidianu."*
