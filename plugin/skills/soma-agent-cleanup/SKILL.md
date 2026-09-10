---
name: soma-agent-cleanup
version: 0.1.1
description: Finds and safely removes duplicate or abandoned AgentStack agents. Detects agents sharing a name, ranks each cluster by real usage (agent-to-agent calls + recent executions + wired flow), proposes which copy to KEEP and which to DELETE, and deletes only after explicit human confirmation. Built for workspaces left with accidental duplicates from repeated batch scaffolding (e.g. Email Campaign Copywriter x5). Use when the user says "clean up agents", "remove duplicates", "obrisi duplikate", "ocisti agente", "imam duplikate", "dedup agents", "which agents are unused", "koji agenti se ne koriste", "delete agent", "obrisi agenta", "sredi listu agenata", or after a scaffolding batch created copies. Do NOT use to fix a broken flow (use soma-agent-debugger), build a new agent (use agent-scaffolder / safe-agent-builder), or edit one field (use as_patch_node_field). Deletion is destructive and never automatic.
compatibility: Requires Agent Studio MCP (as_list_agents, as_get_agent, as_inspect_flow, as_get_recent_executions, as_list_agent_calls, as_find_broken_flows, as_patch_node_field, as_delete_agent) -- ranks duplicate or abandoned agent clusters by real usage before proposing which copy to keep.
do_not_use_when:
  - User wants to fix a broken flow (use soma-agent-debugger)
  - User wants to create a new agent (use agent-scaffolder or safe-agent-builder)
  - User wants to patch one node field (use as_patch_node_field directly)
allowed-tools:
  - Read
  - Glob
  - Grep
  - TodoWrite
  - mcp__agent-studio__as_list_agents
  - mcp__agent-studio-db__as_list_agents
  - mcp__agent-studio__as_get_agent
  - mcp__agent-studio-db__as_get_agent
  - mcp__agent-studio__as_inspect_flow
  - mcp__agent-studio-db__as_inspect_flow
  - mcp__agent-studio__as_get_recent_executions
  - mcp__agent-studio-db__as_get_recent_executions
  - mcp__agent-studio__as_list_agent_calls
  - mcp__agent-studio-db__as_list_agent_calls
  - mcp__agent-studio__as_find_broken_flows
  - mcp__agent-studio-db__as_find_broken_flows
  - mcp__agent-studio__as_patch_node_field
  - mcp__agent-studio-db__as_patch_node_field
  - mcp__agent-studio__as_delete_agent
  - mcp__agent-studio-db__as_delete_agent
---

# SOMA Agent Cleanup

## What this skill does

Repeated batch scaffolding leaves behind copies of the same agent — same name, different
ID, created seconds apart. They clutter the agent list, confuse `call_agent` targeting
(which copy is the live one?), and inflate health checks. This skill detects those clusters,
figures out which copy is actually being used, and removes the rest — but only after you
confirm, because `as_delete_agent` cannot be undone.

## Hard rules (do not break)

1. **Never auto-delete.** Always present a KEEP/DELETE plan and wait for explicit "da" /
   "yes" per cluster (or per agent). Deletion is irreversible.
2. **Usage decides, not creation order alone.** The copy that other agents actually call,
   or that has recent successful executions, is the live one — even if it isn't the oldest.
3. **Never delete an agent that is a live `call_agent` target** until its callers are
   re-pointed to the survivor. Breaking a wired chain is worse than a duplicate. Wiring lives
   in **flow nodes**, not in call logs — a duplicate can be a wired target with zero recent
   calls. You MUST scan flows (Step 4), not just logs, before any delete.
4. **Verify against live data every time.** Re-list agents, scan flows, and read call logs in
   the current session before proposing deletions — never act on a stale list.
5. **One cluster at a time.** Confirm and execute per name-cluster so a mistake can't cascade.

## Workflow

### STEP 0 — Task list
Create: "INVENTORY", "CLUSTER", "USAGE SCORING", "PROPOSE PLAN", "CONFIRM", "DELETE", "VERIFY".

### STEP 1 — Inventory
```
as_list_agents(limit:200)
```
Record id, name, model, isPublic and category for every agent — that is what this
tool returns. `hasFlow` and `createdAt` are NOT in the response; establish flow
presence per candidate in STEP 3 via `as_get_agent` / `as_inspect_flow`.

### STEP 2 — Cluster by name
Group agents with identical (case-insensitive) names. Any group with count ≥2 is a
duplicate cluster. Singletons are out of scope (but flag any agent with `hasFlow:false` as
possibly abandoned — mention, don't delete).

### STEP 3 — Score usage within each cluster
For each agent in a cluster gather live signals:
- `as_get_recent_executions(agent_id:<id>, limit:10, status:"COMPLETED")` → count of
  completed runs. **The status enum is `PENDING | RUNNING | COMPLETED | FAILED | CANCELLED`
  — there is no `SUCCESS`.** Filtering on a value that does not exist silently returns
  nothing, which zeroes this term for every candidate.
- Per-ID caller detection: from the STEP 4 `as_inspect_flow` scan, collect every
  `call_agent` node's `targetAgentId`. **Do not use `as_list_agent_calls` for this** —
  it filters by agent *name* (ILIKE) and returns names, not IDs, so every duplicate in
  a cluster shares the same value and the term cannot discriminate between them.
- Wired flow: derive per candidate from `as_get_agent` / `as_inspect_flow`.
  **`as_list_agents` does not return `hasFlow` or `createdAt`** — it returns name,
  model, isPublic, category and IDs only. Score 0 when the flow cannot be established
  rather than inferring it.

Rank each cluster member:
```
live_score = (this id appears as a call_agent targetAgentId, or has outgoing
              call_agent edges? +100)
           + (COMPLETED executions for this agent_id × 10)
           + (flow confirmed present ? +5 : 0)
           + (creation order as tiebreak ONLY)
```
Highest `live_score` = **KEEP**. The rest = **DELETE candidates**.

### STEP 4 — Dependency check before proposing (flow-level, not just logs)
Call logs only show agents that have *actually been called recently*. A duplicate can be
**wired as a `call_agent` target in a flow yet never called** — deleting it silently breaks
that chain. So check both layers for every DELETE candidate id:

1. **Flow wiring (authoritative).** Scan every agent's flow for `call_agent` nodes pointing at
   the candidate. For each other agent run `as_inspect_flow(agent_id:<other>,
   node_type:"call_agent")` and read each node's `targetAgentId`. (Tip: `as_find_broken_flows`
   already proves all current targets resolve to existing agents — but it won't tell you
   *which* duplicate is the target, so you still need the per-flow `targetAgentId` read.)
2. **Call logs (recency signal).** `as_list_agent_calls(callee_agent_name:<name>,
   since_hours:0)` as a secondary confirmation of live use.

If any flow's `targetAgentId` == a DELETE candidate and the chosen survivor has a different
id → do **not** delete yet. First re-point the caller to the survivor, then delete:
```
as_patch_node_field(agent_id:<caller>, node_id:<call_agent node>,
                    field_name:"targetAgentId", field_value:"\"<survivor_id>\"")
```
(This is the exact wiring pattern documented in the Hook Writer KB agent-card.) Only after the
caller points at the survivor — re-verify with `as_inspect_flow` — is the candidate safe to delete.

### STEP 5 — Present the plan
```
🧹 CLEANUP PLAN
Cluster: "Email Campaign Copywriter" (5 copies)
  KEEP   cmqh3cmnh0007k001oti5pjuw  | flow ✓ | 3 recent runs | called by X  ← survivor
  DELETE cmqh3cn3b000bk001wtwxjhge  | flow ✓ | 0 runs | no callers
  DELETE cmqh3cn82000fk001sv02uib8  | flow ✓ | 0 runs | no callers
  ... (etc)
Reason: survivor selected by usage; deletes have zero executions and no callers.
```
Repeat per cluster. Then ask, per cluster: **"Potvrdi brisanje ovog clustera? (da/ne)"**

### STEP 6 — Delete (only confirmed)
For each user-confirmed DELETE id:
```
as_delete_agent(agent_id:<id>, confirm:true)
```
**`confirm:true` is required.** Without it the tool returns a dry-run preview and
deletes nothing, while the rest of this skill still reports the cleanup as done.
Call it once WITHOUT `confirm` first, show that preview inside the STEP 5 plan so
the user sees exactly what would be removed, then re-call with `confirm:true`
only after per-cluster approval.

Never batch across clusters without per-cluster confirmation.

### STEP 7 — Verify
Re-run `as_list_agents(limit:200)` and confirm the deleted IDs are gone and survivors remain.
Optionally run `agent-health-check` to confirm no broken flows were introduced.

### STEP 8 — Report
```
✅ CLEANUP DONE
Clusters processed : N
Agents deleted     : K  (list ids)
Survivors kept     : list
Singletons flagged as possibly abandoned (NOT deleted): list (hasFlow:false)
```

## Edge cases
- **All copies unused, none called** → keep the one with a flow and the oldest createdAt;
  delete the rest after confirmation.
- **Two copies both actively called by different chains** → not true duplicates; do NOT
  delete. Report the divergence so the user can decide.
- **User wants to delete a singleton** → allowed, but re-confirm because there's no survivor.

## Invocation examples
```
"očisti agente — imam gomilu duplikata"
"remove duplicate Email Campaign Copywriter agents"
"koji agenti se ne koriste i mogu da se obrišu?"
"dedup agents but show me the plan before deleting anything"
"obriši duplikate Risk Management Specialist, zadrži onaj koji se koristi"
```

## Tool reference
| Tool | Used for |
|---|---|
| `as_list_agents` | Inventory + post-delete verify |
| `as_get_recent_executions` | Usage signal per copy |
| `as_inspect_flow` | Flow-level `call_agent` targetAgentId dependency scan |
| `as_list_agent_calls` | Caller/callee recency signal |
| `as_patch_node_field` | Re-point a caller to the survivor before deleting |
| `as_delete_agent` | Irreversible delete (confirmed only) |
| `agent-health-check` (skill) | Optional post-cleanup sanity scan |

## Versioning
| Version | Date | Notes |
|---|---|---|
| v0.2 | 2026-06-26 | P1: flow-level `call_agent` targetAgentId dependency scan + caller rewire before delete; invocation examples |
| v0.1 | 2026-06-26 | Initial — targets the duplicate clusters found in live audit |
