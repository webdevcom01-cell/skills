---
name: retry-backoff-circuit-breaker
description: Configure retry-with-backoff and circuit-breaker resilience logic for outbound service calls — max retries, base delay, backoff multiplier, max delay cap, jitter, and circuit-breaker closed/open/half-open states and thresholds. Use when implementing or reviewing an HTTP client, service wrapper, or any code that calls a flaky or rate-limited external dependency and needs retry and fail-fast behavior.
---

# Retry, Backoff & Circuit Breaker

Resilience logic for calls to a dependency that can fail transiently
(timeouts, network blips, 5xx responses). Two mechanisms, used together:

- **Retry with backoff** — re-attempt a failed call with increasing delay
  between attempts.
- **Circuit breaker** — stop calling a dependency that's clearly down, so
  retries don't pile on top of an outage.

## Retry parameters

| Parameter | What it controls | Typical value |
|---|---|---|
| `max_retries` | Attempts per request before giving up | 3-5 for idempotent calls; 0-1 for non-idempotent writes without an idempotency key |
| `base_delay_ms` | Delay before the first retry | 100-250ms |
| `backoff_multiplier` | Growth factor per retry (exponential backoff) | 2.0 |
| `max_delay_ms` | Ceiling on the computed delay | 10,000-30,000ms |
| `jitter` | Randomization added to each delay | full jitter: `random(0, computed_delay)` |

Backoff formula:

```
delay(n) = min(max_delay_ms, base_delay_ms * backoff_multiplier ^ (n - 1))
sleep_ms = jitter(delay(n))
```

Rules of thumb:

- Never retry a non-idempotent write unless it has an idempotency key or is
  otherwise safe to replay.
- Never skip jitter in any system with more than a handful of concurrent
  clients — unjittered exponential backoff produces synchronized retry
  spikes ("thundering herd") that look like a second outage.
- On final failure (retries exhausted), surface the original error. Don't
  collapse it into a generic "retry exhausted" message.
- Log intermediate retries at DEBUG/INFO; log only the final failure at
  ERROR.

## Circuit breaker states

```
CLOSED --(failures cross failure_threshold)--> OPEN
OPEN --(open_timeout_ms elapses)--> HALF_OPEN
HALF_OPEN --(success_threshold met)--> CLOSED
HALF_OPEN --(any trial request fails)--> OPEN (cooldown resets)
```

| State | Behavior |
|---|---|
| `closed` | Requests pass through normally; failures counted in a rolling window |
| `open` | Calls fail fast, no request reaches the dependency, for `open_timeout_ms` |
| `half_open` | A limited number of trial requests probe recovery |

| Parameter | What it controls | Typical value |
|---|---|---|
| `failure_threshold` | Failure rate/count that trips the breaker to open | 50% over the last 20 requests, min. 10 sampled — or 5 consecutive failures |
| `open_timeout_ms` | Cooldown before trying half-open | 15,000-60,000ms |
| `half_open_trial_requests` | Trial calls allowed through in half-open | 2-3 |
| `success_threshold` | Consecutive trial successes needed to close | 2-3 |

## Recommended defaults

Use these unless the dependency's own SLA or an incident postmortem says
otherwise:

```
max_retries: 3
base_delay_ms: 200
backoff_multiplier: 2.0
max_delay_ms: 20000
jitter: full

failure_threshold: 50% over last 20 requests (min 10 sampled)
open_timeout_ms: 30000
half_open_trial_requests: 3
success_threshold: 2
```

## Common pitfalls to check for in review

- Retrying a non-idempotent operation without an idempotency key.
- Retry logic and circuit breaker not coordinated (retrying inside an
  already-open circuit).
- No jitter.
- A single circuit breaker shared globally instead of scoped per
  downstream host/endpoint — one failing dependency shouldn't fail-fast
  calls to unrelated ones.
- Every retry logged at ERROR level, paging on-call for things that
  self-healed.

See `reference.md` for a worked pseudocode implementation.
