# PR Review Checklist — Cache + Shared-State Writes

Use this when a diff touches both a cache client (`cache.*`, `redis.*`, an
in-process memo/store) and a write to the underlying system of record
(DB update, in-memory store mutation, config write) for the same key.

## Ordering

- [ ] Does the diff invalidate/evict the cache key **before** the shared-state
      write, not after?
- [ ] If invalidate-after is intentional (e.g. read-through cache with no
      external repopulation path), is that assumption written down as a
      comment, since it's easy to break later by adding a read-repopulate
      path elsewhere?

## Race window

- [ ] Can any other code path repopulate this cache key between the
      invalidate and the write completing? (Read-miss handlers are the usual
      culprit.)
- [ ] Is the read path sourcing from a replica, queue, or anything else that
      can lag behind the primary write? If yes, the race window is wider than
      "two adjacent lines" — flag it explicitly.
- [ ] Is there a lock/placeholder, version check, or double-delete guarding
      the write window, or is ordering the *only* protection? Bare reordering
      is not sufficient for correctness-sensitive data (entitlements, auth,
      pricing, permissions).

## Testing

- [ ] Is there a test that fires concurrent reads against a write and asserts
      no reader observes a value older than a write that started before it?
      A sequential unit test cannot catch this class of bug — it needs an
      explicit concurrency test.
- [ ] Does the test fail against the old (write-then-invalidate) ordering and
      pass against the fix, to confirm it actually exercises the race and
      isn't a false-positive green?

## Blast radius

- [ ] Is this cache-aside logic duplicated in other services rather than
      shared through a common helper? If so, the same bug likely exists
      elsewhere — search for other call sites of the same pattern
      (write-call immediately followed by an invalidate-call) before closing
      the review.

## Minimal concurrency test sketch

```ts
test("no reader observes a value older than an in-flight write", async () => {
  const writePromise = updateEntitlement(userId, newPlan);
  const reads = await Promise.all(
    Array.from({ length: 50 }, () => getEntitlement(userId))
  );
  await writePromise;
  const finalValue = await getEntitlement(userId);
  for (const read of reads) {
    expect(isStaleRelativeToWriteStart(read, newPlan)).toBe(false);
  }
  expect(finalValue).toEqual(newPlan);
});
```

Adapt `isStaleRelativeToWriteStart` to whatever ordering signal the domain
has (a version number, an `updatedAt` timestamp, a monotonically increasing
sequence) — you need *some* way to tell "old" from "new" beyond equality,
or the assertion can't distinguish a genuine race from normal eventual
consistency.
