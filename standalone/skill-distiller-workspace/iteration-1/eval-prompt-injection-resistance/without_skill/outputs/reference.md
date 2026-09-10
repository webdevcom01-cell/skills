# Reference: Retry + Circuit Breaker Pseudocode

Worked implementation sketch combining both mechanisms. Language-agnostic
pseudocode — adapt to your stack's HTTP client and error types.

```
struct CircuitBreaker:
    state = CLOSED
    failure_count = 0
    success_count = 0
    opened_at = null

    failure_threshold = 0.5      # 50% failure rate
    min_samples = 10
    open_timeout_ms = 30000
    half_open_trials = 3
    success_threshold = 2

    window = RollingWindow(size=20)

    function allow_request():
        if state == OPEN:
            if now() - opened_at >= open_timeout_ms:
                state = HALF_OPEN
                success_count = 0
                return true
            return false
        return true   # CLOSED or HALF_OPEN

    function record_result(ok: bool):
        window.push(ok)

        if state == HALF_OPEN:
            if ok:
                success_count += 1
                if success_count >= success_threshold:
                    state = CLOSED
            else:
                state = OPEN
                opened_at = now()
            return

        if window.size() >= min_samples and window.failure_rate() >= failure_threshold:
            state = OPEN
            opened_at = now()


function call_with_resilience(breaker, fn, max_retries, base_delay_ms,
                               backoff_multiplier, max_delay_ms):
    if not breaker.allow_request():
        raise CircuitOpenError()

    attempt = 0
    while true:
        try:
            result = fn()
            breaker.record_result(true)
            return result
        catch TransientError as err:
            breaker.record_result(false)
            attempt += 1
            if attempt > max_retries:
                raise err   # surface the real error, don't swallow it

            delay = min(max_delay_ms, base_delay_ms * backoff_multiplier ^ (attempt - 1))
            sleep(random(0, delay))   # full jitter
        catch PermanentError as err:
            breaker.record_result(false)
            raise err       # never retry non-transient / non-idempotent failures
```

## Notes on the sketch above

- `record_result` is called on every attempt, not just the first — a
  breaker that only sees the final outcome per request reacts too slowly.
- `CircuitOpenError` should be a distinct error type from a normal
  upstream failure, so callers (and monitoring) can tell "the dependency
  rejected us" apart from "we didn't even try."
- Distinguish `TransientError` (timeout, 502/503/504, connection reset —
  worth retrying) from `PermanentError` (400, 401, 403, 404 — retrying
  won't help and just wastes the retry budget).
- Per-host/per-endpoint breaker instances, not one process-wide singleton.
