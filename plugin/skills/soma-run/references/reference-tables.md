# Error Recovery Guide, Tool Reference, Constraints Summary

> Loaded from `soma-run` STEP 10 and the two tables that follow it. Consult the Error Recovery Guide when any step FAILED (include the relevant row in the report); the Tool Reference and Constraints Summary are a final self-check.

## STEP 10 — Error Recovery Guide

Include this only in the report if a FAILED step occurred:

| Failed step | Likely cause | Action |
|---|---|---|
| TI FAILED (timeout) | Client 60 s cap — run is probably alive | NE slati ponovo. Poll `as_get_recent_executions`; povećanje `timeout_seconds` ne pomaže |
| Više novih TI execution-a nego poslanih zahtjeva | Client retry storm | Zadrži najraniji, ostale označi `DISCARD` — retry gubi URL iz poruke |
| TI FAILED (abort sentinel) | Agent misconfigured | Pokreni agent-health-check |
| TI FAILED (quality gate 0.0) | TI output bez topic/confidence/angle | Provjeri TI sistem prompt i KB wiring |
| TI WARN (quality gate < 1.0) | TI output nepotpun | Pipeline nastavio sa degraded handoff — provjeri TI instincts i KB |
| HW FAILED (timeout) | Large TI output | Pokušaj ponovo — HW timeout je 120s |
| HW FAILED (abort sentinel) | Bad handoff content | Provjeri {ti_handoff} — potvrdi da {ti_output} nije bio prazan ili malformiran |
| CR FAILED (any) | Pokušaj ponovo | CR rijetko faila na validan HW output |
| Evo-log write failed | Obsidian MCP nedostupan | Provjeri Obsidian MCP konekciju |

---

## Tool Reference

| Tool | Used for | Key params |
|---|---|---|
| `as_chat_with_agent` | Run TI / HW / CR | `agent_name`, `message`, `timeout_seconds` |
| `obsidian_read_note` | Read evo-log before write | `path` |
| `obsidian_update_note` | Append evo-log entry | `path`, `mode: "append"`, `content` |
| `obsidian_create_note` | Create evo-log if missing | `path`, `body` |

---

## Constraints Summary

| Constraint | Rule |
|---|---|
| Date injection | ALWAYS prefix TI message with "Today is YYYY-MM-DD." |
| TI→HW handoff | Always use `{ti_handoff}` — contains structured header + full `{ti_output}` verbatim. Never pass raw `{ti_output}` to HW. |
| HW→CR handoff | Pass raw `{hw_output}` to CR verbatim — no structured handoff needed. |
| Abort on sentinel | Check every agent output before passing downstream |
| Log only real data | Never write fabricated scores, trends, or hook text to evo-log |
| Read before write | Always `obsidian_read_note` before `obsidian_update_note` |
| Timeouts | TI: 180s | HW: 120s | CR: 120s — never use defaults |
| Winners threshold | Score ≥ 17/20 per platform — not just the overall winner |

---

---

## Invocation examples

```
"soma run — Claude Sonnet 4 released, SWE-bench +40%"
"pokreni pipeline — https://anthropic.com/news/claude-sonnet-4"
"run SOMA — samo TI"
"pusti trend kroz pipeline: OpenAI GPT-5 Turbo announced"
"soma-run — TI i HW samo, bez CR"
"run the pipeline on this: Anthropic released Claude 4 Opus today"
```
