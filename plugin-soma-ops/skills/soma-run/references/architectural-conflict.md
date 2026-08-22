# Known Architectural Conflict — Double-Orchestration

> Loaded from `soma-run`. Full evidence for why scope must stay `"TI"` until the decided fix (removing the `call_agent` nodes from TI/HW) ships. Read this before ever running `"TI+HW"` or `"FULL"` scope, and before touching this skill's orchestration model.

## ⚠️ Known architectural conflict — read this before running FULL scope

**The agents already chain themselves server-side. This skill does not know that.**

Verified by reading the live flows and by two measured runs on 2026-07-29
(`2026-07-29-154101`, `2026-07-29-155852`):

- `Trend Intelligence` contains a `call_agent` node targeting `Hook Writer`
  (`targetAgentId: cmp832hkithbhj9suiqgmjqpw`, `timeoutSeconds: 300`, `onError: continue`)
- `Hook Writer` contains `call_agent-cr` targeting `Content Repurposer`
- `Content Repurposer` has no `call_agent` nodes — it is terminal

The IDs quoted in this section are **evidence of what was observed on 2026-07-29**, not lookup
keys. Never paste them into a tool call — resolve agents by name (`as_get_agent`,
`as_list_agents`) and re-read the flows, because an agent recreated in a cleanup gets a new ID
while the name stays.

Calling **only TI** therefore executes the whole chain. Measured, nested, in both runs:

| agent | run 1 | run 2 |
|---|---|---|
| TI | 96.5 s | 113.8 s |
| HW (nested inside TI) | 51.0 s | 50.9 s |
| CR (nested inside HW) | 31.0 s | 30.6 s |

HW and CR deviated by **less than 0.5 s** between the two runs — a stable pattern, not chance.

**Consequence for this skill:** STEP 5b and STEP 6b call HW and CR again, externally. TI has
already called both. Completing those steps means **HW executes twice and CR three times** —
triple cost, three different sets of hooks, and the wrong set logged. This is the exact
failure reproduced on 2026-06-19 (`HW → BLOCKED wrong_count 0/5`, `CR → BLOCKED missing_trend`):
the gates were working correctly, they were being fed the wrong stage's output.

### What to do until this is resolved

**Do NOT run `pipeline_scope: "FULL"` or `"TI+HW"`.** Run scope `"TI"` — it produces the
complete chain anyway. See STEP 1.

### Why this skill has not been rewritten to match

The decision was already made and is recorded in the vault:
`system/soma-run-double-orchestration-conflict.md` (2026-06-19, status `decided`).

The chosen fix is **Option 2 — remove the `call_agent` nodes from TI and HW**, planned as a
separate sprint, so that external stage-by-stage orchestration (which `soma-run`,
`evo-log-writer`, `winners-log-logger`, `pipeline-input-validator`, `pipeline-debug` and
`soma-performance-review` all assume) becomes the single source of truth about who drives
the pipeline.

The same document names the opposite fix — keep internal chaining, rewrite `soma-run` to call
only TI and parse the final posts — but makes it conditional on the pipeline needing to run
autonomously via scheduler/heartbeat without a skill. Checked live on 2026-07-29: TI
(`cmpnu72fy0008p401ixaaehq8`) has **no heartbeat configured** and **no goals linked**; Hook
Writer (`cmp832hkithbhj9suiqgmjqpw`) has **no heartbeat configured**. That condition is not
met, so the inverse rewrite is not the correct change today.

**Do not "fix" this skill by making it supervisory without revisiting that decision document first.**

### One more measured limit — and it is worse than a lost response

The MCP client aborts at **60 s** regardless of `timeout_seconds` (the schema accepts up to
300). TI takes 68-113 s. So **every** blocking call to TI times out client-side while the
server-side run completes normally.

Measured again on 2026-07-29 (18:37-18:49 UTC), and this time the follow-on effect was
observed: **the client retries the aborted request, and each retry launches another full
server-side chain.** Two user requests produced **six** TI runs, six HW calls and six CR
calls - 18 agent executions.

Worse, the retries are not equivalent to the first attempt:

| attempt | source actually fetched | correct |
|---|---|---|
| request 1, try 1 | `anthropic.com/news/claude-science-ai-workbench` | yes |
| request 2, try 1 | `openai.com/index/the-next-evolution-of-the-agents-sdk/` | yes |
| 4 retries | `anthropic.com/research/diff-tool` (in neither input) | no |

Both first attempts honoured the URL in the message. All four retries lost it, fell back to
`search_results`, and picked the `PRI[0]` domain - the exact failure mode patched that same
morning. Every one of those runs still reached `READY_FOR_REVIEW` with clean, grounded posts
about the wrong article. No gate catches this, because nothing about the output is malformed.

**Therefore: never call TI with a blocking wait from this client.** Use fire-and-poll
(STEP 4c). Full evidence: `system/mcp-chat-timeout-retry-storm-2026-07-29.md`.

---

