# Evals za session-start-hook

Ovo je prvi eval set napravljen za skill `session-start-hook` (faza 03-izrada). Skill
je kratak (~150 linija) i uči agenta da napravi SessionStart hook koji instalira
zavisnosti tako da testovi i linteri rade u Claude Code on the web sesijama. Do sada
ovaj skill nije imao nijedan eval slučaj.

## Šta set testira

Set sadrži 6 slučajeva u `evals.json`, i svaki cilja jedno eksplicitno pravilo iz
SKILL.md, a ne izmišljen scenario:

1. **Async mod nije podrazumevan** — "Don't use async mode in the first iteration.
   Only switch to it if the user asks for it."
2. **Hook je samo za web osim ako je drugačije traženo** — proverava `$CLAUDE_CODE_REMOTE`
   pre instalacije, prema datom primeru koda.
3. **npm install umesto npm ci** — zbog keširanja stanja kontejnera nakon hook-a.
4. **Idempotentnost I neinteraktivnost kao dva nezavisna uslova** — slučaj gde je
   skripta neinteraktivna, ali NIJE idempotentna (dupliranje linija u
   `$CLAUDE_ENV_FILE` pri ponovnom pokretanju), pa agent mora oceniti oba principa
   odvojeno, ne samo jedan.
5. **Validacija je namerno uska, ne puna** — linter se pušta na jednom primer fajlu,
   test na jednom testu, ne na celom projektu/suite-u.
6. **Redosled koraka workflow-a** — validacija (koraci 5-7) mora doći pre commit/push
   koraka (korak 8), čak i kad se čini prirodno da se commit-uje odmah posle
   registracije u `settings.json`.

## Šta set namerno NE testira

Ne testira tačan format/tekst finalne poruke agenta korisniku (checklist sa ✅/‼️
emoji-jima, tačne formulacije o prednostima i manama sync/async režima) — to je stilsko
pitanje, ne pravilo koje se lako pogrešno primeni. Takođe ne testira heuristiku
prepoznavanja dependency manifest fajlova (korak 1 workflow-a, npr. koji fajl "pobeđuje"
kad ih ima više), niti edge case oko spajanja postojećeg `.claude/settings.json` ("If
`.claude/settings.json` exists, merge the hooks configuration") — ovo je legitimno
pravilo iz skilla, ali nije uključeno u prvu verziju seta i kandidat je za dopunu.
Set takođe ne izvršava stvarne bash skripte niti git komande — svaki slučaj je čisto
rezonovanje o pravilima, ne integracioni test.

## Format

Isti format kao `skill-creator-pro/evals/evals.json`: svaki slučaj ima `id`, `prompt`
(samostalan hipotetički scenario, bez reference na razgovor ili konkretne putanje),
`expected_output` (tačan zaključak sa referencom na pravilo iz SKILL.md) i
`expectations` (lista konkretnih, proverljivih tvrdnji za grading).

## Ograničenje i sledeći korak

Ovo su čisto tekstualni reasoning evals — proveravaju da li agent iz teksta SKILL.md
izvuče ispravan zaključak, ne da li generisana skripta zaista radi. Sledeći korak je
pokretanje ovog seta kroz eval harness (npr. onaj koji koristi `skill-creator-pro`) sa
svežim agentom bez pristupa ovom razgovoru, plus eventualno dodavanje slučaja za
`settings.json` merge edge case i seta trigger upita za `description` polje.
