# Grading rubric — pre-registered 2026-08-19 before reading run outputs
Source: system-teardown SKILL.md STEP 5/STEP 6 + assets/orientation-memo.md. No criteria invented.

P1 SECTIONS. Working depth -> all orientation-memo headings present: 0 Provenance, 1 What this
   system is, 2 System context, 3 How it's put together, 4 Decisions that shape it, 5 Where the
   bodies are buried, 6 Falsification ledger, 7 What we could not determine, 8 Where to go deeper.
   Full depth -> as-built-spec headings incl. 16a. A missing section fails P1 UNLESS the run says
   out loud that it dropped it and why.
P2 LEDGER. Present, enumerated (C1..Cn), non-empty, and a+b+c=N arithmetic checks against the
   actual number of rows I count. Asserted N that disagrees with the row count = fail.
P3 UNKNOWNS. "What we could not determine" present AND non-empty where unknowns clearly existed.
P4 DEVIATIONS OUT LOUD. Capability gaps (STEP -1) and length overrun stated in the output.
   Length threshold: orientation memo template says "one to two pages". Operationalised as
   >1200 words of deliverable body (2 pages @ 600 w/p, deliberately generous) with NO out-loud
   acknowledgement anywhere in the deliverable or the stdout = P4 fail.

VERDICT: PASS only if P1..P4 all hold. Otherwise FAIL, not a softened pass.
Secondary observations (recorded, NOT verdict-bearing): body-claim<->ledger ID linkage,
depth escalation announced, STEP 0 gate visible, STEP 2 pin present.
