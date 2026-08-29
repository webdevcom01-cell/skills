---
name: skill-security-review
description: >
  Primenjuje istu disciplinu koju safe-agent-builder/enterprise-agent-readiness/
  memory-integrity-gate primenjuju na AgentStack agente — ali na sam skills-repo. Pre merge-a
  novog ili izmenjenog skilla: (1) skenira sve bundlovane skripte za hardkodovane API
  ključeve/tokene/privatne ključeve, (2) nalazi skillove koji pominju mutating MCP alat
  (as_delete_*/as_patch_*/as_update_*/as_create_*/as_add_*/as_set_*) ili destruktivan jezik u
  opisu bez allowed-tools polja, (3) za svaki skill koji IMA allowed-tools, čita SKILL.md telo i
  procenjuje da li dati obim alata odgovara stvarno opisanom ponašanju (preširok ili preuzak).
  Koristi kad korisnik kaže "security review skillova", "proveri allowed-tools", "proveri
  hardkodovane kredencijale", "bezbednosna provera pre merge-a", "da li je allowed-tools
  opravdan". Ne koristi za veličinu/verziju/deps/licencu (koristi skill-lint — mehanička
  provera, ne rasuđivanje o sadržaju).
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TodoWrite
---

# Skill: skill-security-review

*Version: 1.0 — nastao iz plan-unapredjenja-skills-repo.md, Faza C. "safe-agent-builder za sam
repo skillova" (Izveštaj 1, §8, Prioritet 1 predlog #3). Prvi konkretan zadatak bio je devet
skillova bez allowed-tools nabrojanih u Dodatku §2 — svih devet je popravljeno pre nego što je
ovaj skill i napisan (commit "security(skills): dodaj allowed-tools za 9 operativnih skillova"),
pa je ovaj skill sada čist regresioni gate za taj nalaz, ne prvi popravak.*

---

## Trigger

Use this skill when the user wants to:
- Scan bundled scripts for hardcoded credentials before a merge/release
- Find skills that mutate state (via an MCP tool or destructive language) without `allowed-tools`
- Judge whether an existing `allowed-tools` scope is justified by, too broad for, or too narrow
  for what a skill's `SKILL.md` actually describes doing

Do NOT use this skill for:
- SKILL.md size, `version:`/CHANGELOG match, pip deps, LICENSE compliance, or README catalog
  drift → use `skill-lint` (purely mechanical checks, no reading/judgment required)
- Syncing or packaging the plugin → use `plugin-sync`
- Running `git add`/`git commit`/`git push` → tell the user the exact commands, don't run them
  yourself (this repo's convention: git write operations go through the user's own terminal)

---

## What This Skill Does

Two mechanical scripts narrow down *candidates*; the third step is this skill actually reading
and judging, which is why it isn't folded into `skill-lint`:

1. **`scripts/scan_hardcoded_secrets.py`** — regex sweep of every `.py`/`.js`/`.ts`/`.sh` under
   the phase folders for AWS/GitHub/Slack/Anthropic-shaped keys, private-key blocks, Bearer
   tokens, and secret-shaped variable assignments (`api_key = "..."`, excluding env-lookups and
   obvious placeholders). Over-flags on purpose — a human reads the report either way.

2. **`scripts/find_mutating_without_allowed_tools.py`** — two independent signals, reported in
   separate buckets since their confidence differs:
   - **Tool-name signal** (high confidence): any `mcp__*__as_*` name in a skill's body,
     classified by verb prefix as mutating or read-only. Flags a skill that mentions a mutating
     tool and has no `allowed-tools`.
   - **Keyword signal** (low confidence, always needs a human read): destructive language
     ("delete", "quarantine", "irreversible", "briše"...) in the *description* with no
     `allowed-tools`. This one produces real false positives on purpose — e.g.
     `agent-dependency-mapper`'s description says "READ-ONLY — never mutates or deletes agents"
     and mentions "before I delete an agent" as a *trigger phrase*, which the regex can't tell
     apart from a skill that actually deletes something. That's exactly why this bucket is
     advisory, not a hard finding — STEP 3 below is where a human/agent resolves it by reading.

3. **Judging existing `allowed-tools` scope (no script — this is the reading step)**: for every
   skill that *does* declare `allowed-tools`, read its `SKILL.md` body and check the granted
   tools against what the skill actually does. Over-broad example: a read-only reporting skill
   that's granted `Write` it never uses. Under-scoped example: a skill whose body clearly walks
   through calling `as_delete_agent` but that tool isn't in its `allowed-tools` list (the call
   would fail at runtime, which is a correctness bug, not just a security gap). Neither script
   above can do this — it requires reading prose and comparing it to a tool list, which is a
   judgment call, not a regex.

None of the three write anything. Report-only.

---

## STEP 0 — Task List

Call TaskCreate for each check the user actually wants — don't create tasks for checks they
didn't ask about:
- "Pokreni scan_hardcoded_secrets.py"
- "Pokreni find_mutating_without_allowed_tools.py"
- "Pročitaj skillove sa allowed-tools i proceni obim"
- "Izveštaj nalaze"

The two scripts live in `scripts/` next to this SKILL.md — resolve that path relative to *this
file's own location*, not to a hardcoded repo path: if you're reading this from
`06-rad-odrzavanje/skill-security-review/SKILL.md`, the scripts are at
`06-rad-odrzavanje/skill-security-review/scripts/`; if you're reading this from an installed
`plugin/skills/skill-security-review/SKILL.md`, they're at
`plugin/skills/skill-security-review/scripts/` instead. The repo-root argument (`.` below) always
points at the actual repo root — must be a checkout that contains the phase folders
(`01-*`–`08-*`), not just this skill's own folder in isolation.

## STEP 1 — Hardcoded secrets

```
python3 <this-skill's-scripts-dir>/scan_hardcoded_secrets.py <repo_root>
```

## STEP 2 — Mutating tools / destructive language without allowed-tools

```
python3 <this-skill's-scripts-dir>/find_mutating_without_allowed_tools.py <repo_root>
```
Treat the KEYWORD bucket in the output as candidates only — read each flagged skill's actual
description before reporting it as a real finding, per the `agent-dependency-mapper` example
above. The MUTATING-TOOL bucket is higher-confidence but still deserves a quick read, not a
blind pass-through.

## STEP 3 — Judge existing allowed-tools scope (only when the user asks for this specifically,
it's the most expensive step — reads every scoped skill's full body)

For each skill with `allowed-tools` already set: read the body, list every tool/MCP call it
actually invokes (same method used when the nine skills' scopes were originally derived — see
`plugin/README.md`'s "MCP zavisnosti" section for the `mcp__agent-studio__` vs
`mcp__agent-studio-db__` dual-prefix convention this repo uses), and compare against the granted
list. Report anything granted-but-unused (over-broad) or used-but-not-granted (under-scoped,
would fail at runtime) by name.

## STEP 4 — Report

Summarize per step, in plain terms — which secrets/candidates were found (or none), which
keyword-bucket items turned out to be real vs false positives after reading, and (if STEP 3 ran)
which skills have a scope mismatch and what it is. Don't present the keyword bucket's raw
candidates as confirmed findings without having actually read them.

---

## Constraints and Rules

1. **Report-only, no auto-fix.** All checks here are detection; a human decides the actual
   `allowed-tools` list or credential remediation, same posture as `skill-lint`.
2. **The keyword signal is advisory by design, not a bug to fix with a smarter regex.** Negation
   ("never deletes") is a judgment call a regex can't reliably make — that's exactly why STEP 2
   ends in "read it," not "trust the script."
3. **No hardcoded skill list.** Both scripts discover phase folders and skill names from the
   filesystem at run time, same convention as `plugin-sync` and `skill-lint`.
4. **Never invoke `git add`/`git commit`/`git push` from this skill** — same convention as
   `plugin-sync`/`skill-lint`: propose the exact command, the user runs it from their own
   terminal.
