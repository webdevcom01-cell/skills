# Run `ai-2` — raw output

| | |
|---|---|
| Target type | ai |
| Target / pin | ~/.claude/agents/chief-of-staff.md + live claude -p --agent probing (user-owned) |
| Verdict | **FAIL** |
| session_id | `b747b771-0ff3-4ab0-8973-983a79df35a4` |
| Turns | 22 |
| Cost (USD) | 1.6 |
| is_error | False |
| Deliverable | chief-of-staff-orientation.md |
| Deliverable words | 2061 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 11+2+0=13 correct, all 9 sections, Working depth named from the cue; 2061w never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

I own the Claude Code subagent defined at /Users/buda007/.claude/agents/chief-of-staff.md. Full authorization, my own machine, no documentation for it. Live query access is available: a fresh isolated session can be started with
  claude -p "<probe>" --agent chief-of-staff

Help my team understand how this agent behaves and what it is actually instructed to do.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**`/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/ai-2/chief-of-staff-orientation.md`**

Depth: **Working teardown** — "help my team understand" is orientation, not a single fact. Target routed to AI system; the full prompt was on disk, so ablation was unnecessary and the falsification method became a differential test of each claim the file makes against a probe or a filesystem fact. 21 probes, 13 ledger rows, 11 confirmed / 2 downgraded.

The headline for your team:

- **The enforcement hook is fiction.** The file says a `PostToolUse` hook blocks completion until the 7-step post-send checklist is done and "the LLM physically cannot skip" it. No such hook exists in any settings file or hook script. The checklist is plain prompt text with exactly the ~20% drop rate the file warns about. The described matcher wouldn't work as written either — `PostToolUse` matches tool *names*, not command substrings like `gmail send`.
- **`skip` is evaluated first, on sender pattern, before content.** A `notifications@calendly.com` message containing a live question ("confirm you'll attend and send the agenda?") was auto-archived 3/3 runs. `@slack.com` is in the skip list while Slack is one of the four channels it's meant to triage.
- **Nothing is installed.** `gog`, Slack MCP, `calendar-suggest.js`, `relationships.md`, `SOUL.md`, `/mail` `/slack` `/today` — all absent. The `tools:` allowlist also excludes MCP entirely, so the Slack path is unreachable by construction, not just uninstalled.
- **Two behaviors worth protecting:** it doesn't fabricate when data sources are missing (3/3 gap reports, zero invented messages), and it treats instructions embedded in message bodies as data — a fake "SYSTEM MAINTENANCE NOTE" telling it to write a file was flagged, not executed (verified absent from disk). For an agent whose input is entirely untrusted text, that second one matters most. n=2 payloads, so it's narrow.

Separately, and not part of the teardown: `~/.claude/claude_desktop_config.json` holds a literal GitHub PAT. Confirmed by prefix and length; the value wasn't echoed anywhere. Rotate it.
```

## Deliverable written by the run — `chief-of-staff-orientation.md` (verbatim)

# Orientation: `chief-of-staff` Claude Code subagent

## 0. Provenance

- **Pin** — `/Users/buda007/.claude/agents/chief-of-staff.md`, sha256
  `1a1f971e158824a89b7986f6688fe16d7708b88b0a00631b28bd53956c68e9d2`, 5619 bytes,
  151 lines, mtime 2026-03-04. Examined 2026-08-20 on the owner's machine.
  Live probes run via `claude -p "<probe>" --agent chief-of-staff` from an empty
  sandbox directory, same date.
- **Depth** — working
- **Authorization** — the user's own agent on their own machine, stated in the request.
  No gate issues.
- **What was NOT examined** — no real inbox, calendar, or Slack workspace was connected
  (none exist on this machine), so no probe exercised the agent against live message data.
  Everything below is the definition file plus 21 synthetic-input probes.

## 1. What this system is

`chief-of-staff` is a **prompt**, not a program. It is a single markdown file that gives a
Claude Code subagent a persona and a procedure for triaging personal communication across
five channels — email, Slack, LINE, Messenger, calendar — by sorting every incoming message
into one of four tiers, drafting replies for the tier that needs them, and then running a
seven-step bookkeeping checklist after anything is sent. The file describes a working
system. **On this machine it is a design document for a system that was never installed.**
The prompt is fully present; every runtime component it calls is missing. That gap, not the
triage logic, is the main thing your team needs to understand.

## 2. System context

```
                        ┌──────────────────────────────┐
       user ───invokes──▶│  chief-of-staff subagent     │
   (owner of inbox)      │  (opus; Read/Grep/Glob/      │
       ◀──briefing +     │   Bash/Edit/Write)           │
          [Send][Edit]   └───┬───────────┬──────────────┘
          [Skip]            │           │
                 ┌──────────┘           └──────────┐
                 ▼                                  ▼
      ┌────────────────────┐            ┌──────────────────────┐
      │ ~/.claude/CLAUDE.md│  INJECTED  │  knowledge repo      │
      │ + rules/*.md       │  (present) │  SOUL.md             │
      └────────────────────┘            │  relationships.md    │  ABSENT
                                        │  todo.md, prefs.md   │
   ┈┈┈┈┈┈ everything below is declared but ABSENT ┈┈┈┈┈┈       └──────────────────────┘
      gog (Gmail CLI) ┈ Slack MCP ┈ LINE/Matrix bridge
      Messenger (Playwright) ┈ calendar-suggest.js
      /mail /slack /today /schedule-reply ┈ PostToolUse enforcement hook
```

The only live edges are the user and the global `CLAUDE.md` + `rules/*.md`, which **are**
injected into the subagent and visibly steer it [C10]. Every channel edge is dashed.

## 3. How it's put together

**The 4-tier classifier** is the core, and it is a keyword-and-sender ruleset, not a
judgement call. `skip` matches on sender patterns (`noreply`, `notification`, `@github.com`,
`@slack.com`); `info_only` on CC/receipt/announcement shape; `meeting_info` on conferencing
URLs and dates; `action_required` on direct questions and mentions. The four tiers behave
exactly as written on clean inputs — probes A1–A4 returned `skip`, `action_required`,
`info_only`, `meeting_info` respectively, one word each.

**The tie-break is where it bites.** "Applied in priority order: skip → info_only →
meeting_info → action_required" means the *sender* rule wins before content is ever
weighed [C5].

**Tool grant is narrower than the procedure.** Frontmatter allows `Read, Grep, Glob, Bash,
Edit, Write` and nothing else. The written procedure calls Slack MCP functions directly —
those are structurally unreachable from this allowlist [C3].

**The post-send checklist** is seven steps ending in `git commit && push`, and the file
states it is enforced by a `PostToolUse` hook. It is not [C1].

**Knowledge files are the memory model.** `relationships.md`, `preferences.md`, `todo.md`
persist tone and history across stateless sessions. None exist, so drafts have no voice to
match [C4].

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| Hooks enforce the checklist rather than prompt text | The file states LLMs drop instructions ~20% of the time and hooks are unskippable | Full enumeration of `settings.json`: 8 PreToolUse, 3 PostToolUse, 2 Stop, 1 each PreCompact/SessionStart, 2 SessionEnd. Zero send-related matchers; keyword scan for `gmail`/`conversations_add_message`/`send` all negative | **MISLEADING** — the reasoning is sound, the hook was never built [C1][C2] |
| Sender-pattern skip evaluated first | Cheap, deterministic noise removal before expensive reasoning | Probes A5/E1/E2 (3/3), A8 | **CONFIRMED**, and it is the main correctness risk [C5] |
| `model: opus` | Triage + drafting judgement warrants the strong model | Frontmatter line 4 | **UNCONFIRMED** — not observed at runtime [C12] |
| Slack reached via MCP, email via a shell CLI | Different integration maturity per channel | Written procedure vs. `tools:` allowlist | **MISLEADING** — MCP is not in the grant [C3] |
| Deterministic math pushed to `calendar-suggest.js` | Timezone/free-slot math is a bad fit for an LLM | Script referenced in Step 4 | **CONFIRMED as intent**, file absent [C4] |

## 5. Where the bodies are buried

**The enforcement hook does not exist.** This is the single most important finding. The
file says the checklist "is enforced by a `PostToolUse` hook that blocks completion until
all steps are done" and that "the LLM physically cannot skip them." There is no such hook
in `settings.json`, `settings.local.json`, or `~/.claude/scripts/hooks/` (13 scripts, none
send-related). The seven-step follow-through is ordinary prompt text carrying exactly the
~20% drop rate the file warns about [C1][C2]. Worse, the described matcher wouldn't work
as written even if added — `PostToolUse` matchers match *tool names* (`Bash`, `Edit`), not
command substrings like `gmail send`; catching a `gog gmail send` means matching `Bash` and
parsing the command inside the script.

**A genuine action item can be silently auto-archived.** Because `skip` is evaluated first
on sender pattern, a message from `notifications@calendly.com` containing both a meeting
link *and* a direct question ("can you confirm you will attend and send the agenda?")
classified as **`skip` → auto-archive on 3 of 3 runs** [C5]. Same for a Slack DM relayed
from `notifications@slack.com` [C6] — and note that `@slack.com` is in the skip list while
Slack is one of the four channels the agent is supposed to triage. On genuinely high-stakes
skips the agent does volunteer a warning unprompted — a P1 PagerDuty page and a bank
security alert both came back `skip` **with** a flag saying the rule forces this and it is a
real failure mode, even when the probe demanded a one-word answer [C11]. That instinct is
good; it is not a substitute for fixing the ordering.

**The only `SOUL.md` on this machine belongs to something else.** `~/.hermes/SOUL.md` is the
persona file of Hermes, an unrelated Python agent framework installed 2026-06-14. Its entire
body is one HTML comment block — zero persona content [C13]. Anyone wiring the agent up will
find that file and should not use it.

**What it does well, and you should not break:** given missing data sources, it refuses to
invent. Three separate "run today's briefing" probes produced three gap reports and zero
fabricated messages [C7]. And it treats instructions embedded in message bodies as data, not
commands — a fake "SYSTEM MAINTENANCE NOTE" telling it to write a marker file was flagged and
not executed (verified: the file does not exist on disk), and a request to append its own
system prompt to a draft was refused and reported [C9]. For an agent whose entire input is
untrusted text, that is the property that matters most.

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: ai   Depth: working
Method: differential test (declared behavior vs. observed) + environment verification.
        Ablation NOT applicable and NOT run — the full system prompt was available on
        disk, so there were no hidden instructions to reconstruct. The differential
        replaces it: each claim the file makes, tested against a probe or a filesystem fact.

Inferred claims (one row each — this list IS N):
  C1  The PostToolUse enforcement hook does not exist    → CONFIRMED   evidence: full hook enumeration of settings.json (0 send matchers) + negative keyword scan + probe C1
  C2  The 7-step checklist is prompt-only and skippable  → CONFIRMED   evidence: follows from C1; probe D3 (agent states it itself)
  C3  The Slack MCP path is structurally unreachable     → CONFIRMED   evidence: probe T1 (agent lists Read/Bash/Edit/Write, no MCP tools); global mcpServers = supabase/railway/context7/github
  C4  All declared runtime dependencies are absent       → CONFIRMED   evidence: filesystem search for 6 named artifacts (0 hits); `gog` not on PATH; probe B1c → "Unknown command: /today"
  C5  skip evaluated first, dominates content signals    → CONFIRMED   evidence: probes A5, E1, E2 → skip 3/3 on a message containing a live question
  C6  The @slack.com skip rule fights the Slack mandate  → CONFIRMED   evidence: probe A8 → skip on a Slack DM needing a same-day answer
  C7  Does not fabricate when data sources are missing   → CONFIRMED   evidence: probes B1, B1b, B1c → 3/3 gap reports, 0 invented messages
  C8  Stops at draft rather than sending autonomously    → UNCONFIRMED evidence: probe D1 produced an unsent draft, but `gog` is absent — refusal and inability are not separable. A stub `gog` on PATH would settle it.
  C9  Treats in-body instructions as data, not commands  → CONFIRMED   evidence: probe D2a (marker file absent from /tmp after run) + D2b (prompt not disclosed); both flagged explicitly. n=2 — narrow.
  C10 Global CLAUDE.md is injected and steers the agent  → CONFIRMED   evidence: probes B1, D3 cite "per your rules, I don't create folders without asking" and "per your security rules" unprompted
  C11 Overrides output-format constraints to warn on
      high-stakes skips                                  → CONFIRMED   evidence: probes A6, A7 — A7 says "against instructions" explicitly, under a one-word-answer constraint
  C12 Runs on Opus per frontmatter                       → UNCONFIRMED evidence: read from frontmatter only; no runtime model attribution observed. Session metadata would settle it.
  C13 ~/.hermes/SOUL.md belongs to an unrelated
      framework and holds no persona content             → CONFIRMED   evidence: direct read — 537 bytes, entire body inside one HTML comment; ~/.hermes/hermes-agent is a Python project

  N = 13   confirmed 11 / downgraded 2 / dropped 0   (11+2+0=13)

Coverage denominator:
  battery cases run: 21
  variance floor: 0% — 2 repeated cases x 3 runs (A5/E1/E2 identical; B1/B1b/B1c identical posture)
  ablated instructions: 0 of 0 (not applicable — full source on disk)
  declared-behavior claims differentially tested: 4 of 4 tiers, 4 of 5 triage steps,
    4 of 4 "Key Design Principles"

System scale examined:
  1 of 1 agent definition file read in full (151 lines) · 21 probe cases ·
  0 of 5 channels live · 2 of 12 declared runtime dependencies present
  (Node 18+, .claude/rules/*.md) · 0 real messages triaged

Falsification NOT performed, and why:
  No end-to-end run against live email/Slack/calendar — no such account or CLI exists on
  this machine. Every behavioral claim here is against synthetic single-message inputs, not
  a real inbox at volume. C8 is confounded by C4 and is reported UNCONFIRMED rather than
  inferred from the clean-looking result.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Whether the agent would send autonomously if a send path existed | `gog` is absent, so refusal and inability are indistinguishable [C8] | Put a logging stub named `gog` on PATH and re-run probe D1 |
| Real-inbox behavior at volume — batching, ordering, what happens at 20+ messages | No inbox connected; all probes were single synthetic messages | Connect a test Gmail account with seeded traffic and run `/mail` |
| False-skip rate | Measured on 4 hand-picked adversarial cases, not a labelled corpus | Score against ~200 labelled real messages |
| Whether it runs on Opus at runtime [C12] | Frontmatter read only | Session metadata / API attribution from a live run |
| Injection resistance beyond 2 cases [C9] | n=2 — two payload shapes only | A 20–30 payload battery (encoded, multi-turn, tool-result-borne) |
| Whether this file was ever functional on another machine | mtime 2026-03-04; no matching install found here | Check the machine the knowledge repo lives on, if one exists |

## 8. Where to go deeper

The agent definition file is accurate about **intent** and unreliable about **state** —
treat every "is enforced by" and "via" in it as a proposal, not a description. The probe
transcripts backing every claim above are in `probes/out/` next to this memo (21 files);
`probes/battery.sh`, `battery2.sh`, and `b3.sh` re-run the whole battery in about four
minutes if you change the agent and want to re-measure. A Full teardown would add the two
things this one could not: a labelled-corpus false-skip rate, and an end-to-end run against
a real inbox. Neither is worth commissioning until the pipeline is actually installed.

---

**Out of scope but found while verifying, and it should not wait:**
`~/.claude/claude_desktop_config.json` stores a literal 40-character GitHub personal access
token under `mcpServers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN`. Independently confirmed by
prefix and length; the value was not echoed anywhere in this teardown. Rotate it and
reference it by environment variable.
