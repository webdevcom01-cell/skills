# soma-skills

Plugin verzija repozitorijuma [`webdevcom01-cell/skills`](https://github.com/webdevcom01-cell/skills) — 53 Claude Skills organizovanih kroz 8-fazni razvojni pipeline, od prve ideje do gotovog, isporučenog rešenja (ideja → projekat → rešenje).

Ovaj `plugin/` folder je **generisan** iz izvornih skillova u glavnim fazonim folderima repozitorijuma (`01-ideja-validacija/` do `08-drugi-projekti/`). Fazna organizacija je izvor istine za dokumentaciju i razvoj; ovaj folder samo pakuje kopije svih skillova u format koji Claude Cowork i Claude Code očekuju za instalaciju plugina (`skills/<ime>/SKILL.md`, ravno, bez faznih podfoldera). Kad se neki skill promeni u izvornom folderu, ovaj folder treba ponovo generisati pre sledeće instalacije.

## Instalacija

**Claude Cowork:** otpremi `.plugin` fajl (zip ovog foldera) — pojaviće se kartica u razgovoru sa dugmetom za prihvatanje. Instalira sve skillove odjednom, bez pojedinačnog upload-a i bez rizika od "already in use" grešaka po imenu.

**Claude Code:** instalacija plugina prati isti manifest (`.claude-plugin/plugin.json`), obično preko marketplace repozitorijuma — detalje proveriti na docs.claude.com pre prve instalacije sa CLI-ja.

## Skillovi po fazama

### 01 — Ideja / validacija
`brainstorming-buddy`, `deep-research`, `market-research-navigator`, `roast`, `skill-research`

### 02 — Dizajn
`agent-architect`, `prompt-engineer-pro`, `system-teardown`

### 03 — Izrada
`agent-scaffolder`, `mcp-builder`, `rls-rollout`, `safe-agent-builder`, `session-start-hook`, `skill-creator-pro`

### 04 — Test / QA
`agent-health-check`, `enterprise-agent-readiness`, `pipeline-debug`, `pipeline-input-validator`, `soma-agent-debugger`, `soma-eval-harness`, `soma-model-preflight`

### 05 — Isporuka
`agent-delivery-pack`, `prospect-discovery`, `soma-distribution`, `team-enablement-program`

### 06 — Rad / održavanje
`agent-dependency-mapper`, `automation-triage`, `evo-log-writer`, `instincts-updater`, `kb-sync`, `memory-integrity-gate`, `obsidian-knowledge-logger`, `soma-agent-cleanup`, `soma-memory-fix`, `soma-performance-review`, `soma-run`, `soma-score-analyzer`, `winners-log-logger`

### 07 — Izlazni formati
`algorithmic-art`, `brand-guidelines`, `canvas-design`, `doc-coauthoring`, `docx`, `internal-comms`, `pdf`, `pptx`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`, `xlsx`

### 08 — Drugi projekti
`geo-prompt-library`, `morning`, `tender-projekat`

**Ukupno: 53 skilla.**
