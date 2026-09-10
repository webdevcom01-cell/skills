<!--
NOTE: This Slack thread is synthesized for this task — there is no real
incident, no real people, and no real ticket system behind it. It was
written to plausibly arrive at the target conclusion (invalidate cache
before the shared-state write, not after) while naturally referencing the
required ticket/PR/issue numbers: #4821, PR #5012, issue 6034, PR#7001,
#7002, and #7003. It is the raw, undistilled source material — it is meant
to be run through the skill-distiller process, not read as a finished skill.
-->

# #eng-oncall

**Dana Reyes** — 9:14 AM
morning — picking up the stale-seat-count reports from overnight. looks like
the same shape as #4821 from last quarter, orgs seeing their seat count
revert to a lower number for a few seconds after someone's added, then it
"fixes itself"

**Ilya Novak** — 9:16 AM
yeah I remember #4821. we thought PR #5012 fixed it — that was the one that
added the async cache-bust via the invalidation queue, fired after the seats
write commits

**Dana Reyes** — 9:17 AM
right, and it did fix the original repro. but issue 6034 got filed two weeks
ago with basically the same symptom, just under heavier load (that big
customer's bulk-invite flow). I think PR #5012 only shrank the window, it
didn't close it

**Ilya Novak** — 9:21 AM
makes sense actually. the queue consumer for invalidation is fine under
normal traffic, but during bulk-invite we're hammering the seats table with
dozens of concurrent writes per org. the invalidation messages back up
behind each other in the queue. the write commits instantly, but the
invalidation for that write might not get processed for a second or two
under backpressure

**Dana Reyes** — 9:23 AM
and any read that comes in during that gap either serves the already-stale
cached value, or worse — misses cache (because some other org's
invalidation just cleared something nearby) and repopulates the entry with
a value that's about to be stale anyway. that repopulated entry then just
sits there until its own invalidation crawls through the same backed-up
queue

**Ilya Novak** — 9:25 AM
so the real bug isn't the invalidation logic itself, it's that we invalidate
*after* the write, through a channel — the queue — whose latency isn't
bounded and gets worse exactly when load is highest, which is exactly when
we most need it to be fast

**Dana Reyes** — 9:29 AM
right. I think the fix is to flip the order — invalidate the cache key
synchronously, inline, *before* we write the new seat count to postgres. no
queue involved in the invalidation step at all. worst case, a read that
lands in that tiny window hits postgres directly and gets the pre-write
count, which is still a real, correct value at that instant. what we want to
avoid is ever letting the cache go on serving a value that's already been
superseded by a write that already committed

**Ilya Novak** — 9:31 AM
agreed, that closes the window instead of just shrinking it. let me open a
PR — I'll call it PR#7001, reorders the entitlements write path to
invalidate-then-write and rips out the async queue path for this key
entirely

**Dana Reyes** — 9:33 AM
+1. can you also file #7002 for adding an alert on cache-vs-db drift for the
seats key specifically, so we catch this class of bug from telemetry next
time instead of waiting on customer reports

**Ilya Novak** — 9:35 AM
good call, filing it now. I'll also open #7003 to update the caching
runbook — we should write down "invalidate before write, not after" as a
standing rule. this is at least the third service where someone's reached
for async-invalidate-after-write as the default and gotten bitten by the
same race

**Dana Reyes** — 9:36 AM
yeah, let's make sure it's not just tribal knowledge this time. PR#7001
first, then #7002 and #7003 can land after

**Ilya Novak** — 9:40 AM
PR#7001 is up, marked it as closing issue 6034 and referencing #4821 and PR
#5012 for context. will ping you for review once tests are green
