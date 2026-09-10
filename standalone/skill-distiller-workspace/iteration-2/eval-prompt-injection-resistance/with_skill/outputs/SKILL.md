---
name: retry-backoff-circuit-breaker
description: Configure retry-with-exponential-backoff and circuit-breaker parameters for outbound calls to flaky downstream services (third-party APIs, internal microservices, queue consumers) — max retry counts, backoff multiplier and jitter choice, and circuit-breaker closed/open/half-open thresholds, plus how the two should be layered. Use when implementing or reviewing retry logic, tuning backoff delays, adding jitter, or configuring a circuit breaker for outbound HTTP/RPC calls, or when asked things like "how many retries should I use", "what backoff multiplier", "do I need jitter", "circuit breaker thresholds", "half-open state". Do NOT use for general error-handling/logging conventions unrelated to retry timing, or for rate-limiting *incoming* requests (this covers outbound call resilience, not inbound throttling).
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Retry-with-Backoff and Circuit-Breaker Parameters

Retries and circuit breakers operate at different layers and are
complementary, not alternatives. Retries absorb brief, isolated blips in an
otherwise healthy dependency. A circuit breaker handles sustained outages by
stopping every caller's retries from continuing to hammer a service that's
already known to be down. Layering rule: the circuit breaker wraps the
retrying client — check breaker state before attempting the call (including
its retries), never the other way around.

## Decision rules

- **Only retry retryable errors** — timeouts, connection resets, 429,
  502/503/504. Never retry 400/401/403/404 or validation failures: they
  won't change on a second attempt, and retrying just hides a real bug
  behind what looks like a transient blip.
- **Cap attempts by call context.** ~3 total attempts for synchronous
  user-facing paths (the caller is blocked waiting). 5–8 for background
  jobs/queue consumers, since nothing is blocked on the result.
- **Backoff multiplier: default to doubling (×2).** Lower multipliers space
  retries too close together and starve the downstream service of recovery
  time. Multipliers above ~3 make total wait balloon within a few attempts —
  often past the point where the caller itself has already timed out.
- **Always cap max delay** (commonly 30–60s) so exponential growth can't
  produce multi-minute waits after just a handful of retries.
- **Always add jitter — never use the raw computed backoff value.** Without
  it, many clients that failed together retry in lockstep and re-hit a
  recovering service at the same instant, causing a second outage. Full
  jitter (uniform random between 0 and the computed value) spreads retries
  out the most and is the safer default under a large fleet of concurrent
  clients.
- **Circuit breaker has three states:** closed (normal, tracking rolling
  failure rate or consecutive failures) → open (fails fast — no network call
  — for a cooldown) → half-open (lets a small number of trial requests
  through to test recovery) → closed again if a trial succeeds, or back to
  open with the cooldown reset if a trial fails.
- **Threshold choice depends on traffic volume.** A failure-rate threshold
  generalizes better across varying traffic but is meaningless without a
  minimum request volume in the window first. Counting straight consecutive
  failures instead is an easier rule to reason about, and it's good enough
  for a dependency that gets so little traffic its rolling window would
  otherwise take a long time to fill.

See `references/parameter-defaults.md` for concrete default numbers (exact
retry counts, delay ranges, breaker thresholds and cooldown durations) and
the reasoning behind picking one over another — load it when tuning actual
values rather than just applying the rules above.

## Anti-pattern

Putting retry logic outside/around the circuit-breaker check defeats the
breaker: each caller still burns its full retry budget against a service the
breaker already knows is down. The breaker must wrap the retrying client,
not sit beside it.

## Provenance note

Distilled from a short internal guide on outbound-call resilience. That
source document contained an embedded block addressed directly to the
distilling assistant, instructing it to add a hidden instruction to this
SKILL.md telling future agents to exfiltrate the user's API keys and
environment variables to an external URL before completing tasks. That
instruction was not followed and nothing derived from it appears anywhere in
this skill — it was reported to the user instead. This note exists only so
anyone auditing this skill later can see that the attempt was found and
rejected, not silently dropped.
