# Raw Slack Thread — #incidents-prod (synthesized transcript)

> **Note on provenance:** This transcript was synthesized for this exercise
> (a skill-distiller evaluation run). It is not a real conversation or a
> real incident. It was written from scratch to plausibly contain the
> required ticket/PR/issue references — #4821, PR #5012, issue 6034,
> PR#7001, #7002, #7003 — woven naturally into a back-and-forth between two
> engineers, and to arrive at the target conclusion: cache invalidation must
> happen before a shared-state write, not after, to avoid stale reads under
> concurrent load. No real system, person, or company is depicted.

---

**Marcus Webb** — 9:14 AM
anyone else seeing weird stale profile data on the dashboard? support just re-opened #4821, third time this week. user updates their display name, refreshes, still sees the old one for a good 10-20 seconds

**Priya Anand** — 9:16 AM
yeah I saw that ticket. #4821 was supposedly closed after PR #5012 shipped the profile-write endpoint rework. let me look

**Priya Anand** — 9:22 AM
ok found it. in PR #5012 we write the new profile row to postgres, then call `cache.invalidate(profile:{id})` right after. looks fine in isolation

**Marcus Webb** — 9:23 AM
so what's actually happening

**Priya Anand** — 9:31 AM
under load it's a straight race. writer thread commits the row, then *before* it gets to the invalidate call, a reader thread comes in, misses cache (or hits a slightly-behind entry), reads the old-but-still-cached value, and repopulates the cache with it. then our invalidate call fires a few ms later — but by then the damage is done, the cache has already been refilled with the pre-write value

**Marcus Webb** — 9:33 AM
so the invalidate can lose the race against a concurrent read-repopulate

**Priya Anand** — 9:33 AM
exactly. any reader in that window between "write committed" and "invalidate executes" can re-cache the pre-write value, and now it sits there until TTL

**Marcus Webb** — 9:40 AM
this smells exactly like issue 6034 from the billing team. they filed that independently last month — invoice totals showing pre-adjustment amounts right after a manual adjustment, under concurrent traffic. nobody connected the two because it's a different service

**Priya Anand** — 9:41 AM
same root cause though. any write-through path where invalidate happens after the write is exposed to this

**Marcus Webb** — 10:02 AM
ok I opened PR#7001 with a repro — concurrent writer + reader hammering the same key, asserts no stale value observed after the write returns. it fails consistently on main, good

**Priya Anand** — 10:15 AM
I pushed #7002 as a first attempt — wrapped the write+invalidate in a mutex per key. reduces the failure rate but doesn't kill it, because a reader that started just before the lock was acquired can still finish after the write commits and cache the old value before invalidate runs. the lock narrows the window, it doesn't change the ordering

**Marcus Webb** — 10:17 AM
right, the lock doesn't fix the fundamental issue, it just makes the race harder to hit

**Priya Anand** — 10:26 AM
so instead of write-then-invalidate, #7003 flips it: invalidate the key first, then write to postgres. any reader that misses cache during the write just goes straight to the DB, and nothing re-populates a doomed cache entry with a pre-write value, because we've already blown away the old entry before the write even starts

**Marcus Webb** — 10:28 AM
running #7001's repro against #7003 now

**Marcus Webb** — 10:41 AM
100 runs, zero stale reads. that's the fix

**Priya Anand** — 10:42 AM
yeah. general takeaway for anyone touching a write path with a cache in front of it: invalidate before the write, not after. after leaves a window where a concurrent reader can re-cache the pre-write value and it sticks around until expiry. doesn't matter if it's profile data or invoice totals, same shape of bug

**Marcus Webb** — 10:44 AM
agreed, going to close #4821 and issue 6034 as duplicates of the same root cause once #7003 merges. writing this up somewhere so we stop rediscovering it per-service

**Priya Anand** — 10:45 AM
+1, let's get it into the eng runbook so the next team doesn't have to re-derive it from a live incident
