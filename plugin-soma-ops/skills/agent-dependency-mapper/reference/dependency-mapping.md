# Dependency / Blast-Radius Mapping
# Source: SOMA remediation session 2026-06-28 (verified MCP outputs: as_list_agents, as_inspect_flow node_type=call_agent, as_list_agent_calls). Ground-truth confirmed on live 16-agent system.
# Reference for soma-agent-debugger Mode 5. Read-only — this mode NEVER mutates agents.

## Purpose
Build the agent-to-agent call graph and derive: who calls whom, blast radius (if agent X fails, which agents stop), single points of failure (SPOF), orphans (no in/out edges — deletion candidates), and static-vs-runtime mismatches. Closes the "cross-agent dependency mapping" gap previously listed as not-built.

## Two data sources — use BOTH, label every edge
- **Static** (`as_inspect_flow node_type="call_agent"`): complete wiring, includes edges that never executed; does NOT show real behavior.
- **Runtime** (`as_list_agent_calls`): real calls + status/errors; only EXECUTED edges, limited to recent N (max 100). Best-effort, NOT complete.
- They diverge in general. Static is authoritative for wiring; runtime adds behavior. **Every edge gets `source ∈ {static, runtime, both}`.** Never assert an edge without a source.

## Algorithm
1. **Nodes:** `as_list_agents` → map `id → {name, hasFlow}`. Agents with `hasFlow=false` have no outgoing edges — mark "no flow", do not infer.
2. **Static edges:** for each agent with `hasFlow=true`, `as_inspect_flow(agent_id, node_type="call_agent")`. For each `call_agent` node:
   - if `data.targetAgentId` set → edge `caller → targetAgentId` (source `static`), capture `inputMapping`, `onError`, `timeoutSeconds`.
   - if `data.externalUrl` set instead → edge `caller → external:<url>` (treat as external node).
   - Caveat: `edgeCount` in the inspect response is the FULL edge count (not filtered by node_type). To flag an empty-shell agent use `edgeCount==0` together with `nodeCount==0`, not the filtered view alone.
3. **Runtime edges:** `as_list_agent_calls(since_hours=0, limit=100)`. Aggregate distinct `callerAgentName → calleeAgentName` pairs with call count + last status + last error. Source `runtime`. State the window in the report ("runtime: last 100 calls").
4. **Merge:** union static + runtime; set `source` to `both` where an edge appears in both, else `static` or `runtime`.
5. **Cross-check dangling:** if a runtime/static callee id/name is not in `as_list_agents` → mark `dangling` (renamed/deleted target).
6. **Derive metrics per node:**
   - `out-degree` (callees), `in-degree` (callers).
   - **Blast radius(X)** = all agents that depend on X directly or transitively (reverse reachability over edges). Use a `visited` set to handle cycles/self-loops — never infinite-loop.
   - **SPOF rank** = nodes by in-degree / blast-radius size (high = critical; e.g. a shared security/validator agent).
   - **Orphans** = `in-degree==0 && out-degree==0` (cross-check empty flow). Deletion candidates.
   - **Mismatches**: `runtime-only` edge (called but not wired in current flow → stale or recently-removed wiring) and `static-only` edge (wired but never executed → possible dead branch).

## Output template (text/table — NO diagram by design)
```markdown
## Dependency Map — <whole system | agent X> — <date>
Runtime window: last 100 calls (best-effort). Static = authoritative for wiring.

### Edges
<caller> --(source)--> <callee>
...

### Per agent
| Agent | Calls (out) | Called by (in) | Blast radius | Note |
|---|---|---|---|---|
| <name> | <list/—> | <list/—> | <n> | <SPOF / orphan / external / —> |

### Single points of failure (ranked)
1. <agent> — <n> dependents: <list> — if it fails: <impact>

### Orphans (deletion candidates)
- <agent> (in=0, out=0, empty flow?: yes/no)

### Static vs runtime mismatches
- runtime-only: <edge> (called but not in current flow — verify)
- static-only: <edge> (wired but never executed — dead branch?)
- dangling: <edge> (target not in agent list)

### Recommendations (read-only — human acts)
- SPOF <X>: add fallback / fail-closed / reduce coupling
- orphan <Y>: delete (as_delete_agent, after confirmation) or build
```

## Anti-hallucination rules (mandatory)
1. Every edge carries its `source` — never "I believe it calls".
2. Every number (in/out-degree, call counts) is direct tool output, never estimated.
3. `hasFlow=false` → no outgoing edges inferred; mark "no flow".
4. Read-only: list deletion candidates; NEVER call `as_delete_agent` yourself. Human deletes after confirmation.
5. If static and runtime disagree, show BOTH with labels — do not pick one silently.

## Verification (ground truth from build session 2026-06-28)
Run on the live system and confirm:
1. Security Supervisor: static in-degree = 1 (X Trend Scanner, `both`); runtime in-degree = 4 (SAA, Content Creator, Lead Scorer, X Trend Scanner); SAA/CC/LS labeled `runtime-only` (their static edges were removed during remediation). Flagged as SPOF.
2. Empty-shell agents (Email Campaign Copywriter, ETL Pipeline Architect, Risk Management Specialist, UX Architect) → orphans / empty flow.
3. Chains reconstructed: `Input Validator → Trend Intelligence → Hook Writer → Content Repurposer`; `SOMA Evolution Advisor → SOMA Improvement Dispatcher`.
4. Every edge has a source label.
Re-derive the oracle from live state at run time — the system may change.
