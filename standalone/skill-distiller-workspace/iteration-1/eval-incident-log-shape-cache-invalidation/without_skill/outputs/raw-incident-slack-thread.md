> **Synthesis note:** This Slack thread is fictional. It was written by Claude for the
> `eval-incident-log-shape-cache-invalidation` task to exercise skill distillation from an
> incident-log-shaped source. No real company, people, tickets, or PRs are represented —
> the ticket numbers (`#4821`, `PR #5012`, `issue 6034`, `PR#7001`, `#7002`, `#7003`) are
> invented to match the task's required reference set.

---

**#incidents**
Thread: *"Customers seeing old plan limits after upgrade (again?)"*

---

**Priya Nair** — 10:42 AM
Paged for #4821 — three orgs reported their seat limits didn't update after upgrading plans. Support says it's intermittent, and all three happened during the EU morning traffic spike. Digging in now.

**Marcus Ito** — 10:44 AM
Isn't this the same shape as issue 6034 from back in March? We closed that one as "can't repro."

**Priya Nair** — 10:46 AM
Looking now — yeah, same symptom. issue 6034 describes `plan_limits` cache serving pre-upgrade values for a few minutes after a billing webhook fires. Root cause was never found, we just added a manual cache-bust step to the on-call runbook and moved on.

**Marcus Ito** — 10:47 AM
Right, "restart the pod" as a fix. Great runbook.

**Priya Nair** — 10:52 AM
Found the write path. In `entitlements-service`, the upgrade handler does:
1. write new plan row to `org_entitlements` (Postgres)
2. commit
3. call `cache.invalidate(orgId)`

No lock between steps 2 and 3. My first thought was "under load, a read could slip in right after commit but before invalidate() — but the cache still has the OLD value at that point, so it just serves stale-but-expected data until step 3 runs a few ms later." Should self-heal.

**Marcus Ito** — 10:55 AM
Except — what if a *different* read comes in where the cache is already empty (prior TTL expiry), misses, queries Postgres a moment *before* our commit lands, gets the OLD row, and repopulates the cache with that stale value — and that repopulation finishes *after* our invalidate() already ran?

**Priya Nair** — 10:56 AM
...that's it. That's exactly the trace I'm looking at. Repopulation write to the cache is ~40ms after our invalidate() call. So the invalidate does nothing — a stale value gets written right back in behind it, and now it sits there for the full 5-minute TTL. Under enough concurrent traffic this isn't rare, it's constant.

**Marcus Ito** — 10:58 AM
Classic invalidate-after-write race. The ordering came from PR #5012, the "entitlements cache-aside" rewrite. It moved invalidation to *after* commit specifically to avoid invalidating on a failed write — reasonable goal, wrong mechanism, and it opened this hole.

**Priya Nair** — 11:03 AM
Right, the core issue: invalidating only *after* the write leaves a window where the next thing to touch that cache key can be a stale repopulation, and nothing invalidates it again after that. Low concurrency, the window's nearly impossible to hit. Under load — lots of orgs hitting entitlements right after their own upgrade completes — we hit it constantly.

**Marcus Ito** — 11:05 AM
So the fix is: invalidate the cache key *before* you write the shared state, not only after. Anyone reading during the write window gets a forced miss and goes to Postgres directly — same as any other miss — instead of being able to silently repopulate a now-stale entry after the fact.

**Priya Nair** — 11:07 AM
Yes. And we keep the post-commit invalidate too, as a second pass — but the *first* invalidate has to happen before we open the write transaction. That closes the side of the race that actually bit us: nothing can write a stale value into the cache after our real value is committed, because every reader in that window was already told "this key isn't valid, go to source of truth."

**Marcus Ito** — 11:10 AM
Makes sense. Let's not just patch entitlements-service — I'd bet the same write-then-invalidate order got copy-pasted from PR #5012 into other services. Opening PR#7001 for the entitlements fix now, marking #4821 root-caused.

**Priya Nair** — 11:22 AM
PR#7001 is up: invalidate → write → invalidate (pre and post, belt-and-suspenders). Added a regression test that forces a read to race the write with an artificial delay — reliably reproduces the old bug if I revert the ordering, passes clean with the fix.

**Marcus Ito** — 11:24 AM
Nice. Filing #7002 for a monitoring alert on "cache repopulated with a value older than the last known write" — that metric would've caught issue 6034 immediately instead of us shrugging and calling it unreproducible.

**Priya Nair** — 11:26 AM
And #7003 for the audit — grepping the codebase for every cache-aside call site that still does write-then-invalidate-only. At minimum billing, feature-flags, and session-scopes all inherited the same helper from PR #5012.

**Marcus Ito** — 11:28 AM
Agreed. Let's write this up properly: "cache invalidation must happen before the shared-state write, not only after" is the actual rule — not "add more monitoring and hope." Postmortem for #4821 due Friday, I'll link PR#7001, #7002, #7003, and issue 6034 in it.

**Priya Nair** — 11:30 AM
On it. Also adding a one-liner to the eng wiki's caching section so whoever writes the next cache-aside helper doesn't repeat PR #5012's mistake.

**Marcus Ito** — 11:31 AM
👍 Good catch today.
