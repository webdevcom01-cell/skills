# Trigger eval — prompt-engineer-pro

**Date:** 2026-08-14 · **Harness:** `skill-creator-pro/scripts/run_eval.py`
**Model:** sonnet via `claude -p` · 3 runs/query, trigger threshold 0.5
**Environment:** the full ~54-skill library live, so collisions were tested under real
conditions.

## Headline

The skill fires on **20%** of the queries it exists to serve. That is a genuine
defect, confirmed against a positive control, and **it is not caused by the v2
rewrite** — v1 was worse.

Three description variants and a positive control were run to establish this.

## Round 1 — v1 vs v2, uncalibrated set (22 queries)

| | v1 (old) | v2 (new) |
|---|---|---|
| Recall | 8% (1/12) | 17% (2/12) |
| Precision | 100% (10/10) | 100% (10/10) |
| Runs with **no tool call at all** | 37/64 (58%) | 22/63 (35%) |

v2 is not a regression — triggering was already broken. v1 carried a 19-item explicit
keyword list (`"create prompt"`, `"napravi prompt"`, `"optimizuj prompt"`, …) and fired
on **1 of 12**. Keyword stuffing was not doing the work people assume it does.

The no-tool number flagged a problem with the *eval set*, not the skill: on a third to
half of runs the model answered inline. For some queries that is correct behaviour.

## Round 2 — recalibrated set (23 queries)

Positives were split by one question: **does a good answer require a procedure or a
script, or can a strong model just answer?**

- **Class A** (10) — needs the audit script, the diff, the test generator, a repeatable
  procedure. Must trigger.
- **Class B** (3) — advice (`how many few-shot examples`, `does duplication hurt`).
  The model answering inline is the *right* outcome. Moved to negatives.
- **Collision + unrelated** (10) — `skill-creator-pro`, `agent-scaffolder`,
  `agent-architect`, `geo-prompt-library`, plus two off-topic.

| Variant | Recall (class A) | Precision |
|---|---|---|
| v2.0 — current description | **20%** (2/10) | 100% (13/13) |
| v2.1 — description naming the bundled scripts | **10%** (1/10) | 100% (13/13) |

Class B scored 3/3 and collisions 10/10, which validates the recalibration: the round-1
numbers were polluted by queries that should never have been positives.

**The v2.1 hypothesis failed.** The theory was that the model declines to invoke because
the description reads like advice-about-prompts rather than a capability it lacks, so
v2.1 named `evaluate_prompt.py`, `compare_prompts.py` and `generate_test_cases.py`
explicitly. Recall went *down*, 20% → 10%.

Two distinct theories of the description — exhaustive keywords (v1), concrete capability
inventory (v2.1) — both underperformed the plain version. With n=10 queries × 3 runs the
8/10/20% spread is inside the noise band; the honest reading is that all three
descriptions perform about the same, and **the description text is not the lever.**

## Round 3 — positive control

Same harness, same model, same environment, same 54-skill library, run against
`skill-creator-pro` and its own eval set:

**Recall 80% (8/10), 23/26 raw fires.**

So the instrument works, `claude -p` invokes skills readily, and a large skill library
does not suppress firing. The 20% is prompt-engineer-pro's own.

*(Precision on the control is confounded — the real skill and the harness decoy were
both installed — but recall is what the control was for.)*

## Diagnosis

The structural difference between the two skills is the **rarity of the noun they own.**

`skill-creator-pro` owns `skill`, `SKILL.md`, `.skill`, `eval harness` — rare tokens that
map 1:1 onto one capability, with no competing reading. Its passing queries are all of
the form *"napravi mi skill…"*, *"kako da spakujem svoj skill"*.

`prompt-engineer-pro` owns `prompt` — the single most ambient noun in the model's world.
Every request is a prompt. Writing and fixing prompts is something the model does
natively, constantly, without help. Asked to audit a prompt, the model's default
judgment is *"that is just my job"* — and it is not entirely wrong.

That is why rewording does not move the number: no description can make the model
believe it needs a tool for something it is already doing.

## What follows

Ranked, honestly:

1. **Accept it and invoke explicitly.** Call the skill by name when it is wanted. Many
   skills operate this way; ambient triggering is a bonus, not a requirement. Zero work,
   and precision is already perfect so there is no downside risk.
2. **Narrow the skill to what genuinely needs tooling** — the deterministic audit and the
   before/after diff — and drop the advice surface. A narrower skill has a rarer trigger
   surface (`audituj prompt`, `dokaži da nije regresija`) and may clear the bar that
   `write a prompt` never will. This is a real redesign, not a reword.
3. **Do not run `improve_description.py` and ship the output.** Its own prompt warns
   against an ever-expanding keyword list, and v1 is the local proof that the approach
   fails here.

## Limitations

- n = 10 class-A queries × 3 runs. Differences under ~30 percentage points are not
  distinguishable. The 20-vs-80 control gap is.
- Sonnet only. Trigger behaviour may differ on other models.
- Eval-set authorship and skill authorship were the same, which is a bias; the class A/B
  split was written to reduce it but does not eliminate it.

## Wider implication

This skill was measured only because it was being rewritten. The other ~53 have not been.
A skill that never fires throws no error and produces no visible symptom — just slightly
worse answers, indefinitely. The control shows the measurement is cheap and the signal is
strong. On this evidence, silent non-firing is worth checking across the library, and the
skills most at risk are the ones whose domain is the model's own native activity.
