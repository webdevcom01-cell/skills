# CHANGELOG — prospect-discovery

## 1.0.0 — 2026-08-22 (formalizacija verzije, bez zabeleženog delta-a)

`SKILL.md` do sada nije imao `version:` polje, iako ovaj CHANGELOG prati istoriju izmena — bio je
jedini skill sa CHANGELOG-om a bez deklarisane verzije. Ovaj CHANGELOG prati **datume, ne verzije**,
pa se broj nije mogao izvesti iz njega; `1.0.0` je dodeljen kao prva eksplicitna verzija zatečenog
stanja. **Ovog datuma nije promenjen sadržaj skilla** — unos postoji samo da verzija ima polazište.
Sve stvarne izmene su datumski unosi ispod.

## 2026-08-01 — fidelity and read-back patches

Six changes, derived from a root-cause analysis of one real run (a Serbian food
importer) in which the deterministic checker exited 0 while ten factual errors and
ten spec deviations were still in the pack. Fourteen of the twenty traced to a hole
in this spec rather than to operator carelessness.

The patches address **patterns**, not individual defects. Overfitting to one run was
the failure mode to avoid, so two defects whose rules were already clear and
correctly placed — a missing jurisdiction field, an outcome promise in the proposal —
were deliberately left alone.

### What changed

**1. `references/research-method.md` — new section, *Fidelity*.**
The three grades (CONFIRMED / CLAIMED / UNVERIFIED) all answer one question: *whose
assertion is this?* None asks *does the source say it as strongly as I wrote it?* —
and six of the ten factual errors lived in that gap. A registry field labelled
"Delatnost" became "pretežna delatnost"; "Vlasnici" became "osnivač"; "dostavlja
uzorke" became "priprema uzoraka"; "Preko 100m" with no stated currency became
"preko 100 miliona dinara". Each substitution looks harmless alone. The section adds
three corollaries: a restated list is restated whole or marked partial; a derived
figure (count, range, min, max) is computed rather than read and must say what it was
computed over; and platform furniture — a job board's badge, a breadcrumb — is not
the source speaking.

**2. `SKILL.md` Step 3 — the read-back pass.**
"The checker is a floor, not a ceiling" was buried as bullet 5 of 6 under *Honest
limits*, 217 words after the workflow ended, and appeared in no step. Step 3 spent
254 of 262 words on the automated gate and zero on reopening a source. It is now a
step: reopen each cited source and **read the source first, your claim second** —
the order is the technique, because a reader who already knows what a sentence was
meant to say supplies the missing support without noticing.

**3. `SKILL.md` Steps 3 and 7, `references/proposal.md` — the gate runs past the dossier.**
`check_sources.py` was invoked only on the dossier. The deviations clustered exactly
where it did not run: the proposal skeleton lost every citation it should have
carried, two files lost their retention line, the covering note carried an inference
as its headline confidence. Two words — "on the dossier" — had drawn the operator's
care map. The gate now covers the proposal and the intake block, with the reason
stated: the dossier is internal and its errors get corrected in conversation, while
the proposal is the file a client reads. Added the travelling rule — a line moving
from dossier to proposal carries its label *and its grade*.

**4. `references/handoff.md` and `SKILL.md` Step 1b — rules moved inside the copyable block.**
Where a template disagrees with prose about the template, the template wins.
`<candidate 1> [source]` beat "phrased as a question" sitting 35 lines below it, and
Step 1b's "write the pack in the call's language" beat handoff.md's "reproduce
exactly this". Field names now carry their own explanation inside the block, the
candidate placeholders are written as questions, and Step 1b names the intake block
as its one exception.

**5. `SKILL.md` Step 7 — retention on all five files, with the anchor resolved.**
Only the dossier was told to carry a deletion date, and the rule ("90 days after the
call") was unsatisfiable at the moment of writing, since no call is booked yet. All
five files now carry it, as the rule plus a fallback computed from the research date,
so a pack for a call that never happens still expires.

**6. `references/call-agenda.md` — the one-question test becomes an act, and the numbers contradiction is settled.**
Stated as a principle, the test lost to six named blocks with minute budgets waiting
to be filled: seven of twenty questions failed it in a pack whose author had read it.
Each finished question must now name the specific published thing it stands on.
Separately, `dossier.md` §8 requires recording *how long anything takes* while
`call-agenda.md` forbids asking for numbers in the block that section feeds — both
right, and the pipeline produced the forbidden question mechanically. Resolved: the
duration is a gap to observe via "walk me through it", not a figure to request.

### Deliberately not changed

- **`scripts/check_sources.py`.** The reflex fix and the wrong one. All ten factual
  errors were already checker-legible; one became *more* legible by acquiring a
  currency token it should never have had. The failure class is semantic and no regex
  reaches it. The checker's scope was worth widening; its intelligence was not.
- **A fourth grade for restatement.** The three grades share one axis — provenance —
  and a fidelity grade mixes axes. Worse, a label meaning "I reworded this" becomes a
  licence to keep the reworded version, which is the failure it was meant to prevent.
  Fidelity is a rule about which words go in, not a badge for the words that did.
- **A hard question cap per agenda block.** A numeric cap is the rigid checklist this
  skill's house style avoids, and compound questions would game it. The soft version
  carries the reasoning instead.
