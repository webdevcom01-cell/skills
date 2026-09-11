# SOMA Truth Reference

Autoritativan snapshot stvarne SOMA arhitekture, sintetisan iz:
- `system/soma-rules.md` (verbatim citirano)
- `system/config.md` (verbatim citirano)
- `Insights/code-as-agent-harness/05-soma-real-state.md` (Pass 1.5 audit)
- `Insights/code-as-agent-harness/06-pass1-corrections.md` (Pass 1.5 corrections)
- Direktni vault read od strane `agent-architect` skill-a, 2026-05-25

**Princip:** Ovaj fajl je ground truth. Skill ne sme da koristi pretpostavke o SOMA arhitekturi koje nisu ovde.

---

## 0. Šest hard rules (autoritativna lista)

Ovo su pravila koja skill MORA da poštuje. Detalji za svako su razbacani po sekcijama dole; ovo je kanonska lista.

1. **Score Analyzer NIJE deterministic sensor** — LLM-as-judge sa mode collapse rizikom (vidi §12)
2. **Score Analyzer NIJE u TI→HW→CR chainu** — standalone, user-triggered (vidi §9)
3. **Nivo A (Claude Code) ≠ Nivo B (SOMA pipeline)** — uvek pitaj/označi nivo (vidi §15)
4. **Quality gates su per-agent self-check** — NISU cross-agent (vidi §4)
5. **Topologija je chain + implicit blackboard** — NIJE pure linear pipeline (vidi §10)
6. **Instincts ≠ format-templates** — instincts su *rules*, templates su *structures* (vidi §6)

---

## 1. Šta je SOMA

**Pun naziv:** Self-Organizing Microagent Architecture

**Svrha (iz `05-soma-real-state.md`):**
> "marketing agent trio koji generiše multi-platform social content iz trend signala"

**Niche (iz `system/config.md`):**
> "Primary niche: AI development, agent building, LLM tooling"

**Platforme (iz `system/config.md`):**
> "Active platforms: LinkedIn, X (Twitter), YouTube, Instagram, TikTok"

---

## 2. Core principles (verbatim iz `system/soma-rules.md`)

```markdown
1. Single responsibility — each agent does exactly one thing. No agent researches AND writes.
2. Max 3 nodes — if a flow needs a 4th node, split into two agents.
3. A2A handoff — agents chain via call_agent. Output of one is input of next.
4. Memory-first — every agent reads instincts before generating. No cold starts.
5. Evo-log always — every agent writes a log entry after every run, no exceptions.
```

**Buky-jeva interpretacija pravila #2 (potvrđeno 2026-05-25):**
> "`call_agent` se ne broji kao 'node'" — pravilo "Max 3 nodes" se primenjuje na **produktivne node-ove** (kb_search, web_search, ai_response, itd.). `call_agent` je transport.

**Posledica:** TI ima 4 node-a u config-u (`kb_search → web_search → ai_response → call_agent(HW)`), ali samo 3 produktivna — što JE u skladu sa pravilom #2.

---

## 3. Error handling (verbatim iz `system/soma-rules.md`)

```markdown
- Input validation runs first in every agent — halt before wasting LLM calls
- Vague inputs → error code + halt (VAGUE_INPUT, MISSING_TREND, MISSING_HOOK)
- Low confidence → flag, generate anyway, let human decide
- Missing KB data → proceed without, note [no instincts yet] — never block
```

---

## 4. Quality gates (verbatim iz `system/soma-rules.md`)

```markdown
Every agent has a self-check (<quality_gate>) that runs before sending output.
If a check fails, the agent revises before sending — not after.
```

**HARD RULE #4 (Pass 1.5):** Quality gates su **per-agent self-check**, NISU cross-agent. TI ne validira HW output.

---

## 5. Human-in-the-loop (verbatim iz `system/soma-rules.md`)

```markdown
Content Repurposer output goes to human review queue.
Human decides what to publish, when, and in what order.
Agents do not post autonomously.
```

**Posledica za skill:** Predlog koji uvodi autonomy bez human review = soft rule violation, mora biti eksplicitno označen.

---

## 6. Evolution pattern (verbatim iz `system/soma-rules.md`)

```
instinct file:     situation → mistake → fix
winners-log:       date | hook | score | platform
format-templates:  platform → structure → notes
evo-log:           date | input | output_summary | quality_flags
```

**HARD RULE #6 (Pass 1.5):** instincts ≠ format-templates. Instincts su *rules*, templates su *structures*. Skill ih ne sme izjednačavati.

---

## 7. Agent registry

**3 pipeline agenta (verbatim iz `system/config.md`):**

| Agent | ID | Model | Nodes |
|---|---|---|---|
| Trend Intelligence | c1777723587797ch65fqcudn | gpt-4.1-mini | kb_search → web_search → ai_response → call_agent(HW) |
| Hook Writer | c17777235878091qa78qw27c | gpt-4.1-mini | kb_search → ai_response → call_agent(CR) |
| Content Repurposer | c1777723587821zymz38ug0j | gpt-4.1-mini | kb_search → ai_response |

**Score Analyzer (NIJE u `system/config.md`; izvori: `agents/score-analyzer/DESIGN_SPEC.md` direktno pročitan 2026-05-25 + Pass 1.5 audit):**
- Processor: gpt-4.1-mini (temp 0.1) — iz DESIGN_SPEC Tools sekcije
- Extractor: claude-haiku-4-5 — iz DESIGN_SPEC Tools sekcije
- Tools: ai_response, web_search (Tavily) — iz DESIGN_SPEC Tools sekcije
- **Pipeline pozicija: standalone, user-triggered, NIJE u TI→HW→CR chainu** — iz DESIGN_SPEC "Pipeline Position" sekcije

⚠️ Skill koji koristi ovaj fajl: ako u budućnosti `system/config.md` doda Score Analyzer, ovaj odeljak treba ažurirati.

---

## 8. KnowledgeBase registry (verbatim iz `system/config.md`)

| Agent | KB ID | Sources |
|---|---|---|
| Trend Intelligence | c1777724361613zkacaonj60 | instincts, evo-log |
| Hook Writer | c17777243623082bxh7e2crn | instincts, winners-log |
| Content Repurposer | c1777724362990ottwffcep9 | instincts, format-templates |

---

## 9. A2A chain (verbatim iz `system/config.md`)

```
Trend Intelligence
  └─ call_agent → Hook Writer
       └─ call_agent → Content Repurposer
                          └─ [output → human review queue]
```

**Score Analyzer (paralelno, NIJE u chainu):**
```
USER → Score Analyzer → user (no A2A)
```

**HARD RULE #2 (Pass 1.5):** Dodavanje SA u chain je **arhitekturalna promena**, ne "minor tweak". Otvoreno pitanje koje skill mora postaviti pre predlaganja: paralelni validator ili 4. node u chainu?

---

## 10. Stvarna topologija (revidirano Pass 1.5)

**Pass 1.5 citat:**
> "Prava SOMA topologija: **chain (forward) + implicit blackboard feedback (backward through vault)**"

**HARD RULE #5:** Ne reći "SOMA je linear pipeline" — to je netačno.

**Feedback loops kroz vault:**

| Loop | Mehanizam |
|---|---|
| HW reads winners-log | HW writes hooks ≥17 → čita ih u sledećem runu kao KB |
| TI reads sopstveni evo-log | Self-history loop |
| Human updates instincts.md | Out-of-band feedback koji ulazi na sledećem agent run-u |
| Human review queue | Posle CR-a, human prima rezultat, eventualno updateuje instincts |

**Pattern naziv (iz paper-a koji je Buky analizirao):** "implicit blackboard" (§4.2.2)

---

## 11. Trigger flow (verbatim iz `system/config.md`)

```
Manual trigger: Send `scan trends now` to Trend Intelligence
Auto trigger: Not configured (set up cron when ready)
```

**Potvrđeno 2026-05-25:** Buky je potvrdio da je auto trigger i dalje nekonfigurisаn.

---

## 12. Model config (verbatim iz `system/config.md`)

```
Provider: OpenAI
Default model: gpt-4.1-mini
Web search: Tavily API
```

**Implikacija za HARD RULE #1:** Score Analyzer (processor) takođe koristi gpt-4.1-mini, što je **isti model kao HW koji generiše hooks**. Pass 1.5 audit eksplicitno navodi mode collapse rizik.

**Skill preporuka:** Kad neko predloži SA kao gate, predloži **drugačiji model** (npr. claude-haiku-4-5 ili claude-sonnet-4-5) za processor da bi se smanjio mode collapse rizik.

---

## 13. Šta SOMA nema (gap analiza iz Pass 1.5)

| Nedostatak | Paper § | Šta to znači |
|---|---|---|
| Deterministic sensors (lint, type check, unit tests) | §3.4.4 | Verification je LLM-based; mode collapse risk |
| Sandbox za execution | §3.4.3 | Agenti se ne izvršavaju u izolaciji — direktno pišu u vault |
| Permission tiers | §3.4.3 | Sve write operations su full-access |
| Transactional shared state | §5.2.4 | Vault writes nemaju locking; concurrent runs mogu da konfliktuju |
| Regression testing nakon harness mutations | §5.2.3 | Human menja instincts bez automated test-a "da li je novo bolje?" |
| Telemetry van evo-log-a | §3.5.1 | Nema cost tracking, latency tracking, alternativa koje agent nije izabrao |
| Evolution Agent (formalni) | §3.5.2 | Human je trenutno Evolution Agent — manual update instincts.md |
| SA u pipeline-u kao gate | §3.4.4 | SA postoji ali nije wired kao verification stage |
| DESIGN_SPEC za TI/HW/CR | n/a | Samo SA ima DESIGN_SPEC; Buky je potvrdio "možda smo zaboravili da ažuriramo" |
| Cron auto-trigger | n/a | Manualni run-ovi samo |

**Pass 1.5 citat:** "Ovo NIJE kritika — ovo je *map of opportunities* za Pass 2."

---

## 14. Agent-initiated code artifacts (paper §1, §2.2.3)

SOMA već ima 4 primera "agent-initiated code artifacts":

| Artefakt | Ko ga inicira | Ko ga čita |
|---|---|---|
| `winners-log.md` entries | Hook Writer (auto, score ≥ 17) | Hook Writer (sledeći run, kao KB) |
| `evo-log.md` entries | Svi agenti (auto, posle svakog run-a) | Trend Intelligence (sopstvena historija), human review |
| `format-templates.md` | Human (manual posle dobrog rezultata) | Content Repurposer (KB) |
| `instincts.md` | Human (manual update) — i potencijalno agent-suggested | Svi agenti (kb_search Node 1) |

**Format-templates je naročito zanimljiv** (Pass 1.5 citat):
> "reusable code/structure pattern koji *raste vremenom* i koji *agent koristi kao DSL za content generaciju*. Direktan primer 'agent-initiated reusable skill' iz §2.2.3 (Lifelong Code-Based Agents)."

---

## 15. Dva nivoa agent sistema (HARD RULE #3)

**Pass 1.5 citat:**
> "Pass 1 je mešao dva nivoa. Ovo je razdvajanje:"

### Nivo A — Claude (ja) + Claude Code skills + vault

Sistem koji pomaže **Buky-ju da gradi i održava SOMA**. Skills kao `evo-log-writer`, `instincts-updater`, `soma-performance-review`, `kb-sync`, `agent-architect` (OVAJ SKILL) rade u ovom nivou.

- **Agent:** Claude conversational + Claude Code
- **Tools:** MCP (obsidian, agent-studio-db), bash, file ops
- **Skills:** ~20 user skills u Claude Code skills lokaciji
- **Sandbox:** Claude Code execution environment
- **Trigger:** Buky chat

### Nivo B — SOMA pipeline (AgentStack)

Sistem koji **generiše content**. TI, HW, CR, SA su agenti na ovom nivou.

- **Agents:** 4 (TI, HW, CR, SA)
- **Tools:** kb_search, web_search, ai_response, call_agent (AgentStack node types)
- **Skills:** ❌ NEMA — agenti rade samo sa flow nodes
- **Sandbox:** AgentStack runtime
- **Trigger:** API call ili manualno

**HARD RULE #3:** Skill mora pitati ili eksplicitno označiti **koji nivo** pre nego što da savet.

---

## 16. Soma-rules svesni trade-offovi (iz Pass 1.5)

| Pravilo | Trade-off |
|---|---|
| "Max 3 nodes per flow" | Simplicity > capability; sprečava bloated single agents |
| "Memory-first" | Konsistentnost > fresh thinking; agenti uvek čitaju instincts |
| "Vague inputs → halt" | Fail-fast > best-effort |
| "Human review queue" | Safety > autonomy; SOMA ne postuje samostalno |

**Soft rule:** Predlog koji krši core principle MORA biti eksplicitno označen i opravdan ("krši rule X jer Y").

---

## 17. Evo-log format (verbatim iz `agents/hook-writer/evo-log.md`)

**Header:**
```
date | trend | platforms | scores | winner_platform | winner_score | flags
```

**Primer (citat, 2026-05-15):**
> "2026-05-15 | OpenAI's Agents SDK update | all-5 (platform-specific) | LI:19 X:18 YT:17 IG:17 TT:18 | LinkedIn | 19/20 | ✅ FIRST CLEAN RUN — Opcija B active. Five distinct hooks, five different patterns (P1/P2/P3/P6/P4). All scores ≥17. kb_search reading instincts. No structural flags."

**Polja:**
- `date`: YYYY-MM-DD
- `trend`: kratak opis trend signala
- `platforms`: "all-5 (platform-specific)" ili "all-5 (single hook)" ili konkretna lista
- `scores`: "LI:N X:N YT:N IG:N TT:N" — per-platform score iz Score Analyzer-a ili UNSCORED
- `winner_platform`: koja je dala najviše
- `winner_score`: N/20
- `flags`: ✅ CLEAN RUN / QUALITY_VIOLATION / STRUCTURAL BUG / TRANSITIONAL RUN / none

---

## 18. Šta sledi (kad skill bude pisao audit-e)

Skill smije da piše `Insights/audits/<agent-name>-YYYY-MM-DD.md` po sledećem template-u:

```markdown
---
audit_date: YYYY-MM-DD
agent: <name>
auditor: agent-architect (Claude)
sources_read: [list of vault files used]
---

# <Agent> Audit — YYYY-MM-DD

## Sažetak
- Score: N/8 (po audit checklist-u u patterns.md sekcija 7)
- Status: [healthy | minor improvements | serious issues | needs redesign]

## Findings

### Finding 1: <ime>
- **Šta:** ...
- **Severity:** [critical | major | minor]
- **Anthropic referenca:** ... (sa direktnim citatom)
- **Pass 1.5 napomena:** ... (ako primenjivo)
- **Preporuka:** ...
- **Soma rule impact:** [poštuje | krši rule X — opravdanje Y]

## Reading list (šta sam čitao)
- [file_path] - [zašto]
- ...

## Open questions for Buky
- ...
```

**Skill NIKAD ne piše u `agents/`, `system/`, `shared/`, `skills/`.**
