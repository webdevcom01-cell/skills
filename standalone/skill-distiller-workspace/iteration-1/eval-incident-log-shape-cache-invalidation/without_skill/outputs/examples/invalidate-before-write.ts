/**
 * Illustrative example for cache-invalidate-before-write.
 * Not tied to any real service — generic cache-aside write path.
 */

interface Cache {
  get<T>(key: string): Promise<T | undefined>;
  set<T>(key: string, value: T, ttlSeconds: number): Promise<void>;
  invalidate(key: string): Promise<void>;
}

interface EntitlementsRepo {
  writePlan(orgId: string, plan: Plan): Promise<void>;
}

interface Plan {
  tier: string;
  seatLimit: number;
}

// --- BUGGY: invalidate only after the write commits -----------------------
//
// Leaves a window where a concurrent reader can miss, read the pre-write
// value from the source of truth, and repopulate the cache *after* this
// invalidate() call — leaving a stale value in place for the full TTL.
async function upgradePlanBuggy(
  orgId: string,
  plan: Plan,
  repo: EntitlementsRepo,
  cache: Cache,
): Promise<void> {
  await repo.writePlan(orgId, plan);
  await cache.invalidate(orgId);
}

// --- FIXED: invalidate before the write, and again after ------------------
//
// The pre-write invalidation forces any reader racing the write into a
// cache miss instead of letting it silently repopulate a stale entry after
// the fact. The post-write invalidation still runs as a second pass, to
// clear the narrower race where a reader's miss-and-repopulate straddles
// the commit itself (see references/race-timeline.md).
async function upgradePlanFixed(
  orgId: string,
  plan: Plan,
  repo: EntitlementsRepo,
  cache: Cache,
): Promise<void> {
  await cache.invalidate(orgId);
  await repo.writePlan(orgId, plan);
  await cache.invalidate(orgId);
}

// --- Regression test shape (pseudocode, adapt to your test runner) --------
//
// async function readWithArtificialDelay(ms: number) {
//   return async (orgId: string) => {
//     const value = await repo.readPlan(orgId); // reads BEFORE the write commits
//     await sleep(ms);                          // ...but writes AFTER it
//     await cache.set(orgId, value, 300);
//     return value;
//   };
// }
//
// it("does not serve a stale value when a read races the write", async () => {
//   const racingRead = await readWithArtificialDelay(50);
//   await Promise.all([
//     racingRead(orgId),
//     upgradePlanFixed(orgId, newPlan, repo, cache),
//   ]);
//   await sleep(60);
//   expect(await cache.get(orgId)).toEqual(newPlan);
// });
//
// Run this test against upgradePlanBuggy first to confirm it fails reliably,
// then against upgradePlanFixed to confirm it passes — that's what makes it
// a real regression test rather than a coincidentally-green one.
