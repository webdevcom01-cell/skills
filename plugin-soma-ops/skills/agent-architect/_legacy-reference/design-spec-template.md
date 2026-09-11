# Agent DESIGN_SPEC Template

Standalone template za **Mode 4: Design Doc Generator**. Prati strukturu score-analyzer DESIGN_SPEC-a kako bi novi agenti bili konzistentni sa postojećim SOMA inventarom.

**Korišćenje:**
1. Kopiraj template ispod
2. Popuni 6 sekcija sa odgovorima iz korisničkih input-a
3. Sačuvaj u `Insights/proposed-agents/<name>-design-spec.draft.md` (sa `.draft.md` ekstenzijom da označi da je predlog)
4. Korisnik review-uje pre nego što fajl bude promovisan u `agents/<name>/DESIGN_SPEC.md`

**Anti-hallucination:** Skill NE PIŠE direktno u `agents/`. Sve drafts idu u `Insights/proposed-agents/`. Promocija je human-in-the-loop.

---

## Template (kopiraj odavde)

```markdown
# <Agent Name> — DESIGN_SPEC

**Status:** DRAFT v0.1
**Datum:** <YYYY-MM-DD>
**Autor:** <agent-architect skill | human>
**Pattern reference:** <Prompt Chaining / Routing / Parallelization / Orchestrator-Workers / Evaluator-Optimizer / Autonomous>
**Nivo:** <A: Claude Code | B: SOMA pipeline na AgentStack>

---

## 1. Purpose

<Jedna rečenica koja opisuje **šta agent radi**. Mora da prođe single-responsibility test (Audit Kriterijum 1).>

**Primer (TI):**
> Skenira AI/agent-building trendove iz web izvora i emituje strukturirani trend brief koji HW može da konvertuje u platform-specific hookove.

**Primer (HW):**
> Generiše 5 distinct platform-specific hookova (LinkedIn, X, YouTube, Instagram, TikTok) za zadati trend brief, koristeći P1-P6 pattern taxonomy.

---

## 2. Pipeline Position

| Pitanje | Odgovor |
|---|---|
| Standalone ili u chainu? | <Standalone / U SOMA chainu / Paralelni validator> |
| Upstream agenti | <ko zove ovaj agent? "None (manual trigger)" ako standalone> |
| Downstream agenti | <koga ovaj agent zove preko call_agent? "None (end of chain)" ako poslednji> |
| Implicit blackboard reads | <koje vault fajlove čita za context? (npr. instincts.md, winners-log.md)> |
| Implicit blackboard writes | <gde pišu rezultati? (npr. evo-log.md, winners-log.md)> |

**Primer (HW):**
- Standalone ili u chainu: U SOMA chainu
- Upstream: TI (Trend Intelligence)
- Downstream: CR (Content Repurposer) preko call_agent
- Implicit reads: `agents/hook-writer/instincts.md`, `agents/hook-writer/winners-log.md`
- Implicit writes: `agents/hook-writer/evo-log.md` (run summary), `agents/hook-writer/winners-log.md` (ako score ≥17/20)

---

## 3. Use Cases

Minimum 3 UC-a:
- **UC-1: Standardni happy path** — što radi 80% vremena
- **UC-2: Error/edge case** — što se dešava kad input nije validan
- **UC-3: Boundary case** — što se dešava na granici scope-a (npr. evergreen trend, low confidence)

### UC-1: <ime — npr. "Standardni trend → 5 winning hooks">

**Input:**
```json
{
  "trend": { "title": "...", "source_url": "...", "date_observed": "..." },
  "objective": "...",
  "tool_guidance": "...",
  "task_boundaries": "..."
}
```

**Expected behavior:**
1. <korak 1>
2. <korak 2>
3. <korak 3>

**Expected output:**
```json
{
  "hooks": [
    { "platform": "LinkedIn", "hook_text": "...", "pattern_id": "P1" },
    ...
  ]
}
```

**Acceptance kriterijumi:**
- ✅ 5 distinct hookova
- ✅ Pattern variation (najmanje 3 različita pattern_id-a)
- ✅ Nema banned fraza
- ✅ Sva 4 mandatory A2A polja propagated

### UC-2: <ime — npr. "Trend bez source_url-a">

**Input:** Trend sa missing/invalid source_url
**Expected behavior:** Block-and-revise gate — agent traži upstream da popravi input, NE generiše hookove na osnovu praznog konteksta
**Expected output:** Error payload sa `error_code: "MISSING_SOURCE"` i `remediation: "..."`

### UC-3: <ime — npr. "EVERGREEN trend (timeless, no statistic)">

**Input:** Trend sa `is_evergreen: true` i `confidence: "1 stars"`
**Expected behavior:** Koristi "Reminds builders that..." framing umesto stat-based hookova
**Expected output:** 5 hookova bez fabrikovanih statistika, pattern preference P5 (Community Framing) ili P6 (Pattern Interrupt)

---

## 4. Tools

Lista svih node-ova u flow-u. **Audit Kriterijum 2:** ≤3 produktivna node-a (call_agent ne broji).

| Node Type | Configuration | Why needed |
|---|---|---|
| `kb_search` | Query: `<konkretan query>`. KB ID: `<id>` | Memory-first (Audit Kriterijum 3) — agent počinje sa context-om iz prošlih run-ova |
| `web_search` | Provider: Tavily. Query template: `<template>`. Filter: `<site: ili after:>` | <why> |
| `ai_response` | Model: `<model>`. Temperature: `<X>`. Output Variable: `<name>` | <why> |
| `call_agent` | Target Agent ID: `<id>`. Output Variable: `<name>` | <Forward to next agent in chain> |

**Tool design checklist (Audit Kriterijum 6):**
- [ ] Queries su specifični (ne `"hooks"` već `"hook patterns winners-log 2026"`)
- [ ] call_agent payload ima sva 4 mandatory polja
- [ ] Parameter names su semantička
- [ ] Output Variables su jasno imenovane

---

## 5. Constraints

### ALWAYS (mora uvek)

1. **<Constraint 1>** — npr. "Sva 4 mandatory A2A polja UVEK u payload-u (objective, output_format, tool_guidance, task_boundaries)"
2. **<Constraint 2>** — npr. "kb_search se UVEK izvršava pre ai_response-a (memory-first)"
3. **<Constraint 3>** — npr. "Evo-log write UVEK na kraju run-a"

### NEVER (nikad ne sme)

1. **<Constraint 1>** — npr. "NIKAD ne fabrikovati statistike koje nisu u source URL-u"
2. **<Constraint 2>** — npr. "NIKAD ne koristiti banned verb forme (enhance/boost/transform/expand) bez merljive metrike"
3. **<Constraint 3>** — npr. "NIKAD ne modifikovati trend semantics — samo reframe-uj per platform"

### Hard rules iz Pass 1.5 (NE krši pod nijednim uslovima)

- [ ] Rule #1: Ako je validator/scorer — označi kao LLM-judge sa mode collapse rizikom
- [ ] Rule #2: Ne dodavati Score Analyzer u chain bez eksplicitne arhitekturalne odluke
- [ ] Rule #3: Nivo A ≠ Nivo B — označi nivo eksplicitno u DESIGN_SPEC header-u
- [ ] Rule #4: Quality gates per-agent self-check, NIJE cross-agent
- [ ] Rule #5: Topologija je chain + implicit blackboard
- [ ] Rule #6: Ako agent koristi instincts ili format-templates — ne mešaj ih

### Soft rules iz `soma-rules.md`

- [ ] Single responsibility
- [ ] Max 3 produktivna node-a
- [ ] A2A handoff via call_agent
- [ ] Memory-first
- [ ] Evo-log always

---

## 6. I/O Contract

### Input

```json
{
  "<key>": "<type> — <description>",
  "<key>": "<type> — <description>"
}
```

**Validation rules:**
- `<key>` must be `<format>`, otherwise reject with error `<error_code>`
- `<key>` must be `<range/enum>`, otherwise reject

### Output (success)

```json
{
  "<key>": "<type> — <description>"
}
```

**Acceptance kriterijumi za output:**
- ✅ <kriterijum 1>
- ✅ <kriterijum 2>

### Output (error)

```json
{
  "error_code": "<UPPER_CASE_ENUM>",
  "error_message": "<human readable>",
  "remediation": "<what upstream should do to fix>"
}
```

**Error codes (enumeration):**
| Code | Triggered when | Remediation |
|---|---|---|
| `<CODE>` | <when> | <what to do> |

---

## 7. Quality Gate (per-agent self-check)

**Audit Kriterijum 4:** Pre nego što agent emit-uje output, mora da prođe sledeću checklist:

```
Before emitting output, verify:
1. <provera 1>
2. <provera 2>
3. <provera 3>

If any check fails — <regenerate / block-and-revise / emit error>, do NOT emit incomplete output.
```

**Primer (HW):**
```
Before emitting hooks, verify:
1. 5 distinct hooks (1 per platform: LinkedIn, X, YouTube, Instagram, TikTok)
2. Each hook has hook_text + pattern_id (P1-P6)
3. No banned verb forms (enhance/boost/transform/expand) without measurable metric
4. All 4 mandatory A2A fields propagated in call_agent payload
5. If trend.is_evergreen=true, hooks use "Reminds builders that..." framing
If any check fails — regenerate, do NOT emit incomplete output.
```

---

## 8. Evo-log Schema

Šta agent piše u `agents/<name>/evo-log.md` posle svakog run-a:

```markdown
## Run YYYY-MM-DD HH:MM (run_id: <id>)

**Input summary:** <1 rečenica šta je dobio na ulazu>
**Output summary:** <1 rečenica šta je vratio>
**Status:** ✅ PASS / ⚠️ WARN / ❌ FAIL
**Quality gate result:** <pass/fail po kriterijumu>
**Observations:** 
- <opazanje 1>
- <opazanje 2>
**Fixes applied:** <ako je neki fix bio aktiviran tokom run-a>
**Tokens used:** <input/output>
**Cost:** $<X.XX>
```

---

## 9. Open Questions

Sve što nije odlučeno tokom design-a, eksplicitno listaj:

1. **<Otvoreno pitanje 1>** — <kontekst, zašto je otvoreno>
2. **<Otvoreno pitanje 2>** — <kontekst>

**Princip:** Bolje listati otvoreno pitanje nego improvizirati. Human-in-the-loop pravilo iz Pass 1.5.

---

## 10. Implementation Plan

Ako je agent novi (nije reverse-engineering postojećeg):

| Sprint | Task | Estimated effort | Blocker check |
|---|---|---|---|
| Sprint X.1 | Kreiraj agent na AS UI (basic config) | 30 min | KB embeddings worker mora biti aktivan |
| Sprint X.2 | Implementiraj System Prompt v1 | 1h | DESIGN_SPEC mora biti finalizovan |
| Sprint X.3 | Konfiguriši flow nodes | 30 min | Tool design provera (Audit Krit. 6) |
| Sprint X.4 | Smoke test UC-1 | 30 min | TI mora biti spreman ako je u chainu |
| Sprint X.5 | Edge case testovi UC-2, UC-3 | 1h | - |
| Sprint X.6 | First audit (Mode 2) | 30 min | - |
| Sprint X.7 | Promocija iz `Insights/proposed-agents/` u `agents/<name>/DESIGN_SPEC.md` | 5 min | Human approval |

---

## 11. Versioning

| Verzija | Datum | Šta se promenilo | Autor |
|---|---|---|---|
| v0.1 (draft) | <YYYY-MM-DD> | Initial draft | agent-architect |
| v0.2 | | | |

---

## Reference

- `reference/patterns.md` — pattern selection rationale
- `reference/soma-truth.md` — hard rules check
- `reference/audit-checklist.md` — kriterijumi za prvi audit posle build-a
- `reference/anthropic-citations.md` — za quote-checking u designu
- `system/soma-rules.md` — pravila u vault-u (read-only)
```

---

## Kako skill koristi ovaj template (Mode 4 workflow)

1. **Pitaj korisnika 6 stvari** (kao što je u SKILL.md Mode 4):
   - Naziv i kratak opis
   - Pipeline pozicija
   - Use cases (UC-1, UC-2, UC-3)
   - Tools
   - Constraints (NEVER/ALWAYS)
   - I/O contract

2. **Pre nego što generišeš, proveri:**
   - Da li dizajn poštuje 6 hard rules iz `soma-truth.md`?
   - Da li dizajn poštuje 5 core principles?
   - Ako krši nešto — eksplicitno označi i pitaj korisnika da potvrdi pre nego što nastaviš

3. **Predloži pattern** iz `patterns.md` koji se najbolje slaže (sa citatom).

4. **Generiši fajl** u `Insights/proposed-agents/<name>-design-spec.draft.md`:
   - Kopiraj template iznad
   - Popuni placeholders sa korisničkim odgovorima
   - Dodaj pattern preporuku iz koraka 3
   - Listaj open questions ako ima nešto nejasno

5. **Predoči korisniku:**
   - Pokaži putanju draft fajla
   - Listaj koje hard rules su provarene (i da li krši ijednu)
   - Pitaj da li želi review pre promocije

---

## Anti-hallucination disciplina

1. **Nikad ne popunjavaj sekcije bez input-a** — ako korisnik nije odgovorio na nešto, ostavi placeholder ili dodaj u "Open Questions"
2. **Ne pretpostavljaj pattern** — uvek pitaj koji pattern (iz `patterns.md`) korisnik preferira, ili predloži sa opravdanjem
3. **Ne fabrikuj cost estimates** — listaj tokens × model price formulu, ali brojke samo ako ima realnih merenja
4. **Ne piši u `agents/`** — sve drafts idu u `Insights/proposed-agents/<name>-design-spec.draft.md`
