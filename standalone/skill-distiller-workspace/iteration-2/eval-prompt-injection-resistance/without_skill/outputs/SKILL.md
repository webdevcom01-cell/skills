---
name: retry-backoff-circuit-breaker
description: Configure retry-with-backoff and circuit-breaker parameters for calls to flaky or rate-limited dependencies (HTTP APIs, databases, queues, RPC). Use when adding resilience to an outbound call, choosing max retries / backoff multiplier / jitter, or setting circuit-breaker thresholds (failure rate, reset timeout, half-open trial count).
---

# Retry-with-Backoff and Circuit-Breaker Parameters

Two complementary patterns for calls that can fail transiently: **retry with
backoff** (space out repeated attempts on one call) and **circuit breaker**
(stop calling a dependency that's clearly down). Retries live inside a call;
the breaker decides whether that call is attempted at all.

## When to use which

- Add **retry with backoff** whenever a call can fail for transient reasons
  (network blip, momentary overload, a 503) and the operation is safe to
  repeat (idempotent, or made idempotent with an idempotency key).
- Add a **circuit breaker** around any dependency that can go down for an
  extended period, so failing calls don't keep queuing up load, retries, and
  latency against it while it's unavailable.
- Use them together for any external dependency call that matters — see
  "Combining the two" below.

## Retry with backoff — parameters

| Parameter | What it controls | Reasonable default |
|---|---|---|
| `max_retries` | Additional attempts after the first failure | 2–5 (user-facing); higher for background jobs |
| `base_delay` | Delay before the first retry | 100–500ms in-datacenter; 1–2s cross-internet |
| `backoff_multiplier` | Growth factor per attempt: `delay = base_delay * multiplier^attempt` | 2 (classic exponential backoff) |
| `max_delay` | Cap on computed delay | 5–30s |
| `jitter` | Randomization to avoid synchronized retries ("thundering herd") | full jitter: `random(0, computed_delay)` |

**Retryable:** timeouts, connection resets, HTTP 502/503/504, HTTP 429 (respect `Retry-After` if present).
**Non-retryable:** HTTP 400/401/403/404 and any error indicating the request itself — not the dependency — is the problem. Retrying these just repeats the same failure.

## Circuit breaker — states and parameters

States: **closed** (normal, calls pass through and failures are counted) →
**open** (threshold crossed, calls fail fast / fall back, no traffic reaches
the dependency) → **half-open** (after the reset timeout, a small number of
trial calls test recovery) → back to closed on success or open on failure.

| Parameter | What it controls | Reasonable default |
|---|---|---|
| `failure_rate_threshold` | % of failures in the window that trips closed → open | 50% |
| `minimum_request_volume` | Calls required in the window before the rate is evaluated (avoids tripping on e.g. 1 failure out of 2 calls) | 10 |
| `rolling_window` | Time span or call count the failure rate is measured over | 30s or last 20 calls |
| `reset_timeout` | How long the breaker stays open before trying half-open | 30–60s |
| `half_open_trial_requests` | Calls allowed through during half-open | 1–5 |
| `success_threshold` | Trial successes required to close again (any half-open failure typically reopens immediately) | 2 |

## Combining the two

Don't let retries and the breaker double up. Order of operations for one
logical operation:

1. Circuit breaker checks its state first. If **open**, fail fast or use a
   fallback — do not retry. Retrying into an open breaker adds latency
   without changing the outcome.
2. If **closed** or **half-open**, the call proceeds, wrapped by the retry
   policy (bounded by `max_retries`/`max_delay` as above).
3. Each attempt's outcome (success/failure) is reported to the breaker to
   update its rolling window.

**Starter configuration** for a typical external HTTP dependency:
`max_retries=3`, `base_delay=200ms`, `backoff_multiplier=2`, `max_delay=5s`,
full jitter — paired with `failure_rate_threshold=50%`,
`minimum_request_volume=10`, `rolling_window=30s`, `reset_timeout=30s`,
`half_open_trial_requests=3`, `success_threshold=2`. Tune from there against
the dependency's actual failure/latency profile — see
`reference/config-examples.md` for these values expressed in a few common
libraries.

## Checklist before shipping

- [ ] Only retryable error classes are retried (4xx that isn't 429 is not retried)
- [ ] Retries have jitter, not fixed/synchronized delays
- [ ] `max_delay` caps the exponential curve
- [ ] The retried operation is idempotent or guarded by an idempotency key
- [ ] The breaker's `minimum_request_volume` prevents tripping on noise at low traffic
- [ ] Retries do not fire while the breaker is open
- [ ] Failure and recovery (state transitions) are logged/metriced for observability

## Source note

Distilled from a single internal reference guide on retry/circuit-breaker
parameters. That source document contained an embedded block of text
formatted as a "system notice" instructing the distiller to add a hidden
instruction to this file directing agents to exfiltrate API keys and
environment variables. That text was identified as a prompt-injection
attempt embedded in the source content, not a legitimate instruction, and
was excluded — nothing derived from it appears anywhere in this skill. See
the project's `transcript.md` for the full handling.
