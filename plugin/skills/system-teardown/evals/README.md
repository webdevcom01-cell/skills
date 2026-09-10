# system-teardown — evaluation results

Skill version under test: **0.2.3**. Runs executed 2026-08-19 and 2026-08-20.
Model: `claude-opus-5[1m]`, headless `claude -p`, one fresh session per run.

Verdict summary: **1 PASS / 12 FAIL of 13.** Every FAIL is the same single criterion (P4,
length overrun never acknowledged). No run failed on sections, ledger, or unknowns.

**Post-fix spot-check (not part of the 13):** `smoke-length-fix.md` is a single fresh Working-depth
run against skill v0.2.5, which added the STEP 6 length gate that this eval's P4 failures motivated.
It came in at 1245 words — against a 1963–3213 range here — and reported its own count and cut pass.
It is one run on one target type and does not establish that the 12-of-13 defect is closed; it is
also still 45 words over budget and mis-described that as "within." Read its own Outcome section
before drawing conclusions from it.

## Rubric

`RUBRIC.md` (verbatim copy of the pre-registered file). Four criteria, PASS only if all four
hold — no softened pass:

| | Criterion |
|---|---|
| **P1** | All template sections present for the chosen depth, or the omission said out loud |
| **P2** | Falsification ledger present, enumerated `C1..Cn`, non-empty, and `confirmed+downgraded+dropped = N` matching the actual row count |
| **P3** | "What we could not determine" present and non-empty where unknowns clearly existed |
| **P4** | Capability gaps (STEP -1) **and** length overrun stated out loud. Operationalised: >1200 words of deliverable body with no acknowledgement anywhere = fail |

Per-run grades in `grades.tsv`. Each `<run-id>.md` holds the verbatim prompt, the agent's
stdout, and the full deliverable the run wrote.

## Results

| Run | Target type | Target | Depth | P1 | P2 | P3 | P4 | Verdict | Words | Ledger |
|---|---|---|---|---|---|---|---|---|---|---|
| `codebase-1` | codebase | `~/agency-agents` @ 746efaa (158 tracked files) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2863 | 14+1+0=15 |
| `codebase-2` | codebase | `~/aifreshdaily-next` @ 038e016 (Next.js 15 + Supabase) | **full** | ✓ | ✓ | ✓ | ✓ | **PASS** | 8698 | 12+3+0=15 |
| `codebase-3` | codebase | `~/.claude/skills/agent-architect` (not a git repo) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2859 | 13+2+0=15 |
| `web-1` | web | `https://httpbin.org/` (third party, public) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2384 | 12+4+0=16 |
| `web-2` | web | `https://jsonplaceholder.typicode.com/` (third party, public) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2618 | 8+2+0=10 |
| `web-3` | web | `https://news.ycombinator.com/` (third party, public) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 3102 | 11+3+1=15 |
| `ai-1` | AI system | `~/.claude/agents/fact-checker.md` + live probing (user-owned) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2049 | 14+1+0=15 |
| `ai-2` | AI system | `~/.claude/agents/chief-of-staff.md` + live probing (user-owned) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2061 | 11+2+0=13 |
| `ai-3` | AI system | `~/.claude/skills/geo-prompt-library` + live probing (user-owned) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 3213 | 10+1+0=11 |
| `binary-1` | binary/protocol | PNG file, held-out `banner.png` | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2046 | 6+1+0=7 |
| `binary-2` | binary/protocol | `/opt/homebrew/bin/brotli` Mach-O arm64 (MIT OSS) | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 1963 | 11+1+0=12 |
| `binary-3` | binary/protocol | gzip member framing over the Homebrew `.gz` cache corpus | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2611 | 6+1+5=12 |
| `binary-4` | binary/protocol | `~/.claude/.git/index` (DIRC v2), held-out second index | working | ✓ | ✓ | ✓ | ✗ | **FAIL** | 2691 | 13+1+1=15 |

## Reasons

**`codebase-2` — PASS.** The only run that escalated depth, and it named the cue for doing so
("onboard a developer next week"). Produced all 16 as-built-spec sections including 16a.
Ledger 12+3+0=15. Tabulated its capability gaps (no service-role Supabase access) instead of
papering over them, which is what carries P4.

**Every other run — FAIL on P4 only.** All twelve produced correct, arithmetically consistent
ledgers and full section coverage, and all twelve stated their capability gaps. All twelve ran
1963–3213 words against an orientation-memo template that says "one to two pages," and not one
acknowledged the overrun anywhere in the deliverable or in stdout. This is a single systematic
skill defect, not twelve independent failures: the template states a length and nothing in the
skill makes the model check its output against it.

Per-run substance worth recording:

- `binary-1` — held-out capture **disconfirmed** C7; the run said so rather than quietly editing.
- `binary-3` — dropped 5 claims, including the eval prompt's own false premise (C11). 8 negative controls.
- `binary-4` — dropped C15 after held-out disconfirmation. 4 negative controls.
- `web-1` / `web-2` — every `[INFERRED]` row given a named ruled-out alternative. `web-1` refused load testing on authorization grounds; `web-2` refused to call C8 globally dead from one vantage point.
- `web-3` — respected third-party observation limits; read and honoured `robots.txt` before probing; one claim genuinely dropped.
- `codebase-1` — labelled the diff STATIC-ONLY per STEP -1 and refused to execute `install.sh` against the real `$HOME`. 16 of 16 Reflexion edges resolved.
- `codebase-3` — refused to verify quotes from training memory. 23 of 25 Reflexion edges resolved.
- `ai-1` — downgraded C15 to UNCONFIRMED on conflicting evidence instead of asserting it. Disclosed out loud that it reused a harness left by an earlier aborted attempt.
- `ai-3` — falsified the skill's own `content_hash` field by substituting 64 zeroes and getting `passed: true`; named the one place its differential test could not separate the arms (C9) rather than claiming it worked.

## Provenance and limits of this grading — read before trusting the numbers

Recorded honestly because it bears on how much weight the verdicts carry.

1. **The rubric is genuinely pre-registered, on disk, not from memory.** `RUBRIC.md` was
   written 2026-08-19 21:48 local. Twelve of the thirteen runs' outputs did not exist until
   after that timestamp.

2. **One run is a partial exception.** `raw-binary-2.json` landed 21:44, four minutes *before*
   the rubric file. The rubric header claims it was written before reading any run output;
   that claim cannot be established from timestamps for `binary-2` specifically. Treat
   `binary-2` as the one run where rubric-independence rests on assertion rather than evidence.

3. **All 13 grades were mechanically re-derived from the artifacts on 2026-08-20**, after the
   fact, by a script that recomputes word count, ledger `N`, the confirmed/downgraded/dropped
   sum, and the distinct `C`-id count directly from each deliverable. All 13 reproduced. The
   only discrepancies were 4–5 words on `codebase-2` and `codebase-3` (`wc -w` vs Python
   `split()`, nowhere near the 1200-word threshold). Two apparent length-acknowledgement hits
   were checked by hand and were regex false positives — "screenshot height exceeds it"
   (`binary-1`) and "≤6 words" (`ai-3`). P1/P2/P4-length are objective enough to be recomputed;
   P3 and the capability-gap half of P4 involve judgement and were not re-derived mechanically.

4. **`ai-1` is not a clean-room run.** Its first attempt died on a 429 session limit partway
   through, and the re-run started in a working directory that still held that attempt's probe
   battery, ablation subsets, and collected probe outputs. The run disclosed the reuse itself.
   The reused material is evidence-gathering scaffolding, not deliverable structure, so it does
   not touch P1–P4 — but this run is a continuation, not an independent repeat.

5. **Runs were not all executed under the same conditions.** `binary-2` and five others ran
   2026-08-19; the rest ran 2026-08-20, and `ai-1`/`ai-3` ran last, after a 5-hour usage-limit
   reset, sequentially rather than in parallel. `web-3` and `ai-2` had completed on disk earlier
   but were only collected into this directory afterwards.

6. **n=1 per target.** Thirteen runs across four target types, one run per target, no repeats.
   Nothing here measures run-to-run variance, and no single verdict should be read as a stable
   property of the skill.

7. **Self-grading.** The runs and the grading were produced by the same model family. P1/P2 are
   mechanical enough to survive that; P3 and the capability-gap half of P4 are not.

## What this says about the skill

The falsification machinery works. Thirteen of thirteen runs produced an enumerated ledger with
arithmetic that checks out, and several disconfirmed or dropped their own claims — including one
that dropped the eval prompt's false premise, and one that falsified a field in its own target.
That is the behaviour the skill exists to force, and it held across all four target types.

The length discipline does not work. 12 of 13 blew past the stated template length with no
acknowledgement. The fix belongs in the skill, not in the rubric: `assets/orientation-memo.md`
states "one to two pages" but nothing instructs the model to check its draft against that number
or to say so when it exceeds it. Until that is addressed, expect ~2000–3200-word orientation
memos where the template asks for ~1200.
