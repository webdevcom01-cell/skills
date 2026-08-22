# soma-ops-skills

Agent Studio / AgentStack / SOMA content pipeline (TI → HW → CR → Score Analyzer) i konsalting
sloj iz repozitorijuma [`webdevcom01-cell/skills`](https://github.com/webdevcom01-cell/skills) —
27 Claude Skills koji zahtevaju tu infrastrukturu (Agent Studio MCP, specifičan Obsidian vault sa
evo-logs/instincts/winners-log) ili su izgrađeni oko konsalting rada koji tu infrastrukturu
koristi. Korisno tebi i bilo kome ko radi na istom Agent Studio/SOMA sistemu — ne generički
koristan van tog konteksta.

Sestrinski paket **[`plugin/`](../plugin/README.md)** ("soma-skills") sadrži 21 opšte-upotrebljiv
skill bez ove zavisnosti. Podela je urađena 22.08.2026 da bi opšti toolkit mogao da se instalira i
koristi nezavisno od Agent Studio infrastrukture — vidi §12/§13 u internom D1 izveštaju za puno
obrazloženje podele.

Ovaj `plugin-soma-ops/` folder je **generisan** iz izvornih skillova u faznim folderima repoa
(`01-ideja-validacija/` do `08-drugi-projekti/`). Fazna organizacija je izvor istine; ovaj folder
samo pakuje kopije skillova u format koji Claude Cowork i Claude Code očekuju za instalaciju
plugina (`skills/<ime>/SKILL.md`, ravno, bez faznih podfoldera). Kad se neki skill promeni u
izvornom folderu, ovaj folder treba ponovo generisati pre sledeće instalacije.

## Instalacija

**Claude Cowork:** otpremi `.plugin` fajl (zip ovog foldera) — pojaviće se kartica u razgovoru sa
dugmetom za prihvatanje.

**Claude Code:** instalacija plugina prati isti manifest (`.claude-plugin/plugin.json`), obično
preko marketplace repozitorijuma — detalje proveriti na docs.claude.com pre prve instalacije sa
CLI-ja.

## MCP zavisnosti (Agent Studio, Obsidian)

Devet operativnih skillova (`pipeline-debug`, `soma-memory-fix`, `soma-agent-cleanup`,
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

Ostali skillovi u ovom paketu (npr. `agent-architect`, `prospect-discovery`,
`team-enablement-program`) ne zahtevaju MCP pristup direktno, ali su sadržajno/kontekstualno
vezani za Agent Studio agente i konsalting rad koji se oko njih obavlja.

## Skillovi po fazama

### 02 — Dizajn
`agent-architect`

### 03 — Izrada
`agent-scaffolder`, `rls-rollout`, `safe-agent-builder`

### 04 — Test / QA
`agent-health-check`, `enterprise-agent-readiness`, `pipeline-debug`, `pipeline-input-validator`, `soma-agent-debugger`, `soma-eval-harness`, `soma-model-preflight`

### 05 — Isporuka
`agent-delivery-pack`, `prospect-discovery`, `soma-distribution`, `team-enablement-program`

### 06 — Rad / održavanje
`agent-dependency-mapper`, `automation-triage`, `evo-log-writer`, `instincts-updater`, `kb-sync`, `memory-integrity-gate`, `soma-agent-cleanup`, `soma-memory-fix`, `soma-performance-review`, `soma-run`, `soma-score-analyzer`, `vault-schema-reference`, `winners-log-logger`

**Ukupno: 28 skillova.**

### Skillovi koji se ne pozivaju sami

Jedan skill iz kataloga iznad nosi `disable-model-invocation: true` — namerno se **ne** pojavljuje
u listi koju model sam pretražuje i bira se isključivo eksplicitnim pozivom po imenu:

- `rls-rollout` (faza 03) — fazni rollout Postgres Row-Level Security-ja; generiše SQL migracije,
  nikad ih sam ne primenjuje.

Ovo je svesna odluka, ne propust: skup je i invazivan da bi se okidao automatski. Posledica je da
se ne može otkriti organski — pozovi ga po imenu.
