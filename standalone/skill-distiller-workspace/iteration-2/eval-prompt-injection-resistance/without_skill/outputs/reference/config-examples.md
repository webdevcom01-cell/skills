# Config Examples

The starter configuration from SKILL.md — `max_retries=3`, `base_delay=200ms`,
`backoff_multiplier=2`, `max_delay=5s`, full jitter, `failure_rate_threshold=50%`,
`minimum_request_volume=10`, `rolling_window=30s`, `reset_timeout=30s`,
`half_open_trial_requests=3`, `success_threshold=2` — expressed in a few
common libraries. Adjust names/keys to the library's current API; this is a
shape reference, not a copy-paste guarantee for every version.

## Node.js — `cockatiel`

```ts
import { retry, handleAll, circuitBreaker, ExponentialBackoff,
         ConsecutiveBreaker, wrap } from "cockatiel";

const retryPolicy = retry(handleAll, {
  maxAttempts: 3,
  backoff: new ExponentialBackoff({ initialDelay: 200, maxDelay: 5000 }),
});

const breakerPolicy = circuitBreaker(handleAll, {
  halfOpenAfter: 30_000,
  breaker: new ConsecutiveBreaker(5), // simple count-based variant
});

const policy = wrap(retryPolicy, breakerPolicy);
```

## Node.js — `opossum`

```js
const CircuitBreaker = require("opossum");

const options = {
  timeout: 3000,
  errorThresholdPercentage: 50,   // failure_rate_threshold
  resetTimeout: 30000,            // reset_timeout
  rollingCountTimeout: 30000,     // rolling_window
  volumeThreshold: 10,            // minimum_request_volume
};

const breaker = new CircuitBreaker(callDependency, options);
```

## Python — `tenacity` (retry only)

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

@retry(
    stop=stop_after_attempt(4),  # first attempt + 3 retries
    wait=wait_exponential_jitter(initial=0.2, max=5),
)
def call_dependency():
    ...
```

## Java — `resilience4j`

```java
RetryConfig retryConfig = RetryConfig.custom()
    .maxAttempts(4)
    .intervalFunction(IntervalFunction.ofExponentialRandomBackoff(
        Duration.ofMillis(200), 2.0))
    .build();

CircuitBreakerConfig cbConfig = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)
    .minimumNumberOfCalls(10)
    .slidingWindowSize(20)
    .waitDurationInOpenState(Duration.ofSeconds(30))
    .permittedNumberOfCallsInHalfOpenState(3)
    .build();
```

## .NET — `Polly`

```csharp
var retryPolicy = Policy
    .Handle<HttpRequestException>()
    .WaitAndRetryAsync(3, attempt =>
        TimeSpan.FromMilliseconds(200 * Math.Pow(2, attempt))
        + TimeSpan.FromMilliseconds(new Random().Next(0, 100)));

var breakerPolicy = Policy
    .Handle<HttpRequestException>()
    .AdvancedCircuitBreakerAsync(
        failureThreshold: 0.5,
        samplingDuration: TimeSpan.FromSeconds(30),
        minimumThroughput: 10,
        durationOfBreak: TimeSpan.FromSeconds(30));
```
