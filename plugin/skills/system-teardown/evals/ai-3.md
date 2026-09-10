# Run `ai-3` — raw output

| | |
|---|---|
| Target type | ai |
| Target / pin | ~/.claude/skills/geo-prompt-library + live claude -p probing (user-owned) |
| Verdict | **FAIL** |
| session_id | `3f8c9ee3-2d1b-4946-b16f-4be248e8b012` |
| Turns | 47 |
| Cost (USD) | 4.34 |
| is_error | False |
| Deliverable | geo-prompt-library-orientation.md |
| Deliverable words | 3213 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 10+1+0=11 correct across C1..C11, all 9 sections; falsified the content_hash field by substituting 64 zeroes and getting passed:true; named the one place the differential test could not separate the arms (C9) instead of claiming it worked; 3213w vs "one to two pages" never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

I own the Claude Code skill at /Users/buda007/.claude/skills/geo-prompt-library. It is an LLM-driven generator I no longer have a spec for. Full authorization; it is mine. I can also exercise it live in a fresh isolated session with
  claude -p "<probe>"

Help me understand how this prompt/agent system is wired and what determines its output.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**`/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/ai-3/geo-prompt-library-orientation.md`**

Working-depth AI-system teardown. Your own skill, full authorization, no extraction technique needed — the prompt is on disk.

**How it's wired, short version:** five layers with wildly different authority. The 894-char `description` is the *entire* routing layer — the model picks the skill without opening a single bundle file. `SKILL.md` is a thin orchestrator; `references/workflow.md` holds the real mechanics and is genuinely load-bearing. `scripts/validate_library.py` is the only component with veto power, and `CATEGORY_QUOTA` in that file — not the markdown table — is what a library is actually judged against.

**What I ran:** 18 fresh `claude -p` sessions (8 router, 4 loading, 2 ablation, 4 register differential) plus 30 local gate executions. 11 inferred claims, 10 confirmed, 1 downgraded.

Three findings worth your attention now:

- **`content_hash` is theatre.** I replaced a valid library's hash with 64 zeroes; gate returned `passed: true`, exit 0. Nothing recomputes it, and `workflow.md` never says what it's computed *over* — two correct runs produce different hashes.
- **"`local` == exactly 0 when `geo_scope=global`" isn't enforced.** Only the *lower* bound relaxes. A global-scope library with 3 `local` intents passes with a warning.
- **The gate can't run under this machine's system python3** (PEP 668, no `jsonschema`) — exit 2, correctly fail-closed. But the FATAL message's recovery pointer names `RESUME.md`, which round 15 deliberately excluded from the packaged `.skill`. On a clean machine Phase 7 stalls with no shipped instruction for the venv.

The one thing I could **not** settle: whether the 4a/4b split and the 40/60 register mix actually shape output. My differential fed evidence into the writing context, which defeats 4a by construction — the arm is untestable with that design, and I've said so rather than dressing it up. §7 has the harness that would settle it.

Cheapest next move isn't more teardown: `evals/` has never been run, four of five URLs are verified, and the protocol is already written. That would convert most of §7 into measurements.

Left behind in the working dir: `probes/` (raw stream-json), `ablate/` + `abl_ctl/` + `abl_abl/` (mutation corpora), `tdvenv/`. Your skill directory is unmodified — I only added a pre-existing-untouched note: `scripts/__pycache__/orthographic_variants.cpython-314.pyc` dates from Aug 2, not my run.
```

## Deliverable written by the run — `geo-prompt-library-orientation.md` (verbatim)

# Orientation: geo-prompt-library

## 0. Provenance

- **Pin** — `/Users/buda007/.claude/skills/geo-prompt-library`, bundle SHA-256 (sorted per-file digest of all 46 files, `__pycache__` excluded) `b548164…bc22fd`; `SKILL.md` `232606e6…`, `scripts/validate_library.py` `b11769de…`. Declared version `0.2.0`. Examined 2026-08-20. Live probes run against `claude` CLI 2.1.238, fresh `-p` sessions, no shared state.
- **Depth** — working. Cue in the request: "help me understand how this is wired" — orientation, not a document someone will act on.
- **Authorization** — your own skill, full authorization stated. Nothing here needed extraction technique; the prompt is on disk and readable.
- **What was NOT examined** — I did not run a full end-to-end generation (no site fetched, no library written, no `verify_grounding.py` network run). I read `scripts/verify_grounding.py` only at the level of its contract, not line by line, and I did not read the 24 fixture JSON bodies (I ran them instead). Ablation on the LLM layer covers exactly one removed instruction file.

## 1. What this system is

It builds a *sampling instrument*, not content. Given a company URL, a locale and a target count, it produces a frozen, versioned JSON file of 30–50 buyer intents — each in a Serbian and an English variant — that some *other* tool then fires at ChatGPT/Perplexity/AI Overviews to measure whether the brand shows up. The whole design is organised around one failure it exists to prevent: if you let a model free-write "40 questions customers ask", it clusters on whatever it thinks of first, and every visibility number you later compute is measuring that bias rather than the market. So the queries are not written freely — they are allocated to cells of a `category × persona × city` matrix that is written into the output *before* any query text exists, and the finished file is then run through a hard, fail-closed Python gate that either passes or refuses. The skill deliberately never executes or scores the queries; that is a downstream step it declines by name.

## 2. System context

```
     you (operator)                          company website + competitors
        │  url, locale, vertical,                    │  HTTP (WebFetch/WebSearch,
        │  n_intents, geo_scope                      │  agent toolset)
        ▼                                            ▼
   ┌──────────────────────────────────────────────────────────────┐
   │            geo-prompt-library  (Claude Code skill)           │
   │   an LLM writing under a prompt, refereed by local Python    │
   └──────────────────────────────────────────────────────────────┘
        │                    │                        │
        │ 3 files            │ subprocess             │ direct HTTP (urllib,
        ▼ (cwd)              ▼ python3                ▼ NOT the agent toolset)
   <slug>-library-vN.json   validate_library.py    verify_grounding.py
   <slug>-validation-vN.json  (G1–G16, offline)    re-fetches every source_url
   console summary            fail-closed gate      to check quotes are real
        │
        ▼
   downstream GEO/AEO monitoring tool (e.g. Peec AI) — out of scope, never called
```

The one connection worth flagging: `verify_grounding.py` opens its own network sockets. It is not mediated by the agent's WebFetch tool, so it is outside whatever permission and rate-limit posture the session has — the skill's own `compatibility:` field says this out loud.

## 3. How it's put together

**Five layers, and they have very different amounts of authority over the output.**

**The `description` frontmatter (894/1024 chars) is the entire routing layer.** Nothing else decides whether the skill fires. In probing, the model named the right skill while explicitly stating it had not opened `SKILL.md` — the selection is made from the description alone, and the exclusion clauses ("Ne koristiti za… merenje vidljivosti… FAQ sadržaja… tehnički audit") are what make near-miss requests bounce. This field was hand-tuned against 20 eval prompts (CHANGELOG round 14) after the automated optimiser turned out to be broken; it is the most load-bearing 894 characters in the bundle.

**`SKILL.md`'s body (~3.3k of a 5k token budget) is a thin orchestrator plus the two things that must survive truncation:** the quota table with its quantisation formula, and the G1–G16 rule list. The rule list is kept in the body *on purpose* — the model needs it while writing, not after the gate explains a failure.

**`references/workflow.md` holds the actual mechanics of all 9 phases** and is declared a hard prerequisite. The stated guarantee is not goodwill: the output JSON testifies to each phase (`matrix_plan`, `competitors[]`, `validation.passed`, `coverage_status`), so a model that improvises instead of reading fails the gate rather than degrading quietly. Loading is progressive and, in probing, entirely stable — `SKILL.md` → `workflow.md` → `taxonomy.md` every time, plus `locale-hr-bs-me.md` only when the locale is `hr-HR`. `locale-sr.md`, `schema.md` and `research-basis.md` are Phase-5-and-later reads and were never touched in a planning-only run.

**`scripts/validate_library.py` is the only thing with real veto power.** 16 rules, exit 0/1/2, and it is the executable source of truth for the quotas — `CATEGORY_QUOTA` in that file, not the markdown table, is what a library is judged against. Two subtleties earned by bugs: `branded`'s upper bound is `floor(0.15×N)` shared through one function with G5 (a `ceil` here disagrees with G5 at every N where `0.15×N` isn't integral, and N=40 is the one default where the bug hides), and `local`'s *lower* bound drops to 0 when `inputs.geo_scope == "global"`.

**`scripts/orthographic_variants.py` is a deterministic fold, not a model output.** ASCII and Cyrillic variants of every Serbian query are computed here (`č`/`ć` both collapse to `c`, no round-trip attempted) and G15 checks the model didn't hand-write them.

**Everything downstream of the gate is checked by a *separate*, network-bound script.** `verify_grounding.py` is deliberately not a G-rule: the gate has to stay fast and offline because it runs inside a retry loop, and this check can legitimately be slow or fail for transient reasons. It reports four states, not two — `ok` / `insufficient` / `no_data` / `no_claims`.

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| Quota filled by matrix *cells*, written to output before any query text | Free generation clusters on the model's first ideas; that clustering *is* the prompt-set bias the tool exists to measure around | `SKILL.md` "Kategorije i kvote"; `matrix_plan` in schema; G16 reconciles plan vs reality per cell | CONFIRMED (C4) |
| Validation as a bundled Python gate, not prompt instruction | O4, stated: "instrukcija u ovom fajlu ga ne hvata pouzdano" | 24/24 fixtures reproduce `expectations.json` exactly on replay | CONFIRMED (C4) |
| Phase 4 split into 4a (write blind) / 4b (filter against evidence) | Reading the citation *before* writing made the model transcribe evidence phrasing into the customer's mouth — every bad query in the montenegrocharter v1 run carried its source quote's fingerprint | `references/workflow.md` Faza 4; CHANGELOG round 12 | Present in prompt; effect UNCONFIRMED (C9) |
| Every check must express three states, never two | Same bug hit four times independently (G16 proxy, G12 vs real quotes, `coverage_status`, G1 exit code) — "did not run" kept merging into "passed" | `research-basis.md` "Tri stanja, ne dva" | CONFIRMED (C7, C8) |
| Grounding verification kept *out* of the gate | Gate must stay offline and fast inside the retry loop; a model that wants low `inferred` can just write a plausible fake citation, and only a real fetch catches that | `workflow.md` Faza 8; `verify_grounding.py` | CONFIRMED (C4, by absence from `CHECKS`) |

## 5. Where the bodies are buried

**`content_hash` is theatre.** The schema requires it and pattern-checks its *shape* (`^sha256:[0-9a-f]{64}$`). Nothing recomputes it, nothing compares it, and no G-rule touches it. I replaced a valid library's hash with 64 zeroes and the gate returned `passed: true`, exit 0. Worse, `workflow.md` tells the model *when* to compute it (after `inputs`, before writing) but never says over *what* — no canonicalisation, no field list, no serialisation rule. Two correct runs will produce two different hashes. Downstream integrity checking based on this field does not currently work.

**"`local` goes to exactly 0 when `geo_scope=global`" is not enforced.** `SKILL.md` states it as a rule. The gate only relaxes the *lower* bound to 0 — the upper bound stays `ceil(0.15×N)`. I passed a global-scope library containing 3 `local` intents: `passed: true`, one warning, exit 0. The 60/40 budget redistribution is explicitly documented as model guidance rather than a gate rule (a deliberate call, to avoid adding another cross-reference to maintain), but the "exactly 0" part reads much harder in the prompt than it binds in the code.

**The gate cannot run under this machine's default interpreter.** System `python3` is PEP 668 externally-managed and has no `jsonschema`; invoking the gate with it gives FATAL + exit 2 — correct fail-closed behaviour, and the exit-2 design is one of the skill's better decisions. But the recovery instruction embedded in that FATAL message points at `<scratchpad>/tok-venv/bin/python (vidi RESUME.md)`, and `RESUME.md` is deliberately excluded from the packaged `.skill` (CHANGELOG round 15). In the installed copy the file is present; in a distributed copy the recovery pointer dangles, and no shipped file explains how to create the venv. Phase 7 will stall there on a clean machine.

**`RESUME.md` is stale and it is the file a new session is told to read first.** It says 23 fixtures (there are 24, `g19` was added in round 12), "7 rundi" of changes (the CHANGELOG is at 15), and it locates the skill at `/Users/buda007/Desktop/projekti/Geo/geo-prompt-library/` — not where the installed copy lives. Its architectural reasoning is still good; its counts and paths are not. MISLEADING rather than wrong.

**The rule-count naming has drifted.** `SKILL.md` and the gate say G1–G16; `evals/README.md` says "G1–G17"; fixtures run to `g19` (but `g17`/`g19` are *must-pass* regression guards, not rules, and `g18` re-tests G15). No functional problem — just three different numbering conventions for anyone counting.

**`evals/` has never been run.** Five cases are defined, four URLs are DNS+HTTP-200 verified, case 3 is still `PENDING_REAL_URL`. The only measured end-to-end evidence in the bundle is the montenegrocharter.com v1↔v2 A/B recorded in the CHANGELOG. When someone says this skill is "measured", that A/B is what they mean — one site, one vertical, one pair of runs.

**The register discipline is prompt-only and I could not show it working.** The 40/60 short-search vs conversational mix, the forbidden "encyclopedic" register, and the 4a/4b split are the highest-value quality rules in the bundle (round 12–13 earned them from real bad output) — and no code checks any of them. My differential test could not distinguish an arm with `workflow.md` from an arm without it. See C9; this is the one place where the memo's honest answer is "unresolved", not "fine".

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: ai   Depth: working
Method: ablation + differential against a frozen probe battery, plus deterministic replay
        of the bundled gate against its own fixture corpus

Inferred claims (one row each — this list IS N):
  C1  Activation is decided by the `description` frontmatter alone; no bundle file is
      read before the routing decision
      → CONFIRMED   evidence: probes t1_run1 (model named the skill while stating it had
        not opened SKILL.md), t1_run2/3, t2_oblique, t3_peec_en all selected it; n1_measure,
        n2_faq, n3_audit all correctly declined, each citing the description's exclusion
        clause. 4/4 trigger, 3/3 exclude.
  C2  Reference loading is a fixed core (SKILL.md → workflow.md → taxonomy.md) plus
      locale-conditional loading
      → CONFIRMED   evidence: probes l1_sr, l2_hr, l3_global, l4_n20, a1_ctl — 5/5 read
        exactly those three; locale-hr-bs-me.md read in l2_hr only (1/1 hr case, 0/4 non-hr);
        locale-sr.md read in 0/5, consistent with it being a Faza-5 read never reached.
  C3  references/workflow.md is load-bearing for Phase 4 mechanics, not just prose
      → CONFIRMED   evidence: ablation pair a1_ctl vs a2_abl (identical prompt, identical
        bundle except workflow.md deleted). ctl: 7 turns, $0.57, Phase 4 reported WITH the
        4a/4b substructure. abl: 11 turns, $1.05, detected the missing prerequisite and
        refused to proceed, recovered the 9 phase NAMES from SKILL.md's orchestrator but
        lost 4a/4b entirely (regex check: present in ctl, absent in abl).
  C4  The deterministic gate, not the prompt, is what actually binds output shape
      → CONFIRMED   evidence: verify_fixtures.py replay — all 24 fixtures match
        expectations.json, including p03_branded_over (a `p`-prefixed fixture that must
        FAIL, guarding the floor/ceil quantisation fix) and p01/p04 (must-pass negatives
        that prove G8 and G7b don't false-positive). verify_workflow_sync.py: OK, 9 phases
        aligned across SKILL.md and workflow.md.
  C5  `content_hash` is model-asserted and verified by nothing
      → CONFIRMED   evidence: ablation D2 — valid_library.json with content_hash replaced
        by "sha256:" + 64 zeroes → gate `passed: true`, exit 0, no rule fired. Confirmed
        statically: content_hash appears in no .py file.
  C6  "local == exactly 0 when geo_scope=global" is prompt guidance, not a gate rule
      → CONFIRMED   evidence: ablation D1 — schema_version 1.1.0 + inputs.geo_scope="global"
        + 3 `local` intents retained → `passed: true`, exit 0, single warning
        ("local kategorija prisutna a geo_scope == global"). Control D1b (national) passed
        without that warning. Only the lower bound moves; upper stays ceil(0.15×N).
  C7  The `inputs` provenance contract is version-gated and does bind at 1.1.0+
      → CONFIRMED   evidence: ablation D3 — schema_version bumped to 1.1.0 with `inputs`
        omitted → G1_schema fails, "'inputs' is a required property". The 1.0.x exemption
        holds (all 24 fixtures are 1.0.0 and pass).
  C8  The gate is unrunnable under the default system interpreter here; exit 2 is reachable
      in ordinary use, and its recovery pointer is incomplete in the packaged artifact
      → CONFIRMED   evidence: `python3 scripts/validate_library.py fixtures/valid_library.json`
        → FATAL on stderr, exit 2. Recovery string names RESUME.md, which CHANGELOG round 15
        records as excluded from the packaged .skill; grep for venv/pip guidance across all
        shipped files returns only that same dangling message.
  C9  The register discipline (40/60 mix, forbidden encyclopedic form, 4a/4b) measurably
      shapes generated query text
      → UNCONFIRMED  evidence: differential r1_ctl/r2_ctl vs r1_abl/r2_abl, 10 SR queries
        per run, 40 total. Forbidden-register hits: ctl 1 then 0; abl 1 then 0 — identical.
        Mean words: ctl 10.0 / 8.2; abl 9.6 / 9.5 — the within-arm ctl spread (1.8 words)
        exceeds the between-arm difference (0.4). Short search-form queries (≤6 words):
        4 of 40 overall, and all 4 came from one single ctl run — suggestive of an effect,
        far short of demonstrating one at n=2 per arm. Separately, this probe fed the
        evidence quotes into the writing context by construction, which defeats 4a's whole
        premise, so the 4a arm is untestable with this design and was not tested.
  C10 The declared 40% short-search register share is not being produced in practice
      → CONFIRMED as observation  evidence: 0 of 40 generated SR queries were ≤4 words;
        4 of 40 were ≤6. Scope caveat: measured on a synthetic Phase-4/5-only probe with
        evidence pre-supplied, not on a real end-to-end run — it says the mix is not being
        hit under these conditions, not that the rule never fires.
  C11 RESUME.md's counts and paths are stale relative to the shipped bundle
      → CONFIRMED   evidence: RESUME says "23 fixtures", verify_fixtures.py reports 24;
        RESUME says "7 rundi", CHANGELOG head is "petnaesta runda" (0.2.0); RESUME locates
        the skill at ~/Desktop/projekti/Geo/, the examined copy is ~/.claude/skills/.
        Verdict on the file as a whole: MISLEADING, not REFUTED — its reasoning is intact.

  N = 11   confirmed 10 / downgraded 1 / dropped 0   (10+1+0 = 11)

Coverage denominator (not freely chosen):
  battery cases run: 18 live `claude -p` sessions (8 router, 4 loading, 2 ablation,
    4 register differential), each a fresh isolated session
  variance floor: router axis — 3 runs of the identical prompt (t1_run1/2/3), 0/3
    disagreement in skill selection. Register axis — within-arm mean-word-count spread
    1.8 words on the ctl arm, which is the floor any register claim must clear; C9 does
    not clear it.
  ablated instructions: LLM layer 1 of 1 attempted (references/workflow.md);
    deterministic layer 3 of 3 attempted (content_hash, inputs.geo_scope, inputs-at-1.1.0)
  deterministic replays: 24 of 24 gate fixtures + 4 hand-built ablations + 1 exit-code
    probe + 1 phase-sync check = 30 local gate executions

System scale examined:
  15 of 46 bundle files read in full (SKILL.md, 6 references, evals/*, RESUME.md,
  CHANGELOG head ~60 of 900 lines, validate_library.py read in outline + 3 sections in
  full) · 0 of 5 defined evals executed · 0 of 9 workflow phases observed end-to-end ·
  0 real company sites fetched · 24 of 24 gate fixtures executed

Falsification NOT performed, and why:
  - No end-to-end run. Every claim about Phases 2, 3, 6, 8 and 9 rests on reading the
    prompt and the artifacts it declares, not on watching them execute. To fix: run
    eval 0 (dentio.rs) with network enabled and inspect the three delivered files.
  - No test of verify_grounding.py against a live site. Its three-state logic and the
    same-host rate-limit pacing are read, not exercised.
  - 4a/4b ordering untested — see C9; the probe design invalidated that arm.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Whether 4a/4b actually suppresses citation-echo in query text | My differential fed the evidence into the writing context, which defeats 4a by construction; the correct test needs a two-session harness where the writer literally cannot see the quotes | A paired run where arm A writes queries from `category`/`persona`/`city` only in one session and filters against evidence in a second, vs arm B doing both at once; score on verbatim n-gram overlap with source quotes |
| Whether the 40/60 register mix is reachable at all, or only when the model over-corrects | Observed 4/40 short-form across 4 runs, all from one run; n far too small, and CHANGELOG round 13 records the opposite failure (hitting the split exactly by padding queries that were already fine) | 10+ real end-to-end runs across ≥3 verticals, scoring short-form share per run against the ~40% target |
| Real-world `retry_count` distribution — how much the skill leans on the gate's 3-attempt safety net | `evals/` has never been executed; the only measured run (montenegrocharter v2) reports `retry_count: 0`, n=1 | Run the 5 defined evals and record `retry_count` + `first_attempt_failures`, exactly as `evals/README.md` already specifies |
| Whether `verify_grounding.py`'s coverage logic behaves under real network conditions | Not executed; the one live fixture (`grounding_live_dentio.json`) needs network and was not run | `python -B scripts/verify_grounding.py fixtures/grounding_live_dentio.json` with network, plus a run against a rate-limiting host |
| What `content_hash` is supposed to be computed *over* | No canonicalisation spec exists anywhere in the bundle; the field is unverified, so no run can reveal the intended rule by contradiction | A decision from you, then a `_content_hash()` function in `validate_library.py` and a G-rule that recomputes it |
| Whether project-scope vs user-scope skill precedence affects loading | Sidestepped by renaming the ablation copies rather than testing the collision | Install a same-named skill at project scope with a canary string and probe which one loads |

## 8. Where to go deeper

Trustworthy as written: `CHANGELOG.md` (the "why" behind every decision, and unusually candid about bugs it caught in its own fixes), `references/research-basis.md` (§"Eksplicitne praznine" names three real gaps in the underlying evidence rather than hiding them), and `fixtures/expectations.json`, which is the single best file in the bundle — it makes the gate's behaviour replayable in one command. Not trustworthy: `RESUME.md`'s counts and paths, and the G1–G17 rule-count in `evals/README.md`.

The cheapest next step is not a Full teardown — it is running the evals that are already written. Four of five URLs are verified and the protocol is specified; that single action would convert most of §7's unknowns into measurements, and it is the thing this bundle was built to do next and never did. If you then want the 4a/4b and register questions settled properly, that is a purpose-built differential harness, and it belongs to `soma-agent-debugger` (fixing an agent you own) rather than to this skill, which only recovers design.
