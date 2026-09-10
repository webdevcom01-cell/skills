---
name: cache-invalidation-ordering
description: Explains why a cache covering shared state must be invalidated before the write that changes that state, not after, and gives the decision rule and reasoning for any code path that writes to shared state which is also served through a cache under concurrent load. Use when writing or reviewing a handler that updates a database row, counter, config value, session, or feature flag that is also read through a cache-aside or read-through cache; when deciding where to place a cache invalidation/eviction call relative to the write; when choosing between synchronous and queued/async invalidation; or when debugging reports of stale reads, values that "flip back" after being updated, or correctness issues that only reproduce under concurrent or high-traffic load. Do NOT use for general cache-strategy selection such as TTL sizing, eviction policy, or cache warming — this skill covers only the invalidate/write ordering question.
license: Apache-2.0
metadata:
  version: "1.0.0"
  source_type: "conversation"
---

# Cache Invalidation Ordering

## The rule

When a code path writes to shared state that is also served through a
cache, invalidate the cache entry **before** performing the write — not
after. Doing it after leaves a window during which a concurrent reader can
serve, or repopulate, the cache with a value that the write is about to make
incorrect. Under concurrent load that window gets hit repeatedly, not once —
so this is a correctness bug that only shows up under load, not an edge
case.

## Why "invalidate after" fails under load

The failure isn't that the invalidation eventually happens — it's the gap
between "the write is now true" and "the cache stops serving the old
answer." Two things make that gap dangerous in practice:

- **Any invalidation delivered out-of-band from the write** — a queue, an
  async event, a fire-and-forget call — has latency that is not bounded and
  tends to get *worse* under the same load spikes that make the bug matter
  most. A channel that adds a few milliseconds of lag under normal traffic
  can back up to seconds once it's competing with a burst of concurrent
  writes.
- **A reader that misses cache during that gap can repopulate it** with a
  value that's already about to be superseded by the in-flight write. Once
  that happens, the stale value doesn't just linger for the length of the
  original gap — it persists until its own invalidation eventually clears
  it, which, if invalidation is still queued and backlogged, can be much
  later.

## The fix: invalidate first, synchronously

1. Invalidate (evict) the cache entry — inline, synchronously, in the same
   request/transaction as the write. Do not route this step through a queue
   or async event if it can be avoided.
2. Perform the write to the shared-state store.
3. Let the next read repopulate the cache with the now-current value.

This removes the lag window rather than just shrinking it: there is no
interval during which a stale cached value can outlive the write that
superseded it, because the cache is already empty for that key by the time
the write executes. A read that misses cache in the brief gap between steps
1 and 2 goes straight to the source of truth and gets the pre-write value —
correct at the moment it was read — instead of a cached value the system
would otherwise go on serving after it stops being true.

## When this applies

- Any handler that updates a value in shared state (a database row,
  counter, config, session, feature flag, entitlement/quota, etc.) that is
  also read through a cache-aside or read-through cache.
- Especially worth checking when invalidation is currently implemented as
  an async message, event, or queued job rather than an inline call in the
  same request — that shape is the one most likely to reintroduce this bug,
  because its latency is invisible in normal testing and only grows under
  real concurrent load.
- A bug report describing stale reads, a value that "flips back" after
  being changed, or a correctness issue that reproduces only under
  concurrent/high-traffic load and not in manual single-request testing is
  a strong signal this ordering issue is present — check the invalidation
  path before assuming the write logic itself is wrong.

## What this doesn't cover

Cache TTL sizing, eviction policy, and cache warming strategy are separate
concerns from this rule. This skill only answers the ordering question
between an invalidation and the write that makes it necessary — it doesn't
tell you how long to cache something or when to pre-warm it.
