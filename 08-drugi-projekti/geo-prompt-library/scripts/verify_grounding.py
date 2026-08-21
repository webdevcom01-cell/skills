#!/usr/bin/env python3
"""Verify that grounding citations actually exist on their source pages.

validate_library.py (the gate) checks that `source_url` and `evidence`/`quote`
FIELDS ARE PRESENT and non-empty. It does not check that the quoted text is
actually on that page -- a model under pressure to keep `inferred` low can just
write a plausible-sounding citation, and the gate lets it through. That is
exactly the hallucination this skill exists to prevent (Faza 2's
anti-halucinacijsko pravilo in SKILL.md).

Deliberately a SEPARATE script from the gate, not another G-rule:
- The gate runs in a retry loop (Faza 7, up to 3x) and must stay fast and
  offline. This script needs the network per unique source_url and can be slow
  or rate-limited -- wrong to put in that loop.
- A network failure here (timeout, DNS, 5xx, blocked robots) is NOT the same
  finding as a citation that plainly is not on the page. Conflating "we
  couldn't check" with "we checked and it's fake" would itself be a form of
  the dishonesty this exists to catch, so the two are never reported the same
  way: unreachable -> warning, quote-not-found -> hard fail (exit 1).

`passed: true` requires BOTH zero fabricated citations AND enough coverage to
trust that finding. A run where every fetch fails (Cloudflare, rate limit,
network down) has zero not_found citations by construction -- not because
nothing was fake, but because nothing was checked. Early versions of this
script reported that as `passed: true`, which reads as "verified, all good"
when the honest reading is "verified nothing". `coverage_status` (see
`_coverage_status`) makes that distinction explicit and `passed` reflects it.

Run: python -B scripts/verify_grounding.py <file.json>
"""

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

VERSION = "0.1.0-draft"
EXIT_PASS = 0
EXIT_FAIL = 1

USER_AGENT = "geo-prompt-library-verify-grounding/0.1 (+https://cloudflow.rs)"
TIMEOUT_SECONDS = 10

# Same-host courtesy delay: montenegrocharter.com's v2 run dropped from
# 27/50 verified (v1) to 5/50 (v2) between two back-to-back runs with no
# content change -- fast sequential requests to one host were tripping
# something on their side (results came back as SSL handshake timeouts, not
# clean 429s, so this is a courtesy pace-limiter, not 429-triggered backoff).
SAME_HOST_DELAY_SECONDS = 0.75
RATE_LIMIT_ERROR_MARKERS = ("timed out", "timeout", "429", "too many requests")


def _is_rate_limit_like(error):
    """Heuristic, not a guarantee -- the real failure mode observed against
    montenegrocharter.com is an SSL handshake timeout, which is indistinguishable
    from a generic network blip except by pattern-matching the message. Used only
    to size a warning for a human, never to change verified/not_found/unreachable
    classification."""
    lowered = error.lower()
    return any(marker in lowered for marker in RATE_LIMIT_ERROR_MARKERS)

TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text):
    """Collapse whitespace so real-world line wrapping / indentation in HTML
    doesn't cause a false 'not found' on a citation that is genuinely there."""
    return WHITESPACE_RE.sub(" ", text).strip().lower()


def _html_to_text(raw_html):
    """Naive tag stripping, not a real HTML parser. Good enough to catch
    citations in normal server-rendered text; will false-negative on content
    that only exists after client-side JS renders it -- that case should
    report as 'not_found' and a human should double check manually rather
    than the script silently passing it."""
    no_scripts = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw_html)
    text = TAG_RE.sub(" ", no_scripts)
    return html.unescape(text)


def fetch(url):
    """Returns (normalized_text, None) on success, (None, error_message) on
    any failure -- caller treats the second case as 'unreachable', not 'fake'."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            status = getattr(resp, "status", 200)
            if not (200 <= status < 300):
                return None, f"HTTP {status}"
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read().decode(charset, errors="replace")
            return _normalize(_html_to_text(raw)), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        return None, str(exc)


def collect_claims(lib):
    """Every (source_label, url, quote) grounding claim in the library."""
    claims = []
    for i, offering in enumerate(lib.get("company", {}).get("offerings", [])):
        url, quote = offering.get("source_url"), offering.get("evidence")
        if url and quote:
            claims.append((f"company.offerings[{i}] ({offering.get('name', '?')})", url, quote))
    for intent in lib.get("intents", []):
        grounding = intent.get("grounding") or {}
        url, quote = grounding.get("url"), grounding.get("quote")
        if url and quote:
            claims.append((f"{intent.get('intent_id', '?')}.grounding", url, quote))
    return claims


COVERAGE_THRESHOLD = 0.5


def _coverage_status(verified, not_found, unreachable):
    """Coverage over the CHECKABLE claims only -- unreachable is excluded from
    the denominator on purpose. A run where every fetch was blocked (Cloudflare,
    rate limit, network down) must not read as "passed": exclude unreachable
    from the ratio and it silently divides to 0/0 -> looks like "nothing to
    verify" instead of "verified everything we could reach", which is the
    wrong reading when there WERE claims that needed checking.

    Four states, not two, because "no claims existed" (thin-site fallback,
    correctly all inferred:true) and "claims existed but 100% unreachable"
    (this run told us nothing) must not collapse into the same status -- only
    the second one is the bug this exists to catch.
    """
    denom = verified + not_found
    if denom == 0:
        # verified == not_found == 0 always holds here (denom is their sum) --
        # the only way to tell "nothing to check" from "checked nothing" apart
        # is whether any claim existed at all, i.e. unreachable > 0.
        return None, "no_data" if unreachable > 0 else "no_claims"
    coverage = verified / denom
    return coverage, "ok" if coverage >= COVERAGE_THRESHOLD else "insufficient"


def verify(lib):
    claims = collect_claims(lib)
    urls = sorted({url for _, url, _ in claims})

    fetch_cache = {}
    last_request_at = {}  # host -> time.monotonic() of the last request to it
    rate_limited_urls = []
    for url in urls:
        host = urlparse(url).netloc
        last = last_request_at.get(host)
        if last is not None:
            wait = SAME_HOST_DELAY_SECONDS - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        last_request_at[host] = time.monotonic()
        text, error = fetch(url)  # fetch each unique url exactly once
        fetch_cache[url] = (text, error)
        if error is not None and _is_rate_limit_like(error):
            rate_limited_urls.append(url)

    if rate_limited_urls:
        print(
            f"RATE LIMIT: {len(rate_limited_urls)}/{len(urls)} URL-ova nedostupno sa "
            f"greskom nalik rate limitu (timeout/429) i pored {SAME_HOST_DELAY_SECONDS}s "
            "pauze izmedju zahtjeva ka istom hostu.",
            file=sys.stderr,
        )

    results = []
    warnings = []
    for source, url, quote in claims:
        page_text, error = fetch_cache[url]
        if error is not None:
            results.append({"source": source, "url": url, "status": "unreachable", "detail": error})
            warnings.append(f"{source}: {url} nedostupan ({error}) -- citat NIJE proveren, ne tretiraj kao potvrdjen niti kao lazan")
            continue
        if _normalize(quote) in page_text:
            results.append({"source": source, "url": url, "status": "verified", "detail": "citat pronadjen na stranici"})
        else:
            results.append({
                "source": source, "url": url, "status": "not_found",
                "detail": f"citat {quote!r} nije pronadjen na {url} (posle normalizacije whitespace-a)",
            })

    hard_fails = [r for r in results if r["status"] == "not_found"]
    verified_count = sum(1 for r in results if r["status"] == "verified")
    unreachable_count = sum(1 for r in results if r["status"] == "unreachable")
    coverage, coverage_status = _coverage_status(verified_count, len(hard_fails), unreachable_count)

    if coverage_status == "no_data":
        warnings.append(
            f"POKRIVENOST NEDOVOLJNA: {len(claims)} tvrdnji postojalo, 0 provereno -- "
            f"svi fetch-evi neuspesni. Ovaj run NIJE potvrdio nijedan citat, ne tretiraj "
            f"passed=false ovde kao 'nadjen lazan citat', nego kao 'nismo mogli da proverimo'."
        )
    elif coverage_status == "insufficient":
        warnings.append(
            f"POKRIVENOST NEDOVOLJNA: coverage={coverage:.2f} ({verified_count} verified / "
            f"{verified_count + len(hard_fails)} checkable) < {COVERAGE_THRESHOLD} prag. "
            f"Vecina proveza je ili nedostupna ili lazna -- ne veruj ovom run-u bez rucne provere."
        )

    if rate_limited_urls:
        warnings.append(
            f"RATE LIMIT: {len(rate_limited_urls)}/{len(urls)} URL-ova nedostupno sa greskom "
            f"nalik rate limitu (timeout/429) i pored {SAME_HOST_DELAY_SECONDS}s pauze izmedju "
            "zahtjeva ka istom hostu -- pokusaj ponovo kasnije pre nego sto se coverage_status "
            "'insufficient'/'no_data' protumaci kao problem sa sadrzajem."
        )

    blocking_coverage = coverage_status in ("no_data", "insufficient")
    return {
        "verify_grounding_version": VERSION,
        "passed": not hard_fails and not blocking_coverage,
        "urls_checked": len(urls),
        "urls_rate_limited": len(rate_limited_urls),
        "claims_checked": len(claims),
        "claims_verified": verified_count,
        "claims_not_found": len(hard_fails),
        "claims_unreachable": unreachable_count,
        "coverage": coverage,
        "coverage_status": coverage_status,
        "results": results,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library_json", help="Path to <slug>-library-vN.json")
    args = parser.parse_args()

    lib = json.loads(Path(args.library_json).read_text(encoding="utf-8"))
    report = verify(lib)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(EXIT_PASS if report["passed"] else EXIT_FAIL)


if __name__ == "__main__":
    main()
