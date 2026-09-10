---
name: cache-invalidation-ordering
description: Use when writing or reviewing code that updates a cache-aside (or write-through) cache alongside a shared mutable state store — a database row, a read replica, an in-memory store, a config/feature-flag value — under concurrent access. Enforces invalidating the cache before the state write, not after, and flags the write-then-invalidate ordering that causes stale reads under load. Trigger on: cache.del / cache.invalidate / cache eviction, cache-aside, write-through cache, stale cache, stale read, race condition, TTL, read replica lag, "why did the old value come back", entitlement/session/config caching bugs.
---

# Cache Invalidation Ordering

## The rule

When a code path both writes shared state and invalidates a cache entry for
that state, **invalidate the cache first, then write the state — never the
reverse.** Write-then-invalidate leaves a window where a concurrent reader
can repopulate the cache with data older than the write that is about to
land, and nothing will invalidate it again until the TTL expires.

```
BAD  (write, then invalidate):   write state ──► invalidate cache
GOOD (invalidate, then write):   invalidate cache ──► write state
```

## Why the order matters

A cache-aside read path typically does: on a miss, read the value from the
system of record (often a read replica, for scaling) and repopulate the
cache. That repopulation is the hazard. If a write invalidates the cache
*after* updating state, any read that slips into the gap between "state
updated" and "cache invalidated" can still see the pre-write value (directly,
or via replica lag) and write that stale value back into the now-fresh cache
slot — with a full TTL ahead of it and no future event that will clear it.

Invalidating first doesn't eliminate the race by itself (a read can still
land between "cache cleared" and "state written" and repopulate with the old
value) — but it removes the specific failure mode where **the write's own
invalidation call is racing against, and can lose to, a read that the write
itself triggered**. It fails safe (short-lived miss traffic) instead of
failing stale (a wrong value that sits there for the full TTL).

## This is necessary, not sufficient

Reordering alone does not close the race under high concurrency. Pair it
with one of:

- **A short-lived write lock / placeholder.** Invalidate → set a locked
  placeholder (short TTL, e.g. 1-2s) → write state → clear placeholder. Reads
  that see the placeholder fall through to the primary/system-of-record
  instead of a lagging replica or cache, so they can't repopulate stale data
  mid-write.
- **Versioned reads/writes.** Tag cached values with a version or timestamp
  from the write; reject repopulating the cache with a version older than
  what's already there (or than the write in flight).
- **Double-delete.** Invalidate before the write, then invalidate again a few
  hundred ms after, to catch any repopulation that snuck into the gap. Cheap
  insurance, doesn't need a lock, but is best-effort rather than a guarantee.

Pick based on how much you can tolerate a rare, short-lived stale read vs.
how much complexity you can carry. For anything customer-visible and
correctness-sensitive (entitlements, auth/session state, pricing), prefer a
lock or versioning over "reorder and hope."

## Detecting this in code review

Grep/read for the shape, not the exact API:

- A function that both mutates shared state (DB write, `UPDATE`, `.save()`,
  `.set()` on an in-memory store) **and** calls something like `cache.del`,
  `cache.evict`, `cache.invalidate`, or a pub/sub "bust the cache" event.
- Check the order of those two calls. If the state write comes first, ask:
  *what reads this value, and can a read repopulate the cache between these
  two lines?*
- If the read path is cache-aside off a **replica** or an **eventually
  consistent** store, treat this as higher risk — replica lag widens the
  race window even when the write and invalidate are adjacent lines.
- If there's no test that exercises concurrent reads against a write, the
  race is untested by definition — a sequential test cannot catch it. See
  `checklist.md` in this skill for a review checklist and a concurrency-test
  sketch.

## Anti-pattern → fix (pseudocode)

```ts
// BAD — write, then invalidate: readers can repopulate stale data
// in the gap and nothing clears it again.
async function updateEntitlement(userId: string, plan: Plan): Promise<void> {
  await db.entitlements.update(userId, plan);
  await cache.del(entitlementKey(userId));
}
```

```ts
// GOOD — invalidate first, hold a short lock over the write so a
// concurrent read can't repopulate the cache mid-write.
async function updateEntitlement(userId: string, plan: Plan): Promise<void> {
  const key = entitlementKey(userId);
  await cache.del(key);
  await cache.set(lockKey(key), true, { ttlMs: 2000 });
  try {
    await db.entitlements.update(userId, plan);
  } finally {
    await cache.del(lockKey(key));
  }
}

// Read path: a locked key means "don't trust the replica/cache right now."
async function getEntitlement(userId: string): Promise<Plan> {
  const key = entitlementKey(userId);
  if (await cache.exists(lockKey(key))) {
    return db.entitlements.readFromPrimary(userId); // bypass cache + replica
  }
  const cached = await cache.get(key);
  if (cached) return cached;
  const value = await db.entitlements.readFromReplica(userId);
  await cache.set(key, value);
  return value;
}
```

## Case reference

This pattern was distilled from a synthesized incident (see
`../raw-transcript.md`): customers who upgraded their plan intermittently
kept their old limits under traffic spikes (`#4821`), traced to an async
entitlement job (`PR #5012`) that wrote the DB before invalidating the
cache. Root cause and fix are recorded as `issue 6034`; the reorder + lock
landed in `PR#7001`, a concurrency regression test in `#7002`, and the same
fix was rolled out to two other services sharing the affected cache-aside
helper in `#7003`. The specifics are illustrative, not load-bearing — the
generalizable rule is the one at the top of this file.
