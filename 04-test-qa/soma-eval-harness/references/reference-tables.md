# Edge Cases, Scope Boundary, Tool Reference, Integrity Check

> Loaded from `soma-eval-harness`. Consult as needed: the Edge Cases table for unusual conditions during a run (too few triples, all-TIMEOUT, unanswered H1, missing baseline.md, 0/5 regression, guardrails not catching bad input); Scope Boundary to confirm this is the right skill vs. soma-run / evo-log-writer / soma-performance-review / agent-health-check / instincts-updater; Tool Reference for the 4 MCP tools this skill calls; Integrity Check as a post-deploy self-verification of the 8 key markers.

## Edge cases

- **< 3 complete triples in vault:** "Not enough for dataset. Enter a trend manually." → single-task.
- **valid_trials < 3:** INCONCLUSIVE → re-run / agent-health-check.
- **All 5 trials TIMEOUT:** valid=0 → "⛔ All timed out. Run agent-health-check."
- **H1 unanswered after 2 asks:** trial = H1_PENDING, excluded, reported.
- **M1 unparseable:** retry 1×; else M1 = ERROR → H1; if H1 unavailable → trial ERROR (excluded).
- **baseline.md missing:** create with current results; mark all "INITIAL BASELINE — no regression detection".
- **Regression and correct_count = 0/5:** flag BEFORE writing: "⛔ CRITICAL: 0/5 for [trend]. Run instincts-updater + agent-health-check."
- **All guardrail tasks observed PASS (agent accepts bad input):** "⚠️ Guardrails not catching bad input — check CR quality gate."
- **Run-entry found under ## Change Log:** strict parser skips it; only pinned cases pull such runs.

---


## Scope boundary

| Scenario | Skill |
|---|---|
| Production run | soma-run |
| Log a finished run | evo-log-writer / winners-log-logger |
| Summarize past runs | soma-performance-review |
| Pre-run system check | agent-health-check |
| **Reliability / quality-gate eval** | **soma-eval-harness** |
| Update instincts | instincts-updater |

---


## Tool reference

| Tool | Used for |
|---|---|
| `as_chat_with_agent` | Run TI / HW / CR (agent_name, message, timeout_seconds) |
| `obsidian_read_note` | Read evo-logs (read-only) + read eval notes before write |
| `obsidian_update_note` | Append/update eval reports & baseline (mode: append/replace) |
| `obsidian_create_note` | Create eval notes if missing |

---


## Integrity check after deploy

Verify these 8 markers in the installed Instructions:
```
"Trend Intelligence" | "Hook Writer" | "Content Repurposer"
<<SOMA_HANDOFF_START>>
len < 50 characters                     (abort sentinel)
Read ONLY the "## Entries" section
"is_evergreen" OR "fresh"               (dual confidence)
≥ 4 of 5 platforms score ≥ 4            (M1 collapse)
trial_correct = (observed_grade == expected_grade)
correct_count = number of trials with trial_correct = true
```
