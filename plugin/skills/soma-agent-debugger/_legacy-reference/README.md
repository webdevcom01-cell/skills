# soma-agent-debugger

Claude Code skill koji kapitalizuje sve learnings iz 9-sprint Hook Writer debug ciklusa (May 26-29, 2026). Spasava te od grešaka koje su nas koštale 4-6 sati ekstra rada.

**Verzija:** v0.1
**Datum:** 2026-05-29
**Autor:** Buky + Claude (kroz 9-sprint live debug)

---

## Šta ovo radi

4 mode-a za production-grade agent debugging i deployment:

1. **Investigate** — root cause analysis sa anti-hallucination disciplinom
2. **Plan Fix** — strukturisan plan + battle-tested Claude Code prompt
3. **Build Validator** — deterministic quality gate u AS flow-u (3-node pattern)
4. **Verify Deploy** — post-deploy smoke test sa real DB queries

## Struktura skill-a

```
soma-agent-debugger/
├── SKILL.md                              ← core trigger logika
├── README.md                             ← ovaj fajl
└── reference/
    ├── lessons-learned.md                ← 9 lekcija iz Sprint 1-3
    ├── forensic-protocol.md              ← pre-flight verification checklist
    ├── prompt-templates.md               ← 5 battle-tested Claude Code prompts
    ├── deterministic-validator-pattern.md ← function + condition + error-emitter triple
    ├── post-deploy-verification.md       ← SQL queries + acceptance criteria
    └── mcp-cookbook.md                   ← AgentStack MCP tool patterns
```

**Progressive disclosure** (Anthropic Skills pattern): SKILL.md je mali i uvek u system prompt-u; reference fajlovi se učitavaju on-demand.

## Instalacija

### Opcija A: Manual copy

```bash
cp -r /Users/buda007/Desktop/agent-studio/soma-agent-debugger ~/.claude/skills/
```

### Opcija B: Install script

```bash
bash /Users/buda007/Desktop/agent-studio/soma-agent-debugger-install.sh
```

### Test

Posle instalacije, u Claude Code-u probaj:

```
debug my hook-writer agent
# Or:
production je pukla, pomozi
# Or:
hocu validator za quality gate
```

Claude Code bi trebao da prepozna `soma-agent-debugger` skill iz description-a.

## Kada koristiti

- ✅ Debug postojećih AgentStack/SOMA agenata
- ✅ Plan fix-ova za production bugs
- ✅ Build deterministic quality validators
- ✅ Post-deploy verification

## Kada NE koristiti

- ❌ Za design novog agenta — koristi `agent-architect` skill
- ❌ Za pisanje content-a — koristi specifične content skills
- ❌ Za skill koji nije AgentStack/SOMA agent (npr. čisto Claude Code skill)
- ❌ Za low-stakes proba ili test agente

## 9 Lessons Learned (TL;DR)

1. **Pre-Flight Forensic** — verifikuj current state pre svakog fix-a
2. **Live State = Truth** — vault docs su sekundarni
3. **Deterministic > Probabilistic** — function node, ne prompt instruction
4. **Single Test = False Confidence** — minimum 3 diverse test cases
5. **3-Layer Deploy Coordination** — code first, prompt second, docs third
6. **Regex Edge Cases** — eksplicitna lista forme, ne shorthand
7. **Hybrid Consolidation** — mapiraj postojeća audit-a, ne novi od nule
8. **STOP Points** — pre apply, pre commit, pre push, pre merge
9. **Anti-Hallucination** — cite, verify, honestly admit

Vidi `reference/lessons-learned.md` za full details i konkretne primere.

## Šta skill SME da radi (boundaries)

**ČITA:**
- Sve fajlove u repo (`src/`, `prompts/`, `prisma/`, etc.)
- Vault fajlove (DESIGN_SPEC, instincts, evo-log)
- Live agent state kroz MCP (`as_get_agent`, `as_inspect_flow`)
- Production DB (read-only queries)
- Git history

**PIŠE:**
- `Insights/fix-prompts/<name>-<date>.md` — generisani Claude Code prompts
- `Insights/investigations/<agent>-<date>.md` — forensic reports
- `Insights/validators/<name>-spec.md` — validator specs

**NIKAD ne piše u:**
- `agents/` (vault — Buky kontroliše)
- `system/` (vault config)
- `src/` (production code — Claude Code menja)
- `prompts/` (live agent prompts — kroz MCP)

**NE APPLIES code changes** — samo generiše prompts za Claude Code da apply-uje sa user-ovim OK.

## Hard Rules (NE krši)

1. **Anti-hallucination first** — uvek verifikuj kroz tool calls
2. **Forensic before fix** — audit nalaz može biti stale
3. **Live state IS source of truth** — ne pretpostavljaj iz docs
4. **Deterministic > Probabilistic** — za production quality gates
5. **Single test = false confidence** — minimum 3 diverse tests
6. **3-layer deploy coordination** — code first, prompt second, docs third
7. **STOP points pre code change** — Claude Code mora čekati user OK

## Mapa Vrednosti

| Input | Output |
|---|---|
| "agent ne radi" | Forensic report sa root cause + structured fix prompt |
| "treba mi validator" | 3-node spec sa JavaScript code + diverse test cases |
| "deploy gotov, šta sad" | Verification queries + acceptance criteria + report |
| "audituj agent" | Cross-referenced findings (live vs docs) + plan |

## Sledeći koraci

1. **Test sa real use case** — debug-uj sledeći SOMA agent (CR ili SA)
2. **Iteracije** — kad skill napravi grešku, dodaj observation u `reference/lessons-learned.md`
3. **v0.2 plan:**
   - Sprint orchestrator mode (multi-sprint workflow)
   - Mixed-state production window detector
   - Automatic rollback script generator
   - Cross-agent dependency mapping

## Self-Improvement Pattern

Po Anthropic Equipping Skills:

> "As you work on a task with Claude, ask Claude to capture its successful approaches and common mistakes into reusable context and code within a skill."

Kad ovaj skill napravi grešku ili korisnik primeti nešto što treba dopuniti, **predloži update reference/<file>.md sa konkretnim diff-om**, ali ne menjaj sam — human-in-the-loop princip.

## Izvori

Sve naučeno tokom Hook Writer 9-sprint debug:
- Sprint 1: 4 fixes (security, memory, quality gate)
- Sprint 2 Tok A: Objective quality gate
- Sprint 2.5: Deterministic hw-validator
- Sprint 2 Tok B: 4 code fixes (deployed PR #141)
- Sprint 2.6: Validator angle_used fix
- Sprint 3 Part A: L-1 vault + F8 error handling
- Sprint 3 Part A.5: L-1 agent-studio repo
- Sprint 3 Part B: Duplicate bug fix (deployed PR #142)
- Sprint 3 Part C: Documentation sync

**Real production agent:** Hook Writer (cmp832hkithbhj9suiqgmjqpw) na Agent Studio platformi (Railway-hosted).

## Changelog

| Verzija | Datum | Šta |
|---|---|---|
| v0.1 | 2026-05-29 | Initial drop. SKILL.md + 5 reference fajlova + README. Capitalizes 9-sprint Hook Writer learnings. |
