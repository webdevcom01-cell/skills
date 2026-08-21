---
name: winners-log-logger
description: Logs a winning hook (score ≥ 17/20) into the Hook Writer winners-log in the Obsidian vault. Use when a Hook Writer run produces a hook that scores 17 or higher, or when the user says "logiraj winnera", "winner hook", "zapiši winner", "hook je dostigao 17", "log this as a winner", "dodaj u winners log", "winner log za hook", "this hook scored [17+]", "hook je prošao threshold", "hook winner", "best hook", "top hook", or any phrase combining "hook" with a score ≥ 17/20 or terms like "winner", "pobednik", "prošao prag". Also triggers when evo-log-writer redirects because a hook scored ≥ 17/20. Do NOT use for hooks scoring below 17/20 (use evo-log-writer for the run log), do NOT use for instincts updates (use instincts-updater), and do NOT use for general notes (use obsidian-knowledge-logger).
---

# Winners Log Logger

Log a winning hook into `agents/hook-writer/winners-log.md` with zero hallucination and full structural preservation. TWO absolute gates: (1) score >= 17/20, (2) Memory Integrity Gate PROMOTE — no entry is written without both, no exceptions. Every write rebuilds the entire file body to preserve all sections exactly.

## Core idea

The winners-log is a curated archive of the best-performing hooks the SOMA system has ever produced. It serves two functions: (1) an immutable audit trail of high-quality outputs, and (2) a pattern reference that agents use to calibrate future hook generation. Structural integrity matters — this file must remain parseable and consistent across all future runs.

---

## Vault path

`agents/hook-writer/winners-log.md`

---

## Exact file structure (must be preserved verbatim on every write)

The file has four sections. Every replace operation must reproduce all four — no shortcuts.

```
# Hook Writer — Winners Log
*Path: /agents/hook-writer/winners-log*
*Threshold: score ≥ 17/20*

---

## Log Format
Each entry appended after a HOT hook is produced:
[fenced code block: date | trend | platform | hook_text | score | pattern]

---

## Winners

[entries or placeholder]

---

## Reference: What made past hooks work
[placeholder or pattern analysis content]
```

The `## Log Format` section uses a **fenced code block** (triple backticks), not inline backticks. When rebuilding, preserve this exactly — do not convert to inline backtick format.

---

## Log entry format

Single pipe-separated line. Spacing: ` | ` (space-pipe-space) between all fields.

```
2026-05-15 | Claude Agent SDK | linkedin | Claude Agent SDK just shipped. Multi-agent pipelines now take 3 nodes — not 30. | 18/20 | P1 (Hard Stat)
```

---

## Field formats, validation, and normalization

### `date`
Format: `YYYY-MM-DD`. Default: today's date.
Normalize input:
- `"May 14"` / `"14.05.2026"` / `"14/05/2026"` → `YYYY-MM-DD`
- `"yesterday"` / `"juče"` → today minus 1 day → `YYYY-MM-DD`
- Already `YYYY-MM-DD` → use as-is

### `score`
Format: `N/20`. Must be a whole integer 1–20, minimum 17.
Normalize input:
- `"17"` → `17/20`
- `"17 od 20"` / `"17 out of 20"` → `17/20`
- `"17.5"` → INVALID — decimals not accepted in SOMA scoring system
- `"21/20"` → INVALID — out of range
- Score < 17 → STOP (see Score Gate, Step 1)

### `platform`
One of five canonical lowercase values. Normalize variants automatically:

| User input | Canonical |
|---|---|
| `"LinkedIn"`, `"Linkedin"` | `linkedin` |
| `"Twitter"`, `"X/Twitter"`, `"x twitter"`, `"X (Twitter)"` | `x` |
| `"YouTube"`, `"Youtube"` | `youtube` |
| `"Instagram"` | `instagram` |
| `"TikTok"`, `"tiktok"` | `tiktok` |

If platform is anything else (`"Threads"`, `"Facebook"`, `"Blog"`, etc.) → ask: *"Koja platforma — linkedin, x, youtube, instagram, ili tiktok?"*

### `trend`
Short trend name. Verbatim from context. Sanitize: pipe `|` → `—`; newline `\n` → space.

### `hook_text`
Full hook text, verbatim — do NOT truncate. Sanitize: pipe `|` → `—`; newline `\n` → space. After newline collapse, a 2-line LinkedIn hook becomes one long single-line string — this is by design.

### `pattern`
Short pattern label. Known codes from Hook Writer instincts: `P1 (Hard Stat)`, `P3 (Curiosity Gap)`. For all others use descriptive text (e.g., `"Unpopular Opinion + Specificity"`, `"Number + Counterintuitive Implication"`). Do NOT invent P-codes beyond P1 and P3 — use descriptive labels for anything else. Sanitize: pipe `|` → `—`. If user cannot identify pattern → use `-` (dash). Do not block the log entry because of unknown pattern.

---

## Workflow — 10 steps + obavezni Memory Integrity Gate (Step 7.5)

### Step 1 — Score gate (absolute boundary)
Normalize the score to `N/20` format. Validate:
- Is N a whole integer? If not → refuse: *"Score [input] nije validan — SOMA sistem koristi cele brojeve (N/20)."*
- Is N in range 1–20? If not → refuse: *"Score [N]/20 je van opsega."*
- Is N ≥ 17? If NOT → **STOP**. Say: *"Score [N]/20 je ispod praga 17/20 — ovaj hook ne ide u winners-log. Koristite evo-log-writer za logovanje Hook Writer run-a. Podaci za evo-log: trend=[X], platform=[Y], hook=[Z], score=[N]/20, repurposer_hook=-."* Hand off all collected data so the user can immediately switch to evo-log-writer.

### Step 2 — Read winners-log (mandatory, and it must be a COMPLETE read)

> **`obsidian_read_note` does not return the whole file.** It returns at most
> `line_limit` lines — default **300**, maximum 500 — plus `total_lines`,
> `has_more` and `next_line_offset`. Step 9 writes with `mode: "replace"`, which
> overwrites the entire body with whatever you pass. So a single unpaged read of a
> winners-log longer than 300 lines silently destroys every line past the first
> page, and Step 10's verification cannot catch it because it compares against the
> same truncated read.
>
> Read in a loop before doing anything else:
> 1. `obsidian_read_note(path="agents/hook-writer/winners-log.md", line_offset=0, line_limit=500)`
> 2. While `has_more == true`: call again with `line_offset = next_line_offset`
>    and append each returned `body` to what you already have.
> 3. Stop when `has_more == false`.
> 4. **Gate:** the assembled body's line count must equal `total_lines`. If it does
>    not, STOP and report it — do not write. A partial read plus a replace is data
>    loss, and it is not recoverable from the vault.

Call `obsidian_read_note` on `agents/hook-writer/winners-log.md` as described above.
- If file not found → STOP. Say: *"winners-log.md nije pronađen u vaultu. Ne kreiram novi fajl — proverite vault strukturu."*
- From the read, capture and store:
  - (a) Does `## Winners` contain the placeholder `*No winners logged yet...*`? (first_entry flag)
  - (b) How many entries currently exist in `## Winners`? (entry_count)
  - (c) Does `## Reference: What made past hooks work` contain only the placeholder `*(Populated as winners accumulate...)*`? (reference_is_placeholder flag)
  - (d) Exact content of the `## Reference` section body (to preserve verbatim)
  - (e) Exact content of the entire file body — the ASSEMBLED body from the paged
        loop above, not the first page. Confirm its line count equals `total_lines`
        before using it as the basis for the Step 9 replace.

### Step 3 — Multiple winners check
If the user mentions 2 or more hooks both scoring ≥ 17/20: *"Koliko winners — da ih logujem sve, ili samo jedan? Ako sve, daj mi podatke za svaki."* Collect all data upfront before writing anything. Write sequentially: one full replace per entry.

### Step 4 — Deduplication check
Compare the incoming `hook_text` (after sanitization: `.trim().toLowerCase()`) against every existing `hook_text` in `## Winners` (same transform applied). If exact match found → warn: *"Ovaj hook tekst već postoji u winners-logu (datum: [X]). Da li da logujem svejedno, ili preskačemo?"* Wait for user decision before proceeding.

### Step 5 — Collect all 6 fields
Gather from conversation context. For anything missing, ask one concise question covering all gaps: *"Za ovaj winner: [lista nedostajućih polja]?"*
- Platform: normalize automatically if variant recognized; ask if unknown
- Date: normalize to YYYY-MM-DD; default today
- Pattern: use `-` if user cannot identify; do NOT ask again after one failed attempt

### Step 6 — Sanitize all free-text fields
For `trend`, `hook_text`, `pattern`:
- Replace pipe `|` with em-dash `—`
- Replace literal newline `\n` with single space ` `
Keep full text — no truncation.

### Step 7 — Format the entry line
Build a single-line string:
```
YYYY-MM-DD | trend | platform | hook_text | N/20 | pattern
```
Verify the line contains exactly 5 pipe separators (6 fields). If not — stop and recheck sanitization.

### Step 7.5 — Memory Integrity Gate (OBAVEZNO, fail-closed — pre svakog upisa)

Nijedan zapis ne ulazi u winners-log bez PROMOTE odluke Memory Integrity Gate agenta (ASI06 anti-poisoning).

1. Prikupi iz konteksta run-a (NE iz hook teksta):
   - `source_excerpt` — izvorni tekst/excerpt trenda iz TI output-a (source of truth za grounding)
   - `angle` — ugao iz TI output-a
   - `sa_verdict` — verdikt Score Analyzer-a; mora biti tacno `VERIFIED`
   Ako `source_excerpt` ili `sa_verdict` nedostaju → NE upisuj. Pitaj korisnika za izvor / pokreni Score Analyzer (soma-score-analyzer). Bez izvora i verifikacije kandidat ide u quarantine-log, nikad u winners-log.
2. Pozovi gate: `as_chat_with_agent` sa `agent_id: cmqxycati007pmu01y758l51t` (agent "Memory Integrity Gate") i porukom — cist JSON, bez markdown fence-ova:
   `{"trend": "...", "angle": "...", "source_excerpt": "...", "sa_verdict": "VERIFIED", "posts": [{"platform": "...", "text": "<hook_text>", "score": N}]}`
3. Parsiraj odgovor (JSON: `gate`, `perPost[].decision`, `perPost[].flags`):
   - `PROMOTE` → nastavi na Step 8; u `pattern` polje dodaj sufiks ` [GATE-APPROVED]`
   - `QUARANTINE` → **NE upisuj u winners-log.** Upisi u `agents/hook-writer/quarantine-log.md` (format: `date | trend | platform | hook_text | score | gate_flags`, append u `## Entries` sekciju). Reci korisniku sta je karantinovano i zasto (flags).
   - Gate nedostupan / odgovor neparsabilan / bilo sta drugo → **fail-closed: NE upisuj.** Prijavi korisniku. Neparsabilan odgovor NIKAD ne postaje PROMOTE.

### Step 8 — Rebuild complete file body
Reconstruct the ENTIRE file body. Use the exact structure below. Replace `[WINNERS_CONTENT]` and `[REFERENCE_CONTENT]` as specified.

**Header and Log Format (always identical — copy verbatim):**
```
# Hook Writer — Winners Log
*Path: /agents/hook-writer/winners-log*
*Threshold: score ≥ 17/20*

---

## Log Format
Each entry appended after a HOT hook is produced:
```

Then immediately a fenced code block (opening triple-backtick on its own line, content on next line, closing triple-backtick on its own line):
```
date | trend | platform | hook_text | score | pattern
```

Then continue:
```

---

## Winners

[WINNERS_CONTENT]

---

## Reference: What made past hooks work
[REFERENCE_CONTENT]
```

**`[WINNERS_CONTENT]` rules:**
- First entry (first_entry flag = true): new entry line only. Remove placeholder.
- Subsequent entry (first_entry flag = false): all existing entries in original order, then new entry on next line. No blank lines between entries.

**`[REFERENCE_CONTENT]` rules:**
- If reference_is_placeholder = true: keep the placeholder exactly: `*(Populated as winners accumulate — style patterns extracted here)*`
- If reference_is_placeholder = false: copy the exact content from Step 2 capture (d), character by character. Do NOT modify.

### Step 9 — Write using replace mode
Call `obsidian_update_note` with `mode: replace`. Pass the full reconstructed body as content.
- NEVER use `mode: append` — appended content lands after `## Reference`, corrupting the structure
- NEVER use `section_heading` — creates duplicate headers
- **NEVER write if the Step 2 line-count gate did not pass.** `replace` overwrites the
  whole body; passing a body assembled from a partial read deletes the remainder of
  the log permanently.

### Step 10 — Post-write verification (mandatory)
Immediately call `obsidian_read_note` on the same path. Check all four:
1. ✓ New entry appears in `## Winners` section
2. ✓ `## Reference: What made past hooks work` header is present at the same position
3. ✓ Reference section body equals pre-write content (Step 2 capture d)
4. ✓ `## Log Format` section is present with its fenced code block intact

If any check fails → report exact discrepancy to user. Do NOT claim success.

### Confirm
One line: *"✅ Winner logiovan: [trend] / [platform] / [score]. ([bytes_written] bytes)"*

**Always append this reminder:**
*"Reminder: loguji ovaj Hook Writer run i u evo-log (evo-log-writer) ako već nisi."*

---

## Optional — Reference section update

**Condition (evaluated after Step 10):**
- `entry_count` (from Step 2) was < 3, AND the new count is ≥ 3
- AND `reference_is_placeholder` = true (Reference not yet populated)

If both conditions are met, offer **once**: *"Sada ima [N] winners — dovoljan uzorak za pattern analizu. Da li da ažuriram `## Reference` sekciju sa zajedničkim obrascima?"*

If user says yes:
1. Re-read current winners-log to get all entries
2. Analyze entries: identify common platforms, score ranges, pattern labels
3. Write a structured pattern summary into `## Reference`
4. Rebuild full body (same replace mode + post-write verification)

If user says no, or if reference_is_placeholder = false (already has content) → do nothing. Do NOT offer again on subsequent runs.

---

## Scope boundary

| Scenario | Pravi skill |
|---|---|
| Hook score < 17/20 (run logging) | evo-log-writer |
| Agent naučio nešto novo | instincts-updater |
| Opšte beleške van SOMA | obsidian-knowledge-logger |
| Kreiranje novog winners-log fajla | Ne postoji skill — javi grešku |
| Brisanje ili editovanje postojećeg entry-a | Nije podržano — ručna edita |

---

## Anti-hallucination pravila (7)

1. **Score gate je apsolutna granica** — ceo broj, opseg 1–20, minimum 17. Nema zaokruživanja, nema "skoro 17".
2. **Nikad ne izmišljaj hook_text** — mora biti verbatim iz user-a ili agent outputa. Pitaj ako nije dat.
3. **Pattern → `-` ako korisnik ne zna** — nikad izmišljaj P-kodove; poznati su samo P1 (Hard Stat) i P3 (Curiosity Gap).
4. **Uvek replace mode** — append kvari strukturu (entry ide posle `## Reference`).
5. **Rebuilduješ ceo body** — header + fenced-code Log Format + Winners + Reference. Ni jedna sekcija ne sme nedostajati.
6. **`bytes_written` je jedina potvrda** — ne tvrdi "sačuvano" bez tool potvrde.
7. **Reference sadržaj = pre-write stanje** — kopiraj karakter po karakter iz Step 2; nikad spontano menjaj.

---

## Edge cases

**Score 17.5 ili decimala:**
Odbij: *"SOMA scoring sistem koristi cele brojeve. Da li misliš 17/20 ili 18/20?"*

**Nepoznata platforma (Threads, Facebook, itd.):**
Pitaj: *"Koja platforma — linkedin, x, youtube, instagram, ili tiktok?"* — ne prihvataj ništa izvan 5 canonical vrednosti.

**Multiple winners u jednom run-u:**
Prikupi podatke za sve, napravi sve replacement-e sekvencijalno. Ne piši za prvog a zanemaruješ drugog.

**Korisnik ručno editovao Reference u Obsidianu:**
Skill vidi Reference ≠ placeholder → neće nuditi update. To je ispravno ponašanje — ručna edita je korisnikova odgovornost.

**Fajl postoji ali nema `## Winners` sekciju (corrupted):**
STOP. *"winners-log.md postoji ali `## Winners` sekcija nije pronađena — fajl je možda oštećen. Proverite ga ručno pre logovanja."*

**Kasno logovanje (juče ili ranije):**
Prihvati korisnikov datum. Normalizuj u YYYY-MM-DD. Logiraj sa tim datumom.

**Korisnik želi da obriše ili ispravi entry:**
Nije podržano ovim skillom. *"Editovanje postojećih entries nije podržano. Otvorite fajl direktno u Obsidianu."*
