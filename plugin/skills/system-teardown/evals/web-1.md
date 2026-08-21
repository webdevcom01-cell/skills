# Run `web-1` — raw output

| | |
|---|---|
| Target type | web |
| Target / pin | https://httpbin.org/ (third party, public, unauthenticated) |
| Verdict | **FAIL** |
| session_id | `07f607a5-7f2b-450c-9614-c3c2ea46e6e5` |
| Turns | 26 |
| Cost (USD) | 1.72 |
| is_error | False |
| Deliverable | httpbin.org-orientation.md |
| Deliverable words | 2384 |

**Grade:** P1 sections PASS · P2 ledger PASS · P3 unknowns PASS · P4 deviations-out-loud FAIL → **FAIL**

**Reason:** ledger 12+4+0=16 correct, every INFERRED row given a named ruled-out alternative, refused load testing on authorization grounds; 2384w never acknowledged

## Prompt given (verbatim)

```
Use the system-teardown skill.

Target: the public website https://httpbin.org/ . It is a third party's public, unauthenticated site and I only have ordinary permitted use of it — no account, no credentials, no authorization beyond browsing what it serves publicly.

Help me understand how that product is built and served.

Write any output file into the current working directory and tell me the path.
```

## Agent stdout (verbatim)

```
**`/private/tmp/claude-501/-Users-buda007--claude-skills/c1fe6555-a560-4f4a-9571-e36f24c52787/scratchpad/td-runs/web-1/httpbin.org-orientation.md`**

The short version of what's in it:

**Built:** Python/Flask app (Werkzeug 404 page + Werkzeug ETag format + `/flasgger_static/` all agree), docs UI is flasgger rendering a Swagger 2.0 spec at `/spec.json` (52 paths, 11 tags), served by gunicorn 19.9.0. It's the MIT-licensed open-source httpbin at version 0.9.2 — confirmed by four behavioural matches to upstream source, not by recognizing the name.

**Served:** one AWS Application Load Balancer in us-east-1 → the gunicorn process, and that's the whole path. Route 53 DNS, ACM cert, eight A records all reversing to `compute-1.amazonaws.com`. No CDN, no nginx, no object store, no compression layer, no analytics, no database evidence. The app serves its own 150 KB of Swagger CSS.

**Two things worth knowing** (§5 in the memo): `/headers` silently strips `X-Forwarded-*` and friends by default — `?show_env=1` is what exposed the proxy layer at all — and the strip list still filters Heroku and Varnish headers from a hosting arrangement the service no longer uses. Also the homepage's own source link 301s elsewhere; the deployed HTML predates the repo move.

**Ledger:** 16 inferred claims, 12 confirmed with a named alternative ruled out, 4 downgraded to UNCONFIRMED, 0 dropped. Coverage was 13 of 52 documented endpoints, 3 of 8 A records, ~45 requests in one 5-minute window — small numbers, stated as small.

Access basis held to what you specified: documented endpoints only, no fuzzing, no enumeration, no auth, no load or failover testing. That last exclusion is why the worker model, instance count, and compute substrate (EC2 vs ECS vs Beanstalk — indistinguishable from outside) are in §7 as unresolved rather than guessed.
```

## Deliverable written by the run — `httpbin.org-orientation.md` (verbatim)

# Orientation: httpbin.org

## 0. Provenance

- **Pin** — `https://httpbin.org/`, captured 2026-08-19 19:46–19:51 UTC from a client in
  Europe (origin AS-visible IP `95.155.56.26`), unauthenticated, no account. Served app
  self-reports version `0.9.2`. Resolved backends at capture time: eight A records, all
  `ec2-*.compute-1.amazonaws.com`.
- **Depth** — working
- **Access basis** — third party's public, unauthenticated site; ordinary permitted use only.
  Every request was a normal GET/HEAD/OPTIONS to a path the site itself documents in its own
  OpenAPI spec, plus six 404-probes of conventional metadata paths (`/openapi.json`,
  `/sitemap.xml`, `/.well-known/security.txt`, …). **No fuzzing, no enumeration, no
  authentication, no rate-limit or WAF testing, no attempt to reach anything not publicly
  served.** Roughly 45 requests total.
- **What was NOT examined** — 39 of the 52 documented endpoints; the auth, digest-auth and
  redirect families entirely; any behaviour under load; anything inside the AWS account
  (instance count, autoscaling, logging, CI/CD). There are no plan tiers or logins to observe.

## 1. What this system is

httpbin is a request-and-response echo service: a set of ~52 HTTP endpoints that do
deliberately boring, precisely specified things — return your own headers back to you, return
a chosen status code, delay N seconds, stream N lines, set a cookie, serve a gzipped or
brotli'd body. It exists so that HTTP client libraries, proxies, load balancers and CI
pipelines have a stable, public, free thing to test against. It is developer infrastructure,
not a product: no accounts, no pricing, no state that outlives a request. It was written by
Kenneth Reitz as a companion to the Python `requests` library and is MIT-licensed open source;
the homepage links its own source repository in the corner ribbon.

The interesting question is therefore not *what does it do* — the spec answers that — but
*how does something this old stay up*, and the answer turns out to be: by being almost
entirely stateless and almost entirely unchanged.

## 2. System context

```
   ┌────────────────────┐        ┌──────────────────────┐
   │ HTTP client authors│        │ CI pipelines & test  │
   │ (curl, requests,   │        │ suites needing a real│
   │  Postman users)    │        │ HTTP endpoint        │
   └─────────┬──────────┘        └──────────┬───────────┘
             │  HTTPS / HTTP                │
             └──────────────┬───────────────┘
                            ▼
                ┌───────────────────────────┐
                │        httpbin.org        │
                │  echo / status / delay /  │
                │  stream / cookie service  │
                │      (this system)        │
                └───────┬───────────┬───────┘
                        │           │
       serves its own   │           │  no outbound calls observed:
       Swagger UI docs  │           │  no analytics, no CDN, no
       from the same    ▼           ▼  database, no third-party SDK
                ┌──────────────┐  ┌──────────────────────┐
                │ Browsers     │  │ Google Fonts (only   │
                │ reading docs │  │ external dependency, │
                └──────────────┘  │ a CSS <link> in HTML)│
                                  └──────────────────────┘
```

The absence of arrows is the finding. A page-load pulls one external resource — a Google Fonts
stylesheet — and nothing else. No analytics tag, no error-reporting beacon, no CDN edge, no
identity provider, no payment vendor. Whatever this system costs to run, it costs it in one
AWS account and nowhere else.

## 3. How it's put together

**A Python WSGI app, served by gunicorn, behind one AWS load balancer.** That is the whole
architecture, and it is four layers where most sites have eight.

- **The application is Flask.** Nothing says "Flask" in a header, but three independent traces
  do: the 404 body is Werkzeug's verbatim default page (`HTML PUBLIC "-//W3C//DTD HTML 3.2
  Final//EN"`), static files come back with Werkzeug's distinctive
  `"<mtime>-<size>-<adler32>"` ETag format, and the docs UI lives under `/flasgger_static/` —
  flasgger being a Flask-only extension.
- **The docs are the app.** `/` is not a marketing page; it is Swagger UI rendering
  `/spec.json`, a Swagger 2.0 document the app generates from its own route docstrings. The
  spec is the product documentation, the test fixture and the API contract in one file. 52
  paths, 11 tags, `get` on 48 of them.
- **The server is gunicorn 19.9.0**, advertised in every `Server:` header, on every backend
  IP tested. Version 19.9.0 shipped in 2018.
- **Exactly one proxy hop, and it is an AWS Application Load Balancer.** The app sees
  `X-Forwarded-For`, `X-Forwarded-Port`, `X-Forwarded-Proto` and `X-Amzn-Trace-Id` — and
  nothing else. That precise four-header set with no `Via`, no `X-Real-Ip`, no
  `x-amz-cf-id`, no `x-amzn-RequestId` is an ALB's signature and nobody else's.
- **The app serves its own static files.** `swagger-ui.css` (150 KB) comes back with
  `Server: gunicorn`, a Werkzeug ETag and `Cache-Control: public, max-age=43200`. There is no
  nginx, no S3, no CloudFront in the path — the Python process is doing it.
- **Infrastructure is one region, one provider.** All eight A records reverse to
  `compute-1.amazonaws.com` (us-east-1), nameservers are Route 53, and the TLS certificate is
  ACM-issued (`Amazon RSA 2048 M01`, SANs `httpbin.org` and `*.httpbin.org`, valid to
  2027-01-02).

## 4. Decisions that shape it

| Decision | Probable reason | Evidence | Verdict |
|---|---|---|---|
| No CDN in front | Caching would defeat the purpose — every response is supposed to reflect *your* request | No `Age`, `X-Cache`, `CF-Ray`, `Via`; TTFB 0.73–0.99 s from Europe, i.e. transatlantic to origin every time | CONFIRMED |
| No response compression at the transport layer | Compression is a *feature under test* here (`/gzip`, `/brotli`, `/deflate`); compressing everything would corrupt the experiment | `Accept-Encoding: gzip, deflate, br` on `/` returns 9593 bytes with no `Content-Encoding` | CONFIRMED |
| `Access-Control-Allow-Origin: *` on literally every response | The service is meant to be called from other people's browser test pages | Present on HTML, JSON, CSS, images, 404s and 500s alike | CONFIRMED |
| Load balancer accepts any `Host` | Single default target group; nobody bothered with host-based rules | A request with `Host: nosuch.example` to the same IP returns the normal homepage, 200 | CONFIRMED |
| Ship it and stop touching it | It is a stable test fixture; churn would break the ecosystem depending on it | Static assets stamped `Last-Modified: Tue, 14 Jan 2020`; gunicorn 19.9.0; app version 0.9.2 | CONFIRMED |

## 5. Where the bodies are buried

**The source link on the homepage points at a repository that has moved.** The corner ribbon
says `github.com/requests/httpbin`; that URL 301s to `github.com/postmanlabs/httpbin`. The
project changed stewardship and the deployed HTML never got the memo. Anyone following the
in-page link lands on the right code by accident, not by design.

**`/headers` lies to you by default, and that is deliberate.** It will not show you
`X-Forwarded-For`, `X-Forwarded-Proto`, `X-Real-Ip`, `Via` or a batch of Heroku headers — the
app strips a hardcoded `ENV_HEADERS` list before echoing. If you are debugging a proxy chain
against httpbin and concluding "my load balancer isn't setting XFF", you are being misled by
the tool. Append `?show_env=1` and they reappear. This one flag is what let this teardown see
the proxy layer at all: `/headers` showed four headers, `/headers?show_env=1` showed seven.

**The stripped list is a fossil.** It filters `X-Heroku-Queue-Depth`, `X-Heroku-Dynos-In-Use`,
`Total-Route-Time`, `X-Varnish` — headers from a Heroku-and-Varnish deployment this service no
longer has. The code still carries the shape of an earlier hosting arrangement; the running
system is plain EC2 behind an ALB.

**`origin` is not "your IP".** It is the `X-Forwarded-For` chain. Send your own
`X-Forwarded-For: 203.0.113.7` and `/get` reports `"origin": "203.0.113.7, 95.155.56.26"` —
the ALB appended, the app printed the whole chain. Treat it as advisory, never as identity.

**A `Server:` header is the weakest kind of evidence and here it happens to be true.** It was
believed only because Werkzeug's 404 page, Werkzeug's ETag format and flasgger's asset path
independently agree with it. Had they disagreed, the header would have lost.

## 6. Falsification ledger

```
FALSIFICATION LEDGER
Target: web   Depth: working
Method: evidence-column attack — every inferred claim given a named alternative explanation
        that would produce the same evidence, then ruled out or the claim downgraded

Inferred claims (one row each — this list IS N):
  C1  Application framework is Flask/Werkzeug → CONFIRMED
      alt: a bare Werkzeug or other WSGI app that shares the 404 page and ETag format
      ruled out: /flasgger_static/ is served 200, and flasgger is a Flask-only extension
  C2  Docs UI is flasgger rendering a Swagger 2.0 spec → CONFIRMED
      alt: hand-rolled Swagger UI at a coincidentally named path
      ruled out: homepage credits github.com/rochacbruno/flasgger; /spec.json carries
      flasgger's non-standard top-level "protocol" key alongside "swagger": "2.0"
  C3  App server is gunicorn 19.9.0 → CONFIRMED
      alt: a spoofed Server header
      ruled out: consistent across 3 of 8 backend IPs and every content type, and the
      Werkzeug-shaped 404/ETag corroborate a Python WSGI stack
  C4  gunicorn runs the gevent worker class → UNCONFIRMED
      attempted: upstream Dockerfile CMD is `gunicorn ... -k gevent`, but the same Pipfile
      also pins meinheld, and the deployment may override CMD; not observable from outside
  C5  Deployed code is the open-source httpbin project at 0.9.2 → CONFIRMED
      alt: an unrelated service imitating the API
      ruled out by four independent behavioural matches to upstream source: /spec.json
      info.version == repo httpbin/VERSION == 0.9.2; /deny returns the exact ANGRY_ASCII
      art; /robots.txt is byte-identical to ROBOT_TXT; /headers?show_env=1 hides and
      reveals precisely the ENV_HEADERS tuple
  C6  The deployed code is unmodified upstream → UNCONFIRMED
      attempted: four behaviours match, but 39 of 52 endpoints were never exercised and a
      private fork would be invisible from outside
  C7  Static assets are served by the Python app, not a web server or object store → CONFIRMED
      alt: nginx or S3 in front
      ruled out: ETag "1578987262.0-153930-3675134707" is Werkzeug's mtime-size-adler32
      format; nginx uses hex-hex, S3 uses an MD5 — and Server: gunicorn is on those responses
  C8  Exactly one reverse-proxy hop, an AWS Application Load Balancer → CONFIRMED
      alts: CloudFront (would add Via + X-Amz-Cf-Id), API Gateway (x-amzn-RequestId,
      x-amz-apigw-id), nginx (X-Real-Ip), NLB (injects nothing at all) — all ruled out by
      the exact header set at /headers?show_env=1; single-entry XFF proves one hop
  C9  Hosted on AWS us-east-1: EC2 targets, Route 53 DNS, ACM certificate → CONFIRMED
      alt: a non-AWS host using AWS DNS only
      ruled out: all 8 A records PTR to ec2-*.compute-1.amazonaws.com and the leaf cert is
      Amazon-issued with an ALB-compatible SAN set
  C10 No CDN or edge cache in the path → CONFIRMED
      alt: a CDN configured to strip all identifying headers
      ruled out on timing: 0.73–0.99 s TTFB from Europe on cacheable static assets is
      origin-distance latency, not an edge hit
  C11 The load balancer forwards arbitrary Host values to one default target → CONFIRMED
      alt: a wildcard host rule
      not distinguishable from outside, but either way there is no host-based segmentation:
      Host: nosuch.example returns the normal 200 homepage
  C12 No transport-layer response compression → CONFIRMED
      alt: content type deemed incompressible
      ruled out: the resource is text/html and was returned uncompressed at full length
  C13 Served static assets have not changed since 2020-01-14 → CONFIRMED
      evidence: Last-Modified 2020-01-14 07:34:22 (CSS) and 07:02:15 (favicon)
  C14 The container image was built in Jan 2020 and never rebuilt → UNCONFIRMED
      attempted: mtimes are consistent with it, but Docker ADD preserves build-context
      mtimes, so a later rebuild from the same checkout would look identical
  C15 TLS policy rejects TLS 1.0/1.1 → UNCONFIRMED
      attempted: TLS 1.2 and 1.3 both negotiate; the local LibreSSL build silently ignored
      -tls1, so legacy protocol acceptance was never actually tested
  C16 No server-side session or shared state on the paths exercised → CONFIRMED
      alt: a datastore behind endpoints not exercised
      narrowed rather than assumed — the claim is scoped to the 13 paths traced: cookies are
      plain unsigned Set-Cookie echoes, no session cookie is ever issued, /uuid returns
      independent values, and no backend affinity was observable across 3 IPs

  N = 16   confirmed 12 / downgraded 4 / dropped 0   (12+4+0=16)

Coverage denominator (a countable artifact, not a chosen figure):
  INFERRED claims given a named alternative and ruled out: 12 of 16 rows in this ledger

System scale examined:
  13 of 52 documented spec paths exercised · 3 of 8 A records tested · 1 region · 0 of 0
  account tiers (none exist) · ~45 requests total · one capture window, ~5 minutes

Falsification NOT performed, and why:
  No load, concurrency or failover testing — that would be availability testing of a third
  party's service without authorization, which this teardown's access basis excludes. So the
  worker model (C4), instance count and autoscaling behaviour stay unresolved by design.
```

## 7. What we could not determine

| Unknown | Why unresolved | What would resolve it |
|---|---|---|
| Compute substrate — raw EC2, ECS/Fargate, or Elastic Beanstalk behind the ALB | All three present identically to an outside client: EC2-range target IPs, ALB headers, gunicorn | Access to the AWS account, or a public infrastructure repo / IaC definition |
| gunicorn worker class and concurrency (C4) | Not exposed in any header or behaviour; distinguishing gevent from meinheld needs concurrent load | Concurrency testing — requires authorization from the operator |
| Fleet size and autoscaling | 8 A records are the ALB's own IPs, not a target count | CloudWatch/ASG visibility, i.e. account access |
| Whether the running code is a modified fork (C6) | 39 of 52 endpoints unexercised; a fork is invisible externally | Exercising the full spec, or an operator statement about the deployed ref |
| TLS 1.0/1.1 acceptance (C15) | Local OpenSSL build ignored the legacy-protocol flag | `sslyze`/`testssl.sh` against the host, or a modern OpenSSL build |
| Logging, monitoring, alerting, deploy pipeline | Entirely internal; nothing leaks into responses | Operator access |
| Whether any endpoint touches a datastore | Only 13 paths traced; none needed persistence | Exercising the remaining 39, chiefly the auth and cookie families |

## 8. Where to go deeper

The trustworthy documentation is the system's own `/spec.json` — it is generated from the
running code, so it cannot drift from the routes it describes, and it is the right starting
point for anything you want to build against. The untrustworthy artifact is the homepage's
source link, which points at a repository that has moved (see §5). The upstream repo at
`github.com/postmanlabs/httpbin` — MIT-licensed, so reading it carries no clean-room
concern — corroborated four separate deployed behaviours here and is the fastest route to
answering anything about application internals.

A Full teardown would add little that matters: for the application layer the source is public,
and everything genuinely unresolved in §7 sits inside an AWS account no outside observation can
reach. If you need those answers, the path is asking the operator, not looking harder.
