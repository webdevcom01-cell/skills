# soma-skills

Plugin verzija repozitorijuma [`webdevcom01-cell/skills`](https://github.com/webdevcom01-cell/skills) — 50 Claude Skills organizovanih kroz 8-fazni razvojni pipeline, od prve ideje do gotovog, isporučenog rešenja (ideja → projekat → rešenje).

Ovaj `plugin/` folder je **generisan** iz izvornih skillova u glavnim fazonim folderima repozitorijuma (`01-ideja-validacija/` do `08-drugi-projekti/`). Fazna organizacija je izvor istine za dokumentaciju i razvoj; ovaj folder samo pakuje kopije svih skillova u format koji Claude Cowork i Claude Code očekuju za instalaciju plugina (`skills/<ime>/SKILL.md`, ravno, bez faznih podfoldera). Kad se neki skill promeni u izvornom folderu, ovaj folder treba ponovo generisati pre sledeće instalacije.

## Instalacija

**Claude Cowork:** otpremi `.plugin` fajl (zip ovog foldera) — pojaviće se kartica u razgovoru sa dugmetom za prihvatanje. Instalira sve skillove odjednom, bez pojedinačnog upload-a i bez rizika od "already in use" grešaka po imenu.

**Claude Code:** instalacija plugina prati isti manifest (`.claude-plugin/plugin.json`), obično preko marketplace repozitorijuma — detalje proveriti na docs.claude.com pre prve instalacije sa CLI-ja.

## MCP zavisnosti (Agent Studio, Obsidian)

Devet operativnih skillova (faze 04–06: `pipeline-debug`, `soma-memory-fix`, `soma-agent-cleanup`,
`enterprise-agent-readiness`, `memory-integrity-gate`, `instincts-updater`, `kb-sync`,
`soma-distribution`, `soma-model-preflight`) imaju `allowed-tools` ograničen na Agent Studio MCP
(`as_*`) i/ili Obsidian MCP alate. Da bi radili, ti serveri moraju biti povezani u sesiji koja
poziva skill — `allowed-tools` samo ograničava, ne dodaje pristup.

Ime pod kojim je Agent Studio MCP server povezan zavisi od okruženja — na istom sistemu viđena su
dva različita imena (`agent-studio` u nekim Claude Code konfiguracijama, `agent-studio-db` preko
Cowork/Desktop bridge konekcije). Zato `allowed-tools` za svih devet skillova namerno navodi OBA
prefiksa za svaki `as_*` alat (`mcp__agent-studio__as_X` i `mcp__agent-studio-db__as_X`) — skill
radi bez obzira pod kojim je od ta dva imena server povezan. Ako je kod tebe povezan pod trećim
imenom, skill neće imati pristup — dodaj taj prefiks ručno u `allowed-tools` tog skilla, ili
preimenuj konekciju u jedno od ova dva.

Obsidian MCP server se očekuje pod imenom `obsidian`.

## Skillovi po fazama

### 01 — Ideja / validacija
`brainstorming-buddy`, `deep-research`, `roast`, `skill-research`

### 02 — Dizajn
`agent-architect`, `prompt-engineer-pro`

### 03 — Izrada
`agent-scaffolder`, `mcp-builder`, `rls-rollout`, `safe-agent-builder`, `session-start-hook`, `skill-creator-pro`

### 04 — Test / QA
`agent-health-check`, `enterprise-agent-readiness`, `pipeline-debug`, `pipeline-input-validator`, `soma-agent-debugger`, `soma-eval-harness`, `soma-model-preflight`

### 05 — Isporuka
`agent-delivery-pack`, `prospect-discovery`, `soma-distribution`, `team-enablement-program`

### 06 — Rad / održavanje
`agent-dependency-mapper`, `automation-triage`, `evo-log-writer`, `instincts-updater`, `kb-sync`, `memory-integrity-gate`, `obsidian-knowledge-logger`, `plugin-sync`, `skill-lint`, `skill-security-review`, `soma-agent-cleanup`, `soma-memory-fix`, `soma-performance-review`, `soma-run`, `soma-score-analyzer`, `winners-log-logger`

### 07 — Izlazni formati
`algorithmic-art`, `brand-guidelines`, `canvas-design`, `doc-coauthoring`, `internal-comms`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`

### 08 — Drugi projekti
`geo-prompt-library`, `morning`, `tender-projekat`

**Ukupno: 50 skillova.**

`market-research-navigator` (faza 01) i `system-teardown` (faza 02) postoje u faznim folderima
repoa ali su namerno izostavljeni iz ovog plugina — njihov `LICENSE.txt` je "all rights reserved"
bez dozvole za redistribuciju, pa ne mogu ući u paket koji se deli sa drugima.

### Skillovi koji se ne pozivaju sami

Dva skilla iz kataloga iznad nose `disable-model-invocation: true` — namerno se **ne** pojavljuju u listi koju model sam pretražuje i biraju se isključivo eksplicitnim pozivom po imenu:

- `roast` (faza 01) — adversarijalno "veće persona" koje traži fatalne mane u ideji pre nego što se u nju uloži vreme ili novac.
- `rls-rollout` (faza 03) — fazni rollout Postgres Row-Level Security-ja; generiše SQL migracije, nikad ih sam ne primenjuje.

Ovo je svesna odluka, ne propust: oba su skupa ili invazivna da bi se okidala automatski. Posledica je da se ne mogu otkriti organski — pozovi ih po imenu.
