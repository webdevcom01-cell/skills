---
name: cache-invalidation-ordering
description: Use when a write path updates a shared data store that also sits behind a cache or other read layer (Redis, in-memory cache, CDN, materialized view, read replica) and clients observe stale values shortly after a write appears to have succeeded, particularly under concurrent traffic. Gives the rule that the cache entry must be invalidated before the underlying write commits, not after, and explains the race window that the reversed order leaves open. Trigger phrases include "stale read right after a write", "cache shows the old value under load", "race between write and cache invalidation", "cache got repopulated with old data", "why does the cache disagree with the database right after I wrote to it". Do NOT use this for TTL/expiry tuning, cache-warming strategy, or general eviction-policy design — those don't involve a write-vs-invalidate ordering race and this skill doesn't cover them.
license: Apache-2.0
metadata:
  version: "1.0.0"
  source-type: "synthesized-conversation"
---

# Cache invalidation ordering

## The rule

If a code path writes to a shared data store that has a cache (or any other
read layer) sitting in front of it, invalidate the cache entry for that key
**before** the write to the underlying store commits — never after. Getting
this backward is what causes stale reads under concurrent load, even though
the write itself succeeds and the underlying store ends up correct.

## Why write-then-invalidate fails

The failure isn't in the write, and it isn't in the invalidation call itself
— it's in the gap between them. Once the write commits, there is a window,
however small, before the invalidation call executes. Any read that lands in
that window and misses (or gets a stale hit on) the cache will fetch the
pre-write value from the underlying store and write it back into the cache.
When the invalidation call finally runs, there's nothing to clean up — the
cache has already been refreshed with the old value, and it now sits there
until the entry naturally expires. From the outside this looks like the
write silently failed to propagate, even though the underlying store was
updated correctly the whole time.

This is a genuine race, not a rare edge case: the more concurrent read
traffic on that key, the more likely something lands in the window.

## Anti-pattern: a lock around write-then-invalidate

Wrapping the write and the subsequent invalidation call in a mutex narrows
the window but does not remove it. A read that started just before the lock
was acquired can still complete — and repopulate the cache with the old
value — after the write inside the lock has committed but before the
invalidation call inside the lock has run. A lock changes timing, not
ordering; it makes the race less likely to be hit, not impossible. Treat any
fix that only adds locking around the existing write-then-invalidate
sequence as incomplete.

## The fix: invalidate, then write

Reverse the order: delete (or otherwise invalidate) the cache entry first,
then perform the write to the underlying store. With the entry already gone
before the write starts, a concurrent read that misses cache during the
write goes straight to the underlying store — which holds either the
pre-write or post-write value depending on timing, but never gets a chance
to re-populate the cache with a value that invalidation was supposed to
clear. There is no leftover cache entry for a stale read to be served from.

## Decision checklist

Apply this to any code path that writes to a data store with a cache (or
other read-through layer) in front of it:

1. Confirm the order is invalidate-then-write, not write-then-invalidate. If
   it's the latter, that's the bug, regardless of what else is wrong.
2. Don't treat a mutex or per-key lock around the existing order as a fix —
   it only shrinks the race window. The fix is the ordering change, not
   added locking.
3. If multiple writers can touch the same key concurrently, invalidate-then-
   write reduces the specific failure mode above, but a second writer racing
   inside the same window is a separate concern this rule does not resolve
   on its own — see "Scope and open questions" below.
4. Apply the same fix uniformly across services that share this pattern. The
   same root cause can surface in unrelated-looking places (e.g. a display
   name that doesn't update vs. a total that doesn't update) — don't treat
   each occurrence as a one-off.

## How to verify the fix

Write a test that runs a writer and a reader concurrently against the same
key: the writer performs the write-path under test, the reader polls (or is
scheduled to land inside the vulnerable window), and the assertion is that
no read ever observes a value older than the last completed write. Run it
against the old ordering first to confirm it actually fails, then against
the corrected ordering to confirm it passes consistently — not just once,
since a race that only shows up sometimes needs multiple runs to trust a
green result.

## Scope and open questions

This rule is specifically about the ordering of a single writer's
invalidate-and-write pair. The source this skill was distilled from
(a two-person discussion of a specific fix) does not go into:

- What happens when two writers race against each other on the same key
  (that needs its own concurrency-control mechanism — e.g. versioning,
  optimistic locking — on top of getting this ordering right first).
- Which caching technology this applies to. The underlying logic doesn't
  depend on Redis vs. in-memory vs. CDN vs. a materialized view, but the
  exact invalidation call and its guarantees will differ by technology, and
  the source didn't cover those specifics.
- Whether invalidate-then-write is safe for every kind of shared state (e.g.
  stores where a missing cache entry is itself expensive or unsafe to
  recompute under load). Where that's a concern, evaluate it separately
  rather than assuming this rule applies unmodified.

Treat these as gaps to check for the specific system at hand, not as settled
by this skill.
