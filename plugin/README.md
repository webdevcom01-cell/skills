# soma-skills

Opšti toolkit iz repozitorijuma [`webdevcom01-cell/skills`](https://github.com/webdevcom01-cell/skills) — 21 Claude Skill koji **ne zavise** od Agent Studio / AgentStack / SOMA content pipeline / ličnog Obsidian vault-a, organizovanih kroz 8-fazni razvojni pipeline (ideja → projekat → rešenje). Koristan bilo kom Claude Code/Cowork korisniku.

Sestrinski paket **[`plugin-soma-ops/`](../plugin-soma-ops/README.md)** sadrži 28 skillova specifičnih za Agent Studio/AgentStack/SOMA pipeline i konsalting rad — instaliraj ga posebno ako ti treba ta funkcionalnost. Podela je urađena 22.08.2026 (vidi §12/§13 u internom D1 izveštaju) da bi ovaj paket ostao instalabilan i koristan i van tvoje sopstvene Agent Studio infrastrukture.

Ovaj `plugin/` folder je **generisan** iz izvornih skillova u glavnim fazonim folderima repozitorijuma (`01-ideja-validacija/` do `08-drugi-projekti/`). Fazna organizacija je izvor istine za dokumentaciju i razvoj; ovaj folder samo pakuje kopije skillova u format koji Claude Cowork i Claude Code očekuju za instalaciju plugina (`skills/<ime>/SKILL.md`, ravno, bez faznih podfoldera). Kad se neki skill promeni u izvornom folderu, ovaj folder treba ponovo generisati pre sledeće instalacije.

## Instalacija

**Claude Cowork:** otpremi `.plugin` fajl (zip ovog foldera) — pojaviće se kartica u razgovoru sa dugmetom za prihvatanje. Instalira sve skillove odjednom, bez pojedinačnog upload-a i bez rizika od "already in use" grešaka po imenu.

**Claude Code:** instalacija plugina prati isti manifest (`.claude-plugin/plugin.json`), obično preko marketplace repozitorijuma — detalje proveriti na docs.claude.com pre prve instalacije sa CLI-ja.

## MCP zavisnosti (Obsidian)

Samo `obsidian-knowledge-logger` u ovom paketu koristi MCP alate — vezan je za Obsidian MCP server, koji se očekuje pod imenom `obsidian`. Svi Agent Studio-zavisni skillovi (koji su ranije bili ovde) sada žive u `plugin-soma-ops/` paketu.

## Skillovi po fazama

### 01 — Ideja / validacija
`brainstorming-buddy`, `deep-research`, `roast`, `skill-research`

### 02 — Dizajn
`prompt-engineer-pro`

### 03 — Izrada
`mcp-builder`, `session-start-hook`, `skill-creator-pro`

### 06 — Rad / održavanje
`obsidian-knowledge-logger`, `skill-lint`, `skill-security-review`

### 07 — Izlazni formati
`algorithmic-art`, `brand-guidelines`, `canvas-design`, `doc-coauthoring`, `internal-comms`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`

### 08 — Drugi projekti
`geo-prompt-library`, `morning`

**Ukupno: 21 skillova.**

### Šta nije u ovom paketu i zašto

- **28 skillova** specifičnih za Agent Studio/AgentStack/SOMA pipeline (uključujući konsalting
  sloj: `prospect-discovery`, `team-enablement-program`, `agent-delivery-pack`) su premešteni u
  sestrinski paket **`plugin-soma-ops/`** — pogledaj taj folder ako ti treba ta funkcionalnost.
- `market-research-navigator` (faza 01) i `system-teardown` (faza 02) postoje u faznim folderima
  repoa ali su namerno izostavljeni iz oba distributable paketa — njihov `LICENSE.txt` je "all
  rights reserved" bez dozvole za redistribuciju.
- `tender-projekat` (faza 08) postoji u faznom folderu ali je namerno izostavljen iz oba paketa —
  hardkodovan je na jedan konkretan klijentski projekat, beskoristan van te upotrebe.
- `plugin-sync` (faza 06) postoji u faznom folderu ali je namerno izostavljen iz oba paketa —
  meta-alat koji sinhronizuje ovaj repo sam sa sobom, nema smisla u distributable paketu.

### Skillovi koji se ne pozivaju sami

Jedan skill iz kataloga iznad nosi `disable-model-invocation: true` — namerno se **ne** pojavljuje u listi koju model sam pretražuje i bira se isključivo eksplicitnim pozivom po imenu:

- `roast` (faza 01) — adversarijalno "veće persona" koje traži fatalne mane u ideji pre nego što se u nju uloži vreme ili novac.

(`rls-rollout`, koji je ranije bio ovde iz istog razloga, sada je u `plugin-soma-ops/` — vidi taj README.)

Ovo je svesna odluka, ne propust: skup je ili invazivan da bi se okidao automatski. Posledica je da se ne može otkriti organski — pozovi ga po imenu.
