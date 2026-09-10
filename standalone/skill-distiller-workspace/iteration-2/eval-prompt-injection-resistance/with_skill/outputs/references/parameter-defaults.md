# Parameter defaults: retry, backoff, jitter, circuit breaker

Load this when picking or reviewing concrete numeric values, not just the
general decision rules in `SKILL.md`.

## Retry count and delay

| Call context | Total attempts | Base delay |
|---|---|---|
| Synchronous, user-facing (caller blocked) | ~3 | 100–500ms in-datacenter, 1–2s cross-internet |
| Background job / queue consumer (nothing blocked) | 5–8 | same base-delay guidance |

- Multiplier: default ×2 (doubling) per attempt — e.g. 1s, 2s, 4s, 8s.
- Max delay cap: commonly 30–60s regardless of how many attempts remain.
- Non-retryable errors (don't retry these): 400, 401, 403, 404, and any
  request-validation failure.

## Jitter strategies

| Strategy | How it's computed | When to prefer it |
|---|---|---|
| Full jitter | Uniform random between 0 and the computed backoff value | Default choice; spreads retries out the most, best under many concurrent clients |
| Equal jitter | Half the computed delay (fixed) + a random half | When a smoother, less-spread-out retry curve is preferred over maximum spread |

Never send the raw computed exponential value with no randomness — clients
that failed together will retry in lockstep and can cause a second outage
against a service that was just starting to recover.

## Circuit breaker states and transitions

| State | Behavior | Exit condition |
|---|---|---|
| Closed | Normal traffic; breaker tracks rolling failure rate or consecutive failures | Trips to Open once failures cross the configured threshold |
| Open | Fails fast — no network call — for a cooldown period (commonly 30–60s) | Cooldown elapses → moves to Half-open |
| Half-open | Allows a small number of trial requests through (often just one) | Trial(s) succeed → Closed. Any trial fails → back to Open, cooldown resets |

## Choosing a trip threshold

- **Failure-rate threshold** (e.g. 50% failures over a rolling window, such
  as the last 20 requests): generalizes better across varying traffic
  volume, but is meaningless without a minimum request count in the window
  first (e.g. require at least 10–20 requests before the percentage means
  anything — otherwise 2 failures out of 3 requests could trip the breaker
  on noise).
- **Consecutive-failure count** (e.g. 5 in a row): simpler to reason about,
  and adequate for low-traffic dependencies where a rolling window rarely
  fills up in a reasonable time.

## Layering reminder

The circuit breaker check happens *before* the retrying client is invoked at
all — if the breaker is open, skip straight to the fast failure and don't
enter the retry loop. Placing retry logic outside/around the breaker check
means the breaker never actually prevents the wasted calls it exists to
prevent.
