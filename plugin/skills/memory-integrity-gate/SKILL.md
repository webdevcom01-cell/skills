---
name: memory-integrity-gate
description: >-
  Adds a DETERMINISTIC, fail-closed Memory Integrity Gate to any agent or loop that promotes its own outputs into LEARNED MEMORY (winners-log, instincts, KB read by kb_search). It vets every candidate before it is learned — grounding facts against the SOURCE (not the candidate itself), blocking banned/vague-hype phrasing, requiring a named anchor and an independent score verdict — and QUARANTINES anything that fails. The concrete defense against OWASP ASI06 (Memory & Context Poisoning) in a self-improving agent. Use when the user says "add a memory gate", "vet outputs before learning", "anti memory poisoning", "stop bad data entering the KB", or Serbian "dodaj memory gate", "zaštiti learning loop", "spreči memory poisoning", "neka loop bezbedno uči". ALSO use when hardening an agent the enterprise-readiness audit flags as "learns / feeds memory" (C5/D3/F4). Do NOT use for a one-shot agent with no self-memory, for pre-publish output safety (separate gate), or to build the whole agent (use a scaffolder).
standards:
  - OWASP Top 10 for Agentic Applications 2026 — ASI06 Memory & Context Poisoning
  - Anthropic engineering (anti-fabrication, deterministic validation in code)
  - NIST AI RMF / EU AI Act (human oversight for runtime-steering memory)
version: 1.0.0
---

# Memory Integrity Gate

A self-improving agent learns from its own runs — it promotes "good" outputs into winners-logs, instincts, and KB documents that `kb_search` later feeds back into generation. If a fabricated, hyped, or poisoned output is learned, it is amplified across every future run (ASI06). This skill inserts a **deterministic gate that must approve a candidate before it is learned**, and quarantines the rest for human review.

## Core principles

1. **Fail-closed.** Anything that is not explicitly clean is QUARANTINED, never promoted. Unparseable input, missing/failed independent verification, or any flag → quarantine. A parse error must never become a promotion.
2. **Ground against the SOURCE, not the candidate.** A statistic/claim is "grounded" only if it appears in the trend title / source URL / angle / source excerpt — NEVER in the candidate text being vetted (or every claim is trivially "grounded" in itself; this is the single most common bug — test for it explicitly).
3. **Independent verification is mandatory.** The candidate's self-reported score is not trusted; an independent recomputation (e.g. a Score Analyzer) must return VERIFIED before promotion. Discrepancy → quarantine.
4. **Determinism in code, not prompt.** The gate is a `function` node, fully hermetic-testable. No "the LLM decides what to learn."
5. **Vet → quarantine → human-gated promotion of high-blast-radius memory.** Reversible memory (a winners reference) may auto-promote on a clean gate (HOTL). Memory that steers runtime — instincts/KB read by `kb_search`, prompts, flows — is HITL: gate + canary + auto-rollback, human approves the write.

## When to use vs not

- **Use:** any agent/loop that writes its own winners/instincts/KB; hardening an agent the readiness audit flagged as "learns/feeds memory".
- **Do NOT use:** one-shot agents with no self-memory; pre-publish output safety (different gate); whole-agent build (scaffolder).

---

## STEP 0 — Task list
Create: "Map what gets learned + the source of truth", "Design gate checks", "Hermetically test the gate function", "Deploy gate (function agent or inline)", "Wire into promotion path", "Add the gate's own eval suite", "Smoke + sign-off".

## STEP 1 — Map the learning path
Identify, from the live system (`as_inspect_flow`, the loop's scheduled task, the vault):
- **What is learned:** winners-log entries? instincts.md? KB docs? List each sink.
- **From what candidate:** the per-item output (hook text, claim, post).
- **What is the SOURCE OF TRUTH for grounding:** trend title, source_url, angle, fetched source excerpt — the things that came from outside the candidate. Record the exact variable/field names from the live payload — never assume.
- **Is there an independent score/verifier?** If not, that is a prerequisite gap (a self-score is not enough).

## STEP 2 — Design the gate checks (deterministic, per candidate)
The reference gate (battle-tested) applies, per item:
1. **UNGROUNDED_STAT** — every numeric stat (`%`, `x`, `times`, `fold`, `points`, `hours`, `tokens`, `k`) must appear in the SOURCE set (title + source_url + angle + source_excerpt). NOT in the candidate text. Else → quarantine. (Fail-closed bias: quarantining a real-but-unverifiable stat is cheap; promoting a fabricated one is the ASI06 risk.)
2. **BANNED_PHRASE** — hard clichés (game-changer, revolutionize, groundbreaking, paradigm shift, harness the power, unlock potential, changes everything).
3. **LOW_SPECIFICITY** — vague hype (signals a new era, raises the bar, leap forward/leap in, redefine, pushes the limits, sets a new standard, the future of, …). Extend this list from your own quarantine history; it is a deterministic function, so re-test after each addition.
4. **NO_ANCHOR** — the candidate must contain at least one named token from the trend title (so it actually names its subject; prevents generic, swappable claims).
5. **SCORE_UNVERIFIED** — the independent verifier's verdict must be exactly VERIFIED (and no per-item discrepancy); else the whole batch → quarantine (fail-closed).
- **Robust input parsing:** strip code fences; if `JSON.parse` fails, extract the first `{` … last `}` substring and retry; if still unparseable → quarantine_all (never promote). This survives preambles/newlines that an LLM-built payload may carry.

Output per item: `PROMOTE` (no flags) or `QUARANTINE` (with reasons). Aggregate verdict: PROMOTE_ALL / QUARANTINE_SOME / QUARANTINE_ALL.

A working starting template is in `mig.code.js` at the skill root (the deployed v2). Copy and adapt the SOURCE field names and the FILLER list to the target loop.

## STEP 3 — Hermetically test the gate function (BEFORE deploy)
Run the function in a sandbox (node) against golden cases. The non-negotiable set:
- clean grounded candidate → PROMOTE_ALL
- vague hype (e.g. "redefine") → QUARANTINE / LOW_SPECIFICITY
- fabricated stat NOT in source (e.g. "80%") → QUARANTINE / UNGROUNDED_STAT  ← this case catches the "grounded-in-itself" bug; if it PROMOTES, your allowed-set wrongly includes the candidate text
- independent verdict = DISCREPANCY / missing → QUARANTINE / SCORE_UNVERIFIED
- candidate missing the product name → QUARANTINE / NO_ANCHOR
- preamble + JSON → parses and grades (robustness)
- pure garbage → QUARANTINE_ALL / unparseable_input (fail-closed)
- a stat that IS in the source excerpt → PROMOTE (no false positive)
Iterate until all pass. Do not deploy a gate that has not passed its golden set.

## STEP 4 — Deploy the gate
- As a reusable, auditable agent: `as_create_agent` → `as_update_flow` with `function` node (the gate code, `outputVariable: gate_result`) → `message` node `{{gate_result}}` → edge. Dry-run, then apply (change protocol: snapshot → dry_run → apply → smoke).
- Or inline in the loop's promotion step if a standalone agent is overkill. Either way the logic is the same deterministic function.

## STEP 5 — Wire into the promotion path
In the loop that promotes to memory:
1. Get the candidate batch + the independent verifier's verdict (pass the FULL untruncated payload to the verifier — truncation causes false discrepancies).
2. Call the gate with `{trend, angle, source_excerpt, sa_verdict, posts:[{platform, text, score}]}`.
3. **Only PROMOTE items enter learned memory** (winners/instincts/KB). QUARANTINE items go to a quarantine log for human review — never silently dropped, never learned.
4. For high-blast-radius memory (instincts/KB that `kb_search` reads): require human approval (HITL) + canary (post-promotion eval ≥ threshold) + auto-rollback. Promote to the KB via a hash-deduped sync (e.g. kb-sync), never an ad-hoc standalone add, to avoid divergence/duplication.

## STEP 6 — Give the gate its OWN eval suite ("who guards the guards")
The gate enforces the bar, so it must meet the bar (enterprise checklist B7). Create an eval suite of the golden cases from STEP 3 with `contains` assertions (e.g. hype→`LOW_SPECIFICITY`, fabricated→`UNGROUNDED_STAT`, garbage→`unparseable_input`), enable runOnDeploy. A deterministic gate is trivially eval-able; a code edit that breaks it is then caught on deploy.

## STEP 7 — Smoke + sign-off
- `as_chat_with_agent` smoke: one clean payload (PROMOTE_ALL) and one hype/fabricated payload (QUARANTINE). 
- Record the gate, its golden set, its eval suite, and the promotion wiring in the agent's sign-off note.

---

## Anti-hallucination & safety rules
1. **Fail-closed always:** unparseable / unverified / any flag → quarantine. Never let a parse error or a missing verifier verdict become a promotion.
2. **Ground only against the source** (title/url/angle/excerpt), never the candidate text. Always include the "fabricated stat" golden case to prove it.
3. **The self-score is not trusted** — require an independent VERIFIED verdict.
4. **Quarantine, do not delete.** Quarantined items are kept for human review (a false positive can be promoted by a human; a poisoned item is contained).
5. **HITL for runtime-steering memory** (instincts/KB/prompt/flow): gate + canary + auto-rollback; human approves the write.
6. **Deterministic function, hermetically tested before deploy;** copy long code VERBATIM (or via a validated file), never retype from memory.
7. **Promote to KB via hash-deduped sync, not ad-hoc add** — prevents vault↔KB divergence and duplicate retrieval.

## Edge cases
- **No independent verifier exists:** build/wire one first (a deterministic recompute) — a self-reported score must not gate promotion.
- **Source excerpt not in the payload:** ground against title+angle+url; bias fail-closed (quarantine a stat you cannot verify) rather than trust it.
- **Gate quarantines a genuinely good item (false positive):** acceptable — a human promotes it from the quarantine log; tighten the FILLER/anchor rules only with a new golden case + re-test.
- **Learning signal is the quarantine log itself:** recurring quarantine reasons are a high-value instinct source ("avoid these phrasings") for the generator upstream — feed them to the instinct-proposal step (human-approved).

## Tool reference
| Tool | Use |
|---|---|
| `as_inspect_flow` | map the learning path / source variables |
| node sandbox (bash) | hermetic test of the gate function |
| `as_create_agent` + `as_update_flow`/`as_patch_node_field` (dry_run) | deploy the gate (snapshot first) |
| `as_chat_with_agent` | smoke + (manual) golden checks |
| `as_create_eval_case` (suite created in UI) | the gate's own eval suite (B7) |
| kb-sync skill | hash-deduped promotion of learned memory to the KB |
