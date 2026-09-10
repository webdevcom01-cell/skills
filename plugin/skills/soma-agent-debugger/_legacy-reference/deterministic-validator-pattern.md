# Deterministic Validator Pattern
# Source: safe-agent-builder/references/flow-templates.md (confirmed read 2026-06-14)
# Complete function + condition + emitter triple for AgentStack gate flows.

## Core Protocol

The validator returns exactly two possible values:
- The string `"PASS"` — when all checks pass (no blocking violations)
- A JSON array of violation objects — when one or more blocking checks fail

The condition (gate) node checks: `variable == "PASS"` using `operator: "equals"`.
Do NOT check `violations.length === 0` — the validator does not return an empty array on pass.

---

## Node 1: Validator (function type)

### asText() helper — ALWAYS include at top of validator code
```js
function asText(x) {
  if (typeof x === "string") return x;
  try { return JSON.stringify(x); } catch(e) { return String(x); }
}
```

### Full validator template (parametrize {{PLACEHOLDERS}})
```js
var raw = variables.{{PAYLOAD_VAR}} || "";
raw = raw.replace(/^```(?:json)?\s*\n?/, "").replace(/\n?```$/, "").trim();
var p;
try { p = JSON.parse(raw); }
catch (e) {
  var head = String(raw).slice(0, 80);
  if (head.indexOf("BLOCKED:") === 0 || head.indexOf("MALFORMED_PAYLOAD:") === 0) {
    return JSON.stringify([{ field: "all", rule: "agent_error", detail: head, severity: "error" }]);
  }
  return JSON.stringify([{ field: "all", rule: "json_parse_error", detail: "cannot parse payload", severity: "error" }]);
}

var v = [];

// INPUT GUARD: reject fabricated / absent core input
var core = (p.{{CORE_FIELD}} && (p.{{CORE_FIELD}}.title || p.{{CORE_FIELD}}.id || p.{{CORE_FIELD}})) || "";
var coreNorm = String(core).trim().toLowerCase();
if (!coreNorm || coreNorm === "n/a" || coreNorm === "na" || coreNorm === "none" || coreNorm === "unknown") {
  v.push({ field: "all", rule: "missing_{{CORE_FIELD}}", detail: "{{CORE_FIELD}} empty/N/A — fabricated or absent", severity: "error" });
}

// ITEM COUNT CHECK
var items = p.{{ITEMS_KEY}} || [];
if (!Array.isArray(items) || items.length !== {{EXPECTED_COUNT}}) {
  v.push({ field: "all", rule: "wrong_count", detail: (Array.isArray(items) ? items.length : 0) + "/{{EXPECTED_COUNT}}", severity: "error" });
}

// BANNED PHRASE CHECK
var BANNED = /\b(game[- ]?changer|revolutionize|revolutionary|groundbreaking|paradigm shift|harness the power|unlock potential|enhance|enhances|enhanced|enhancing|boost|boosts|boosted|boosting|transform|transforms|transformed|transforming)\b/i;
var BANNED_OK = /\b(enhance\w*|boost\w*|transform\w*)\s+(?:by\s+)?\d+(?:\.\d+)?\s*(?:%|x|times|fold)/i;
var STAT = /\d+(?:\.\d+)?\s*[%x]|\d+(?:\.\d+)?\s*(?:times|fold)\b/gi;

var allowed = (JSON.stringify(p.{{CORE_FIELD}} || {}) + " " + (p.angle_used || p.angle || "")).toLowerCase().replace(/\s+/g, "");

for (var i = 0; i < items.length; i++) {
  var it = items[i];
  var id = it.platform || it.id || ("item" + i);

  // Flatten item text (handles string OR nested object)
  var txt = "";
  var body = it.full_post != null ? it.full_post : it;
  if (typeof body === "string") { txt = body; }
  else if (body && typeof body === "object") {
    var parts = [];
    for (var k in body) {
      if (body.hasOwnProperty(k)) {
        var val = body[k];
        if (typeof val === "string") parts.push(val);
        else if (Array.isArray(val)) parts.push(val.join(" "));
      }
    }
    txt = parts.join(" ");
  }

  // Banned phrase check (severity: error)
  if (BANNED.test(txt) && !BANNED_OK.test(txt)) {
    var m = txt.match(BANNED);
    v.push({ field: id, rule: "banned_phrase", detail: (m ? m[0] : "?"), severity: "error" });
  }

  // Stat traceability (severity: warning — surfaces but does not block)
  var stats = (txt.toLowerCase().match(STAT) || []);
  for (var s = 0; s < stats.length; s++) {
    var nm = stats[s].replace(/\s+/g, "");
    if (allowed.indexOf(nm) === -1) {
      v.push({ field: id, rule: "stat_introduced", detail: stats[s].trim(), severity: "warning" });
    }
  }

  // ADD per-item format checks here (char limits, required subfields, etc.)
  // Verbatim opener check — normalize both sides first:
  // function norm(s){ return String(s).toLowerCase().replace(/\s+/g," ").replace(/[^a-z0-9 ]/g,"").trim(); }
  // if (norm(hookFirstLine).length && norm(postText).indexOf(norm(hookFirstLine)) === -1) { push not_verbatim error }
}

// errors block; warnings do not
var blocking = v.filter(function(x) { return x.severity !== "warning"; });
if (blocking.length === 0) return "PASS";
return JSON.stringify(v);
```

---

## Node 2: Gate (condition type)

```json
{
  "id": "{{slug}}-gate",
  "type": "condition",
  "position": {"x": 0, "y": 660},
  "data": {
    "label": "Gate: Pass or Block",
    "branches": [
      {
        "id": "branch-pass",
        "variable": "{{slug}}_gate_result",
        "operator": "equals",
        "value": "PASS"
      }
    ]
  }
}
```

Edges from gate:
- `sourceHandle: "branch-pass"` → pass-emitter (PASS path)
- `sourceHandle: "else"` → error-emitter (BLOCK path)

**Critical:** The branch variable must match the validator's outputVariable. The value is the string `"PASS"` — not an array, not a boolean.

---

## Node 3: Pass-emitter (function type)

```js
var raw = variables.{{PAYLOAD_VAR}} || "";
try {
  var s = raw.replace(/^```(?:json)?\s*\n?/, "").replace(/\n?```$/, "").trim();
  var p = JSON.parse(s);
  // Optional: compute warning flags and attach to output for reviewer UI
  return JSON.stringify(p);
} catch (e) { return raw; }
```

Output variable: `{{slug}}_final`

---

## Node 4: Error-emitter (function type)

```js
var raw = variables.{{slug}}_gate_result || "[]";
var v;
try { v = JSON.parse(raw); } catch (e) { v = []; }
var errors = v.filter(function(x) { return x.severity !== "warning"; });
var warnings = v.filter(function(x) { return x.severity === "warning"; });
return JSON.stringify({
  status: "BLOCKED",
  agent: "{{agent_name}}",
  reason: "QUALITY_GATE_FAIL",
  violations: errors,
  warnings: warnings
});
```

Output variable: `{{slug}}_error`

---

## Nodes 5-6: Terminal message nodes (BOTH branches must end here)

```json
{ "id": "{{slug}}-pass-msg", "type": "message", "position": {"x": 0, "y": 1140},
  "data": { "label": "Pass Output", "message": "{{{{slug}}_final}}" } }

{ "id": "{{slug}}-fail-msg", "type": "message", "position": {"x": 400, "y": 1140},
  "data": { "label": "Block Output", "message": "{{{{slug}}_error}}" } }
```

**Rule:** Every branch MUST end in a message node. A branch ending on a function node silently leaks the raw upstream output. Only ai_response, message, and call_agent nodes emit output.

---

## Standard edges (no web_search, no downstream)

```json
[
  {"id":"e-kb-proc","source":"kb_search-{{slug}}","target":"{{slug}}-processor"},
  {"id":"e-proc-val","source":"{{slug}}-processor","target":"{{slug}}-validator"},
  {"id":"e-val-gate","source":"{{slug}}-validator","target":"{{slug}}-gate"},
  {"id":"e-gate-pass","source":"{{slug}}-gate","target":"{{slug}}-pass-emitter","sourceHandle":"branch-pass"},
  {"id":"e-gate-else","source":"{{slug}}-gate","target":"{{slug}}-error-emitter","sourceHandle":"else"},
  {"id":"e-pass-msg","source":"{{slug}}-pass-emitter","target":"{{slug}}-pass-msg"},
  {"id":"e-fail-msg","source":"{{slug}}-error-emitter","target":"{{slug}}-fail-msg"}
]
```

If adding web_search: insert between kb_search and processor, re-route those two edges.
If adding downstream call_agent: insert between pass-emitter and pass-msg.

---

## Repair/Middleware pattern (newer — invented 2026-06-14)

Different from the validator pattern above. A repair node FIXES output before the validator sees it, instead of BLOCKING it.

Position: between ai_response processor and validator.
outputVariable: same as processor's outputVariable (overwrites it).
Use when: the AI output has a predictable, algorithmically fixable issue (e.g. char limit overage after hashtag stripping).
Do NOT use when: the fix requires semantic judgement — that's the validator's job.

Example: cr-x-repair function node (CR agent, 2026-06-14)
- Phase 1: Strip trailing hashtags iteratively
- Phase 2: Word-boundary truncate with `…` ONLY if hook text fits under limit (preserves hook verbatim)
- Sets `po.x_trim_applied = true` as a separate field (survives pass-emitter overwrite of quality_flags)
