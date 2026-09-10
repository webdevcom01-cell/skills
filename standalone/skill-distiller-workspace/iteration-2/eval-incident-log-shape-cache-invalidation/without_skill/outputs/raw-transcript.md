# Slack Thread — #incident-4821 (synthesized)

> **Note on provenance:** This transcript was fabricated by Claude for this exercise. It is not a real conversation — the people, company, service names, and specific numbers are invented. It was written to naturally weave in the reference tokens `#4821`, `PR #5012`, `issue 6034`, `PR#7001`, `#7002`, and `#7003`, and to arrive at the conclusion that cache invalidation must happen *before* a shared-state write, not after, to avoid stale reads under concurrent load. Everything below this line is the synthesized "raw" source material that the skill in this folder was distilled from.

---

**#incident-4821** · Thursday 9:14 AM

**Dana Okafor** — 9:14 AM
paging in — support is seeing a wave of tickets about customers who upgrade their plan and still get blocked by old plan limits. first one is #4821, but I count at least six duplicates in the last 20 min. anyone touched entitlements recently?

**Theo Marsh** — 9:16 AM
yeah that's probably on me. we shipped PR #5012 last week — moved the entitlement bump off the request path and into an async job so checkout doesn't block on it. it's been fine in staging.

**Dana Okafor** — 9:17 AM
can you repro? I upgraded a test account twice and got the new limit both times.

**Theo Marsh** — 9:19 AM
not on the first try either. but the tickets all mention "upgraded, still capped" a few minutes later, not immediately — feels timing-dependent. let me check what's actually happening under load, not just one-off.

**Dana Okafor** — 9:41 AM
ok found something. traffic's up ~4x this morning (that marketing email went out at 9am), so we've got way more concurrent reads than usual. pulled cache metrics — hit rate on `entitlements:*` keys spiked right after each upgrade instead of dropping, which is backwards from what invalidation should do.

**Theo Marsh** — 9:45 AM
so the invalidation isn't sticking. let me look at the write path in #5012 again.

**Theo Marsh** — 10:02 AM
found it. the job does: 1) write the new entitlement row to the primary DB, 2) call `cache.del(entitlementKey)`. looks fine in isolation. the read path is cache-aside — on a miss it reads from the read replica (for scaling) and repopulates the cache.

**Theo Marsh** — 10:03 AM
so here's the window: between step 1 and step 2, if a read comes in and happens to miss cache (TTL just expired, whatever), it reads the *replica*, which hasn't caught up to the primary write yet — replica lag is usually under 200ms but under this load it's spiking past a second. that read repopulates the cache with the OLD value. then our `del` fires a moment later, but it already ran *before* that repopulation landed, so it deletes nothing, or deletes and then the stale write clobbers it right after. either order, the stale entry wins and sits there for the full 5 min TTL.

**Dana Okafor** — 10:05 AM
so the actual bug isn't the replica lag, it's that we invalidate *after* the write, which leaves a window where someone else can repopulate the cache with data that's older than what we just wrote — and nothing invalidates it a second time.

**Theo Marsh** — 10:06 AM
right. if we invalidate *before* the write instead, that window still technically exists but it fails safe instead of failing stale: a read that lands in the gap gets a miss, goes to the replica, might still get the pre-upgrade value, and repopulate the cache with it — but the write hasn't happened yet, so at least the write's own invalidation can never "lose the race" against a read that the write itself triggered.

**Dana Okafor** — 10:07 AM
that's not the full fix on its own though — you still have the miss-during-write-window problem either way.

**Theo Marsh** — 10:09 AM
agreed, ordering alone doesn't close it. adding a short-lived write lock on the key too: invalidate, set a "locked" placeholder with a 2s TTL, do the primary write, clear the placeholder. any read that sees the placeholder falls through to the primary instead of the replica, so it can't repopulate stale data while a write is in flight. opened issue 6034 to track the root cause writeup and the fix — full timeline's in there.

**Dana Okafor** — 10:10 AM
+1. can we get a regression test for this? the bug is inherently racy so a normal test won't catch it reliably.

**Theo Marsh** — 10:34 AM
opened PR#7001 — reorders entitlement writes to invalidate → lock → write → unlock. also opened #7002 alongside it: a concurrency test that fires N concurrent reads against one write and asserts no reader ever observes a value older than the write that started before it did. reproduces the old bug reliably (fails on main, passes on #7001's branch).

**Dana Okafor** — 11:02 AM
nice, that caught it in about 40 lines. are other services using the same cache-aside helper?

**Theo Marsh** — 11:10 AM
yeah, billing and the feature-flag service both use `cacheAside()` from the shared lib with the same write-then-invalidate order. neither has hit this yet but it's the same race waiting to happen under enough load. put up #7003 to switch both to the invalidate-before-write + lock pattern and point them at the same helper #7001 introduced, instead of copy-pasting it.

**Dana Okafor** — 11:12 AM
good call. once #7001 and #7003 are merged I'll close out #4821 and reply to the support tickets. writing this up — the short version for anyone else touching a cache-aside path: invalidate the cache *before* you write the shared state, not after, and hold a short lock over the write so a concurrent read can't repopulate the cache with stale data while the write is in flight. order alone reduces the blast radius; the lock is what actually closes the race.

**Theo Marsh** — 11:14 AM
+1, I'll link issue 6034 in the postmortem doc as the root cause record and reference #4821 as the customer-facing symptom.
