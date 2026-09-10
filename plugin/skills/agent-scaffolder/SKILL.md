---
name: agent-scaffolder
description: >
  Fully scaffolds a new AgentStack agent from spec to live deployment using SOMA-standard architecture.
  Automates: agent creation, standard flow building (kb_search → processor → extractor → optional
  web_search and call_agent nodes), Obsidian vault initialization (DESIGN_SPEC.md, agent-card.md,
  instincts.md, evo-log.md), KB seeding with 3 documents, and smoke testing.
  Triggers: "create a new agent", "scaffold an agent", "napravi novog agenta", "add agent to pipeline",
  "dodaj agenta u pipeline", "set up new AgentStack agent", "build a new agent from scratch",
  "I want a new agent that does X", "kreiraj agenta", "hocu novog agenta", "napravi mi agenta".
  Use this only when plain scaffolding is what you want — no deterministic quality gate. If safety,
  anti-hallucination, or fail-closed behavior matters at all, use safe-agent-builder instead; it is
  the safer default for an unqualified "napravi mi agenta".
  Do NOT use for modifying existing agents (use as_patch_node_field directly) or debugging flows.
compatibility: Requires Agent Studio MCP (as_create_agent, as_get_agent, as_update_flow, as_update_agent_model, as_patch_node_field, as_add_kb_text, as_get_kb_embedding_status, as_list_agents, as_list_knowledge_bases, as_chat_with_agent, as_inspect_flow) to build and wire the live agent, and Obsidian MCP (obsidian_create_note, obsidian_read_note, obsidian_update_note) to write its Insights/instincts notes. Without both, scaffolding stops short of a deployed agent.
allowed-tools:
  - TodoWrite
  - mcp__agent-studio__as_create_agent
  - mcp__agent-studio-db__as_create_agent
  - mcp__agent-studio__as_get_agent
  - mcp__agent-studio-db__as_get_agent
  - mcp__agent-studio__as_update_flow
  - mcp__agent-studio-db__as_update_flow
  - mcp__agent-studio__as_update_agent_model
  - mcp__agent-studio-db__as_update_agent_model
  - mcp__agent-studio__as_patch_node_field
  - mcp__agent-studio-db__as_patch_node_field
  - mcp__agent-studio__as_add_kb_text
  - mcp__agent-studio-db__as_add_kb_text
  - mcp__agent-studio__as_get_kb_embedding_status
  - mcp__agent-studio-db__as_get_kb_embedding_status
  - mcp__agent-studio__as_list_agents
  - mcp__agent-studio-db__as_list_agents
  - mcp__agent-studio__as_list_knowledge_bases
  - mcp__agent-studio-db__as_list_knowledge_bases
  - mcp__agent-studio__as_chat_with_agent
  - mcp__agent-studio-db__as_chat_with_agent
  - mcp__agent-studio__as_inspect_flow
  - mcp__agent-studio-db__as_inspect_flow
  - mcp__obsidian__obsidian_create_note
  - mcp__obsidian__obsidian_read_note
  - mcp__obsidian__obsidian_update_note
---

# Skill: agent-scaffolder
*Version: 2.3 | Based on: IMPLEMENTATION_PLAN_V2.md*
*2.1 (2026-07-29): STEP 5d now dry-runs `as_update_flow` before applying — the call has no undo.*
*2.2 (2026-08-22): STEP 2/3/6/9 and their templates moved to `references/` — SKILL.md*
*2.3 (2026-08-22): Added `compatibility:` frontmatter field describing Agent Studio/Obsidian MCP dependency. No behavior change.*
*was 811 lines / ~7280 tokens, over the repo's own 500-line/5000-token limit (see*
*`skill-creator-pro/references/skill-writing-guide.md`). No behavioural change.*

## Trigger
Use this skill when the user wants to:
- "create a new agent", "scaffold an agent", "napravi novog agenta"
- "add agent to pipeline", "dodaj agenta u pipeline"
- "set up new AgentStack agent", "build a new agent from scratch"
- "I want a new agent that does X"

If the user did not explicitly ask to skip the quality gate: use **safe-agent-builder** instead. It builds the same agent plus a `function`-node validator and a fail-closed condition gate, and smoke-tests a deliberately bad input to prove the gate blocks. This skill is the right choice only when that gate is knowingly unwanted.

For modifying an existing agent's flow or prompts: describe what needs changing and use `as_patch_node_field` or `as_update_flow` directly.
For debugging a broken flow: use the flow-debugger skill (when available).
For syncing KB documents: use the kb-sync skill (when available).

---

## What This Skill Does

Fully scaffolds a new AgentStack agent using the SOMA-standard architecture:

1. Extracts agent name from trigger + collects 3 structured choices
2. Generates system prompts (processor + extractor) — output keys defined HERE first
3. Writes DESIGN_SPEC.md using real output keys
4. Creates agent in AgentStack
5. Builds standard flow: kb_search → [web_search?] → processor → extractor → [call_agent?]
6. Verifies flow was written correctly
7. Creates vault files: agent-card.md + instincts.md + evo-log.md
8. Seeds KB with 3 documents + patches kb_search node with real KB ID
9. Runs smoke test with UC-1 sample
10. Reports scaffold summary

---

## STEP 0 — Task List

Before anything else, call TaskCreate for each remaining step:
- "Extract agent name and collect spec"
- "Generate processor and extractor prompts"
- "Write DESIGN_SPEC.md to vault"
- "Create agent in AgentStack"
- "Build and verify flow"
- "Write vault files (agent-card, instincts, evo-log)"
- "Seed KB and patch kb_search node"
- "Run smoke test"
- "Deliver scaffold report"

Mark each task in_progress before starting it. Mark completed when done.

---

## STEP 1 — Extract Name + Collect Spec

### 1a. Extract agent name from the user's message

Look for patterns like:
- "create a new agent called X" → name = X
- "scaffold a X agent" → name = X
- "napravi agenta za X" → name = X (translate/infer)

If name is NOT clear: ask in plain text: "What do you want to call this agent?"

Derive `agent_slug` = name lowercased, spaces replaced with hyphens, no special characters.
Example: "Price Monitor" → `price-monitor`

### 1b. AskUserQuestion — 3 questions in ONE call

**Q1 — header="Pipeline Role"**
Question: "How does `{agent_name}` connect to other agents?"
Options:
- Standalone — triggered by user, no A2A connections (description: "Not connected to other agents")
- Receives input — gets input from an upstream agent (description: "Downstream end of a chain")
- Sends output — triggers a downstream agent when done (description: "Upstream end of a chain")
- Middle link — receives from one agent and triggers another (description: "Middle link in A2A chain")

**Q2 — header="Model"**
Question: "Which model should `{agent_name}` use?"
Options:
- claude-sonnet-4-6 (description: "Balanced quality + speed — best for most agents (Recommended)")
- claude-opus-4-6 (description: "Best reasoning, highest cost — for complex multi-step work")
- claude-haiku-4-5-20251001 (description: "Fastest and cheapest — good for simple extraction or classification")
- gpt-4.1-mini (description: "Cost-optimized OpenAI model — use if GPT ecosystem required")

**Q3 — header="Web Search"**
Question: "Does `{agent_name}` need to search the web for live data?"
Options:
- No — works from KB memory and input payload only (description: "Most agents — no web access needed")
- Yes — needs real-time web search (description: "Research, trend, or monitoring agents")

After answers, compute:
```
model_id       = Q2 answer string
has_web_search = Q3 = "Yes"
pipeline_role  = Q1 answer
```

Infer agent type from name for temperature:
| Pattern in name | Type | Temperature |
|----------------|------|-------------|
| intelligence / scout / research / monitor + Q3=Yes | Research | 0.3 |
| score / rank / rate / classify / analyze | Classifier | 0.1 |
| writer / creator / hook / composer / generator | Content | 0.8 |
| transform / convert / extract / parse / format / repurpose | Middleware | 0.4 |
| anything else | General | 0.6 |

### 1c. Conditional — resolve downstream agent

**Only if Q1 = "Sends output" OR "Middle link":**

Ask: "Which existing agent will `{agent_name}` trigger?" Then call `as_list_agents` to find matches. Store `downstream_agent_id`.

If downstream agent doesn't exist yet: set `downstream_agent_id = "TODO:{downstream_name}"` and note this in the final report.

---

## STEP 2 — Generate System Prompts

Read `references/prompt-templates.md` now and generate BOTH prompts (processor +
extractor) before writing any files. Output keys must be known before DESIGN_SPEC.md
(STEP 3) can be completed.

Decide the OUTPUT KEYS for this agent based on: what the downstream agent needs (if
pipeline), what domain the agent operates in (inferred from name), and the standard
pattern of always including CONFIDENCE and DATE at the end. The reference file has the
full 6-section Anthropic-structure processor prompt template (Role / Memory / Input
Contract / Processing Instructions / Output Contract / Failure Modes) and the fixed
extractor prompt used for every agent. Store both prompts in memory for use in STEP 5.

---

## STEP 3 — Write DESIGN_SPEC.md

Now that output keys exist (STEP 2), read `references/design-spec-template.md` and
write it to vault: `agents/{agent_slug}/DESIGN_SPEC.md`, via `obsidian_create_note`.
The template covers Purpose, Pipeline Position, three Use Cases (UC-1 standard, UC-2
error case, UC-3 edge case), Tools & Resources, Constraints & Safety Rules, and the
Input/Output Contracts — fill every placeholder using the real output keys from STEP 2,
not generic text.

---

## STEP 4 — Create Agent in AgentStack

```json
as_create_agent({
  "name": "{agent_name}",
  "description": "{1-sentence version of DESIGN_SPEC Purpose paragraph 1}",
  "model": "{model_id}",
  "system_prompt": "You are {agent_name}. Your detailed instructions are in your flow nodes. Await input."
})
```

⚠️ **Always explicitly set `model`** — the API default is `gpt-4.1-mini`. Never rely on it.

Store from response: `agentId`, `publicUrl`.

**Verify:** Call `as_get_agent(agent_name="{agent_name}")` and confirm:
- `model` = `{model_id}` (not gpt-4.1-mini)
- `name` = `{agent_name}`

If `as_create_agent` fails (name conflict): call `as_list_agents(search="{agent_name}")`, show result, ask user: "Agent '{name}' already exists (ID: {id}). Do you want to overwrite its flow, or use a different name?"

---

## STEP 5 — Build Flow + Verify

### 5a. Read current flow state

Call `as_inspect_flow(agent_name="{agent_name}")` first. Note current node/edge state.

### 5b. Build node array

**Node 1 — kb_search (always):**
```json
{
  "id": "kb_search-{agent_slug}-memory",
  "type": "kb_search",
  "data": {
    "topK": 5,
    "label": "{agent_name} Memory",
    "queryVariable": "user_message",
    "knowledgeBaseId": "PENDING_KB_CREATION"
  },
  "position": {"x": 200, "y": 50}
}
```

**[Node 2 — web_search — ONLY if Q3=Yes]:**
```json
{
  "id": "web_search-{agent_slug}-live",
  "type": "web_search",
  "data": {
    "label": "Live Web Search",
    "queryVariable": "user_message",
    "outputVariable": "search_results"
  },
  "position": {"x": 200, "y": 175}
}
```

**Node 3 — ai_response processor (always):**
```json
{
  "id": "ai_response-{agent_slug}-processor",
  "type": "ai_response",
  "data": {
    "label": "{agent_name} Processor",
    "model": "{model_id}",
    "prompt": "{PROCESSOR_PROMPT from STEP 2 — full text, no truncation}",
    "outputVariable": "agent_response",
    "temperature": {temperature from table}
  },
  "position": {"x": 200, "y": 300}
}
```

**Node 4 — ai_response extractor (always):**
```json
{
  "id": "ai_response-{agent_slug}-extractor",
  "type": "ai_response",
  "data": {
    "label": "Output Extractor",
    "model": "claude-haiku-4-5-20251001",
    "prompt": "{EXTRACTOR_PROMPT from STEP 2}",
    "outputVariable": "structured_output",
    "temperature": 0.1
  },
  "position": {"x": 200, "y": 450}
}
```

**[Node 5 — call_agent — ONLY if pipeline_role = Sends output OR Middle link]:**
```json
{
  "id": "call_agent-{agent_slug}-handoff",
  "type": "call_agent",
  "data": {
    "label": "Handoff to {downstream_name}",
    "agentId": "{downstream_agent_id}",
    "inputVariable": "structured_output"
  },
  "position": {"x": 200, "y": 600}
}
```

⚠️ **BINDING RULE:** `call_agent.inputVariable` MUST equal `extractor.outputVariable`. Both must be `"structured_output"`. Never change one without changing the other.

### 5c. Build edge array

**If NO web_search, NO call_agent:**
```json
[
  {"id": "e-memory-processor", "source": "kb_search-{slug}-memory", "target": "ai_response-{slug}-processor"},
  {"id": "e-processor-extractor", "source": "ai_response-{slug}-processor", "target": "ai_response-{slug}-extractor"}
]
```

**If web_search YES, NO call_agent:**
```json
[
  {"id": "e-memory-search", "source": "kb_search-{slug}-memory", "target": "web_search-{slug}-live"},
  {"id": "e-search-processor", "source": "web_search-{slug}-live", "target": "ai_response-{slug}-processor"},
  {"id": "e-processor-extractor", "source": "ai_response-{slug}-processor", "target": "ai_response-{slug}-extractor"}
]
```

**If call_agent YES (add to whichever edge set above):**
```json
  {"id": "e-extractor-handoff", "source": "ai_response-{slug}-extractor", "target": "call_agent-{slug}-handoff"}
```

### 5d. Write flow — dry run FIRST

`as_update_flow` **replaces the entire flow and has no undo.** Never call it directly.

1. Dry run — nothing is written:

```
as_update_flow(
  agent_name: "{agent_name}",
  nodes_json: ...,
  edges_json: ...,
  dry_run:    true
)
```

2. Read the dry-run result. Confirm the node and edge counts match what STEP 5a-5c built.
   If the tool reports any error or an unexpected count → **stop**, report it, do not apply.

3. Only then repeat the identical call with `dry_run: false`.

For an agent that already has a flow, also capture the current one with
`as_inspect_flow(agent_name="{agent_name}")` before step 3 and keep it in the run report,
so a rollback is possible.

### 5e. Verify — MANDATORY

Immediately call `as_inspect_flow(agent_name="{agent_name}")`. Confirm:
- [ ] `kb_search-{slug}-memory` node exists
- [ ] `ai_response-{slug}-processor` node exists
- [ ] `ai_response-{slug}-extractor` node exists
- [ ] If web_search: `web_search-{slug}-live` exists
- [ ] If call_agent: `call_agent-{slug}-handoff` exists
- [ ] Edge count = node count - 1 (linear chain)

If any check fails → STOP. Report exactly which node or edge is missing. Do not proceed to STEP 6.

---

## STEP 6 — Write Vault Files

Read `references/vault-file-templates.md` now and create 3 files via
`obsidian_create_note`:

- `agents/{agent_slug}/agent-card.md` — identity, KB, pipeline, input/output summary,
  and the exact `as_patch_node_field` call needed to wire another agent to this one
- `agents/{agent_slug}/instincts.md` — quality gate rules, input validation, output
  format rules, PLUS one domain-specific starter block (pick ONE based on the agent
  type inferred in STEP 1: research/trend, content creation, classification/scoring,
  pipeline middleware, or general purpose — never leave it blank)
- `agents/{agent_slug}/evo-log.md` — log format header, empty entries section

---

## STEP 7 — KB Seeding + Node Patching

### 7a. Guide user to create KB (manual step)

Tell user:
> "One manual step needed: Open **AgentStack UI** → find **{agent_name}** → go to **Knowledge Base** tab → create a new KB. Once created, come back and confirm."

Wait for confirmation: "KB ready", "done", "napravio sam", or similar.

### 7b. Get KB ID

Call `as_list_knowledge_bases(agent_name="{agent_name}")`.
Extract `id` field from the returned KB object. Store as `kb_id`.

If returns empty: KB not created yet — re-send the UI instruction.

### 7c. Seed 3 documents

Read each file from vault first:
```
obsidian_read_note("agents/{agent_slug}/DESIGN_SPEC.md")
obsidian_read_note("agents/{agent_slug}/instincts.md")
obsidian_read_note("agents/{agent_slug}/evo-log.md")
```

Then seed:
```
as_add_kb_text(kb_id="{kb_id}", text="{DESIGN_SPEC content}", title="DESIGN_SPEC")
as_add_kb_text(kb_id="{kb_id}", text="{instincts content}", title="instincts")
as_add_kb_text(kb_id="{kb_id}", text="{evo-log content}", title="evo-log")
```

### 7d. Patch kb_search node

```
as_patch_node_field(
  agent_name="{agent_name}",
  node_id="kb_search-{agent_slug}-memory",
  field_name="knowledgeBaseId",
  field_value="\"{kb_id}\""
)
```

### 7e. Update agent-card.md with real KB ID

`obsidian_update_note` has no substring-substitution mode — `mode` is `append` (default), `replace` (whole body) or `prepend`. To swap the placeholder:
1. `obsidian_read_note(path="...")`, paging until `has_more == false`.
2. Replace `PENDING_KB_CREATION` with `{kb_id}` in the body you read.
3. `obsidian_update_note(path="...", mode="replace", content=<full new body>)`.
Skipping the read, or reading only the first page, truncates agent-card.md.

### 7f. Poll embedding status

Call `as_get_kb_embedding_status(kb_id="{kb_id}")` every 20s, up to 5 times.
- `"ready"` → continue to STEP 8
- `"processing"` → wait and retry
- `"failed"` → report error, offer to re-seed (re-run 7c)

---

## STEP 8 — Smoke Test

### 8a. Get test input from DESIGN_SPEC UC-1

Read `agents/{agent_slug}/DESIGN_SPEC.md` and extract the UC-1 `**Input:**` value.

### 8b. Run test

```
as_chat_with_agent(
  agent_name="{agent_name}",
  message="{UC-1 input}"
)
```

### 8c. Validate response — check ALL of these:

- [ ] Response is not empty
- [ ] `FORMAT_ERROR` is NOT present
- [ ] All output keys from Output Contract are present in response
- [ ] `CONFIDENCE:` is present with a ⭐ value
- [ ] `DATE:` is present in YYYY-MM-DD format

### 8d. Pass → go to STEP 9.

### 8e. Fail → report what failed:

| Failure | Likely cause | How to fix |
|---------|-------------|-----------|
| Empty response | Agent not responding | Check `as_get_agent` — agent may be paused |
| FORMAT_ERROR on valid input | Processor prompt detection key wrong | `as_inspect_flow` → check processor prompt |
| Missing output keys | Output Contract in prompt incomplete | `as_patch_node_field` → update processor prompt |
| `{{kb_context}}` empty | KB not embedded yet | Wait for embedding or re-seed |

Do NOT mark scaffold complete if smoke test fails unless user explicitly overrides.

---

## STEP 9 — Scaffold Report, Error Handling, Rollback, Quality Bar

Read `references/report-and-checklists.md` now. It has:

- the STEP 9 scaffold report template (AgentStack summary, vault file checklist,
  pipeline wiring status, variable-binding integrity check, next steps) — fill it in
  from everything gathered in STEPs 1–8
- **Error Handling Reference** — likely cause and fix for each failure point in
  STEPs 1–8
- **Rollback Guide** — what exists and how to recover, keyed by which step failed
- **Quality Bar (14 checks)** — AgentStack / Vault / Smoke Test checklist to
  self-verify against before reporting the scaffold complete

Do not report the scaffold complete without running the Quality Bar checklist first.
