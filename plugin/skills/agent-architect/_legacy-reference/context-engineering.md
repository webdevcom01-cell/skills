# Context Engineering Reference (Klaster B)

**Izvor:** "Effective context engineering for AI agents" — Anthropic Applied AI Team (Prithvi Rajasekaran, Ethan Dixon, Carly Ryan, Jeremy Hadfield), Sep 29 2025.
**URL:** https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
**Last verified:** 2026-05-27 (fetched fresh kroz Chrome MCP)

**Princip:** Svaka tvrdnja u navodnicima je doslovan citat iz članka. SOMA mapping sekcije su moja interpretacija — eksplicitno označene, ne izvor.

---

## 1. Centralna definicija

### Šta je context engineering

**Citat:**
> "context engineering refers to the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference, including all the other information that may land there outside of the prompts."

**Razlika od prompt engineering (citat):**
> "Prompt engineering refers to methods for writing and organizing LLM instructions for optimal outcomes ... However, as we move towards engineering more capable agents that operate over multiple turns of inference and longer time horizons, we need strategies for managing the entire context state (system instructions, tools, MCP, external data, message history, etc)."

**Ključna razlika (citat):**
> "In contrast to the discrete task of writing a prompt, context engineering is iterative and the curation phase happens each time we decide what to pass to the model."

### SOMA mapping — gde context engineering ulazi

| SOMA element | Context engineering aspekt |
|---|---|
| `kb_search` u flow-u | **Retrieval** — pulled context iz KB |
| `instincts.md` u sistem prompt-u | Prompt-level context curation |
| `winners-log.md` čitan po run-u | Just-in-time references |
| Evo-log entries između run-ova | Compaction substitute za persistent memory |
| Call_agent payload (4 mandatory polja) | Sub-agent context isolation |

---

## 2. Zašto context engineering važan — fizika ograničenja

### Context rot

**Citat:**
> "as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases."

### Attention budget

**Citat:**
> "Like humans, who have limited working memory capacity, LLMs have an 'attention budget' that they draw on when parsing large volumes of context. Every new token introduced depletes this budget by some amount, increasing the need to carefully curate the tokens available to the LLM."

### Arhitektonsko ograničenje (n² pairwise relationships)

**Citat:**
> "LLMs are based on the transformer architecture, which enables every token to attend to every other token across the entire context. This results in n² pairwise relationships for n tokens. As its context length increases, a model's ability to capture these pairwise relationships gets stretched thin, creating a natural tension between context size and attention focus."

### Performance gradient, ne hard cliff

**Citat:**
> "These factors create a performance gradient rather than a hard cliff: models remain highly capable at longer contexts but may show reduced precision for information retrieval and long-range reasoning compared to their performance on shorter contexts."

### SOMA implikacije

- Svaki SOMA agent ima **2-3 minuta run window** sa ograničenim contextom (kb_search results + web_search results + system prompt)
- TI prompt sa Fix H+I+J ima ~120 linija — već se približava granici "minimal što radi"
- **Audit Kriterijum 9 (predlog za v0.3):** prebroji tokens u system prompt-u + očekivanim KB results-ima; flag ako >50% modela context window-a pre prvog ai_response-a

---

## 3. Anatomija efikasnog context-a

### Gold quote — definicija "dobrog" konteksta

**Citat:**
> "good context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome."

### 3.1 System prompts — "right altitude"

**Citat (centralna ideja):**
> "System prompts should be extremely clear and use simple, direct language that presents ideas at the right altitude for the agent. The right altitude is the Goldilocks zone between two common failure modes."

**Dva failure mode-a (citat):**
> "At one extreme, we see engineers hardcoding complex, brittle logic in their prompts to elicit exact agentic behavior. This approach creates fragility and increases maintenance complexity over time. At the other extreme, engineers sometimes provide vague, high-level guidance that fails to give the LLM concrete signals for desired outputs or falsely assumes shared context."

**Optimum (citat):**
> "The optimal altitude strikes a balance: specific enough to guide behavior effectively, yet flexible enough to provide the model with strong heuristics to guide behavior."

**Format preporuka (citat):**
> "We recommend organizing prompts into distinct sections (like `<background_information>`, `<instructions>`, `## Tool guidance`, `## Output description`, etc) and using techniques like XML tagging or Markdown headers to delineate these sections"

**Minimal ≠ short (citat — kritično):**
> "you should be striving for the minimal set of information that fully outlines your expected behavior. (Note that minimal does not necessarily mean short; you still need to give the agent sufficient information up front to ensure it adheres to the desired behavior.)"

**Iterativan workflow (citat):**
> "It's best to start by testing a minimal prompt with the best model available to see how it performs on your task, and then add clear instructions and examples to improve performance based on failure modes found during initial testing."

### SOMA mapiranje — system prompts

**Trenutno stanje SOMA agent prompts-a (po pass 1.5 audit-u):**
- TI v6 (Fix H+I+J): ~120 linija sa hardcoded rules → **borderline "complex, brittle logic"** failure mode
- HW v1: ~120 linija sa P1-P6 taxonomy + 4 mandatory fields → slično
- CR v? (nije još build): treba dizajnirati sa "right altitude" pristupom

**Akcioni predlog za audit Kriterijum 4 (Quality Gate):**
- Pre rephrase pravila u prompt-u, pitaj: "Da li ovo pravilo može da se izrazi kao **heuristika** (LLM razume) ili je nužno hardcoded if-else?"
- Ako heuristika radi — koristi heuristiku (Goldilocks zone)
- Ako stalno failuje na edge case-u — onda hardcoded gate

### 3.2 Tools — token efficiency + minimal viable set

**Citat:**
> "tools should be self-contained, robust to error, and extremely clear with respect to their intended use. Input parameters should similarly be descriptive, unambiguous, and play to the inherent strengths of the model."

**Najčešća greška (citat):**
> "One of the most common failure modes we see is bloated tool sets that cover too much functionality or lead to ambiguous decision points about which tool to use. If a human engineer can't definitively say which tool should be used in a given situation, an AI agent can't be expected to do better."

### SOMA mapiranje — tools

| SOMA tool | Audit pitanje |
|---|---|
| `kb_search` | Da li query specifičan? Postoji li overlap sa drugim kb_search node-om u istom flow-u? |
| `web_search` (Tavily) | Da li `site:` / `after:` filteri postoje? |
| `ai_response` | Da li System Prompt jasno definiše output format? |
| `call_agent` | Da li 4 mandatory polja (objective, output_format, tool_guidance, task_boundaries) u payload-u? |

### 3.3 Examples — diverse canonical, ne laundry list

**Citat (anti-pattern):**
> "teams will often stuff a laundry list of edge cases into a prompt in an attempt to articulate every possible rule the LLM should follow for a particular task. We do not recommend this."

**Correct pattern (citat):**
> "Instead, we recommend working to curate a set of diverse, canonical examples that effectively portray the expected behavior of the agent. For an LLM, examples are the 'pictures' worth a thousand words."

### SOMA implikacije

- HW v1 prompt ima `winners-log.md` reference za 3-5 winning hookova kao examples → ✅ canonical pattern
- TI v6 prompt ima full list od 15+ "invalid patterns" hardcoded → ⚠️ laundry list anti-pattern
- **v0.3 audit pitanje:** Da li `instincts.md` files ima "examples" sekciju sa diverse canonical primerima ili je laundry list of edge cases?

---

## 4. Context retrieval — agentic search

### Konvergencija na "simple definition" agenta

**Citat:**
> "LLMs autonomously using tools in a loop."

### Just-in-time vs pre-inference retrieval

**Tradicionalan pristup (citat):**
> "Today, many AI-native applications employ some form of embedding-based pre-inference time retrieval to surface important context for the agent to reason over."

**Just-in-time pristup (citat — gold quote):**
> "Rather than pre-processing all relevant data up front, agents built with the 'just in time' approach maintain lightweight identifiers (file paths, stored queries, web links, etc.) and use these references to dynamically load data into context at runtime using tools."

**Anthropic primer (Claude Code):**
> "Claude Code uses this approach to perform complex data analysis over large databases. The model can write targeted queries, store results, and leverage Bash commands like head and tail to analyze large volumes of data without ever loading the full data objects into context."

**Metafora (citat):**
> "This approach mirrors human cognition: we generally don't memorize entire corpuses of information, but rather introduce external organization and indexing systems like file systems, inboxes, and bookmarks to retrieve relevant information on demand."

### Metadata kao signal

**Citat:**
> "the metadata of these references provides a mechanism to efficiently refine behavior, whether explicitly provided or intuitive. To an agent operating in a file system, the presence of a file named `test_utils.py` in a `tests` folder implies a different purpose than a file with the same name located in `src/core_logic/`. Folder hierarchies, naming conventions, and timestamps all provide important signals that help both humans and agents understand how and when to utilize information."

### Progressive disclosure

**Citat:**
> "Letting agents navigate and retrieve data autonomously also enables progressive disclosure—in other words, allows agents to incrementally discover relevant context through exploration. Each interaction yields context that informs the next decision: file sizes suggest complexity; naming conventions hint at purpose; timestamps can be a proxy for relevance."

### Trade-off — kada NIJE pravi pristup

**Citat:**
> "there's a trade-off: runtime exploration is slower than retrieving pre-computed data. Not only that, but opinionated and thoughtful engineering is required to ensure that an LLM has the right tools and heuristics for effectively navigating its information landscape. Without proper guidance, an agent can waste context by misusing tools, chasing dead-ends, or failing to identify key information."

### Hybrid pristup

**Citat:**
> "In certain settings, the most effective agents might employ a hybrid strategy, retrieving some data up front for speed, and pursuing further autonomous exploration at its discretion."

**Claude Code primer:**
> "Claude Code is an agent that employs this hybrid model: CLAUDE.md files are naively dropped into context up front, while primitives like glob and grep allow it to navigate its environment and retrieve files just-in-time, effectively bypassing the issues of stale indexing and complex syntax trees."

### SOMA mapiranje — retrieval

**Trenutno SOMA stanje:**
- Pre-inference: `kb_search` pulled context iz embedded KB → **embedding-based pre-inference time retrieval**
- Just-in-time: NEMA — SOMA agenti nemaju primitives kao glob/grep za autonomous exploration

**v0.3 razmatranje:**
- Da li bi TI imao koristi od **just-in-time pristupa** za web search? (sada radi single batch search, pa fixed processing)
- Da li bi HW imao koristi od **autonomous winners-log exploration**? (sada pre-loads ceo winners-log, ne navigira)

**HARD RULE check (iz soma-truth.md):**
- ⚠️ Just-in-time agenti tendency-iraju ka više node-ova → može krši **Max 3 nodes** soft rule
- ⚠️ Autonomous exploration → krši **Human review queue** ako se ne pažljivo dizajnira

**Generalni princip (citat — direktna preporuka za SOMA):**
> "do the simplest thing that works"

---

## 5. Long-horizon tasks — tri tehnike

### Šta su long-horizon tasks (citat)

> "Long-horizon tasks require agents to maintain coherence, context, and goal-directed behavior over sequences of actions where the token count exceeds the LLM's context window. For tasks that span tens of minutes to multiple hours of continuous work, like large codebase migrations or comprehensive research projects, agents require specialized techniques to work around the context window size limitation."

### Zašto čekanje na veće context windows nije rešenje (citat)

> "Waiting for larger context windows might seem like an obvious tactic. But it's likely that for the foreseeable future, context windows of all sizes will be subject to context pollution and information relevance concerns—at least for situations where the strongest agent performance is desired."

### 5.1 Compaction

**Definicija (citat):**
> "Compaction is the practice of taking a conversation nearing the context window limit, summarizing its contents, and reinitiating a new context window with the summary. Compaction typically serves as the first lever in context engineering to drive better long-term coherence."

**Cilj (citat):**
> "At its core, compaction distills the contents of a context window in a high-fidelity manner, enabling the agent to continue with minimal performance degradation."

**Claude Code implementacija (citat):**
> "In Claude Code, for example, we implement this by passing the message history to the model to summarize and compress the most critical details. The model preserves architectural decisions, unresolved bugs, and implementation details while discarding redundant tool outputs or messages. The agent can then continue with this compressed context plus the five most recently accessed files."

**Tuning preporuka (citat):**
> "we recommend carefully tuning your prompt on complex agent traces. Start by maximizing recall to ensure your compaction prompt captures every relevant piece of information from the trace, then iterate to improve precision by eliminating superfluous content."

**Low-hanging fruit (citat):**
> "An example of low-hanging superfluous content is clearing tool calls and results – once a tool has been called deep in the message history, why would the agent need to see the raw result again? One of the safest lightest touch forms of compaction is tool result clearing"

### 5.2 Structured note-taking (agentic memory)

**Definicija (citat):**
> "Structured note-taking, or agentic memory, is a technique where the agent regularly writes notes persisted to memory outside of the context window. These notes get pulked back into the context window at later times."

**Vrednost (citat):**
> "This strategy provides persistent memory with minimal overhead. Like Claude Code creating a to-do list, or your custom agent maintaining a NOTES.md file, this simple pattern allows the agent to track progress across complex tasks, maintaining critical context and dependencies that would otherwise be lost across dozens of tool calls."

**Claude Plays Pokémon primer (citat — konkretni numbers):**
> "The agent maintains precise tallies across thousands of game steps—tracking objectives like 'for the last 1,234 steps I've been training my Pokémon in Route 1, Pikachu has gained 8 levels toward the target of 10.'"

**Posle context resetа (citat):**
> "After context resets, the agent reads its own notes and continues multi-hour training sequences or dungeon explorations. This coherence across summarization steps enables long-horizon strategies that would be impossible when keeping all the information in the LLM's context window alone."

### 5.3 Sub-agent architectures

**Definicija (citat):**
> "Sub-agent architectures provide another way around context limitations. Rather than one agent attempting to maintain state across an entire project, specialized sub-agents can handle focused tasks with clean context windows. The main agent coordinates with a high-level plan while subagents perform deep technical work or use tools to find relevant information."

**Token efficiency (citat — bitan number):**
> "Each subagent might explore extensively, using tens of thousands of tokens or more, but returns only a condensed, distilled summary of its work (often 1,000-2,000 tokens)."

**Pattern preporuka (citat):**
> "This approach achieves a clear separation of concerns—the detailed search context remains isolated within sub-agents, while the lead agent focuses on synthesizing and analyzing the results."

### Kada koristiti koju tehniku (citat)

**Decision matrix:**
> - "Compaction maintains conversational flow for tasks requiring extensive back-and-forth;
> - Note-taking excels for iterative development with clear milestones;
> - Multi-agent architectures handle complex research and analysis where parallel exploration pays dividends."

---

## 6. SOMA mapping — long-horizon tehnike

| Tehnika | SOMA primena | Status |
|---|---|---|
| **Compaction** | Trenutno NEMA. SOMA run je single-shot (~2 min), ne nailazi na context limit. | Verovatno ne treba. |
| **Structured note-taking** | ✅ POSTOJI implicitno. `evo-log.md`, `winners-log.md`, `instincts.md` su agent notes outside context. | Mapped ✅ |
| **Sub-agent architectures** | ✅ POSTOJI. TI → HW → CR chain je sub-agent pattern (svaki agent isolated context). | Mapped ✅ |

### Bitan insight za SOMA

**Citat (preuzet doslovno iz Sub-agent sekcije):**
> "Each subagent might explore extensively, using tens of thousands of tokens or more, but returns only a condensed, distilled summary of its work (often 1,000-2,000 tokens)."

**Implikacija za SOMA:**
- TI vraća trend brief (~500 tokens) ✅ — u skladu sa 1-2k summary preporukom
- HW vraća hooks array (~800 tokens) ✅ — u skladu
- CR će vraćati platform content (~2-3k tokens) ⚠️ — verovatno na granici, treba pažljivo dizajnirati output format

---

## 7. Audit implikacije za skill

**Novi audit pitanja koja proizilaze iz Klaster B (za dodavanje u `audit-checklist.md` v0.3):**

### Kriterijum 9 — Token budget awareness 🟡 MINOR
- Da li je System Prompt + očekivani KB results + očekivani web_search results < 50% context window-a modela?
- Da li agent ostavlja prostora za nepredviđene retries / pojašnjenja?

### Kriterijum 10 — Right altitude check 🟠 MAJOR
- Da li System Prompt sadrži hardcoded if-else logic koja bi mogla biti heuristika?
- Da li hardcoded pravila krše "Goldilocks zone" — preterano specifična?
- Test: Da li bi novi developer mogao da razume zašto svako pravilo postoji u jednoj rečenici?

### Kriterijum 11 — Just-in-time vs pre-inference balance 🟡 MINOR
- Da li sve što agent pulled u kontekst pri startu **stvarno koristi** u svakom run-u?
- Postoji li deo KB-a koji bi mogao da se pull-uje just-in-time (na osnovu trend tipa, npr.) umesto pre-inference?

### Kriterijum 12 — Compaction strategy 🟡 MINOR (samo za long-horizon agente)
- Ako agent radi >5 minuta — postoji li compaction strategy?
- Da li compaction prompt prošao through recall → precision tuning ciklus?

---

## 8. Zaključna preporuka iz Anthropic članka

**Centralna zlatna izjava (citat):**
> "find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome."

**Trend ka manje engineering-a (citat):**
> "smarter models require less prescriptive engineering, allowing agents to operate with more autonomy."

**Ali (citat):**
> "even as capabilities scale, treating context as a precious, finite resource will remain central to building reliable, effective agents."

---

## 9. Veza sa drugim reference fajlovima

- **patterns.md § 3 (Long-running patterns)** — preklapa se sa sekcijom 5 ovde (Compaction, Structured note-taking, Sub-agents). Ovde je dublji "zašto", tamo "kada".
- **patterns.md § 4 (Multi-agent principi)** — A2A 4 polja (objective, output_format, tool_guidance, task_boundaries) potiču iz Multi-agent članka. Ovde se vide u kontekstu **sub-agent architecture** kao context isolation tehnika.
- **audit-checklist.md** — predloženi novi kriterijumi 9-12 ovde, biće dodati u v0.3.
- **anthropic-citations.md** — sekcija 15 (Context Engineering) ovde se mora dodati u v0.3 ažuriranje citations fajla.
- **soma-truth.md** — Klaster B ne menja 6 hard rules, ali otvara pitanje: da li **structured note-taking** treba da postane SOMA rule #7? (Trenutno je implicitno kroz evo-log/winners-log.)

---

## 10. Open questions za sledeći iteration

1. **Compaction za SOMA evo-logove** — kad evo-log poraste >5k tokens, da li agent treba auto-compaction? Trenutno raste indefinitely.
2. **Just-in-time za web_search** — TI sada radi 1 batch search; da li bi koristio iterative search sa novim queries po pronađenom results-u?
3. **Token budget telemetrija** — postoji li u AgentStack-u tracking koliko tokens svaki agent koristi? (Treba za audit Kriterijum 9.)
4. **Subagent summary discipline** — CR će verovatno vratiti >2k tokens; treba li imati explicit limit u DESIGN_SPEC-u?

---

## 11. Versioning

| Verzija | Datum | Šta se promenilo | Autor |
|---|---|---|---|
| v0.1 | 2026-05-27 | Inicijalni drop — Klaster B sinteza iz "Effective context engineering" članka | agent-architect v0.2 |
