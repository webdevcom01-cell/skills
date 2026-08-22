# Eval set — soma-performance-review

Ovo je prvi eval set za skill `soma-performance-review` (faza 06-rad-odrzavanje). Faza trenutno ima 13 skillova i nijedan nema svoj eval set, tako da ovaj set služi i kao referentni primer za ostalih 12 skillova iz iste faze.

## Šta testira i zašto

Skill `soma-performance-review` je gust, deterministički skill: parsira 4 log fajla, računa desetak metrika, primenjuje trostepenu health-score tabelu i do 10 if-then pravila preporuka. Rizik nije u tome da agent ne razume *šta* treba da uradi — rizik je u tome da pogrešno primeni jedno od eksplicitnih, ali lako-za-preskočiti pravila usred inače ispravnog toka. Zato su svih 6 test slučajeva fokusirana isključivo na te tačke, a ne na opšte razumevanje skilla:

1. **SOMA Health Score — "worst-case" agregacija.** Tri nezavisna uslova (TI halt rate, HW winner rate, CR non-OK flag rate) svaki dobija svoju boju, a finalni rezultat je najgora (najozbiljnija) boja od sve tri — ne prosek, ne glasanje većinom. Test namerno daje 2 "dobra" uslova i 1 kritičan, da proveri da li agent popušta pod pritiskom većine.
2. **Dash (`-`) pravilo.** `-` znači "nema podataka", isključuje se iz agregacija, ali se NE isključuje iz brojača ukupnih run-ova (hw_runs), i ne sme se tretirati kao 0. Test proverava i imenilac za winner rate (ukupno run-ova, ne samo brojčani unosi).
3. **Decimalni skor (17.5) — nevalidan format.** Ovo je posebno pravilo, odvojeno od dash pravila, sa sopstvenim tekstom napomene u izveštaju. Test proverava da agent ne pomeša ova dva različita "isključi iz agregacije" slučaja.
4. **`(partial: X)` aritmetika.** SKILL.md eksplicitno navodi primer gde `(partial: 3)` daje completed=2.5, a ne 3 — lako se pročita kao X direktno.
5. **Uslovljenost Step 3b / R10.** R10 (staleness instinkta) sme da se aktivira samo ako je review period ≥ 30 dana; ako je kraći, Step 3b se u potpunosti preskače i R10 ne može da se aktivira bez obzira na to koliko je instinct zaista zastareo. Test namerno daje "očigledno zastareo" instinct u periodu kraćem od 30 dana, da proveri da li agent poštuje redosled/uslov koraka umesto da sudi po sadržaju.
6. **R5 cross-log strogo poklapanje teksta.** Poklapanje je `.strip().lower()` — bez uklanjanja interpunkcije. Test daje dva hook teksta koja se razlikuju samo po tački na kraju, što čoveku izgleda kao "isti hook", ali po doslovnom pravilu NIJE poklapanje.

## Šta se namerno NE testira

Ne testiraju se: parsiranje formata log linija (field count, skip pravila), workflow redosled 13 koraka u celini, format izveštaja (Report structure), niti obični "srećni put" scenariji gde su svi brojevi čisti. Ovi delovi su važni, ali manje rizični — greška u njima se lako primeti vizuelnom proverom izveštaja. Ovaj set cilja na tiha, teško uočljiva odstupanja u računanju i primeni pravila, gde je pogrešan odgovor "verovatan" na prvi pogled.

## Format

Prati format `skill-creator-pro/evals/evals.json`: `id`, `prompt` (samostalan hipotetički scenario sa svim potrebnim brojevima ugrađenim u tekst), `expected_output` (tačan zaključak + citat/parafraza konkretnog pravila iz SKILL.md), `expectations` (4-6 proverljivih tvrdnji po slučaju). Svaki prompt je rešiv čistim rezonovanjem — bez pristupa Obsidian vault-u, fajlovima ili prethodnom razgovoru.

## Ograničenje i sledeći korak

Set ne uključuje scenario za prag "manje od 3 unosa → INSUFFICIENT DATA, bez izveštaja" niti edge case nevalidnog `platforms_completed` formata — oba su takođe eksplicitno pomenuta u SKILL.md i kandidati su za sledeću iteraciju seta. Takođe nedostaje end-to-end test koji pokriva ceo 13-koračni workflow sa stvarnim (simuliranim) Obsidian pozivima — ovaj set testira samo pravila računanja/odlučivanja, ne i orkestraciju alata.
