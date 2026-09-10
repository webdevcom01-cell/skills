# Anthropic Citations — Consolidated Quote Bank

**Verzija:** v0.2 (prvi consolidated drop)
**Datum:** 2026-05-27
**Princip:** Svaki citat je **doslovan** iz Anthropic engineering bloga, verifikovan kroz Chrome MCP fetch (poslednja verifikacija u patterns.md: 2026-05-25).

## Šta ovaj fajl radi

Single-source-of-truth za quote checking. Kad agent-architect skill koristi citat u **Mode 3 (Reference Library)** ili kao deo audit reporta/DESIGN_SPEC-a, **MORA** ga proveriti protiv ove liste. Ako citat nije ovde — ne sme se koristiti dok se ne fetch-uje fresh i doda u listu.

**Anti-hallucination disciplina:**
1. Nikad ne parafraziraj citat — uvek doslovno, u navodnicima
2. Uvek priloži source URL i datum publikacije
3. Ako citat nije u ovom fajlu — koristi `mcp__Claude_in_Chrome__navigate` + `get_page_text` da ga verifikuješ fresh, pa dodaj u listu
4. Ako Anthropic update-uje članak i citat se promeni — bumpni "Last verified" datum

---

## Bibliografija (8 izvora)

| # | Naslov | Autor(i) | Datum | URL | Last verified |
|---|---|---|---|---|---|
| 1 | Scaling Managed Agents | Lance Martin, Gabe Cemaj, Michael Cohen | Apr 8, 2026 | https://www.anthropic.com/engineering/managed-agents | 2026-05-25 |
| 2 | Harness design for long-running app dev | Prithvi Rajasekaran | Mar 24, 2026 | https://www.anthropic.com/engineering/harness-design-long-running-apps | 2026-05-25 |
| 3 | Effective harnesses for long-running agents | Justin Young | Nov 26, 2025 | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | 2026-05-25 |
| 4 | How we built our multi-agent research system | Hadfield, Zhang, Lien, Scholz, Fox, Ford | Jun 13, 2025 | https://www.anthropic.com/engineering/multi-agent-research-system | 2026-05-25 |
| 5 | Building effective agents | Erik S., Barry Zhang | Dec 19, 2024 | https://www.anthropic.com/engineering/building-effective-agents | 2026-05-25 |
| 6 | Equipping agents with Agent Skills | Barry Zhang, Keith Lazuka, Mahesh Murag | Oct 16, 2025 | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | 2026-05-25 |
| 7 | Claude Code auto mode | John Hughes | Mar 25, 2026 | https://www.anthropic.com/engineering/claude-code-auto-mode | 2026-05-25 |
| 8 | Beyond permission prompts (sandboxing) | David Dworken, Oliver Weller-Davies | Oct 20, 2025 | https://www.anthropic.com/engineering/claude-code-sandboxing | 2026-05-25 |

---

## Citation Index — po kategoriji

| Kategorija | # citata | Najvažniji izvor |
|---|---|---|
| Decision tree / simplicity | 1 | BEA (#5) |
| Prompt Chaining | 3 | BEA (#5) |
| Routing | 2 | BEA (#5) |
| Parallelization (Sectioning + Voting) | 3 | BEA (#5) |
| Orchestrator-Workers | 4 | BEA (#5) + Multi-agent (#4) |
| Evaluator-Optimizer | 3 | BEA (#5) + Harness (#2) + Auto Mode (#7) |
| Autonomous Agent | 4 | BEA (#5) |
| Long-running (Initializer + Coding) | 3 | Effective harnesses (#3) |
| Long-running (Planner+Generator+Evaluator) | 3 | Harness design (#2) |
| Managed Agents / decoupled | 4 | Managed Agents (#1) |
| Multi-agent principi | 8 | Multi-agent (#4) |
| Skills system | 3 | Equipping Skills (#6) |
| Security / Auto Mode classifier | 1 | Auto Mode (#7) |
| Sandboxing | 1 | Sandboxing (#8) |
| **Numerički podaci** | **9** | Multi-agent (#4), Harness (#2), Managed (#1) |

---

## Sekcija 1 — Decision tree / Simplicity

### C1.1 — Simplicity princip
**Citat:** "we recommend finding the simplest solution possible, and only increasing complexity when needed. This might mean not building agentic systems at all."
**Izvor:** Building Effective Agents (#5), Dec 19 2024
**Korišćeno u:** `patterns.md` sekcija 1 (decision tree header)
**Kontekst:** Anchor princip za sve pattern preporuke. Default → "ne praviti agent" ako workflow rešava.

---

## Sekcija 2 — Prompt Chaining

### C2.1 — Definicija
**Citat:** "Prompt chaining decomposes a task into a sequence of steps, where each LLM call processes the output of the previous one."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.1

### C2.2 — Kada koristiti
**Citat:** "task can be easily and cleanly decomposed into fixed subtasks. The main goal is to trade off latency for higher accuracy, by making each LLM call an easier task."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.1

### C2.3 — Anthropic primeri
**Citat:** "Generating Marketing copy, then translating it into a different language."
**Citat:** "Writing an outline of a document, checking that the outline meets certain criteria, then writing the document based on the outline."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.1

---

## Sekcija 3 — Routing

### C3.1 — Definicija
**Citat:** "Routing classifies an input and directs it to a specialized followup task. This workflow allows for separation of concerns, and building more specialized prompts."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.2

### C3.2 — Kada koristiti + cost optimization
**Citat:** "complex tasks where there are distinct categories that are better handled separately, and where classification can be handled accurately, either by an LLM or a more traditional classification model/algorithm."
**Citat:** "Routing easy/common questions to smaller, cost-efficient models like Claude Haiku 4.5 and hard/unusual questions to more capable models like Claude Sonnet 4.5"
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.2

---

## Sekcija 4 — Parallelization

### C4.1 — Definicija + 2 varijante
**Citat:** "LLMs can sometimes work simultaneously on a task and have their outputs aggregated programmatically. This workflow, parallelization, manifests in two key variations:
- **Sectioning:** Breaking a task into independent subtasks run in parallel.
- **Voting:** Running the same task multiple times to get diverse outputs."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.3

### C4.2 — Kada koristiti (gold quote)
**Citat:** "Parallelization is effective when the divided subtasks can be parallelized for speed, or when multiple perspectives or attempts are needed for higher confidence results. For complex tasks with multiple considerations, LLMs generally perform better when each consideration is handled by a separate LLM call"
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.3, audit findings za HW (per-platform paralelno)

### C4.3 — Anthropic primeri
**Citat (Sectioning):** "Implementing guardrails where one model instance processes user queries while another screens them for inappropriate content"
**Citat (Voting):** "Reviewing a piece of code for vulnerabilities, where several different prompts review and flag the code if they find a problem."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.3

---

## Sekcija 5 — Orchestrator-Workers

### C5.1 — Definicija
**Citat:** "In the orchestrator-workers workflow, a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.4

### C5.2 — Razlika od Parallelization
**Citat:** "the key difference from parallelization is its flexibility—subtasks aren't pre-defined, but determined by the orchestrator based on the specific input."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.4

### C5.3 — Production primer (Research)
**Citat:** "Our Research system uses a multi-agent architecture with an orchestrator-worker pattern, where a lead agent coordinates the process while delegating to specialized subagents that operate in parallel."
**Izvor:** Multi-agent research system (#4), Jun 13 2025
**Korišćeno u:** `patterns.md` § 2.4

### C5.4 — Kada NE koristiti
**Citat:** "some domains that require all agents to share the same context or involve many dependencies between agents are not a good fit for multi-agent systems today. For instance, most coding tasks involve fewer truly parallelizable tasks than research"
**Izvor:** Multi-agent research system (#4)
**Korišćeno u:** `patterns.md` § 2.4

---

## Sekcija 6 — Evaluator-Optimizer

### C6.1 — Definicija
**Citat:** "In the evaluator-optimizer workflow, one LLM call generates a response while another provides evaluation and feedback in a loop."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.5

### C6.2 — Kada koristiti (2 signala)
**Citat:** "particularly effective when we have clear evaluation criteria, and when iterative refinement provides measurable value. The two signs of good fit are, first, that LLM responses can be demonstrably improved when a human articulates their feedback; and second, that the LLM can provide such feedback."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.5

### C6.3 — Standalone evaluator (mode collapse fix)
**Citat:** "Separating the agent doing the work from the agent judging it proves to be a strong lever to address this issue. The separation doesn't immediately eliminate that leniency on its own; the evaluator is still an LLM that is inclined to be generous towards LLM-generated outputs. But tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work"
**Izvor:** Harness design for long-running app dev (#2), Mar 24 2026
**Korišćeno u:** `patterns.md` § 2.5 — direktan dokaz za **HARD RULE #1** (SA mode collapse risk)

### C6.4 — Strip assistant text (anti-rationalization)
**Citat:** "We strip assistant text so the agent can't talk the classifier into making a bad call. The agent could generate persuasive rationalizations... If the classifier reads those, it can be talked into the wrong decision."
**Izvor:** Claude Code auto mode (#7), Mar 25 2026
**Korišćeno u:** `patterns.md` § 2.5, dizajn izbor za SA

---

## Sekcija 7 — Autonomous Agent

### C7.1 — Definicija
**Citat:** "Agents can handle sophisticated tasks, but their implementation is often straightforward. They are typically just LLMs using tools based on environmental feedback in a loop."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.6

### C7.2 — Kada koristiti
**Citat:** "open-ended problems where it's difficult or impossible to predict the required number of steps, and where you can't hardcode a fixed path. The LLM will potentially operate for many turns, and you must have some level of trust in its decision-making."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.6

### C7.3 — Tri core principa (BEA zaključak)
**Citati:**
1. "Maintain simplicity in your agent's design."
2. "Prioritize transparency by explicitly showing the agent's planning steps."
3. "Carefully craft your agent-computer interface (ACI) through thorough tool documentation and testing."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.6, audit kriterijumi (1, 4, 6)

### C7.4 — Tool design prioritet
**Citat:** "While building our agent for SWE-bench, we actually spent more time optimizing our tools than the overall prompt."
**Izvor:** Building Effective Agents (#5)
**Korišćeno u:** `patterns.md` § 2.6, audit Kriterijum 6 (Tool Design)

---

## Sekcija 8 — Long-running: Initializer + Coding (Effective harnesses)

### C8.1 — Initializer agent
**Citat:** "Initializer agent: The very first agent session uses a specialized prompt that asks the model to set up the initial environment: an init.sh script, a claude-progress.txt file that keeps a log of what agents have done, and an initial git commit"
**Izvor:** Effective harnesses for long-running agents (#3), Nov 26 2025
**Korišćeno u:** `patterns.md` § 3.1

### C8.2 — Feature list pattern
**Citat:** "we prompted the initializer agent to write a comprehensive file of feature requirements expanding on the user's initial prompt. In the claude.ai clone example, this meant over 200 features"
**Izvor:** Effective harnesses (#3)
**Korišćeno u:** `patterns.md` § 3.1

### C8.3 — JSON preference
**Citat:** "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files"
**Izvor:** Effective harnesses (#3)
**Korišćeno u:** `patterns.md` § 3.1, design preporuka za state files

---

## Sekcija 9 — Long-running: Planner + Generator + Evaluator (Harness design)

### C9.1 — Tri uloge
**Citati:**
- Planner: "took a simple 1-4 sentence prompt and expanded it into a full product spec"
- Generator: "instructing the generator to work in sprints, picking up one feature at a time"
- Evaluator: "used the Playwright MCP to click through the running application the way a user would"
**Izvor:** Harness design for long-running app dev (#2), Mar 24 2026
**Korišćeno u:** `patterns.md` § 3.2

### C9.2 — Sprint contract
**Citat:** "agreeing on what 'done' looked like for that chunk of work before any code was written. This existed because the product spec was intentionally high-level, and I wanted a step to bridge the gap between user stories and testable implementation."
**Izvor:** Harness design (#2)
**Korišćeno u:** `patterns.md` § 3.2

### C9.3 — Cost data (Opus 4.5 DAW build)
**Doslovni podaci:**
| Phase | Duration | Cost |
|---|---|---|
| Planner | 4.7 min | $0.46 |
| Build R1 | 2h 7min | $71.08 |
| QA R1 | 8.8 min | $3.24 |
| Total | 3h 50min | $124.70 |
**Izvor:** Harness design (#2)
**Korišćeno u:** `patterns.md` § 3.2, cost benchmark za multi-agent setupove

---

## Sekcija 10 — Managed Agents (decoupled architecture)

### C10.1 — Virtualizacija (centralna ideja)
**Citat:** "We virtualized the components of an agent: a session (the append-only log of everything that happened), a harness (the loop that calls Claude and routes Claude's tool calls to the relevant infrastructure), and a sandbox (an execution environment where Claude can run code and edit files)."
**Izvor:** Scaling Managed Agents (#1), Apr 8 2026
**Korišćeno u:** `patterns.md` § 3.3

### C10.2 — Pets vs cattle
**Citat:** "a pet is a named, hand-tended individual you can't afford to lose, while cattle are interchangeable"
**Izvor:** Managed Agents (#1)
**Korišćeno u:** `patterns.md` § 3.3

### C10.3 — Latency improvement
**Citat:** "our p50 TTFT dropped roughly 60% and p95 dropped over 90%"
**Izvor:** Managed Agents (#1)
**Korišćeno u:** `patterns.md` § 3.3

### C10.4 — Meta-princip (gold za skill)
**Citat:** "harnesses encode assumptions about what Claude can't do on its own. However, those assumptions need to be frequently questioned because they can go stale as models improve."
**Izvor:** Managed Agents (#1)
**Korišćeno u:** `patterns.md` § 3.3, audit Kriterijum 8 (Model-update tested)

---

## Sekcija 11 — Multi-agent prompting principi (8 stavki)

Iz Multi-agent research system (#4), Jun 13 2025 — citirani direktno:

### C11.1 — Think like your agents
**Citat:** "Think like your agents."
**Korišćeno u:** `patterns.md` § 4

### C11.2 — Teach orchestrator (A2A standard — 4 mandatory polja)
**Citat:** Svaki subagent mora dobiti "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."
**Korišćeno u:** `patterns.md` § 4, A2A standard u svim DESIGN_SPEC-ovima

### C11.3 — Scale effort
**Citat:** "Simple fact-finding requires just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents with 10-15 calls each, and complex research might use more than 10 subagents"
**Korišćeno u:** `patterns.md` § 4

### C11.4 — Tool design critical
**Citat:** "Tool design and selection are critical."
**Korišćeno u:** `patterns.md` § 4, audit Kriterijum 6

### C11.5 — Tool-testing agent (self-improve)
**Citat:** "Let agents improve themselves." → "40% decrease in task completion time"
**Korišćeno u:** `patterns.md` § 4

### C11.6 — Start wide
**Citat:** "Start wide, then narrow down."
**Korišćeno u:** `patterns.md` § 4

### C11.7 — Guide thinking
**Citat:** "Guide the thinking process." → extended thinking kao "controllable scratchpad"
**Korišćeno u:** `patterns.md` § 4

### C11.8 — Parallel tool calling
**Citat:** "Parallel tool calling transforms speed and performance." → "cut research time by up to 90% for complex queries"
**Korišćeno u:** `patterns.md` § 4

### C11.9 — Multi-agent numeric outcome (90.2%)
**Citat:** "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval"
**Korišćeno u:** `patterns.md` § 2.4

### C11.10 — Token cost (15x)
**Citat:** "agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats"
**Korišćeno u:** `patterns.md` § 2.4, audit Kriterijum 7 (Cost-conscious)

---

## Sekcija 12 — Skills system (Equipping Skills)

### C12.1 — Definicija
**Citat:** "organized folders of instructions, scripts, and resources that agents can discover and load dynamically to perform better at specific tasks"
**Izvor:** Equipping agents with Agent Skills (#6), Oct 16 2025
**Korišćeno u:** `patterns.md` § 5

### C12.2 — Anatomija
**Citati:**
- "directory that contains a SKILL.md file"
- "must start with YAML frontmatter that contains some required metadata: name and description"
- "At startup, the agent pre-loads the name and description of every installed skill into its system prompt"
**Izvor:** Equipping Skills (#6)
**Korišćeno u:** `patterns.md` § 5, SKILL.md frontmatter validacija

### C12.3 — Progressive disclosure (3 nivoa)
**Citati:**
1. Metadata (name, description) — uvek u system prompt-u
2. Body SKILL.md — kad Claude proceni da je skill relevantan
3. Bundled files — on-demand
**Izvor:** Equipping Skills (#6)
**Korišćeno u:** `patterns.md` § 5, `README.md` "progressive disclosure" objašnjenje

### C12.4 — Self-improvement (za agent-architect Mode 5)
**Citat:** "As you work on a task with Claude, ask Claude to capture its successful approaches and common mistakes into reusable context and code within a skill. If it goes off track when using a skill to complete a task, ask it to self-reflect on what went wrong."
**Izvor:** Equipping Skills (#6)
**Korišćeno u:** `SKILL.md` "Self-improvement pattern" sekcija

---

## Sekcija 13 — Security: Auto Mode classifier

### C13.1 — 4 threat kategorije
**Citat:** "Overeager behavior, Honest mistakes, Prompt injection, Misaligned model"
**Izvor:** Claude Code auto mode (#7), Mar 25 2026
**Korišćeno u:** `patterns.md` § 6

### C13.2 — Numeric (FPR/FNR)
**Citati:**
- "0.4% FPR"
- "17% FNR on real overeager actions" (n=52)
**Izvor:** Auto Mode (#7)
**Korišćeno u:** `patterns.md` § 6

---

## Sekcija 14 — Sandboxing

### C14.1 — Numeric outcome
**Citat:** "sandboxing safely reduces permission prompts by 84%"
**Izvor:** Beyond permission prompts (#8), Oct 20 2025
**Korišćeno u:** `patterns.md` § 6

---

## Verification checklist (za skill, kad koristi citat)

Pre nego što ubaciš citat u bilo koji output (audit report, DESIGN_SPEC, reference odgovor), prođi kroz ovo:

- [ ] Citat je u ovom fajlu (anthropic-citations.md)
- [ ] Citat je u **identičnim navodnicima** kao u izvoru (nema parafrazriranja)
- [ ] Source URL je priložen
- [ ] Datum publikacije je priložen
- [ ] Last verified datum je < 90 dana star (ako nije, ponovo fetch-uj kroz Chrome MCP)
- [ ] Korišćenje citata je relevantno za kontekst (ne forsiraj citat samo da popuniš space)

**Ako neki check fail-uje — NE koristi citat.** Bolje "nemam direktan citat za ovo" nego pogrešna atribucija.

---

## Šta NIJE u ovom fajlu (v0.2 ograničenja)

1. **Klaster B — Context Engineering article (Sep 29 2025)** — biće dodato u v0.2 next iteration (task #69)
2. **Writing effective tools for agents (Sep 11 2025)** — planirano za v0.3
3. **Code execution with MCP (Nov 04 2025)** — planirano za v0.3
4. **Bilo koji Anthropic članak posle Apr 8 2026** — treba periodični re-scan

---

## Versioning

| Verzija | Datum | Šta se promenilo | Autor |
|---|---|---|---|
| v0.1 | 2026-05-25 | Citati distribuirani u patterns.md (nije zaseban fajl) | agent-architect |
| v0.2 | 2026-05-27 | Konsolidovano u standalone fajl. 8 izvora, 14 sekcija, ~45 verifikovanih citata | agent-architect |

---

## Reference

- `reference/patterns.md` — gde se citati koriste u kontekstu
- `reference/audit-checklist.md` — koji citati su anchor za audit kriterijume
- `reference/design-spec-template.md` — citati koji se koriste za DESIGN_SPEC opravdanja
- `SKILL.md` — gde Mode 3 (Reference Library) ulazi u ovaj fajl
