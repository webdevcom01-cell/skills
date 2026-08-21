---
name: soma-model-preflight
version: 0.1.0
description: Pre-run guard for AgentStack model/API-key mismatches. Before an agent runs, checks every model it (and each flow node) uses against the API keys actually set on the server, catching the silent "input variable is empty" / no-op failures that happen when a required key is missing. Proposes a safe fallback (e.g. deepseek-chat or llama to gpt-4.1-mini, since only OPENAI_API_KEY is set) and applies it with as_update_agent_model after confirmation, or warns and stops. Built because ETL Pipeline Architect uses deepseek-chat + llama-3.3-70b with neither key set, so it fails at runtime. Use when the user says "preflight", "provjeri model", "check api keys", "why is the agent failing silently", "model fallback", "zameni model", "agent vraca prazno", "WILL FAIL", "pre nego sto pokrenem", or before running any non-OpenAI-model agent. Do NOT use to debug flow logic (use soma-agent-debugger) or check KB embeddings (use agent-health-check).
do_not_use_when:
  - User wants to debug flow/node logic (use soma-agent-debugger)
  - User wants a full system health scan incl. KB/embeddings (use agent-health-check)
---

# SOMA Model Preflight

## What this skill does

When an AgentStack agent is set to a model whose API key isn't configured on the server, it
doesn't error loudly — it fails quietly: empty AI responses, "input variable is empty"
downstream, a chain that just stops. This skill catches that **before** the run. It compares
each agent's configured models against the keys actually present, and when there's a gap it
offers a one-line fallback to a model that *does* have a key, applying it only on your say-so.

## Confirmed constants (live-verified this session, 2026-06-26)

```
API KEYS ON SERVER:
  OPENAI_API_KEY    ✅ SET
  DEEPSEEK_API_KEY  ❌ NOT SET
  GROQ_API_KEY      ❌ NOT SET

MODEL → REQUIRED KEY:
  gpt-4.1, gpt-4.1-mini, gpt-*        → OPENAI_API_KEY
  deepseek-chat, deepseek-*           → DEEPSEEK_API_KEY
  llama-3.3-70b-versatile, llama-*    → GROQ_API_KEY

DEFAULT SAFE FALLBACK (only key currently set): gpt-4.1-mini
KNOWN BROKEN AGENT: ETL Pipeline Architect (cmqi3knmt0007ko01nuezhtwg)
  node models: deepseek-chat (needs DEEPSEEK_API_KEY ❌), llama-3.3-70b-versatile (needs GROQ_API_KEY ❌)
```

These keys can change — re-verify with `as_diagnose_models` every run; never trust this
snapshot blindly.

## Hard rules (do not break)

1. **Verify keys live every time.** Run `as_diagnose_models` at the start — the key set may
   have changed since this file was written. Decisions follow live data, not the snapshot.
2. **Check node models, not just the agent model.** An agent can be `gpt-4.1-mini` overall
   while a single node uses `deepseek-chat`. Per-node mismatches cause the same silent fail.
3. **Never swap a model without confirmation.** `as_update_agent_model` changes behavior and
   cost; the user must approve each swap.
4. **Prefer the smallest behavior change.** Map a missing-key model to the closest available
   one (default `gpt-4.1-mini`), and say plainly that outputs may differ from the original
   model. Don't silently "upgrade" to an expensive model.
5. **If no key is available for any sane fallback → STOP and tell the user to add the key.**
   Don't pretend a run will succeed.

## Workflow

### STEP 0 — Task list
Create: "DIAGNOSE", "MAP GAPS", "PROPOSE FALLBACK", "CONFIRM", "APPLY", "VERIFY".

### STEP 1 — Diagnose
```
as_diagnose_models()                 # all agents
```
or for a single agent, also pull node-level detail:
```
as_get_agent(agent_id:<id>)          # confirms agentModel + node models
```
Record per agent: `agentModel`, `nodeModels[]`, `requiredKey`, `keyConfigured`, `status`.

### STEP 2 — Map the gaps
List every agent/node whose `requiredKey` is not set → these `WILL FAIL`. For the single-run
case, only the agent the user is about to run matters; for a system pass, list all.

### STEP 3 — Propose fallback
For each failing model, pick a replacement whose key IS set:
- `deepseek-*`, `llama-*`, any non-OpenAI model with a missing key → `gpt-4.1-mini`
  (the only family with a live key right now).
- If the agent already mixes a working OpenAI node, match that node's model for consistency.

Present clearly:
```
⚠️ PREFLIGHT — ETL Pipeline Architect (cmqi3knmt0007ko01nuezhtwg)
  node deepseek-chat            → needs DEEPSEEK_API_KEY ❌  → propose gpt-4.1-mini
  node llama-3.3-70b-versatile  → needs GROQ_API_KEY ❌      → propose gpt-4.1-mini
  Note: outputs will differ from deepseek/llama. Alternative: add the missing keys instead.
Apply swaps? (da / ne / "dodaću ključeve")
```

### STEP 4 — Apply (only confirmed)
For each confirmed swap:
```
as_update_agent_model(agent_id:<id>, model:"gpt-4.1-mini")
```
For per-node model overrides, use `as_patch_node_field(field_name:"model", ...)` on the
specific node rather than changing the whole agent, when only one node is wrong.

> Note: a node with an **empty prompt** (e.g. the ETL `ai_response-1781814128371` ERROR from
> the broken-flow scan) is a separate bug — swapping its model won't fix it. Flag it and
> route to `as_update_agent_prompt` / soma-agent-debugger.

### STEP 5 — Verify
Re-run `as_diagnose_models()` (or `as_get_agent`) and confirm the agent now shows `✅ OK`
with every model's key configured. Only then is it safe to run.

### STEP 6 — Report
```
🛡️ PREFLIGHT — DONE
Agent      : {name}
Before     : {n} model(s) with missing keys → WILL FAIL
Action     : {swaps applied} | {keys user will add} | {none}
After      : {✅ OK | ⚠️ still blocked — keys needed: <list>}
Safe to run: {yes | no}
```

## Optional: bake it into soma-run
Recommend running this as the first gate inside `soma-run` for any chain that includes a
non-OpenAI model, so a missing key is caught before TI ever fires.

## Invocation examples
```
"preflight ETL Pipeline Architect pre nego što ga pokrenem"
"zašto agent vraća prazan output?"
"check api keys za sve agente"
"model fallback — deepseek nema ključ, prebaci na nešto što radi"
"provjeri da li je sve spremno za run, da ne pukne tiho"
```

## Tool reference
| Tool | Used for |
|---|---|
| `as_diagnose_models` | Live key vs model check (start + verify) |
| `as_get_agent` | Per-node model confirmation |
| `as_update_agent_model` | Apply agent-level fallback (confirmed) |
| `as_patch_node_field` | Apply single-node model fallback (confirmed) |
| `as_update_agent_prompt` | Hand-off for empty-prompt nodes (separate bug) |

## Versioning
| Version | Date | Notes |
|---|---|---|
| v0.2 | 2026-06-26 | Invocation examples (house-style consistency) |
| v0.1 | 2026-06-26 | Initial — built around the ETL Pipeline Architect key-mismatch found in live audit |
