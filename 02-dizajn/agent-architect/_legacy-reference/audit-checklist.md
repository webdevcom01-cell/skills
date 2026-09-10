# Agent Audit Checklist

Standalone checklist za **Mode 2: Agent Audit**. 8 kriterijuma sa weights, severity skalom, i konkretnim primerima šta je dobro / loše.

**Izvor:** Sintetisano iz `patterns.md` (sekcija 7) + `soma-truth.md` (6 hard rules + 5 core principles) + Anthropic engineering postova.

**Korišćenje:** Kad audituješ SOMA agenta (TI, HW, CR, SA, ili budući), prolaziš kroz svih 8 kriterijuma. Za svaki: zabeleži score (✅ PASS / ⚠️ WARN / ❌ FAIL), citat dokaza iz fajlova agenta, i remediation preporuku.

---

## Weights & Severity Skala

| Severity | Šta to znači | Kad se koristi |
|---|---|---|
| 🔴 BLOCKER | Krši hard rule. Agent ne sme u produkciju dok se ne fix-uje. | Kriterijumi 1, 3, 5 (single resp, memory-first, evo-log) |
| 🟠 MAJOR | Krši soft rule ili core princip. Treba fix u sledećem sprintu. | Kriterijumi 2, 4, 6 (≤3 nodes, quality gate, tool design) |
| 🟡 MINOR | Optimizacijski. Ne blokira, ali snižava skor. | Kriterijumi 7, 8 (cost, model-update) |

**Skor sistem:**

| Skor | Status | Akcija |
|---|---|---|
| 0/8 | 💥 Fundamentalni redizajn | Krši core principles — agent verovatno ne treba postojati u trenutnom obliku |
| 1-3/8 | 🚨 Ozbiljni propusti | Prioritetni fix sprint pre bilo kakvog daljeg rada |
| 4-6/8 | ⚠️ Funkcionalno, ali ima propusta | Plan remediation u 2-3 sprinta |
| 7-8/8 | ✅ Zdrav | Samo manja optimizacija; routine review za 30 dana |

---

## Kriterijum 1 — Single Responsibility 🔴 BLOCKER

**Pitanje:** Da li agent radi tačno **jednu** stvar?

**Izvor:** `soma-rules.md` rule #1 + Building Effective Agents (Dec 19 2024)

**Citat iz BEA:**
> "we recommend finding the simplest solution possible, and only increasing complexity when needed."

**Kako da provariš:**
1. Pročitaj `agents/<name>/DESIGN_SPEC.md` (Purpose sekcija)
2. Pročitaj System Prompt agenta (na AS UI)
3. Postavi pitanje: "Da li mogu da opišem šta agent radi u **jednoj rečenici** bez "i" / "takođe" / "uz to"?"

**✅ Dobro:**
- TI: "Skenira AI/agent-building trendove i emituje strukturirani trend brief za HW."
- HW: "Generiše 5 platform-specific hookova za zadati trend brief."

**❌ Loše:**
- "Skenira trendove, generiše hookove, i piše rezultate u Obsidian." → 3 responsibilities
- "Validira input, scoruje output, i predlaže improvements." → 3 responsibilities (treba 3 agenta ili 1 sa jasnijim scope-om)

**Remediation:** Ako agent radi više stvari, predloži split na 2+ agenata. Označi kao **arhitekturalnu promenu**, ne automatsku.

---

## Kriterijum 2 — Max 3 Produktivna Node-a 🟠 MAJOR

**Pitanje:** Ima li flow ≤3 produktivna node-a (call_agent ne broji)?

**Izvor:** `soma-rules.md` rule #2 (Buky-jeva interpretacija)

**Kako da provariš:**
1. Otvori flow na AS UI (ili `as_inspect_flow` MCP)
2. Prebroji nodes po tipu
3. **Ne broji:** `call_agent`, `output`, decorative nodes (komentari)
4. **Broji:** `kb_search`, `web_search`, `ai_response`, `processor`, `extractor`, bilo koji LLM call

**✅ Dobro:**
- TI flow: kb_search → web_search → ai_response → call_agent = 3 produktivna ✅
- HW flow: kb_search → ai_response → call_agent = 2 produktivna ✅

**❌ Loše:**
- TI flow: kb_search → web_search → extractor → ai_response → validator → ai_response → call_agent = 5 produktivnih → krši
- HW sa "Score Analyzer dodato u chain" = 4 produktivna → krši + krši HARD RULE #2

**Remediation:** Spoji više node-ova u jedan ako rade isti tip operacije. Ako stvarno treba >3, opravdaj eksplicitno u DESIGN_SPEC i bumpni soft rule.

**Edge case:** Ako je agent NIVO A (Claude Code, ne SOMA pipeline), ovo pravilo se ne primenjuje — Claude Code agenti rade sa ToolLoop i nemaju node graph.

---

## Kriterijum 3 — Memory-First 🔴 BLOCKER

**Pitanje:** Da li flow počinje sa `kb_search` node-om?

**Izvor:** `soma-rules.md` rule #4 (Memory-first principle)

**Kako da provariš:**
1. Otvori flow na AS UI
2. Identifikuj prvi node posle `input` (ili posle trigger node-a)
3. Mora biti `kb_search` koji pulled relevant context iz KB-a

**✅ Dobro:**
- HW flow: `input` → `kb_search` (winners-log + instincts) → `ai_response` → `call_agent`
- TI flow: `input` → `kb_search` (instincts + evo-log) → `web_search` → `ai_response`

**❌ Loše:**
- HW flow bez `kb_search`: `input` → `ai_response` → `call_agent` → krši memory-first
- HW flow sa kb_search ali ne PRVO: `input` → `web_search` → `kb_search` → `ai_response` → krši ordering

**Remediation:** Ubaci `kb_search` kao prvi node posle input-a. Wire-uj na pravu KB (instincts + winners-log).

**Edge case:** Score Analyzer može da preskoči ovo ako je standalone validator (ne piše ništa, samo skoruje). Označi kao opravdano u DESIGN_SPEC.

---

## Kriterijum 4 — Quality Gate Per-Agent 🟠 MAJOR

**Pitanje:** Postoji li self-check pre output-a?

**Izvor:** `soma-rules.md` quality_gate pattern + HARD RULE #4 ("Quality gates su per-agent self-check, NIJE cross-agent")

**Kako da provariš:**
1. Pročitaj System Prompt agenta
2. Traži explicit checklist pre nego što agent emit-uje output
3. Primeri provera: "Da li sva 4 mandatory polja prisutna?", "Da li ima banned phrases?", "Da li score ≥ threshold?"

**✅ Dobro (iz HW System Prompt v1):**
```
Before emitting hooks, verify:
1. 5 distinct hooks, one per platform
2. Each hook has hook_text + pattern_id
3. No banned verb forms (enhance/boost/transform/expand without metric)
4. All 4 mandatory fields in payload (objective, output_format, tool_guidance, task_boundaries)
If any check fails — regenerate, do not emit.
```

**❌ Loše:**
- System Prompt nema bilo kakvu pre-emit verifikaciju → agent emit-uje i polovičan output
- Quality gate je delegiran na **drugi agent** (npr. CR validira HW output) → krši HARD RULE #4

**Remediation:** Dodaj "Before emitting, verify..." sekciju u System Prompt sa checklist-om koji odgovara agent purpose-u.

---

## Kriterijum 5 — Evo-log Write 🔴 BLOCKER

**Pitanje:** Da li agent piše evo-log entry posle run-a?

**Izvor:** `soma-rules.md` rule #5 (Evo-log always)

**Kako da provariš:**
1. Otvori `agents/<name>/evo-log.md` u vault-u
2. Proveri da li ima entries iz poslednjih run-ova (datum + run summary)
3. Proveri da li je entry pisanje **automatizovano** (kroz skill `evo-log-writer`) ili **manuelno** (Buky upisuje)

**✅ Dobro:**
- TI evo-log ima entries za svaki test #1, #2, #3, #4, #5, #6 sa datumom, scope, status, observations
- Pisanje automatizovano kroz `evo-log-writer` skill

**❌ Loše:**
- `evo-log.md` ne postoji ili je prazan → krši rule #5
- Postoji ali nema entries posle poslednjih 5 run-ova → bypass-ovano
- Entries postoje ali bez strukture (samo "ran agent, worked") → niska kvaliteta

**Remediation:** 
1. Ako evo-log fajl ne postoji — kreiraj template (datum, run_id, input, output, observations, fixes_applied)
2. Ako postoji ali nije punjen — verifikuj da `evo-log-writer` skill trigger-uje posle svakog run-a
3. Ako entries niskog kvaliteta — update skill template-a

**Exception note (added 2026-05-29):**
Agent može da pass-uje ovaj kriterijum ako evo-log piše Level A orchestrator (npr. soma-run skill) i agent ima DOKUMENTOVAN constraint u DESIGN_SPEC da je trigger SAMO kroz tog orchestrator-a. Direktan A2A trigger BEZ dokumentovanog constraint-a JE failure.

---

## Kriterijum 6 — Tool Design 🟠 MAJOR

**Pitanje:** Da li tools imaju jasan opis? Da li parametri imaju dobre nazive?

**Izvor:** Building Effective Agents Appendix 2 + Multi-agent research (Jun 13 2025)

**Citat iz BEA:**
> "While building our agent for SWE-bench, we actually spent more time optimizing our tools than the overall prompt."

**Citat iz Multi-agent research:**
> Svaki subagent mora dobiti "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."

**Kako da provariš:**
1. Pročitaj tool definicije u flow node-ovima (kb_search query, web_search query, ai_response prompt)
2. Za call_agent: proveri payload — ima li sva 4 polja (objective, output_format, tool_guidance, task_boundaries)
3. Proveri da li parametri imaju semantičke nazive (ne `param1`, `data`, `input`)

**✅ Dobro:**
- `kb_search query`: `"hook patterns winners-log 2026"` — specifičan
- HW call_agent payload: `{ objective: "...", output_format: "...", tool_guidance: "...", task_boundaries: "..." }` — kompletan
- Parameter names: `trend_url`, `confidence_score`, `is_evergreen` — semantička

**❌ Loše:**
- `kb_search query`: `"hooks"` — preširoko
- call_agent payload: `{ data: {...} }` — nema 4 polja
- Parameter names: `arg1`, `payload2`, `temp_str` — nesemantička

**Remediation:** 
1. Re-write tool descriptions sa konkretnim "what + why + when"
2. Dodaj sva 4 A2A mandatory polja u call_agent payload-e
3. Rename parametre po semantici task-a

---

## Kriterijum 7 — Cost-Conscious 🟡 MINOR

**Pitanje:** Da li je arhitektura opravdana cost-wise?

**Izvor:** Multi-agent research (Jun 13 2025) numeric data

**Citat:**
> "agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about **15× more tokens** than chats"

**Kako da provariš:**
1. Procena: koliko LLM poziva po run-u? (npr. TI = 1 ai_response, HW = 1 ai_response, CR = 1 ai_response → 3 calls)
2. Procena: koliko tokens po pozivu? (input + output)
3. Multiply: calls × avg tokens × model price
4. Uporedi sa **vrednošću** task-a (revenue per hook published? per content piece?)

**✅ Dobro (HW analiza):**
- HW radi 1 ai_response sa gpt-4.1-mini (~$0.0002 per run)
- Output 5 hooks (1 per platform) → ~$0.00004 per hook
- Ako jedan winner hook generiše >$0.04 vrednosti — agent cost-justified

**❌ Loše:**
- Multi-agent orchestrator-worker za task koji može single LLM call → 15x trošak za marginalnu vrednost
- Model upgrade (gpt-4.1-mini → gpt-4-turbo) bez merljivog quality boost-a → nepravdano

**Remediation:** Ako cost > value, ili predloži downgrade modela, ili spoji više agenata, ili eliminisanje agent-a.

---

## Kriterijum 8 — Model-Update Tested 🟡 MINOR

**Pitanje:** Kad je poslednji audit izveden posle promene modela?

**Izvor:** Managed Agents (Apr 8 2026) meta-princip

**Citat:**
> "harnesses encode assumptions about what Claude can't do on its own. However, those assumptions need to be frequently questioned because they can go stale as models improve."

**Kako da provariš:**
1. Otvori `system/model-change-log.md` u vault-u
2. Pronađi datum poslednje promene modela za ovaj agent
3. Pronađi datum poslednjeg audit-a posle te promene
4. Ako razmak >90 dana → MINOR flag

**✅ Dobro:**
- Model promenjen: 2026-04-15 (gpt-4.1-mini → claude-haiku-4-5)
- Audit izveden: 2026-04-22 (7 dana posle) ✅

**❌ Loše:**
- Model promenjen: 2026-01-10
- Poslednji audit: 2026-01-12, više nije diran → 4+ meseca staro

**Remediation:** Schedule routine audit nakon svake model promene. Posebno proveri da li novi model menja:
- Da li su quality gates još potrebne (možda novi model ne pravi greške koje stari pravi)
- Da li su instincts još relevantne (možda novi model već "zna" stvari iz instincts.md)
- Da li flow nodes mogu da se spoje (možda novi model može single-shot ono što je staro tražilo 2 node-a)

---

## Audit Report Format

Kad završiš sve 8 provera, napiši report u `Insights/audits/<agent-name>-<YYYY-MM-DD>.md`:

```markdown
# <Agent Name> Audit — <YYYY-MM-DD>

## Skor
X/8 — <Status: 💥 / 🚨 / ⚠️ / ✅>

## Summary
<2-3 rečenice o glavnim nalazima>

## Finding 1: <ime> [Severity: 🔴/🟠/🟡]
- **Šta:** <opis problema>
- **Dokaz:** <citat iz koda/configa/promptu agenta>
- **Anthropic referenca:** <citat + URL ako primenjivo>
- **Pass 1.5 napomena:** <ako primenjivo>
- **Remediation:** <konkretan korak; označi krši/ne krši SOMA rule>

## Finding 2: ...
...

## Cross-cutting observations
<Pattern-i koji se javljaju kroz više finding-a>

## Recommended sprint plan
- Sprint 1 (BLOCKERs): ...
- Sprint 2 (MAJORs): ...
- Sprint 3 (MINORs): ...

## Re-audit schedule
Next audit: <datum, npr. 30/60/90 dana>
Trigger conditions: <šta dovodi do ranog re-audit-a>
```

---

## Anti-hallucination disciplina za audit

1. **Svako "Loše" mora imati dokaz** — citat iz koda, configa, ili prompt-a. Ne "mislim da". Ne "verovatno".
2. **Svaki "Citat" mora biti doslovan** — iz reference fajlova ili Anthropic članaka direktno fetched.
3. **Severity assignment** — koristi tabelu iz vrha ovog fajla, ne improvizuj.
4. **Ako nemaš dokaz za nešto** — eksplicitno reci "Nisam mogao da verifikujem X jer Y" umesto da pretpostaviš.
5. **Ne menjaj sam agent** — audit piše samo u `Insights/audits/`. Promene u `agents/` su Buky-jeva odluka.

---

## Reference

- `reference/patterns.md` — 6 patterna + bibliografija
- `reference/soma-truth.md` — 6 hard rules + 5 core principles
- `reference/anthropic-citations.md` — konsolidovani citati za quote-checking
- `system/soma-rules.md` — pravila u vault-u (read-only za skill)
