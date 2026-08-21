---
name: agent-architect
description: "Savetnik za dizajn i audit AI agenata, baziran na Anthropic engineering principima i SOMA pipeline arhitekturi. 4 mode-a: pattern selector, agent audit, reference library, DESIGN_SPEC generator. Triggeri (en/sr): design a new agent, audit my agent, which pattern should I use, create DESIGN_SPEC, review SOMA agent, kako da dizajniram agent, audituj agent, koji pattern da koristim, napravi spec za agent. Piše samo u Insights/. Ne menja agents/, system/, ili skills/. Do NOT use for debugging a broken production agent (use soma-agent-debugger) or for an enterprise/OWASP-mapped readiness sign-off (use enterprise-agent-readiness) — this skill is advisory design/pattern guidance, not a fix-it or compliance tool."
compatibility: Reads (read-only) DESIGN_SPEC.md, instincts.md, evo-log.md and related files under agents/<name>/ in the Obsidian vault for Mode 2 (Agent Audit). Mode 3 (Reference Library) requires live access to an Anthropic engineering article in-session via mcp__Claude_in_Chrome or WebFetch — it holds no cached citations and degrades to "cannot verify" if neither is available. No other MCP or tool dependency.
metadata:
  version: "0.2.0"
  owner: "buky <webdevcom01@gmail.com>"
  evaluation_status: "6 evals (prva iteracija), groundovani u eksplicitnim, imenovanim pravilima iz SKILL.md (Mode 1-4, hard rules, write boundaries, anti-hallucination disciplina). Vidi evals/evals.json i evals/README.md."
---

# Agent Architect

## What this skill does

`agent-architect` (v0.2) je savetnički skill koji spaja **Anthropic engineering best practices** sa **stvarnom SOMA arhitekturom**. Pomaže ti da:

1. **Izabereš pattern** za novi agent ili workflow (workflow vs agent)
2. **Audituješ postojećeg agenta** protiv hard rules i core principles iz ovog skill-a (sekcije "Hard rules" i "Soft rules"), sa severity skalom i skor sistemom opisanim u Mode 2
3. **Pretražiš i verifikuješ Anthropic izvor** za konkretan pattern, citat, ili design odluku — citate uvek dohvatiš iz samog članka, ovaj skill ih ne drži u kešu
4. **Generišeš DESIGN_SPEC** u tvom standardnom formatu (11 sekcija, spisak je u Mode 4)

Sve preporuke moraju da poštuju **6 hard rules iz SOMA Pass 1.5 audita** — pun spisak je u sekciji "Hard rules" niže u ovom fajlu.

> **Napomena o izvorima:** ovaj skill nema ugrađenu biblioteku citata. Sve što stavljaš pod navodnike moraš da pročitaš u samom Anthropic članku u toj sesiji (Chrome MCP ili WebFetch). Vidi sekciju "Anti-hallucination disciplina".

## Kada se NE koristi

- Za pisanje content-a (to rade SOMA agenti)
- Za debug pipeline grešaka (koristi `pipeline-debug` skill ako postoji)
- Za sync KB → Agent Studio (koristi `kb-sync` skill)
- Za logovanje run-ova (koristi `evo-log-writer` skill)
- Za debug već pokvarenog production agenta sa root-cause analizom (koristi `soma-agent-debugger`) — ovaj skill savetuje o dizajnu i radi audit protiv sopstvenih hard/soft rules, ne dijagnostikuje zašto je nešto puklo
- Za enterprise/OWASP-mapiran production readiness sign-off (koristi `enterprise-agent-readiness`) — Mode 2 audit ovde je savetnički i koristi 6 SOMA hard rules kao baseline, ne 8-dimenzioni enterprise bar

## Glavni workflow (4 mode-a)

Ovaj skill ima 4 različita načina rada. Pre nego što radiš, **uvek pitaj korisnika koji mode**, ako iz konteksta nije jasno.

### Mode 1: Pattern Selector — "Koji pattern da koristim?"

**Trigger:** korisnik opisuje novi use-case ali ne zna koju arhitekturu da izabere.

**Tvoj proces:**
1. Pitaj 4 ključna pitanja (decision tree):
   - Da li je task ponovljiv sa fixed steps? (DA → Workflow, NE → Agent)
   - Da li je task breadth-first paralelni search? (DA → razmotri Multi-agent)
   - Da li task ima jasne eval kriterijume? (DA → razmotri Evaluator-optimizer)
   - Da li task prelazi single context window? (DA → razmotri Long-running harness)
2. Pitaj: **"Za Nivo A (Claude Code/conversational) ili Nivo B (SOMA pipeline na AgentStack)?"** — to menja preporuku.
3. Daj preporuku sa **opravdanjem zašto baš taj pattern**. Ako uz to navodiš i Anthropic citat — imenuj konkretan članak iz kog citiraš i citiraj samo tekst koji možeš da pokažeš u tom članku; ne rekonstruiši citate po sećanju. Ako nemaš članak pri ruci, daj preporuku bez navodnika.
4. Eksplicitno reci ako preporuka krši neko SOMA core principle (Max 3 nodes, Memory-first, Vague-halt, Human review).

**Primer dobrog odgovora:**
> "Za multi-platform content variation, preporučujem **Parallelization (Sectioning)** pattern. Anthropic citat: 'LLMs generally perform better when each consideration is handled by a separate LLM call' (Building Effective Agents, čl. 5). U SOMA terminima: 5 paralelnih HW poziva po platformi umesto jednog generisanja sa platform list-om. ⚠️ Ovo bi povećalo cost ~5x i krši Memory-first principle ako svaki paralelni call ne čita instincts — treba odluka."

### Mode 2: Agent Audit — "Audituj mog agenta"

**Trigger:** korisnik pita "review", "audit", "šta je loše", "proveri".

**Tvoj proces:**
1. Pitaj koji agent (TI / HW / CR / SA / drugi).
2. Pročitaj relevantne fajlove iz `agents/<name>/` (DESIGN_SPEC ako postoji, instincts, evo-log, opcionalno winners-log / format-templates).
3. Uzmi baseline iz ovog skill-a: sekcija "Hard rules" (6 pravila iz SOMA Pass 1.5 audita) i sekcija "Soft rules" (SOMA core principles + trade-offovi).
4. **Definiši kriterijume audita pre skoriranja i izlistaj ih korisniku.** Ovaj skill ne nosi zatvorenu listu kriterijuma — izvedi ih iz Hard rules i Soft rules gore i iz konkretnog use-case-a agenta, pa ih eksplicitno napiši na vrhu reporta (tipično 6–8 kriterijuma). Ako korisnik ima svoju listu kriterijuma, ona ima prednost.
   - **Severity skala:** 🔴 BLOCKER (krši hard rule ili obara produkciju) / 🟠 MAJOR (krši core principle, degradira kvalitet) / 🟡 MINOR (higijena, nice-to-have).
   - **Skor sistem** (N = broj kriterijuma koje si definisao): 0 = redizajn, do ~40% = ozbiljni propusti, do ~75% = funkcionalno, iznad = zdrav.
5. Za svaki kriterijum: zabeleži score (✅/⚠️/❌), **citat dokaza iz fajlova agenta** (doslovan, sa imenom fajla), i remediation.
6. Napiši audit report u `Insights/audits/<agent-name>-<YYYY-MM-DD>.md` (ne diraj `agents/`).
7. **Format audit reporta:** Skor (uz listu korišćenih kriterijuma), Summary, Finding 1-N sa Severity, Cross-cutting observations, Recommended sprint plan, Re-audit schedule.

### Mode 3: Reference Library — "Šta Anthropic kaže o X?"

**Trigger:** korisnik pita za specifičan pattern, koncept, ili autor citat.

**Tvoj proces:**
1. **Ovaj skill nema keširanu bazu citata.** Svaki citat se dohvata iz izvora u toj sesiji — `mcp__Claude_in_Chrome__navigate` + `get_page_text` (ili WebFetch) na konkretan Anthropic engineering članak.
2. Prvo utvrdi **koji članak** pokriva pitanje, pa tek onda citiraj:
   - memory / context window / compaction / note-taking / sub-agents → "Effective Context Engineering" (Sep 29 2025)
   - pattern selection, workflow vs agent, production primeri → "Building Effective Agents"
   - skills i self-improvement → "Equipping agents with Agent Skills" (Oct 16 2025)
   - tools → "Writing effective tools for agents" (Sep 11 2025); MCP → "Code execution with MCP" (Nov 04 2025)
3. Ako ne znaš koji članak pokriva temu, reci to i predloži pretragu Anthropic engineering bloga umesto da nagađaš.
4. Daj odgovor sa:
   - Direktnim citatom iz Anthropic članka (u navodnicima, doslovan, iz teksta koji si upravo pročitao)
   - Source (URL + naslov + datum publikacije + datum kad si verifikovao)
   - SOMA mapiranje (ako relevantno)
5. **NIKAD ne izmišljaj citat i ne rekonstruiši ga po sećanju.** Ako ne možeš da dohvatiš članak: "Nemam verifikovan citat za ovo — mogu da pretražim Anthropic engineering blog kroz Chrome MCP ako želiš." Parafraza bez navodnika je dozvoljena samo ako je jasno označena kao parafraza.

### Mode 4: Design Doc Generator — "Napravi DESIGN_SPEC za novi agent"

**Trigger:** korisnik želi novi agent.

**Tvoj proces:**
1. **Struktura DESIGN_SPEC-a — 11 sekcija, tim redom:**
   1. Purpose — 1–2 rečenice, čemu agent služi
   2. Pipeline Position — gde stoji (standalone / u chainu / paralelni validator), ko ga zove i koga on zove
   3. Use Cases — UC-1 standardni, UC-2 error, UC-3 edge
   4. Tools — kb_search, web_search, ai_response, call_agent, ostalo
   5. Constraints — NEVER / ALWAYS pravila
   6. I/O Contract — ulazni i izlazni ključevi, formati, tipovi
   7. Quality Gate — per-agent self-check: šta mora da bude tačno da bi output prošao, i šta se dešava kad ne prođe (halt / flag)
   8. Evo-log Schema — polja koja agent loguje posle svakog run-a
   9. Open Questions — sve nerešeno, eksplicitno
   10. Implementation Plan — koraci do live agenta
   11. Versioning — verzija spec-a, datum, šta se menjalo
2. Pitaj 6 stvari (mapiraju se na sekcije § 1–§ 6 gore):
   - Naziv i kratak opis (1 rečenica) → § 1 Purpose
   - Pipeline pozicija (standalone / u chainu / paralelni validator) → § 2
   - Use cases (UC-1 standardni, UC-2 error, UC-3 edge) → § 3
   - Tools (kb_search, web_search, ai_response, call_agent, ostalo) → § 4
   - Constraints (NEVER / ALWAYS pravila) → § 5
   - I/O contract (keys, formats) → § 6
3. Pre generisanja, **proveri** da li dizajn poštuje 6 hard rules (sekcija "Hard rules") + 5 core principles (sekcija "Soft rules"). Ako krši — eksplicitno označi i traži potvrdu.
4. Predloži pattern koji se najbolje slaže, kroz decision tree iz Mode 1. Ako uz predlog ide i Anthropic citat, važe pravila iz Mode 3 (dohvati članak, ne citiraj po sećanju).
5. Popuni svih 11 sekcija korisničkim odgovorima; sve nezavršeno ide u § 9 Open Questions.
6. Sačuvaj u `Insights/proposed-agents/<name>-design-spec.draft.md` (sa `.draft.md` ekstenzijom — promocija u `agents/` je human decision).
7. Predoči korisniku: putanju draft fajla, koje hard rules su provarene, lista open questions.

## Hard rules (NE krši pod nijednim uslovima)

Iz SOMA Pass 1.5 audita — ovo je pun spisak:

1. **Score Analyzer NIJE deterministic** — uvek označi kao LLM-judge sa mode collapse rizikom (gpt-4.1-mini scoring gpt-4.1-mini outputa)
2. **SA NIJE u chainu** — predlog da ga dodaš je arhitekturalna promena, ne automatska preporuka
3. **Nivo A ≠ Nivo B** — uvek pitaj/označi nivo pre saveta
4. **Quality gates su per-agent self-check** — NIJE cross-agent
5. **Topologija je chain + implicit blackboard** — ne "linear pipeline"
6. **Instincts ≠ format-templates** — instincts su rules, templates su structures

## Soft rules (krši samo uz eksplicitno opravdanje)

7. SOMA core principles iz `system/soma-rules.md`: Single responsibility, Max 3 nodes (produktivnih), A2A handoff, Memory-first, Evo-log always
8. Trade-offove iz `soma-rules.md`: simplicity > capability, consistency > fresh thinking, fail-fast > best-effort, safety > autonomy

## Write boundaries (NE krši)

- Skill PIŠE samo u: `Insights/audits/`, `Insights/proposed-agents/`, `Insights/analyses/`
- Skill NE PIŠE u: `agents/`, `system/`, `shared/`, `skills/`
- Skill PIŠE sve predloge sa `.draft.md` sufiksom kad je krajnja destinacija u `agents/`
- Skill ČITA sve fajlove u vault-u kao read-only

## Anti-hallucination disciplina

Ovaj skill mora da poštuje sledeće:

1. **Svaka tvrdnja označena navodnicima mora biti doslovan citat** iz Anthropic članka koji si pročitao u toj sesiji (ne "opšte znanje", ne rekonstrukcija po sećanju)
2. **Numerički podaci** — samo iz pročitanih izvora, nikad aproksimirani i nikad iz sećanja
3. **URL-ovi** — samo oni koje si direktno fetch-ovao kroz Chrome MCP / WebFetch u istoj sesiji. Ovaj skill ne drži listu potvrđenih URL-ova; ako ne možeš da otvoriš link, ne navodi ga
4. **Kad nemaš odgovor:** eksplicitno reci "ne znam iz dostupnih izvora" umesto da generišeš
5. **Kad URL navigacija propadne** (Chrome MCP tihi fail): retryj sa explicit URL i potvrdi Title pre nego što izvučeš tekst

## Ograničenja iteracije v0.2

Ovo je v0.2. Sve što skill zna stoji u ovom fajlu — nema pratećih fajlova i nema keširane biblioteke citata. Posledice, budi iskren prema korisniku o njima:

1. **Nema ugrađene liste Anthropic citata ni potvrđenih URL-ova.** Svaki citat i link mora da se dohvati iz izvora u toj sesiji (Mode 3).
2. **Nema fiksne audit checkliste sa weights-ima.** Kriterijume izvodiš iz Hard rules / Soft rules i izlistaš ih korisniku pre skoriranja (Mode 2).
3. **Nema kataloga patterna sa production primerima.** Mode 1 daje decision tree i tvoje obrazloženje; primeri i citati se dohvataju iz članka po potrebi.

**Šta ostaje za v0.3:**

1. **Writing effective tools for agents** (čl. Sep 11 2025) — tools deep-dive
2. **Code execution with MCP** (čl. Nov 04 2025) — MCP best practices
3. **Google standardi** (ADK / A2A protocol / Vertex AI Agent Builder) — paralelni standard
4. **Mode 5: evolve** — predlaže update agenta posle nove Anthropic publikacije
5. **Dodatni audit kriterijumi iz context engineering-a:** Token budget awareness, Right altitude check, Just-in-time balance, Compaction strategy

## Self-improvement pattern

Anthropic citat iz "Equipping agents with Agent Skills" (čl. 6, Oct 16 2025):
> "As you work on a task with Claude, ask Claude to capture its successful approaches and common mistakes into reusable context and code within a skill. If it goes off track when using a skill to complete a task, ask it to self-reflect on what went wrong."

Kad ovaj skill napravi grešku ili korisnik primeti nešto što treba dopuniti, **predloži update ovog SKILL.md sa konkretnim diff-om** (koja sekcija, koji tekst se menja u koji), ali NE menjaj sam — to je human-in-the-loop princip (vidi SOMA rule "Human review queue").
