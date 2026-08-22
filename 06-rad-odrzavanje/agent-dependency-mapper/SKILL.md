---
name: agent-dependency-mapper
description: >-
  Maps agent-to-agent call dependencies in an AgentStack / Agent Studio system
  and derives blast radius, single points of failure (SPOF), orphan agents, and
  static-vs-runtime mismatches. READ-ONLY — never mutates or deletes agents. Use
  whenever the user asks "who calls this agent", "what breaks if X fails",
  "blast radius", "dependency map", "call graph", "find orphan or unused agents",
  "single point of failure", "before I delete an agent", or Serbian equivalents
  like "ko zove", "ko koga zove", "mapa zavisnosti", "sta puca ako pukne",
  "nadji sirocice", "pre nego sto obrisem agenta", "koji agenti zavise". Builds
  the call graph from BOTH static flow wiring (as_inspect_flow call_agent nodes)
  and the runtime call log (as_list_agent_calls), labels every edge by source,
  and produces a dependency report. Requires the Agent Studio MCP (as_* tools).
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__agent-studio__as_inspect_flow
  - mcp__agent-studio-db__as_inspect_flow
  - mcp__agent-studio__as_list_agent_calls
  - mcp__agent-studio-db__as_list_agent_calls
  - mcp__agent-studio__as_list_agents
  - mcp__agent-studio-db__as_list_agents
---

# Agent Dependency / Blast-Radius Mapper

Build the agent-to-agent call graph for an AgentStack / Agent Studio system and
answer: who calls whom, what breaks if a given agent fails (blast radius), which
agents are single points of failure, which are orphans (deletion candidates),
and where static wiring disagrees with real runtime behavior.

**This skill is READ-ONLY.** It inspects and reports. It NEVER edits flows and
NEVER deletes agents. It only *lists* deletion candidates — a human decides and
acts.

## Why both data sources (the core idea)
- **Static** (`as_inspect_flow` with `node_type="call_agent"`) = complete wiring,
  including edges that never executed; does not show real behavior.
- **Runtime** (`as_list_agent_calls`) = real calls + status/errors, but only
  EXECUTED edges, capped at the most recent N (max 100). Best-effort, not complete.
These diverge in practice. Static is authoritative for *wiring*; runtime adds
*behavior*. **Label every edge with its source: `static`, `runtime`, or `both`.**
Never assert an edge without a source — that is the anti-hallucination rule.

## Workflow
1. Read `reference/dependency-mapping.md` for the full algorithm, output template,
   and rules. Follow it.
2. Collect (all read-only):
   - `as_list_agents` → nodes (note `hasFlow`).
   - For each agent with a flow: `as_inspect_flow(agent_id, node_type="call_agent")`
     → static edges (`targetAgentId`, or `externalUrl` for external targets).
   - `as_list_agent_calls(since_hours=0, limit=100)` → runtime edges (aggregate
     distinct caller→callee with counts + last status). State the window in the report.
3. Merge static + runtime; set each edge's `source`. Cross-check callee ids/names
   against `as_list_agents` → flag `dangling` if a target no longer exists.
4. Derive: in/out-degree; blast radius (reverse reachability, use a `visited` set
   so cycles/self-loops can't infinite-loop); SPOF ranking; orphans (`in==0 && out==0`,
   cross-checked with empty flow); static-vs-runtime mismatches.
5. Produce the report using the template in `reference/dependency-mapping.md`.
   If a focus agent was named, scope to its upstream/downstream neighborhood.

## Hard rules
- READ-ONLY: never call mutation tools (`as_update_flow`, `as_patch_node_field`,
  `as_delete_agent`). List deletion candidates; the human acts.
- Every edge carries a `source`. Every number is direct tool output, never estimated.
- `hasFlow=false` → infer no outgoing edges; mark "no flow".
- Distinguish **orphan / empty-shell** (in=0, out=0, AND empty flow → deletion
  candidate) from **standalone leaf** (has a working flow but calls no other agent →
  normal, NOT a deletion candidate).
- If `as_list_agent_calls` output is too large to read inline, save it and extract
  distinct caller→callee pairs with a script (jq/python) rather than truncating.
- If static and runtime disagree, show BOTH with labels — do not pick one silently.

## Notes
- Runtime is capped at 100 recent calls; for large systems treat it as best-effort
  and rely on static for completeness of wiring.
- Tool names may be prefixed by the MCP server id (e.g. `mcp__<server>__as_list_agents`)
  and may need loading via ToolSearch before first use.

See `reference/dependency-mapping.md` for the algorithm details, the exact output
template, and the verification checklist.
