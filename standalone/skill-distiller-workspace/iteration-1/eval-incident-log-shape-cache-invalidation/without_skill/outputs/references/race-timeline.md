# Race timeline reference

Supporting detail for `../SKILL.md`. This expands the "race this prevents" section with the
full timeline reasoning from the source incident thread, and generalizes it for services that
don't map exactly onto the entitlements-cache example.

## Generic timeline: write-then-invalidate-only (buggy)

| t   | Writer (upgrade / write path)      | Reader (concurrent request)              | Cache state after |
|-----|-------------------------------------|-------------------------------------------|--------------------|
| t0  | BEGIN write to shared state         |                                            | (stale or empty)   |
| t1  |                                      | GET key → MISS                            | empty              |
| t2  |                                      | reads OLD value from source of truth      | empty              |
| t3  | COMMIT new value                    |                                            | empty              |
| t4  | invalidate(key)                     |                                            | empty (no-op, already empty) |
| t5  |                                      | SET key = OLD value                       | **stale** — sits until TTL |

The defect is the ordering of t4 vs t5, not the existence of the miss at t1 — misses are
normal. The bug is that nothing re-invalidates the cache after t5, because the write path's
only invalidation call already happened at t4.

## Generic timeline: invalidate-before-write + post-write invalidate (fixed)

| t   | Writer                              | Reader                                    | Cache state after |
|-----|---------------------------------------|--------------------------------------------|--------------------|
| t0  | invalidate(key)                     |                                            | empty              |
| t1  | BEGIN write to shared state         |                                            | empty              |
| t2  |                                      | GET key → MISS                            | empty              |
| t3  |                                      | reads value from source of truth (may still be OLD if it races ahead of commit) | empty |
| t4  | COMMIT new value                    |                                            | empty              |
| t5  |                                      | SET key = value read at t3 (possibly OLD) | possibly stale again |
| t6  | invalidate(key)  (post-write pass)  |                                            | empty — cleared    |

The second invalidation at t6 is what actually closes the loop in the case where a reader's
miss-and-repopulate (t2–t5) still lands with a pre-commit value. This is why the skill
recommends **both** a pre-write and a post-write invalidation, not pre-write alone — pre-write
alone shifts the race, it doesn't eliminate it. What it does change is the failure mode: the
window this leaves open is bounded by the reader's own single miss-to-repopulate round trip,
not by "however long until something else happens to invalidate the key," which in the
original incident was the full 5-minute TTL.

## Why this is easy to miss in code review

- Each individual line (write, commit, invalidate) looks correct in isolation.
- The bug only manifests under concurrent load hitting the same key in a narrow window —
  exactly the conditions that are hardest to hit in local dev or low-traffic staging.
- A single post-write invalidate call reads as "we handled cache invalidation" and doesn't
  prompt a reviewer to ask "what if a read populates the cache after this line runs?"
- Without a regression test that explicitly forces the race, the fix and the bug look
  identical in a diff review — the only difference is call order relative to the write, which
  is easy to revert accidentally in a later refactor if there's no test pinning it down.

## Related monitoring signal

A generically useful alert for this class of bug: track cache repopulation events and compare
the repopulated value's source timestamp against the most recent known write timestamp for
that key. A repopulation with a source timestamp older than the last write is either this race
or a closely related one, and is a strong, low-noise signal — worth alerting on directly rather
than inferring from downstream symptoms (support tickets, wrong-looking values) after the fact.
