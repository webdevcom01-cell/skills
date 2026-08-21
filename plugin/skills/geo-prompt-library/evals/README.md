# Evals — protokol

## Pre pokretanja: URL mora biti stvaran

`evals.json` je prvobitno imao 5 izmišljenih URL-ova — svih pet NXDOMAIN, provereno `host` komandom, ne pretpostavljeno. Da su evali pušteni takvi, sva 5 bi pala na fallback granu za nedostupan sajt i `A8`/`A13` bi bili besmisleni svuda — merili bismo pokvarene test podatke, ne skill.

**Pravilo, bez izuzetka:** pre nego što se bilo koji eval iz ovog fajla pokrene, njegov URL mora proći:

```bash
host <domen>              # mora resolvovati, ne NXDOMAIN
curl -sI <url> | head -1  # mora vratiti HTTP 200 (ili 3xx ka 200, ne 404/5xx/timeout)
```

Ne izmišljati zamenske URL-ove kao workaround.

**Status URL-ova (2026-08-01):**

| # | Eval | URL | Status |
|---|---|---|---|
| 0 | local-service-sr | `https://dentio.rs` | DNS + HTTP 200 potvrđeno. Stomatološka ordinacija, Novi Sad, 9 kategorija usluga, pun cenovnik — stvaran sadržaj za grounding. |
| 1 | b2b-saas-mixed-code | `https://pausal.rs` | DNS + HTTP 200 potvrđeno. |
| 2 | croatian-ecommerce | `https://instar-informatika.hr` | DNS + HTTP 200 potvrđeno. |
| 3 | thin-site-fallback | `PENDING_REAL_URL` | **I dalje na čekanju.** Ne zameniti izmišljenim ili nepostojećim domenom — vidi napomenu ispod. |
| 4 | global-saas-no-local | `https://savvycal.com` | DNS + HTTP 200 potvrđeno. Namerno biran umesto cal.com/linear.app: poznati SaaS-ovi su gusto zastupljeni u trening podacima modela, pa model može napisati biblioteku IZ SEĆANJA umesto sa stvarnog fetch-a, i to se ne bi primetilo. |

**Zašto eval 3 NE sme dobiti izmišljen/nepostojeći domen kao privremeno rešenje:** izmišljen domen testira `ConnectionError`/NXDOMAIN — fetch pukne PRE HTTP-a. To nije scenario koji ovaj eval treba da testira. Realan `thin-site-fallback` slučaj je: sajt vrati HTTP 200, ali je JS ljuska bez izvučivog teksta (SPA koja renderuje sadržaj tek u browseru). Skill mora prepoznati "imam 200, nemam sadržaj" i tražiti input od korisnika (ili generisati sa `confidence: low`) — to je suštinski druga grana koda od "sajt ne postoji". Dok se ne dobije stvaran tanak sajt, eval 3 ostaje `PENDING_REAL_URL` i ne pokreće se.

## Zašto baseline (bez skilla) ovde skoro ništa ne meri

Standardni skill-creator-pro obrazac je with-skill vs baseline (bez skilla) poređenje po istom promptu. Za ovaj skill je to poređenje slabo informativno: subagent bez skilla neće ni pokušati da proizvede JSON po `library.schema.json` — nema odakle da zna šemu, kvote, ili G1–G17 pravila. `A1`–`A17` će kod baseline-a biti ~0 skoro sigurno. To dokazuje da skill POSTOJI, ne da je DOBAR.

**Prava metrika je druga:** da li izlaz prolazi SOPSTVENI gate na stvarnom sajtu, i iz kog pokušaja. Faza 6 u SKILL.md dozvoljava do 3 pokušaja regenerisanja pogođenih ćelija — koliko se skill oslanja na taj retry safety net, umesto da pogodi ispravno iz prve, jeste signal da li su ranije faze (najviše Faza 4 — formulisanje SR upita) dovoljno precizne.

## Šta zapisati iz svakog with_skill run-a

Pored standardnog `timing.json` (tokens/duration, vidi glavni skill-creator-pro `SKILL.md`), zapisati iz izlaza svakog with_skill run-a:

| Polje | Odakle |
|---|---|
| `validation.passed` | `<slug>-validation-vN.json`, top-level |
| `retry_count` | Konzolni rezime skilla (Faza 8 u SKILL.md) — broj pokušaja gate-a pre uspeha, 0–3 |
| `first_attempt_failures` | Lista G-pravila koja su pala na PRVI poziv `validate_library.py`, pre bilo kog retry-ja — iz transkripta agenta ili konzolnog rezimea |
| `inferred_ratio` | `distribution.actual` ili prebroj `intents[].inferred == true` / `n_intents` |

## Šta to govori

- `retry_count == 0` na svih 5 evala → Faza 3–5 (matrica → SR tekst → EN parovi) su dovoljno precizne, gate je samo mreža za retku grešku.
- `retry_count > 0` na više od jednog eval-a → Faza 4 (ili ranije) sistemski proizvodi nešto što gate hvata tek naknadno — vredi pogledati koja G-pravila se ponavljaju u `first_attempt_failures` pre nego što se skill smatra gotovim.
- `inferred_ratio` visok ali `validation.passed: true` na `thin-site-fallback` evalu — očekivano i ispravno (to je tačno šta taj eval testira). Isti obrazac na `local-service-sr` ili `b2b-saas-mixed-code` evalu (sajt sa stvarnim sadržajem) → Faza 1 (ekstrakcija) ne koristi dostupan sadržaj sa sajta dobro.
