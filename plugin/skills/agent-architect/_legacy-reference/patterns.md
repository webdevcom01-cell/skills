# Agent Patterns Reference

Sintetisano iz 8 Anthropic engineering članaka (Dec 2024 – Apr 2026), revidirano kroz SOMA Pass 1.5 audit.

**Princip:** Svaka tvrdnja u navodnicima je doslovan citat iz izvora. URL-ovi i citati verifikovani fetchovanjem stranica kroz Chrome MCP (poslednja verifikacija: 2026-05-25, sve potvrđeno). Brojni podaci direktno iz teksta, ne aproksimirani.

---

## 1. Hijerarhija odluka (Decision tree)

Pre nego što izabereš pattern, prođi kroz ova 4 pitanja:

```
Q1: Da li je task ponovljiv sa fixed steps?
    DA → ide na Q2 (Workflow patterns)
    NE → ide na Q4 (Agent patterns)

Q2: Koliko paralelnih ili kondicionalnih grana?
    1 sekvencijalna → Prompt Chaining (§ 2.1)
    Više grana po kategoriji → Routing (§ 2.2)
    Paralelne nezavisne grane → Parallelization (§ 2.3)
    Dinamički decomposed worker tasks → Orchestrator-Workers (§ 2.4)

Q3: Da li task ima jasne eval kriterijume + iterativno poboljšanje vredi?
    DA → Evaluator-Optimizer (§ 2.5)
    NE → ostani na izabranom Q2 patternu

Q4: Da li task prelazi single context window?
    DA → Long-running Harness (§ 3) sa Initializer + Coding agent ili 3-agent setup
    NE → Autonomous Agent (§ 2.6)

I uvek pitaj prvo: NIVO A (Claude Code) ili NIVO B (SOMA pipeline)?
    Razlika menja preporuku, jer su tools, runtime, i constraints različiti.
```

**Citat iz Building Effective Agents (čl. Dec 19 2024):**
> "we recommend finding the simplest solution possible, and only increasing complexity when needed. This might mean not building agentic systems at all."

---

## 2. Šest patterna iz "Building Effective Agents"

### 2.1 Prompt Chaining

**Definicija (citat):**
> "Prompt chaining decomposes a task into a sequence of steps, where each LLM call processes the output of the previous one."

**Kada koristiti (citat):**
> "task can be easily and cleanly decomposed into fixed subtasks. The main goal is to trade off latency for higher accuracy, by making each LLM call an easier task."

**Anthropic primeri:**
> "Generating Marketing copy, then translating it into a different language."
> "Writing an outline of a document, checking that the outline meets certain criteria, then writing the document based on the outline."

**SOMA mapiranje (revidirano Pass 1.5):**
- TI → HW → CR jeste **forward chaining**, ali sa **implicit blackboard feedback kroz vault** (HW reads winners-log u sledećem run-u; TI reads sopstveni evo-log; human updates instincts)
- **NIJE pure linear chain** — ne smeš tako reći. Tačno: "chain (forward) + asinhroni feedback kroz vault"
- Programatic gate iz BEA pattern-a → SOMA implementira to kao **per-agent quality_gate node** (self-check), NIJE cross-agent gate

**Trade-off za SOMA:**
- ✅ Konzistentno sa Single Responsibility (SOMA rule #1)
- ✅ A2A handoff via call_agent (SOMA rule #3)
- ⚠️ Latency linearna sa brojem agenata (TI ~30s + HW ~20s + CR ~15s = ~65s typical)

---

### 2.2 Routing

**Definicija (citat):**
> "Routing classifies an input and directs it to a specialized followup task. This workflow allows for separation of concerns, and building more specialized prompts."

**Kada koristiti (citat):**
> "complex tasks where there are distinct categories that are better handled separately, and where classification can be handled accurately, either by an LLM or a more traditional classification model/algorithm."

**Anthropic primeri:**
> "Directing different types of customer service queries (general questions, refund requests, technical support) into different downstream processes"
> "Routing easy/common questions to smaller, cost-efficient models like Claude Haiku 4.5 and hard/unusual questions to more capable models like Claude Sonnet 4.5"

**SOMA mapiranje:**
- ❌ SOMA trenutno NEMA routing pattern. Svi TI run-ovi idu kroz isti HW chain.
- Potencijalna primena: TI mogao bi da klasifikuje trend tip (announcement vs. opinion vs. technical) i route-uje na različite HW prompt-ove
- ⚠️ Da bi se ovo dodalo, treba LLM classifier korak — povećava cost i može krši "Max 3 produktivna node-a" pravilo ako se ubaci u TI

---

### 2.3 Parallelization (dve varijante)

**Definicija (citat):**
> "LLMs can sometimes work simultaneously on a task and have their outputs aggregated programmatically. This workflow, parallelization, manifests in two key variations:
> - **Sectioning:** Breaking a task into independent subtasks run in parallel.
> - **Voting:** Running the same task multiple times to get diverse outputs."

**Kada koristiti (citat):**
> "Parallelization is effective when the divided subtasks can be parallelized for speed, or when multiple perspectives or attempts are needed for higher confidence results. For complex tasks with multiple considerations, LLMs generally perform better when each consideration is handled by a separate LLM call"

**Anthropic primeri:**
- Sectioning: "Implementing guardrails where one model instance processes user queries while another screens them for inappropriate content"
- Voting: "Reviewing a piece of code for vulnerabilities, where several different prompts review and flag the code if they find a problem."

**SOMA mapiranje:**
- HW generiše **5 hooks paralelno** (per platform: LinkedIn, X, YouTube, Instagram, TikTok). Ovo je **Sectioning varijanta**.
- Evo-log potvrđuje: "all-5 (platform-specific) | LI:19 X:18 YT:17 IG:17 TT:18" (citat iz `agents/hook-writer/evo-log.md`, 2026-05-15)
- Voting NIJE u SOMA — Score Analyzer skoruje jednom, ne više puta

---

### 2.4 Orchestrator-Workers

**Definicija (citat):**
> "In the orchestrator-workers workflow, a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results."

**Razlika od Parallelization (citat):**
> "the key difference from parallelization is its flexibility—subtasks aren't pre-defined, but determined by the orchestrator based on the specific input."

**Production primer — Anthropic Research feature (čl. Jun 13 2025):**
> "Our Research system uses a multi-agent architecture with an orchestrator-worker pattern, where a lead agent coordinates the process while delegating to specialized subagents that operate in parallel."

**Numerički podaci iz Research feature-a:**
- "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by **90.2%** on our internal research eval"
- "agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about **15× more tokens** than chats"
- "parallel tool calling... cut research time by up to **90%** for complex queries"

**Kada NE koristiti (citat):**
> "some domains that require all agents to share the same context or involve many dependencies between agents are not a good fit for multi-agent systems today. For instance, most coding tasks involve fewer truly parallelizable tasks than research"

**SOMA mapiranje:**
- ❌ SOMA NEMA orchestrator-worker. SOMA je fixed chain TI→HW→CR.
- Potencijalna primena: ako TI treba da skenira **N različitih niche-ova paralelno**, orchestrator-TI mogao bi da spawn-uje N worker-TI instanci
- ⚠️ Verovatno overkill za sadašnji obim SOMA-e (1 niche: "AI development, agent building, LLM tooling")
- ⚠️ Cost: 15x više tokena znači da ovo treba samo ako je vrednost task-a *visoka*

---

### 2.5 Evaluator-Optimizer

**Definicija (citat):**
> "In the evaluator-optimizer workflow, one LLM call generates a response while another provides evaluation and feedback in a loop."

**Kada koristiti (citat):**
> "particularly effective when we have clear evaluation criteria, and when iterative refinement provides measurable value. The two signs of good fit are, first, that LLM responses can be demonstrably improved when a human articulates their feedback; and second, that the LLM can provide such feedback."

**Production primer — Harness Design (čl. Mar 24 2026):**
> "Separating the agent doing the work from the agent judging it proves to be a strong lever to address this issue. The separation doesn't immediately eliminate that leniency on its own; the evaluator is still an LLM that is inclined to be generous towards LLM-generated outputs. But tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work"

**Bitan dizajn izbor (iz Auto Mode, čl. Mar 25 2026):**
> "We strip assistant text so the agent can't talk the classifier into making a bad call. The agent could generate persuasive rationalizations... If the classifier reads those, it can be talked into the wrong decision."

**SOMA mapiranje (REVIDIRANO Pass 1.5):**
- **Score Analyzer JESTE Evaluator pattern**, ALI sa upozorenjima:
  - ⚠️ HARD RULE #1: SA je **LLM-as-judge, NIJE deterministic sensor**
  - ⚠️ SA koristi `gpt-4.1-mini` (processor) — **isti model kao HW koji generiše hooks**
  - ⚠️ Citat iz Pass 1.5 corrections: "gpt-4.1-mini scoring gpt-4.1-mini hooks je upravo **NIJE** independent. Paper preporučuje *independent* verification (verifier sa drugačijim biases nego generator)."
  - ⚠️ Mode collapse risk je realan
- **HARD RULE #2:** SA NIJE u chainu. Dodavanje u chain je arhitekturalna odluka, ne automatski savet.
- **Otvoreno pitanje** (iz Pass 1.5): "da li SA postaje 4. node u chainu (HW → SA → CR), ili paralelni validator? Ako paralelni: kako se njegov verdict koristi? Block CR? Flag samo? Update HW instincts?"

**Preporuka za skill:** Kad neko predloži evaluator-optimizer za SOMA, predloži **drugačiji model za evaluator** (npr. claude-haiku-4-5 ili claude-sonnet-4-5) da se smanji mode collapse rizik.

---

### 2.6 Autonomous Agent

**Definicija (citat):**
> "Agents can handle sophisticated tasks, but their implementation is often straightforward. They are typically just LLMs using tools based on environmental feedback in a loop."

**Kada koristiti (citat):**
> "open-ended problems where it's difficult or impossible to predict the required number of steps, and where you can't hardcode a fixed path. The LLM will potentially operate for many turns, and you must have some level of trust in its decision-making."

**Tri core principa za agent dizajn (citat — Building Effective Agents zaključak):**
> 1. "Maintain simplicity in your agent's design."
> 2. "Prioritize transparency by explicitly showing the agent's planning steps."
> 3. "Carefully craft your agent-computer interface (ACI) through thorough tool documentation and testing."

**Tool design prioritet (citat):**
> "While building our agent for SWE-bench, we actually spent more time optimizing our tools than the overall prompt."

**SOMA mapiranje:**
- ❌ SOMA NEMA autonomous agent. SOMA je workflow (fixed steps).
- Najbliža autonomna komponenta je TI sa web_search — ali i to je fixed flow (kb_search → web_search → ai_response → call_agent)
- Verovatno NE TREBA u SOMA — to bi krilo "Max 3 nodes" i "Human review queue" pravila

---

## 3. Long-running patterns (kada task prelazi context window)

### 3.1 Initializer + Coding agent (čl. Nov 26 2025)

**Citat:**
> "Initializer agent: The very first agent session uses a specialized prompt that asks the model to set up the initial environment: an init.sh script, a claude-progress.txt file that keeps a log of what agents have done, and an initial git commit"

**Citat — feature_list pattern:**
> "we prompted the initializer agent to write a comprehensive file of feature requirements expanding on the user's initial prompt. In the claude.ai clone example, this meant over 200 features"

**JSON preference:**
> "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files"

**SOMA primenljivost:**
- ❌ SOMA pojedinačni run-ovi su brzi (<2 min) — nemaju context window problem
- ✅ Ali za **build-out budućih SOMA agenata** (npr. Nivo A task gde Claude Code gradi novi SOMA pipeline), ovaj pattern može da pomogne

### 3.2 Three-agent Planner + Generator + Evaluator (čl. Mar 24 2026)

**Tri uloge (citat):**
> - Planner: "took a simple 1-4 sentence prompt and expanded it into a full product spec"
> - Generator: "instructing the generator to work in sprints, picking up one feature at a time"
> - Evaluator: "used the Playwright MCP to click through the running application the way a user would"

**Sprint contract (citat):**
> "agreeing on what 'done' looked like for that chunk of work before any code was written. This existed because the product spec was intentionally high-level, and I wanted a step to bridge the gap between user stories and testable implementation."

**Cost data za Opus 4.5 DAW build (citat):**
| Phase | Duration | Cost |
|---|---|---|
| Planner | 4.7 min | $0.46 |
| Build R1 | 2h 7min | $71.08 |
| QA R1 | 8.8 min | $3.24 |
| ... | ... | ... |
| **Total** | **3h 50min** | **$124.70** |

**SOMA primenljivost:**
- ❌ SOMA NEMA sprint contract koncept. TI/HW/CR ne dogovaraju "definition of done" pre nego što HW počne.
- Potencijal: dodavanje "sprint contract" sloja između TI i HW (HW kaže "evo šta planiram da napravim za ovaj trend", TI potvrđuje pre nego što HW počne)
- ⚠️ Trade-off: dodaje ~1 LLM call latency po run-u

### 3.3 Managed Agents — decoupled (čl. Apr 8 2026)

**Citat (centralna ideja):**
> "We virtualized the components of an agent: a session (the append-only log of everything that happened), a harness (the loop that calls Claude and routes Claude's tool calls to the relevant infrastructure), and a sandbox (an execution environment where Claude can run code and edit files)."

**Pets vs cattle (citat):**
> "a pet is a named, hand-tended individual you can't afford to lose, while cattle are interchangeable"

**Numeric outcome (citat):**
> "our p50 TTFT dropped roughly 60% and p95 dropped over 90%"

**Centralni meta-princip (citat — zlato za skill):**
> "harnesses encode assumptions about what Claude can't do on its own. However, those assumptions need to be frequently questioned because they can go stale as models improve."

**SOMA primenljivost:**
- ❌ SOMA je *single-runtime* (sve u AgentStack-u), nije "decoupled brain/hands/session"
- ⚠️ Ali meta-princip "harness assumptions go stale" se DIREKTNO primenjuje. Primer: ako budući OpenAI model bude bolji u single-shot multi-platform generaciji, možda HW ne treba 3 odvojena node-a — može jedan.
- Skill mora periodično pitati: "kad je poslednji put neko proverio da li su SOMA flow nodes opravdani sa trenutnim modelom?"

---

## 4. Multi-agent specifični prompting principi (čl. Jun 13 2025)

Iz "How we built our multi-agent research system" — citirano direktno:

1. **"Think like your agents."** Buildovati simulacije za uvid.
2. **"Teach the orchestrator how to delegate."** Svaki subagent mora dobiti "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."
3. **"Scale effort to query complexity."** Citat: "Simple fact-finding requires just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents with 10-15 calls each, and complex research might use more than 10 subagents"
4. **"Tool design and selection are critical."**
5. **"Let agents improve themselves."** Tool-testing agent dao "40% decrease in task completion time"
6. **"Start wide, then narrow down."**
7. **"Guide the thinking process."** Extended thinking kao "controllable scratchpad"
8. **"Parallel tool calling transforms speed and performance."** "cut research time by up to 90% for complex queries"

---

## 5. Skills system (čl. Oct 16 2025)

**Definicija (citat):**
> "organized folders of instructions, scripts, and resources that agents can discover and load dynamically to perform better at specific tasks"

**Anatomija (citat):**
> "directory that contains a SKILL.md file"
> "must start with YAML frontmatter that contains some required metadata: name and description"
> "At startup, the agent pre-loads the name and description of every installed skill into its system prompt"

**Progressive disclosure (3 nivoa, citat):**
> 1. Metadata (name, description) — uvek u system prompt-u
> 2. Body SKILL.md — kad Claude proceni da je skill relevantan
> 3. Bundled files — on-demand

**SOMA mapiranje (revidirano Pass 1.5):**
- `agents/<name>/instincts.md` = **mapira se na bundled skill files** koji nose *rules*
- `agents/content-repurposer/format-templates.md` = **mapira se na bundled skill files** koji nose *structures* (DSL)
- ⚠️ HARD RULE #6: instincts ≠ format-templates. Ne smeš ih izjednačavati.
- SOMA agenti NEMAJU SKILL.md format — to je AgentStack runtime, ne Claude Code runtime
- ALI: `agent-architect` (ovaj skill) JESTE pravi Claude Code skill sa SKILL.md (Nivo A)

---

## 6. Security & autonomy patterns (čl. Mar 25 + Oct 20 2025)

### Auto Mode classifier (čl. Mar 25 2026)
- 2-layer defense: input PI probe + output transcript classifier
- 2-stage classifier: fast yes/no filter + chain-of-thought escalation
- 4 threat kategorije (citirano): "Overeager behavior, Honest mistakes, Prompt injection, Misaligned model"
- Numeric (citirano): "0.4% FPR" i "17% FNR on real overeager actions" (n=52)

### Sandboxing (čl. Oct 20 2025)
- Filesystem isolation + Network isolation (oba citirano kao zahtev za "effective sandboxing")
- OS-level: Linux bubblewrap, macOS seatbelt
- Numeric (citirano): "sandboxing safely reduces permission prompts by 84%"

**SOMA mapiranje:**
- ❌ SOMA NEMA sandboxing — agenti direktno pišu u vault
- ❌ SOMA NEMA classifier gate pre write-a u winners-log ili evo-log
- ⚠️ Pass 1.5 audit potvrđuje ove gap-ove

---

## 7. Audit checklist (za Mode 2)

Kad audituješ SOMA agent, prođi kroz 8 kriterijuma:

| # | Kriterijum | Šta da provariš | Source |
|---|---|---|---|
| 1 | Single responsibility | Da li agent radi tačno jednu stvar? | SOMA rule #1 |
| 2 | ≤3 produktivna node-a | call_agent ne broji; ostali da | SOMA rule #2 + Buky-jeva interpretacija |
| 3 | Memory-first | Da li flow počinje sa kb_search? | SOMA rule #4 |
| 4 | Quality gate per-agent | Postoji li self-check pre output-a? | soma-rules.md |
| 5 | Evo-log write | Da li agent piše evo-log entry posle run-a? | SOMA rule #5 |
| 6 | Tool design | Da li tools imaju jasan opis? Da li parametri imaju dobre nazive? | BEA App. 2 |
| 7 | Cost-conscious | Da li je arhitektura opravdana cost-wise? (multi-agent = 15x) | Multi-agent research |
| 8 | Model-update tested | Kad je poslednji audit izveden posle promene modela? | Managed Agents meta-princip |

**Skor sistem (predlog):**
- 0/8 = krši fundamentalno, treba redizajn
- 1-3/8 = ozbiljni propusti, prioritetni fix
- 4-6/8 = funkcionalno, ima šta da se popravi
- 7-8/8 = zdrav, samo manja optimizacija

---

## 8. Bibliografija (8 izvora)

| # | Naslov | Autor(i) | Datum | URL |
|---|---|---|---|---|
| 1 | Scaling Managed Agents | Lance Martin, Gabe Cemaj, Michael Cohen | Apr 8, 2026 | https://www.anthropic.com/engineering/managed-agents |
| 2 | Harness design for long-running app dev | Prithvi Rajasekaran | Mar 24, 2026 | https://www.anthropic.com/engineering/harness-design-long-running-apps |
| 3 | Effective harnesses for long-running agents | Justin Young | Nov 26, 2025 | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents |
| 4 | How we built our multi-agent research system | Hadfield, Zhang, Lien, Scholz, Fox, Ford | Jun 13, 2025 | https://www.anthropic.com/engineering/multi-agent-research-system |
| 5 | Building effective agents | Erik S., Barry Zhang | Dec 19, 2024 | https://www.anthropic.com/engineering/building-effective-agents |
| 6 | Equipping agents with Agent Skills | Barry Zhang, Keith Lazuka, Mahesh Murag | Oct 16, 2025 | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills |
| 7 | Claude Code auto mode | John Hughes | Mar 25, 2026 | https://www.anthropic.com/engineering/claude-code-auto-mode |
| 8 | Beyond permission prompts (sandboxing) | David Dworken, Oliver Weller-Davies | Oct 20, 2025 | https://www.anthropic.com/engineering/claude-code-sandboxing |
