# DESIGN_SPEC.md Template (STEP 3)

> Loaded from `agent-scaffolder` STEP 3. Write to `agents/{agent_slug}/DESIGN_SPEC.md` via `obsidian_create_note`, using the output keys decided in STEP 2 (see references/prompt-templates.md).

## STEP 3 — Write DESIGN_SPEC.md

Now that output keys exist, write the spec to vault:
Path: `agents/{agent_slug}/DESIGN_SPEC.md`

```markdown
# {agent_name} — Design Spec
*Created: {today_date} | Version: 1.0 | Slug: {agent_slug}*

---

## Purpose
{Paragraph 1: what this agent does — its specific function in the pipeline or standalone}
{Paragraph 2: why it exists — what problem it solves, why it can't be skipped}
{Paragraph 3: what makes its output valuable — who or what consumes it and why}

## Pipeline Position
- **Receives from:** {upstream agent name OR "User trigger"}
- **Sends to:** {downstream agent name OR "Final output — no handoff"}
- **A2A format:** KEY:VALUE plain text (FORMAT C)
- **Detection key:** {FIRST_KEY}

## Use Cases

### UC-1: Standard run — strong input
**Input:** `{FIRST_KEY}: {realistic example value with good data}`
**Expected output:**
```
{OUTPUT_KEY_1}: {realistic expected output}
CONFIDENCE: ⭐⭐⭐
DATE: {today_date}
```

### UC-2: Error case — missing or unstructured input
**Input:** `{a message without the detection key, or completely unstructured}`
**Expected output:** `FORMAT_ERROR: Expected {FIRST_KEY} not found`

### UC-3: Edge case — valid input, borderline quality
**Input:** `{FIRST_KEY}: {vague or ambiguous value}`
**Expected output:**
```
{OUTPUT_KEY_1}: {minimal but valid output}
CONFIDENCE: ⭐
DATE: {today_date}
```
*Low confidence triggers review in evo-log — correct behavior.*

## Tools & Resources
| Tool | Purpose | Notes |
|------|---------|-------|
| kb_search | Memory recall at runtime | KB created via UI; topK=5 (increase to 15 after 20+ evo-log entries) |
| ai_response (processor) | Core reasoning + generation | Model: {model_id}, temp: {temperature} |
| ai_response (extractor) | Normalize to KEY:VALUE | Model: claude-haiku-4-5-20251001, temp: 0.1 |
{If has_web_search: "| web_search | Live web data retrieval | Required for real-time input |"}
{If has_downstream: "| call_agent | A2A trigger to {downstream_name} | agentId: {downstream_agent_id} |"}

## Constraints & Safety Rules
- NEVER fabricate statistics, metrics, or data not present in input or web results
- NEVER pass malformed output to downstream — use error codes
- NEVER use: "change the game", "revolutionize", "groundbreaking", "game-changer"
- If input detection fails → FORMAT_ERROR immediately, do not guess
- Quality gate must pass before call_agent fires
- {Domain-specific constraint 1 based on agent purpose}
- {Domain-specific constraint 2}

## Input Contract
Detection signal: `{FIRST_KEY}:` present in message.
Full expected payload:
- `{INPUT_KEY_1}`: {description}
- `{INPUT_KEY_2}`: {description}
(all expected keys from the upstream agent's output contract)

## Output Contract
{List every OUTPUT_KEY with description, matching what was generated in STEP 2}
- `CONFIDENCE`: ⭐ weak | ⭐⭐ credible | ⭐⭐⭐ strong
- `DATE`: YYYY-MM-DD
```

Use `obsidian_create_note` to write this file.

---

