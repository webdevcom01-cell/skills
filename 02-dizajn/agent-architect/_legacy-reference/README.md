# agent-architect

Claude Code skill koji spaja Anthropic engineering best practices sa stvarnom SOMA arhitekturom. Pomaže u dizajnu, auditu i dokumentaciji AI agenata.

**Verzija:** v0.2
**Datum (v0.1):** 25 May 2026
**Datum (v0.2):** 27 May 2026
**Autor:** Buky + Claude (kroz iterativni proces, vault audit + 9 Anthropic članaka — 8 originalnih + Context Engineering Klaster B)

---

## Šta ovo radi

Ovaj skill ima 4 mode-a:

1. **Pattern Selector** — savetuje koji od 6 Anthropic patterna da koristiš za novi use-case
2. **Agent Audit** — audituje postojećeg SOMA agenta po 8 kriterijuma, piše audit report u `Insights/audits/`
3. **Reference Library** — odgovara na pitanja o specifičnim patternima, sa direktnim citatima iz Anthropic članaka
4. **Design Doc Generator** — generiše DESIGN_SPEC predlog za novi agent, u `Insights/proposed-agents/`

---

## Struktura skill-a (v0.2)

```
agent-architect/
├── SKILL.md                       ← core trigger logika (loads always)
├── README.md                      ← ovaj fajl
└── reference/
    ├── patterns.md                ← 6 Anthropic patterna + SOMA mapping
    ├── soma-truth.md              ← stvarna SOMA arhitektura, 6 hard rules
    ├── audit-checklist.md         ← (v0.2 NEW) 8 kriterijuma sa weights, severity, primerima
    ├── design-spec-template.md    ← (v0.2 NEW) DESIGN_SPEC template, 11 sekcija
    ├── anthropic-citations.md     ← (v0.2 NEW) ~45 konsolidovanih citata, verification checklist
    └── context-engineering.md     ← (v0.2 NEW) Klaster B sinteza (attention budget, just-in-time, compaction, note-taking, sub-agents)
```

**Progressive disclosure** (Anthropic Skills pattern): SKILL.md je mali i uvek u sistem prompt-u; reference fajlovi se učitavaju **samo kad Claude proceni da su mu potrebni** za konkretan task.

**Šta-učitati-kada:**

| Mode | Reference fajlovi koji se učitavaju |
|---|---|
| 1: Pattern Selector | `patterns.md` (uvek), `context-engineering.md` (ako je pitanje o memory/context) |
| 2: Agent Audit | `audit-checklist.md` (uvek), `soma-truth.md` (baseline), `patterns.md` (za findings citate) |
| 3: Reference Library | `anthropic-citations.md` (PRVO), `context-engineering.md` ili `patterns.md` (zavisno od pitanja) |
| 4: DESIGN_SPEC Generator | `design-spec-template.md` (uvek), `soma-truth.md` (rule check), `patterns.md` (pattern preporuka), `anthropic-citations.md` (opravdanja) |

---

## Instalacija

Skill mora biti dostupan Claude Code-u kao user skill. Dve opcije:

### Opcija A: User skills folder (preporučeno)

Kopiraj ceo `agent-architect/` folder u Claude Code user skills lokaciju (proveri u Claude Code settings gde je tačno na tvom sistemu — obično `~/.claude/skills/` ili sličnoj putanji).

### Opcija B: Plugin sistem

Ako koristiš plugin manager za Claude Code, zip-uj ceo folder sa `.skill` ekstenzijom i instaliraj kao plugin.

### Test

Nakon instalacije, u sledećoj Claude Code sesiji probaj:

```
buky: "audit my hook-writer agent"
```

Claude bi trebao da prepozna `agent-architect` skill iz description-a i krene sa Mode 2 (Agent Audit).

---

## Šta skill SME da radi (boundaries)

**ČITA:**
- Sve fajlove u vault-u (`agents/`, `system/`, `Insights/`, `shared/`, `skills/`)
- Anthropic engineering blog kroz Chrome MCP (kad treba dodatni citat)

**PIŠE:**
- `Insights/audits/<agent-name>-<YYYY-MM-DD>.md` — audit reports
- `Insights/proposed-agents/<name>-design-spec.draft.md` — predlozi novih agenata (sa `.draft.md` ekstenzijom)
- `Insights/analyses/<topic>-<YYYY-MM-DD>.md` — pattern analize

**NIKAD ne piše u:**
- `agents/` (tu su pravi agent fajlovi koje Buky kontroliše)
- `system/` (config i pravila)
- `shared/` (deljen vocabular)
- `skills/` (drugi user skill-ovi)

---

## Hard rules (NE krši)

Sve iz SOMA Pass 1.5 audit-a. Wording je sinhronizovan sa SKILL.md i `reference/soma-truth.md` §0:

1. **Score Analyzer NIJE deterministic sensor** — uvek označi kao LLM-judge sa mode collapse rizikom (gpt-4.1-mini scoring gpt-4.1-mini outputa)
2. **SA NIJE u chainu** — predlog dodavanja je arhitekturalna promena, ne automatska preporuka
3. **Nivo A (Claude Code) ≠ Nivo B (SOMA pipeline)** — uvek pitaj/označi nivo pre saveta
4. **Quality gates su per-agent self-check** — NISU cross-agent
5. **Topologija je chain + implicit blackboard** — ne "linear pipeline"
6. **Instincts ≠ format-templates** — instincts su rules, templates su structures

Autoritativna lista u `reference/soma-truth.md` §0. Detalji po pravilu razbacani u soma-truth.md sekcijama.

---

## Anti-hallucination disciplina

Sve tvrdnje označene navodnicima moraju biti **doslovni citati** iz reference fajlova ili izvora pročitanih u istoj sesiji. Nikakvo "opšte znanje".

Numerički podaci (90.2% multi-agent boost, $124.70 DAW build, itd.) — samo iz pročitanog teksta, nikad aproksimirani.

URL-ovi — samo verifikovani u `reference/anthropic-citations.md` bibliografiji (single source of truth od v0.2). Backup lista u `reference/patterns.md` sekcija 8.

Kad nemam odgovor: **"ne znam iz dostupnih izvora"**, ne improvizuj.

---

## Šta je dodato u v0.2 (vs v0.1)

1. ✅ **Klaster B integrisan** — `context-engineering.md` sa direktnim citatima iz "Effective context engineering for AI agents" (Sep 29 2025). Pokriva attention budget, context rot, just-in-time retrieval, compaction, structured note-taking, sub-agent architectures.
2. ✅ **`audit-checklist.md` razdvojen** — više nije embedovan u SKILL.md Mode 2. Sadrži severity skalu (🔴 BLOCKER / 🟠 MAJOR / 🟡 MINOR), good/bad primere, audit report format template.
3. ✅ **`design-spec-template.md` razdvojen** — više nije embedovan u SKILL.md Mode 4. 11 sekcija: Purpose, Pipeline Position, Use Cases, Tools, Constraints, I/O Contract, Quality Gate, Evo-log Schema, Open Questions, Implementation Plan, Versioning.
4. ✅ **`anthropic-citations.md` konsolidovan** — ~45 verifikovanih citata iz 9 članaka, organizovano po 15 sekcija, sa verification checklist-om.

## Šta NE radi (granice v0.2 iteracije)

- **NE pokriva Tools deep-dive** (čl. "Writing effective tools for agents", Sep 11 2025) — planirano za v0.3
- **NE pokriva Code execution sa MCP** (čl. Nov 04 2025) — planirano za v0.3
- **NE pokriva Google standarde** (ADK / A2A protocol / Vertex AI Agent Builder) — planirano za v0.3 kao paralelni standard
- **NEMA Mode 5: "evolve"** — predlog update-a postojećeg agenta na osnovu nove Anthropic publikacije — planirano za v0.3
- **NEMA Audit Kriterijume 9-12** (Token budget, Right altitude, Just-in-time balance, Compaction strategy) — predloženi u `context-engineering.md`, biće dodati u v0.3 audit-checklist
- **NE menja sam sebe** — kad uoči potrebu za update reference, predlaže diff Buky-ju (human-in-the-loop princip)

---

## Mapa vrednosti

Šta donosi (kompleksno) sintetisano iz 9 Anthropic članaka + tvog vault-a:

| Input | Output |
|---|---|
| Nejasna ideja za novi agent | Pattern preporuka sa Anthropic citatom + SOMA constraints check |
| Postojeći SOMA agent | 8-kriterijuma audit report sa severity skalom + sprint plan template |
| Pitanje "kako Anthropic radi X" | Direktan citat sa source URL-om (iz konsolidovane liste ~45 citata) |
| Spremna ideja za novi agent | DESIGN_SPEC draft sa 11 sekcija (uključujući Quality Gate, Evo-log Schema, Open Questions) |
| Pitanje "kako da menadžujem context u dugotrajnom task-u" | Tri tehnike (compaction, note-taking, sub-agents) sa decision matrix |

---

## Sledeći koraci

1. **Test v0.2** sa konkretnim use-case-ovima:
   - Mode 2: audit Hook Writer agenta (najviše vault sadržaja)
   - Mode 4: generate DESIGN_SPEC za Score Analyzer (sledeći SOMA agent koji još nije izgrađen)
   - Mode 3: testiraj quote retrieval kroz nova citations fajl
2. **Feedback loop:** kad skill napravi grešku ili propusti nešto, dodaj observation u vault note i razmotri update reference fajlova
3. **v0.3 plan:**
   - **Writing effective tools for agents** (čl. Sep 11 2025) — tools deep-dive
   - **Code execution with MCP** (čl. Nov 04 2025) — MCP best practices
   - **Google standardi** (ADK / A2A protocol / Vertex AI Agent Builder) — paralelni standard kao `reference/google-standards.md`
   - **Mode 5: "evolve"** — predlaže update agenta posle nove publikacije
   - **Audit Kriterijumi 9-12** — Token budget, Right altitude, Just-in-time balance, Compaction strategy (predloženi u context-engineering.md)

---

## Izvori

**9 Anthropic engineering postova** (Dec 2024 – Apr 2026), konsolidovani u:
- `reference/anthropic-citations.md` (single source of truth, ~45 verifikovanih citata, v0.2)
- `reference/patterns.md` (citati u kontekstu pattern-a, distribuirani, v0.1)
- `reference/context-engineering.md` (Klaster B sinteza, v0.2 NEW)

**Predhodne sinteze (referenca):**
- `/Users/buda007/Desktop/agent-studio/anthropic-klaster-A-E-sinteza.md` (Klaster A+E sa direktnim citatima)
- `/Users/buda007/Desktop/agent-studio/soma-pass1-5-sinteza.md` (Pass 1.5 implikacije)

**Tvoj vault:**
- `/Users/buda007/Desktop/agent-studio-vault/system/soma-rules.md`
- `/Users/buda007/Desktop/agent-studio-vault/system/config.md`
- `/Users/buda007/Desktop/agent-studio-vault/Insights/code-as-agent-harness/` (Pass 1 + Pass 1.5)
- `/Users/buda007/Desktop/agent-studio-vault/agents/*/` (4 SOMA agenta: TI, HW, CR, SA)

---

## Changelog

| Verzija | Datum | Šta se promenilo |
|---|---|---|
| v0.1 | 2026-05-25 | Inicijalni drop: SKILL.md + patterns.md + soma-truth.md + README.md. Audit checklist i DESIGN_SPEC template embedovani u SKILL.md. Citati distribuirani u patterns.md. |
| v0.2 | 2026-05-27 | Razdvojeni audit-checklist.md, design-spec-template.md, anthropic-citations.md. Dodato context-engineering.md (Klaster B). SKILL.md Mode 2/3/4 update-ovani da koriste nove fajlove. README struktura ažurirana. |
