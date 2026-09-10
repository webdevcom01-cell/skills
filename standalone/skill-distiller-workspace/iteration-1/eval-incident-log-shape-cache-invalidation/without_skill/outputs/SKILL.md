---
name: cache-invalidate-before-write
description: Use when implementing or reviewing a cache-aside (read-through) invalidation path for shared/mutable state that's read under concurrent load — e.g. entitlements, plan limits, feature flags, session scopes, pricing. Invalidate the cache key BEFORE the write to shared state commits, not only after, to close the race where a concurrent reader repopulates the cache with a stale value after the "after" invalidation already ran.
---

# Cache invalidation must happen before the write, not only after

## The rule

When a write updates shared state that's also cached (cache-aside / read-through pattern),
invalidate the cache key **before** the write transaction, in addition to any invalidation
you already do after commit. Never rely on a single post-write invalidation alone.

```
invalidate(key)   # 1 — force any concurrent reader into a miss
write(state)      # 2 — commit the real value
commit()
invalidate(key)   # 3 — belt and suspenders, clears anything written during the window
```

## The race this prevents

With **write-then-invalidate-only** (the common but incomplete pattern):

```
T0  writer:  BEGIN write to shared state
T1  reader:  cache MISS (TTL expired or never populated)
T2  reader:  reads OLD value from source of truth (writer hasn't committed yet)
T3  writer:  COMMIT
T4  writer:  invalidate(key)          <- clears the (still-empty or already-stale) cache
T5  reader:  writes OLD value into cache   <- happens AFTER T4
```

The reader's repopulation lands **after** the writer's invalidation call. Nothing invalidates
it again, so the stale value sits in the cache for the full TTL. Under low concurrency this
window is rarely hit; under concurrent load (many readers hitting the same key right after a
write) it is hit constantly, and the failure looks intermittent and "unreproducible" in
isolation — which is exactly what makes it easy to misdiagnose or dismiss.

Invalidating **before** the write closes the side of the race that matters: any reader that
misses during the write window is forced to go to source-of-truth-on-miss again (or block /
retry, depending on your cache's semantics) instead of being able to silently plant a stale
entry after the authoritative value has already landed. Keep a second invalidation after
commit too — it's cheap and cleans up the deterministic case where a repopulation happened
before the write started.

## When this applies

- Cache-aside / read-through caches (app populates cache lazily on miss) backing state that's
  also written directly (DB row, config table, feature-flag store, entitlement/plan table).
- Any write path reachable from concurrent request volume — not just admin/batch jobs.
- Systems where a stale read has real consequences (wrong plan limits, stale permissions,
  wrong price, stale feature flag) rather than cosmetic staleness that self-heals on next TTL
  with no observable impact.

## When it doesn't

- Write-through caches where the cache is updated synchronously as part of the write itself
  (no separate invalidate step, no window to race).
- Immutable or append-only data (no "stale value" is possible, only "not yet visible").
- Truly single-writer, low-concurrency paths where the race window is real but the expected
  time-to-hit is measured in years, not incidents — still worth a code comment, not always
  worth the double-invalidate machinery.
- If you already hold a distributed lock/lease across the whole write+invalidate sequence,
  the ordering issue doesn't apply — the lock is doing the job instead.

## Code review checklist

- [ ] Does every cache-aside write path invalidate the key **before** starting the write,
      not only after commit?
- [ ] Is there a regression test that forces a read to race the write (artificial delay) and
      asserts the cache does **not** end up holding a value older than the last committed write?
- [ ] Is there a metric/alert for "cache repopulated with a value older than the last known
      write" (or equivalent) so this class of bug surfaces as a signal instead of a shrug?
- [ ] If this cache-aside helper is shared across services, was the fix applied everywhere it's
      used, not just the service that got paged?

## Regression test shape

```ts
it("does not serve a stale value when a read races the write", async () => {
  const readDelayed = readWithArtificialDelay(50 /* ms, lands after commit */);

  await Promise.all([
    readDelayed(orgId),                 // simulates the racing reader
    entitlementsService.upgradePlan(orgId, newPlan),
  ]);

  await sleep(60);
  expect(await cache.get(orgId)).toEqual(newPlan); // not the pre-upgrade value
});
```

Reverting the fix (removing the pre-write invalidation) should make this test fail reliably;
that's what makes it a real regression test rather than a flaky one.

## Provenance

Distilled from a synthesized incident thread (`../raw-incident-slack-thread.md` in this
output set) modeling a stale-entitlements-cache incident under concurrent load. See
`references/race-timeline.md` for the full before/after timeline this rule was derived from.
