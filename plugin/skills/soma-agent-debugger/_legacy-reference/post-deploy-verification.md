# Post-Deploy Verification Protocol
# Source: soma-agent-debugger SKILL.md Mode 4 template (confirmed read 2026-06-14)
# Use after ANY production deployment. Skip no steps.

## Verification Steps (Korak A-E)

### Korak A: Confirm deploy is for the right commit

```bash
git log origin/main -1 --format="%H %s"
# Railway: railway status (or check dashboard)
# Cross-reference: commit hash on main must match what platform reports
```

Expected: hashes match. If not, the new code is NOT live — wait for deploy to complete.

### STOP if hashes don't match: do not run tests against an old deploy.

---

### Korak B: Pre-test DB baseline

Before running any test input, record current state count:

```sql
SELECT COUNT(*) FROM "<YourTable>" WHERE "createdAt" > NOW() - INTERVAL '10 minutes';
-- Expected: 0 (nothing recent before your test)
```

Do not hardcode table names here. Query your actual schema.
Run via: psql connection, Prisma Studio, or platform DB tool.

---

### Korak C: Run test through pipeline
as_chat_with_agent agentId=<entry-agent-id> message="<real test input, not 'test trend'>"

**Input must be realistic.** Use a real trend URL or title. Real inputs exercise the full pipeline path.

Wait for response. Note:
- Did the chain complete? (check terminal message node output)
- What was the final output?
- Any error or BLOCKED in the response?

---

### Korak D: DB verification

```sql
-- New entry was created
SELECT COUNT(*) FROM "<YourTable>" WHERE "createdAt" > NOW() - INTERVAL '5 minutes';
-- Expected: 1

-- Schema is correct
SELECT * FROM "<YourTable>" ORDER BY "createdAt" DESC LIMIT 1;
-- Verify: required fields present, no unexpected nulls, timestamps correct

-- No duplicates: count must be exactly 1
```

---

### Korak E: Acceptance criteria

| Check | Expected | Actual | Result |
|---|---|---|---|
| Commit hash match | main HEAD == platform deploy | observed | P/F |
| Pipeline completed | Terminal message responded | yes/no | P/F |
| DB entry created | COUNT = 1 | count | P/F |
| Schema correct | All required fields present | verified | P/F |
| No duplicates | COUNT exactly 1 | count | P/F |
| Eval suite | lastRunScore = 1.0 | score | P/F |

**Overall verdict:**
- ALL PASS: production-ready
- 1-2 minor FAIL: rollback candidate, assess impact
- Any critical FAIL: rollback immediately + open debug session

---

## eval suite verification (added 2026-06-14 — missing from original Mode 4)

After any flow change, run the agent's regression eval suite:
as_run_eval eval_id=<suite-id>

Returns jobId (NOT runId). Poll result with:
as_list_evals agent_name="<Agent Name>"

Check: lastRunStatus = "COMPLETED", lastRunScore = 1.0

If as_run_eval returns 403: ownership issue — see lessons-learned.md L8.
Do NOT use as_get_eval_result (requires run_id that as_run_eval does not return).

**Not regression-safe until eval suite COMPLETED with score 1.0.**
