---
name: evo-log-writer
description: Logs SOMA agent run results into the correct evo-log.md file in the Obsidian vault. Use this skill whenever a SOMA agent (Trend Intelligence, Hook Writer, or Content Repurposer) has finished a run and the result needs to be recorded. Triggers on phrases like "logiraj run", "zapiši evo-log", "log this run", "log the agent", "evo log za [agent]", "Trend Intelligence je završio", "Hook Writer je generisao", "Content Repurposer je završio", "log the pipeline", "zapiši pipeline run", or any mention of a SOMA agent completing work. Also triggers when the user describes agent output and says "zapamti ovo" or "sačuvaj ovo" in a SOMA context. Do NOT use for general knowledge saving (use obsidian-knowledge-logger for that), and do NOT use for winners-log entries (use winners-log-logger for that).
allowed-tools:
  - mcp__obsidian__obsidian_read_note
  - mcp__obsidian__obsidian_update_note
---

# Evo-Log Writer

Log SOMA agent run results into the correct evo-log.md file with zero friction and zero hallucination. Every run gets logged — no exceptions (SOMA Rule #5).

## Core idea

The evo-log is the SOMA system's memory of what happened. Every entry must be accurate and consistently formatted so future analysis (performance reviews, instincts updates) can rely on it. This skill knows each agent's exact log format, handles the first-entry placeholder, sanitizes field values, and confirms the write with bytes_written — never simulates a save.

---

## Agents, vault paths & log formats

| Agent | Vault path | Log format |
|---|---|---|
| Trend Intelligence | `agents/trend-intelligence/evo-log.md` | `date \| trend_found \| confidence \| angle_suggested \| hook_writer_triggered` |
| Hook Writer | `agents/hook-writer/evo-log.md` | `date \| trend \| platform \| winner_hook \| winner_score \| repurposer_hook` |
| Content Repurposer | `agents/content-repurposer/evo-log.md` | `date \| trend \| confidence \| platforms_completed \| any_needs_flags \| linkedin_word_count \| tiktok_duration_estimate` |

---

## Field formats

### Confidence
Always use the star rating system — never numbers or percentages:
- `⭐⭐⭐` — Official release + measurable metric + practitioner reaction visible
- `⭐⭐` — Credible source + specificity, but limited reaction data
- `⭐` — Single source, no reactions, or trend older than 48h

### Score (Hook Writer)
Format: `N/20` — e.g. `18/20`. Never just a number alone.

### Platform (Hook Writer)
One of: `linkedin`, `x`, `youtube`, `instagram`, `tiktok`. Lowercase only.

### hook_writer_triggered (Trend Intelligence)
- `yes` — normal run, Hook Writer was called via A2A
- `no` — agent halted (quality gate failed: VAGUE_INPUT, MISSING_TREND)

### any_needs_flags (Content Repurposer)
Valid values only — never invent flags:
- `none` — clean run, no issues
- `LOW_CONFIDENCE` — output generated but confidence is low
- `HUMAN_REVIEW_NEEDED` — human must check before publishing
- `PARTIAL_OUTPUT` — not all platforms completed

### Free-text fields (angle_suggested, winner_hook, repurposer_hook)
These fields hold natural language. Before writing:
1. Replace any `|` character with `—` (pipe breaks the log format)
2. Replace any newline `\n` with a space (entries must be single-line)
3. Do NOT truncate — store full text

### Nullable fields
When data is unavailable, use `-` (a single dash). Never leave a field empty or skip it.

---

## Minimum viable entry

Each agent has required fields and nullable fields:

| Agent | Required | Nullable (use `-` if missing) |
|---|---|---|
| Trend Intelligence | `date`, `trend_found`, `confidence` | `angle_suggested`, `hook_writer_triggered` |
| Hook Writer | `date`, `trend`, `platform`, `winner_hook` | `winner_score`, `repurposer_hook` |
| Content Repurposer | `date`, `trend`, `platforms_completed` | `confidence`, `any_needs_flags`, `linkedin_word_count`, `tiktok_duration_estimate` |

---

## Workflow

### Step 0 — Determine scope
Ask (or infer from context): is this one agent or the full pipeline?
- **One agent**: run steps 1–6 once
- **Full pipeline**: run steps 1–6 for each agent sequentially (Trend Intelligence → Hook Writer → Content Repurposer). Collect all data upfront before writing anything.

### Step 1 — Identify agent
Infer from context (user mentions agent name, describes output type). If truly ambiguous, ask: *"Koji agent — Trend Intelligence, Hook Writer, ili Content Repurposer?"*

### Step 2 — Read the evo-log
Use `obsidian_read_note` on the agent's vault path. This is mandatory — never write blind.

> **Page the read if you will write with `mode: replace`.** `obsidian_read_note`
> returns at most `line_limit` lines (default **300**, max 500) plus `total_lines`,
> `has_more` and `next_line_offset`. Step 6's first-entry branch replaces the whole
> body, so a truncated read there would drop everything past line 300. That branch
> only fires while the placeholder is present — i.e. on a near-empty file — so the
> blast radius is normally small, but do not rely on that: if `has_more == true`,
> keep calling with `line_offset = next_line_offset` and concatenate the bodies
> until `has_more == false`, and verify the assembled line count equals
> `total_lines` before any replace.
- Check if `## Entries` section contains the placeholder: `*No runs yet — first entry will appear after initial test run.*`
- Note: if the file doesn't exist, stop and tell the user. Do not create a new evo-log — that would break the SOMA vault structure.

### Step 3 — Collect field values
Gather data for all fields from the conversation context. Infer what you can. For missing required fields, ask one concise question covering all gaps: *"Za ovaj run: koji je bio confidence i da li je hook_writer pokrenut?"*

Never ask for nullable fields — use `-` automatically.

### Step 4 — Sanitize free-text fields
For `angle_suggested`, `winner_hook`, `repurposer_hook`:
- Replace `|` → `—`
- Replace `\n` → ` `
- Keep full text, no truncation

### Step 5 — Format the entry
Build a single-line pipe-separated entry using today's date (YYYY-MM-DD format):

**Trend Intelligence example:**
```
2026-05-15 | Claude Agent SDK ships stateful multi-agent | ⭐⭐⭐ | Shows how 3 nodes replace custom orchestration for builders | yes
```

**Hook Writer example:**
```
2026-05-15 | Claude Agent SDK | linkedin | Claude Agent SDK just shipped. Multi-agent pipelines now take 3 nodes — not 30. | 18/20 | Same hook, platform-optimized for LinkedIn feed
```

**Content Repurposer example:**
```
2026-05-15 | Claude Agent SDK | ⭐⭐⭐ | linkedin,x,instagram | none | 542 | 48s
```

### Step 6 — Write to vault

**If placeholder is present (first entry ever):**
Use `obsidian_update_note` with `mode: replace`. Replace the entire body, preserving the header and `## Log Format` section, and replacing only the `## Entries` section content.

**If entries already exist (subsequent runs):**
Use `obsidian_update_note` with `mode: append`, **without** `section_heading`. The entry appends directly to the end of the file.

Never use `section_heading` — it creates a new `## Entries` header every time, which corrupts the file.

### Step 7 — Confirm
One sentence: *"✅ Evo-log za [Agent] — run logiovan: [trend]. ([bytes_written] bytes)"*

For full pipeline: *"✅ Sva 3 agenta logovana: TI ([X]b), HW ([X]b), CR ([X]b)."*

---

## Scope boundary — što NIJE ovaj skill

| Scenario | Pravi skill |
|---|---|
| Opšte "sačuvaj ovo" / "zapiši ideju" | obsidian-knowledge-logger |
| Hook je dobio ≥17/20 i treba da ide u winners-log | winners-log-logger |
| Kreiranje novog evo-log fajla | Ne postoji skill — javi grešku |
| Logovanje van SOMA agentske trojke | Ne postoji skill — javi grešku |

---

## Anti-hallucination pravila

1. **Nikad ne izmišljaj sadržaj polja** — posebno `winner_hook` i `angle_suggested`. Ako korisnik nije dao tekst, pitaj ili stavi `-`.
2. **Nikad ne procenjuj confidence sam** — to je procena agenta, ne tvoja. Pitaj ili stavi `-`.
3. **Nikad ne kreiraj evo-log fajl** — ako file not found, stani i javi.
4. **`bytes_written` je jedina potvrda** — ne govori "sačuvano" bez potvrde od tool-a.
5. **Nikad ne koristis `section_heading` u append modu** — to kvari strukturu fajla.

---

## Edge cases

**Korisnik opisuje run ali ne daje sve podatke:**
Inferuj ono što možeš, pitaj samo za kritična polja koja ne možeš da zaključiš. Primer: ako je korisnik opisao trend ali nije dao confidence — pitaj samo za confidence.

**Agent je haltovao pre završetka:**
Logiraj svejedno sa dostupnim podacima. `hook_writer_triggered: no`, nullable polja → `-`. Halt je validan run — treba da bude u logu.

**Ceo chain je prošao ali korisnik daje podatke postepeno:**
Prikupi sve podatke za sva 3 agenta pre nego što pišeš ijedan fajl. Piši sva 3 sekvencijalno.

**Partial completion na Content Repurposeru:**
Koristi format: `linkedin,x (partial: instagram)` za `platforms_completed`. U `any_needs_flags` stavi `PARTIAL_OUTPUT`.

**Platform nije specificiran za Hook Writer:**
Pitaj — platforma je required polje i ne može se inferovati.
