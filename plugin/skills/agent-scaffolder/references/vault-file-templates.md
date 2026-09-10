# Vault File Templates (STEP 6)

> Loaded from `agent-scaffolder` STEP 6. Three files, all written via `obsidian_create_note`: agent-card.md, instincts.md (pick ONE domain-specific starter block based on the agent type inferred in STEP 1), and evo-log.md.

## STEP 6 — Write Vault Files

Create 3 files using `obsidian_create_note`.

### agent-card.md — `agents/{agent_slug}/agent-card.md`
```markdown
# {agent_name} — Agent Card
*Created: {today_date}*

## Identity
- Agent Name : {agent_name}
- Agent ID   : {agentId}
- Public URL : {publicUrl}
- Model      : {model_id}
- Slug       : {agent_slug}

## Knowledge Base
- KB ID      : PENDING_KB_CREATION  ← Updated in STEP 7
- Documents  : DESIGN_SPEC, instincts, evo-log
- topK       : 5  (increase to 15 after 20+ evo-log entries)

## Pipeline
- Receives from       : {upstream OR "User trigger"}
- Sends to            : {downstream OR "Final output"}
- Downstream Agent ID : {downstream_agent_id OR "N/A"}

## Input
- Detection key : {FIRST_KEY}
- Full contract : See DESIGN_SPEC.md → Input Contract

## Output
{list output keys}
- CONFIDENCE, DATE

## How to Wire Another Agent to This One
```
as_patch_node_field(
  agent_name="{upstream_agent_name}",
  node_id="call_agent-{upstream_slug}-handoff",
  field_name="agentId",
  field_value="\"{agentId}\""
)
```
```

### instincts.md — `agents/{agent_slug}/instincts.md`

Generate with DOMAIN-SPECIFIC STARTER CONTENT (do not leave blank):

```markdown
# {agent_name} — Instincts
*Path: /agents/{agent_slug}/instincts*
*Last updated: {today_date}*

---

## Quality Gate Rules
- NEVER fabricate data not present in input or search results
- NEVER output partial KEY:VALUE — all output keys must be present, or use error code
- Banned phrases: "change the game", "revolutionize", "groundbreaking", "game-changer"
- If CONFIDENCE is ⭐ → note the reason in your output summary

## Input Validation
- Detection key: `{FIRST_KEY}:`
- If detection fails → FORMAT_ERROR immediately, do not attempt to process anyway
- If secondary key is missing but FIRST_KEY is present → process, treat missing key as empty

## Output Format Rules
- All outputs: KEY:VALUE, one pair per line, plain text, no markdown, no preamble
- CONFIDENCE uses stars only: ⭐ ⭐⭐ ⭐⭐⭐ — never write "high" or "medium"
- DATE format: YYYY-MM-DD — use {{current_date}} variable, do not hardcode

---

{INJECT domain-specific starter block based on inferred agent type:}

[RESEARCH / TREND DETECTION AGENTS — use when has_web_search=Yes or "intelligence/monitor/scout" in name]
## Signal Quality Rules
- Signals with version numbers or specific benchmarks outperform vague category descriptions by 3x
- Official source + measurable metric + practitioner reaction = ⭐⭐⭐
- Single source, no reactions, or content older than 48h = ⭐
- NEVER report "X is transforming Y industry" — too generic, downstream will reject
- When 2+ signals compete: pick the most specific name (tool name > category name)
- Angle suggestion must tie to what developers/users can DO — not just what it IS

[CONTENT CREATION / HOOK WRITING AGENTS — use when "writer/creator/hook/composer" in name]
## Content Quality Rules
- Each generated piece must contain: specific number OR named tool/person OR direct challenge
- Avoid passive voice in the opening 2 lines of any piece
- Each variation must use a different rhetorical pattern — never repeat patterns in one run
- If all variations feel similar → regenerate with explicit diversity instruction
- Confidence ⭐⭐⭐ = hook passes pattern interrupt + specificity + platform fit

[CLASSIFICATION / SCORING AGENTS — use when "score/rank/rate/classify/analyze" in name]
## Scoring Rules
- Score must be derived from explicit criteria, not gut feel
- If scoring criteria are partially met → score the met percentage, do not round up
- Document which criteria drove the score in the output field
- Confidence ⭐⭐⭐ = all scoring criteria could be evaluated; ⭐ = criteria were missing

[PIPELINE MIDDLEWARE AGENTS — use when "transform/convert/extract/parse/repurpose" in name]
## Transformation Rules
- Never drop keys from the input payload — pass unmodified keys through if not transforming them
- Only transform keys defined in your Output Contract — do not invent new keys
- If a key value is unusable → transform to empty string, do not omit the key entirely
- Chain integrity: downstream agent depends on exact key names — never rename keys mid-chain

[GENERAL PURPOSE — fallback]
## General Quality Rules
- Prefer specificity over generality in all output fields
- When uncertain about a value → use ⭐ confidence, do not omit
- Never guess at data you don't have — use error codes instead

---

## Common Mistakes to Avoid
*(Add after first runs — use evo-log-writer skill)*

## Quality Gate Failures
*(Add after first failed runs — use evo-log-writer skill)*
```

### evo-log.md — `agents/{agent_slug}/evo-log.md`
```markdown
# {agent_name} — Evolution Log
*Path: /agents/{agent_slug}/evo-log*

---

## Log Format
```
date | {primary_output_key} | confidence | summary | downstream_triggered
```

---

## Entries

*No entries yet. Agent created {today_date}.*
```

---

