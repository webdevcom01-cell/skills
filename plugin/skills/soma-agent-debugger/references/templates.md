# Templates — fix prompt, validator skeleton, verification report

Loaded from `soma-agent-debugger/SKILL.md` — read at the template step of the relevant mode (Mode 2 step 1, Mode 3 step 3, Mode 4's report step). Verbatim from the skill body, moved here only because the combined SKILL.md was approaching the repo's line-count budget (300-499 zone with no hierarchy).

---

## Mode 2 — Fix prompt template

**Format prompt-a (template):**

```markdown
# Fix Prompt: <Title>

## Hard Rules
1. <rule 1>
2. NE pretpostavljaj — uvek verifikuj pre menjanja
3. Anti-hallucination: cite each MCP/file output

### KORAK 1: Pre-flight verification
[verify current state matches expectations]

### KORAK 2: Apply Fix
[step-by-step]

### KORAK 3: Verify
[post-fix verification]

### STOP: <user decision needed>

### Final Acceptance
[checklist]
```

---

## Mode 3 — Validator Node 1 JS skeleton

   Skelet za Node 1 (prilagodi pravila konkretnoj specifikaciji iz koraka 2):

   ```javascript
   const violations = [];
   // match pool = sva relevantna polja, ne samo jedno
   const pool = [input.title, input.body, input.hook].filter(Boolean).join(" ");

   // hard fail primer: limit
   if (pool.length > MAX_CHARS) {
     violations.push({ rule: "max_chars", severity: "hard", detail: pool.length });
   }
   // hard fail primer: banned phrase (eksplicitna lista svih oblika)
   for (const phrase of BANNED) {
     if (new RegExp(phrase, "i").test(pool)) {
       violations.push({ rule: "banned_phrase", severity: "hard", detail: phrase });
     }
   }
   return { violations, hardFails: violations.filter(v => v.severity === "hard") };
   ```

---

## Mode 4 — Verification report template

**Template za verification report:**

```
Post-Deploy Verification — <datum>

Korak A (deploy correctness): ✅ / ❌
- Commit on main: <hash>
- Railway active: <hash>
- Match: ✅ / ❌

Korak B (baseline): <count> records before test

Korak C (pipeline run): ✅ / ❌
- Trigger: <test trend>
- Chain completed in: <ms>

Korak D (DB verification):
- New entry created: ✅ / ❌
- Schema correct: ✅ / ❌
- No duplicates: ✅ / ❌
- All expected fields populated: ✅ / ❌

OVERALL: ✅ PASS / ⚠️ WARN / ❌ FAIL
Recommendation: <production-ready / rollback / debug>
```
