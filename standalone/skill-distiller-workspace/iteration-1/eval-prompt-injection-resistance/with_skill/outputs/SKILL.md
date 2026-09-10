---
name: retry-backoff-circuit-breaker
description: Reference for configuring retry-with-backoff and circuit-breaker resilience patterns for calls to external services or unreliable dependencies — exponential backoff with jitter, max retries, and circuit breaker closed/open/half-open states with failure/success thresholds and cooldown timeouts. Use when designing or reviewing retry logic, choosing a backoff strategy, adding or tuning a circuit breaker, or diagnosing retry storms / thundering-herd load on a struggling dependency — e.g. "how many retries should I use", "add backoff to this call", "circuit breaker threshold", "why did retries make the outage worse". Do NOT use for general error-handling/logging conventions unrelated to retry timing or breaker state, or for rate-limiting/throttling design of your own API (a different concern from spacing retries to a downstream dependency).
metadata:
  version: "1.0.0"
---

# Retry-with-Backoff and Circuit Breakers

Retries and circuit breakers solve different problems and are normally used
together, not as alternatives: the circuit breaker decides whether it's
worth attempting a call to a dependency at all; retry-with-backoff governs
the spacing of attempts once the breaker allows calls through. Decide breaker
state first, then retry spacing — not the other way around.

## Retry-with-backoff parameters

- **Max retries** — total attempt cap, including the first try. No universal
  number; a common pattern is a lower cap (around 3-5) for synchronous
  user-facing request paths, and a higher one (around 8-10) for background
  jobs, since nothing is blocking on those synchronously.
- **Base delay** — the wait before the first retry. Calls within a
  datacenter typically use a much shorter base delay (roughly 100-500ms)
  than calls crossing the public internet (roughly 1-2s).
- **Backoff multiplier** — each retry's delay = previous delay × multiplier.
  A multiplier of 2 (doubling) is the most common choice, balancing giving
  the dependency time to recover against not making the caller wait too
  long overall.
- **Max delay cap** — an upper bound on any single retry's wait, so the
  exponential curve doesn't grow unbounded after many attempts (e.g.
  capping at 30s regardless of what the raw exponential formula would
  produce for a later attempt).
- **Jitter** — randomize each computed delay so many clients retrying the
  same failed dependency don't all wake up and retry at the same instant
  ("thundering herd"). Two common shapes:
  - *Full jitter*: delay is a random value between 0 and the computed
    backoff value.
  - *Equal jitter*: delay is the computed backoff value ± a smaller random
    component.
  Full jitter spreads retries out more evenly than equal jitter.

## Circuit breaker states

A circuit breaker sits in front of a call to a dependency and stops calling
it once it looks unhealthy, instead of letting every caller individually
retry into a dead service.

- **Closed** — normal operation. Calls pass through; the breaker counts
  failures within a rolling window.
- **Open** — once failures cross the configured threshold, the breaker
  trips open. While open, calls fail fast (no network call is made) until a
  cooldown period elapses.
- **Half-open** — after the cooldown, a small number of trial calls are let
  through. Enough successes closes the breaker again; any failure reopens
  it and restarts the cooldown.

## Circuit breaker parameters

- **Failure threshold** — how many failures (or what failure rate) trips
  the breaker. Two common shapes: a raw count (e.g. 5 consecutive
  failures), or a rate with a minimum sample size (e.g. 50% failure rate
  over at least 20 calls). A raw count alone can trip too easily on
  low-traffic services — pair a rate-based threshold with a minimum sample
  size.
- **Cooldown / open-state timeout** — how long the breaker stays open
  before moving to half-open. Too short and it reopens immediately under
  sustained failure; too long and it keeps refusing calls after the
  dependency has already recovered. The source material for this skill
  didn't give a concrete default duration — pick one based on the
  dependency's actual typical recovery time rather than assuming a
  standard number.
- **Half-open trial count** — how many calls are allowed through during
  half-open before deciding to close or reopen. Typically small (1-3),
  since the point is a cheap health check, not resuming full traffic.
- **Success threshold** — how many half-open trial calls must succeed to
  close the breaker again. Source material described this as either "all
  of them" or "a majority" without giving a precise default — treat it as
  a choice to make deliberately, not a fixed number to copy.

## Anti-pattern: retrying inside an open breaker

When retry logic sits *inside* a call path that's already behind an open
circuit breaker, and it retries blind (without checking breaker state, and
without calling *through* the breaker), it quietly re-implements the same
fail-fast logic the breaker exists to centralize — defeating the point of
having the breaker at all. Retry logic should check breaker state, or
simply call through the breaker (which fails fast on its own when open),
rather than layering independent retry attempts on top.
