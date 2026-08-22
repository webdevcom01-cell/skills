---
name: soma-agent-debugger
description: "Specijalizovan skill za debug, fix i deploy production AgentStack agenata (SOMA pipeline). Kapitalizuje learnings iz Hook Writer 9-sprint debug-a. 4 mode-a: Investigate (root cause), Plan Fix (structured Claude Code prompt), Build Validator (deterministic quality gate), Verify Deploy (post-deploy smoke test). Triggeri: debug agent, fix agent, audit agent, agent ne radi, agent broken, production broken, build quality gate, smoke test agent, verify deploy, popravi agent, audituj agent, pukla produkcija, hocu validator, validate deploy. Anti-hallucination first: forensic verification PRE svake izmene koda."
allowed-tools:
  - Read
  - Grep
  - Bash
  - mcp__agent-studio__as_chat_with_agent
  - mcp__agent-studio-db__as_chat_with_agent
  - mcp__agent-studio__as_get_agent
  - mcp__agent-studio-db__as_get_agent
  - mcp__agent-studio__as_get_recent_executions
  - mcp__agent-studio-db__as_get_recent_executions
  - mcp__agent-studio__as_inspect_flow
  - mcp__agent-studio-db__as_inspect_flow
  - mcp__agent-studio__as_patch_node_field
  - mcp__agent-studio-db__as_patch_node_field
  - mcp__agent-studio__as_update_flow
  - mcp__agent-studio-db__as_update_flow
  - mcp__obsidian__obsidian_read_note
---

# SOMA Agent Debugger

## What this skill does

Production-grade debug + fix + deploy workflow za AgentStack agente. Izgrađen iz lessons learned tokom 9-sprint debug ciklusa Hook Writer agenta (May 2026). Spasava te od grešaka koje su nas koštale 4-6 sati ekstra rada.

**4 mode-a (workflow stages):**
1. **Investigate** — root cause analysis sa anti-hallucination disciplinom
2. **Plan Fix** — strukturisan plan + battle-tested Claude Code prompt
3. **Build Validator** — deterministic quality gate u AS flow-u
4. **Verify Deploy** — post-deploy smoke test sa real DB queries

**Kada NE koristiti:**
- Za design novog agenta (koristi `agent-architect` skill)
- Za pisanje content-a (koristi specifične content skills)
- Za skill sa low-stakes (npr. proba ili test)
- Kad nije AgentStack/SOMA agent (npr. čisto Claude Code skill)

## Hard Rules (ne krši)

Sve iz 9-sprint Hook Writer debug iskustva:

1. **Anti-hallucination first** — pre svake code/prompt izmene, verifikuj current state direktno (Read/Grep/MCP), ne oslanjaj se na audit ili memory
2. **Forensic before fix** — audit nalaz može biti stale; uvek proveri da li bug stvarno postoji u current code-u
3. **Live state IS source of truth** — vault dokumentacija je sekundarna; ako se ne slaže sa live agent prompt-om (kroz `as_get_agent`), live je pravi
4. **Deterministic > Probabilistic** — za quality gates, function node sa regex je 100x pouzdaniji od LLM self-check u prompt-u
5. **Single test = false confidence** — uvek test sa **diverse** trend types (announcement + technical + evergreen), ne jedan happy-path
6. **3-layer deploy coordination** — prompt (MCP), code (Railway), vault (docs) moraju ići po pravom redosledu da se izbegne regression window
7. **STOP points pre code change** — Claude Code mora STAJATI pre apply-a, ne smelti samostalno menjati production code

## Forensic Protocol (pre-flight)

Ovo je pre-flight checklist koji važi za sve mode-e. Mode 1 ga izvršava u celosti; ostali mode-i ga koriste pre bilo kakve izmene.

1. **Formuliši symptom** — jedna rečenica, reproducible. Ako ne možeš da ga reprodukuješ, to je prvo pitanje korisniku, ne pretpostavka.
2. **Povuci live state direktno** (nikad iz memorije, audit izveštaja ili vault-a):
   - `as_get_agent(<agent_id>)` — live system prompt kakav jeste sada
   - `as_inspect_flow(<agent_id>)` — nodes + edges kakvi jesu sada
   - `git log --oneline -10`, pa `git log -p <sumnjiv fajl>` — šta se stvarno menjalo
   - Read/Grep nad stvarnim kodom u `src/`
   - DB query za production state
3. **Cross-reference svaki raniji nalaz** (audit, vault dokument, prethodni razgovor) sa live state-om. Ako se ne slažu — live je istina (Hard Rule #3), a vault ide na listu "za ispravku", ne u dokaze.
4. **Svaki nalaz nosi izvor** — `file:line`, ime MCP alata + argumenti, ili commit hash. Nalaz bez izvora nije nalaz. Navodnici = doslovan citat iz live output-a; brojevi (line numbers, timestamps, hashes) = direktan copy-paste, nikad aproksimacija.
5. **Oboriti alternativne hipoteze eksplicitno** — za svaku odbačenu hipotezu napiši razlog i dokaz koji je obara.
6. **Ako nešto ne možeš da verifikuješ → STOP i pitaj korisnika.** Rupu u dokazima ne popunjavaj pretpostavkom.
7. **STOP pre svake destruktivne operacije** (izmena production prompt-a/flow-a, delete, force push, schema migracija) — čekaj eksplicitnu potvrdu.

## Glavni Workflow (4 mode-a)

Pre rada, **uvek pitaj korisnika koji mode** ako iz konteksta nije jasno.

### Mode 1: Investigate — "Šta ne radi?"

**Trigger:** korisnik opisuje grešku, neočekivano ponašanje, ili production issue.

**Tvoj proces:**

1. **Pitaj 4 ključna pitanja:**
   - Koji agent (ID ili ime)?
   - Šta očekivano vs. šta dešava se?
   - Kad se pojavilo (posle koje promene)?
   - Imaš li reproducible test case?

2. **Prođi Forensic Protocol** (sekcija iznad) kao pre-flight checklist — korak po korak, bez preskakanja.

3. **Izvrši forensic investigation (NE pretpostavljaj):**
   - `as_get_agent(<id>)` — current live system prompt
   - `as_inspect_flow(<id>)` — current flow nodes + edges
   - `git log --oneline -10` — recent commits
   - `git log -p <file>` za sumnjive fajlove
   - Bash inspect actual code u src/
   - DB query za production state

4. **Identifikuj root cause:**
   - Rekonstruiši execution sequence korak po korak (šta se izvršava, kojim redom, gde puca)
   - Cite file:line za svaki claim
   - Razlikuj race condition od literal duplicate
   - Razlikuj design issue od code bug

5. **Output: Investigation Report**

```markdown
## Investigation Report — <datum>

### Symptom
<reproducible description>

### Live State (verified)
- Agent ID: <id>
- Current system prompt sections: <list>
- Current flow nodes: <list sa types>
- Recent commits: <hashes + messages>

### Root Cause
<file:line citations + execution sequence korak po korak>

### Evidence
1. <verifiable fact 1 + source>
2. <verifiable fact 2 + source>
...

### Hypothesis Ruled Out
- NOT <hypothesis A>: <reason>
- NOT <hypothesis B>: <reason>

### Next Action
[Mode 2: Plan Fix | Sprint planning | Architectural decision]
```

**STOP point:** Ne idi na fix bez korisnikove potvrde root cause-a.

### Mode 2: Plan Fix — "Kako da popravim?"

**Trigger:** Posle Investigation, korisnik traži fix plan.

**Tvoj proces:**

1. **Uzmi skelet iz "Format prompt-a" (template niže u ovoj sekciji)** — svaki generisani prompt obavezno ima: Hard Rules, pre-flight verifikaciju, korake, verifikaciju posle svakog koraka, STOP point i acceptance criteria.

2. **Klasifikuj fix tip:**
   - **Prompt fix** — live update kroz MCP, instant (no deploy)
   - **Flow fix** — flow editor change, instant (no deploy)
   - **Vault fix** — documentation update, no deploy
   - **Code fix** — TypeScript change, requires PR + Railway deploy
   - **Multi-layer fix** — combination, NEEDS COORDINATION (see Hard Rule #6)

3. **Generiraj structured Claude Code prompt** sa:
   - Pre-flight verification koraci (sa očekivanim state-ovima)
   - Step-by-step implementation
   - Verification posle svakog koraka
   - STOP points pre destructive operations
   - Final acceptance criteria
   - Anti-hallucination instrukcije

4. **Sačuvaj prompt u** `Insights/fix-prompts/<agent>-<datum>-<fix-name>.md`

5. **Predoči korisniku:**
   - File path generisanog prompt-a
   - Estimated effort
   - Risk assessment (low/medium/high)
   - Rollback plan

**Format prompt-a (template):**

```markdown
# Fix Prompt: <Title>

## Hard Rules
1. <rule 1>
2. NE pretpostavljaj — uvek verifikuj pre menjanja
3. Anti-hallucination: cite each MCP/file output

### KORAK 1: Pre-flight verification
[verify current state matches expectations]

### KORAK 2: Apply Fix
[step-by-step]

### KORAK 3: Verify
[post-fix verification]

### STOP: <user decision needed>

### Final Acceptance
[checklist]
```

### Mode 3: Build Validator — "Treba mi quality gate"

**Trigger:** korisnik želi production-grade validation u AS flow-u.

**Tvoj proces:**

1. **Primeni deterministic validator pattern** — triple: `function` (validator) → `condition` (gate) → `function` (error emitter). Princip iz Hard Rule #4: provera je **kod**, ne rečenica u prompt-u. Validator ne "ocenjuje" izlaz, nego ga meri po eksplicitnim pravilima i vraća listu prekršaja; gate rutira na osnovu te liste; error emitter vraća strukturisan payload umesto tihog prolaza.

2. **Pitaj 4 specifikacijska pitanja:**
   - Šta tačno validiraš? (char limits, banned phrases, schema, etc.)
   - Šta je hard fail (block) vs soft warning?
   - Šta se desi posle block (route gde)?
   - Šta je input/output schema?

3. **Generiraj 3 node-a:**

   **Node 1: <name>-validator (function type)**
   - JavaScript code sa eksplicitnim regex/check logic
   - Vraća violations array
   - Test cases inline (cite expected pass/fail)

   **Node 2: <name>-gate (condition type)**
   - If violations.length === 0 → proceed
   - Else → route to error emitter

   **Node 3: <name>-error-emitter (function type)**
   - Strukturisan error payload (status, reason, violations, timestamp)
   - Eksplicitan output format

   Skelet za Node 1 (prilagodi pravila konkretnoj specifikaciji iz koraka 2):

   ```javascript
   const violations = [];
   // match pool = sva relevantna polja, ne samo jedno
   const pool = [input.title, input.body, input.hook].filter(Boolean).join(" ");

   // hard fail primer: limit
   if (pool.length > MAX_CHARS) {
     violations.push({ rule: "max_chars", severity: "hard", detail: pool.length });
   }
   // hard fail primer: banned phrase (eksplicitna lista svih oblika)
   for (const phrase of BANNED) {
     if (new RegExp(phrase, "i").test(pool)) {
       violations.push({ rule: "banned_phrase", severity: "hard", detail: phrase });
     }
   }
   return { violations, hardFails: violations.filter(v => v.severity === "hard") };
   ```

4. **Generiraj test cases:**
   - Happy path (5 PASS)
   - Each violation type (1 case per rule)
   - Edge cases (empty input, null fields, unicode, etc.)

5. **Output: Validator Spec sa code**

**Critical lessons primenjuju:**
- Regex sa eksplicitnom listom svih oblika reči (ne `[sed]?` shortcuts — takve skraćenice hvataju i ono što ne treba)
- Match pool kombinuje sve relevantne fields (ne samo title — provera nad jednim poljem daje false positive/negative)
- Test sa **diverse** input data (ne samo happy path)
- BLOCKED routing eksplicitan, ne silent end node

**Ako se spec primenjuje na live flow:** vidi "AgentStack MCP — provjerene napomene o alatima" niže — `as_update_flow` zamenjuje ceo flow i nema undo, pa prvo `dry_run`.

### Mode 4: Verify Deploy — "Posle deploy-a, šta?"

**Trigger:** korisnik završio merge + Railway deploy, treba production verification.

**Tvoj proces:**

1. **Post-deploy smoke test protokol** (koraci A–E ispod) — izvršava se redom, svaki korak daje eksplicitan PASS/FAIL sa citiranim output-om. Ne preskači korak zato što "logično mora da radi"; nešto što nije provereno nije PASS. Konkretne SQL upite i imena tabela izvedi iz šeme koju si pročitao u Mode 1 — ne pretpostavljaj imena kolona.

2. **Generiraj verification prompt** koji uključuje:

   **Korak A: Verify deploy je za pravi commit**
   - `git log origin/main -1` — current main HEAD
   - Railway status (kroz MCP ili CLI)
   - Cross-reference commit hash

   **Korak B: Pre-test DB baseline**
   - SQL query za current state count

   **Korak C: Run test trend kroz pipeline**
   - `as_chat_with_agent` na entry agent (npr. TI za SOMA chain)
   - Real trend (ne fake "test trend")
   - Wait for chain completion — status potvrdi kroz `as_get_recent_executions`; završen run je `COMPLETED` (validni statusi: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED — "SUCCESS" ne postoji)

   **Korak D: DB verification**
   - SQL queries za novu entry
   - Check schema (correct timestamps, IDs, formats)
   - Check count (no duplicates, no silent skips)

   **Korak E: Acceptance criteria**
   - Eksplicitno PASS/FAIL po svakoj proveri
   - Cite output, ne pretpostavljaj

3. **Risk assessment:**
   - Sve PASS → production-ready ✅
   - Mali FAIL → rollback candidate ⚠️
   - Veliki FAIL → urgent rollback + debug ❌

**Template za verification report:**

```
Post-Deploy Verification — <datum>

Korak A (deploy correctness): ✅ / ❌
- Commit on main: <hash>
- Railway active: <hash>
- Match: ✅ / ❌

Korak B (baseline): <count> records before test

Korak C (pipeline run): ✅ / ❌
- Trigger: <test trend>
- Chain completed in: <ms>

Korak D (DB verification):
- New entry created: ✅ / ❌
- Schema correct: ✅ / ❌
- No duplicates: ✅ / ❌
- All expected fields populated: ✅ / ❌

OVERALL: ✅ PASS / ⚠️ WARN / ❌ FAIL
Recommendation: <production-ready / rollback / debug>
```

## Write Boundaries (NE krši)

- Skill **PIŠE** samo u: `Insights/fix-prompts/`, `Insights/investigations/`, `Insights/validators/`
- Skill **NE PIŠE** u: `agents/`, `system/`, `src/`, `prompts/`
- Skill **NE APPLIES** code changes — samo generiše prompts za Claude Code
- Skill **ČITA** sve fajlove kao read-only

## Anti-Hallucination Discipline

Ovaj skill **mora** da poštuje Forensic Protocol (sekcija iznad) u svakom mode-u, plus:

1. Svaka tvrdnja označena navodnicima = doslovan citat iz live source-a
2. Numerički podaci (line numbers, timestamps, hashes) = direktan output, nikad aproksimirani
3. Cross-reference svaki audit nalaz sa current code state pre fix-a
4. Ako nešto ne možeš da verifikuješ → STOP + pitaj korisnika
5. STOP points pre destructive operations (delete, force push, schema migrations)

## AgentStack MCP — provjerene napomene o alatima

Ove činjenice su provjerene na živim tool schema-ma. Kad se kose sa nečim što piše u vault-u ili audit-u, važi ovo.

- **`as_patch_node_field`** — parametri su tačno: `agent_id`, `agent_name`, `field_name`, `field_value`, `node_id`. `field_value` se parsira kao JSON: string mora imati unutrašnje navodnike (`'"my-value"'`), broj ne (`42`).
- **`as_get_recent_executions`** — `status` prima samo: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`. Nema `SUCCESS`.
- **`as_update_flow`** — zamenjuje **ceo** flow i **nema undo**. Podržava `dry_run` — uvek prvo `dry_run`, pa tek onda pravi poziv. Za izmenu jednog polja koristi `as_patch_node_field`, ne `as_update_flow`.
- **`obsidian_read_note`** — default `line_limit` je 300 (max 500) i vraća `has_more` / `next_line_offset`. Ako je `has_more` true, nisi pročitao ceo dokument — nastavi od `next_line_offset` pre nego što išta tvrdiš o sadržaju.

## Šta NIJE u v0.1 (planirano za v0.2)

- Sprint orchestrator mode (multi-sprint workflow)
- Mixed-state production window detection
- Automatic rollback script generator
- Cross-agent dependency mapping
- Integration sa GitHub Actions
- Cost analysis za predloženi fix

## Versioning

| Verzija | Datum | Šta |
|---|---|---|
| v0.1 | 2026-05-29 | Initial drop: 4 mode-a, hard rules, forensic protokol, validator pattern, post-deploy smoke test |
