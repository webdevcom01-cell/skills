# Eval set — pipeline-input-validator

Ovo je prvi eval set napravljen za skill `pipeline-input-validator` (faza `04-test-qa`). Skill do sada nije imao nikakvu proveru da li zaista primenjuje sopstvene rubrike onako kako SKILL.md tvrdi — ovaj set je prvi korak u tom pravcu, po istom principu koji je već primenjen na `soma-eval-harness`.

## Šta set testira

`pipeline-input-validator` je deterministički scoring sistem: 4 dimenzije (D1 Specificity, D2 Niche, D3 Freshness, D4 Actionability), dva veto uslova (V1, V2), jedno cap pravilo za D3, tabela pragova statusa i jedno override pravilo za injection flag. Upravo to je najlakše pogrešiti — ne "da li skill zna šta je AI trend", nego da li ispravno primenjuje sopstvenu aritmetiku i redosled provera. Šest slučajeva u ovom setu cilja tačno šest eksplicitnih pravila iz SKILL.md:

1. **V1 veto short-circuit** — kad je D1=0, skoring se odmah zaustavlja i D2/D3/D4 se NE računaju (test da agent ne "kompenzuje" vetovan input drugim jakim dimenzijama).
2. **V2 veto uz D1≠0** — razlikovanje FAIL-VETO(D1) od FAIL-VETO(D2) kad je input specifičan, ali off-niche (npr. sportski rezultat sa konkretnim brojevima).
3. **D3 cap pravilo** — `D3_effective = min(D3_raw, 1)` kada je D1=1; test da agent ne koristi sirovi D3_raw direktno u zbiru, što bi dalo pogrešan status (PASS umesto WARN+).
4. **Granica praga statusa** — tačka gde total=4 pripada WARN- (4-5) a ne FAIL (0-3), iako dve od četiri dimenzije iznose 0.
5. **Injection override, ograničen domet** — upgrade na WARN+ važi samo kad je computed status PASS ili WARN-, NE i kad je FAIL (razlika između opisa u Step 1 i preciznijeg pravila u sekciji Score computation, potkrepljenog primerom 5 iz SKILL.md).
6. **D2 URL pravilo — domen, ne sadržaj** — `github.com` je uvek Tier 1 bez obzira na temu repozitorijuma, jer pravilo eksplicitno kaže "regardless of the article topic".

## Šta set NAMERNO ne testira

Ovo je logic-only sloj. Skill u realnoj upotrebi zavisi od žive infrastrukture kojoj ovde nemamo pristup:

- **Step 0 (čitanje config-a)** — skill poziva `obsidian_read_note` na `system/config.md` da izvuče `{primary_niche}`, uključujući fallback logiku ako fajl ne postoji ili polje nedostaje. Pošto nemamo pristup Obsidian vault-u niti tom alatu, u svakom promptu smo `primary_niche` dali kao već poznatu činjenicu ("već pročitan iz config-a") umesto da testiramo sam čin čitanja i fallback grane — to bi zahtevalo pravi ili simulirani fajl-sistem.
- **Batch/multi-input format** — pravilo za više inputa (summary tabela pa detaljan breakdown po `Input #1`, `#2`...) nije pokriveno; svaki eval ovde ima tačno jedan input radi jednoznačnosti.
- **Tačan Markdown output format** (tabele, emoji, redosled sekcija) — evals proveravaju ZAKLJUČAK i PRIMENJENO PRAVILO, ne piksel-tačnu formu izlaza.
- **Regex engine u praksi** — da li stvarna implementacija injection pattern-a hvata varijacije fraza van šest navedenih primera nije testirano; eval 5 koristi tačnu frazu iz SKILL.md primera.

## Format

Isti format kao `skill-creator-pro/evals/evals.json`: svaki slučaj ima `id`, `prompt` (samostalan hipotetički scenario sa svim brojevima/činjenicama potrebnim za jednoznačno rešenje, bez ikakve reference na spoljna stanja), `expected_output` (tačan zaključak i EKSPLICITNO pravilo iz SKILL.md koje ga opravdava) i `expectations` (lista konkretnih, proverljivih tvrdnji koje grader može da označi kao ispunjene/neispunjene nezavisno jednu od druge).

## Ograničenje i sledeći korak

Ovaj set proverava samo da li agent ispravno rezonuje o pravilima kad su mu data kao tekst. Sledeći korak bi bio drugi, "integration" sloj eval-ova koji stvarno poziva `obsidian_read_note` nad test config fajlom (uključujući missing-file i missing-field fallback grane) i proverava tačan Markdown izlaz i batch-format ponašanje — to zahteva pristup živom Obsidian okruženju koji ovde nije dostupan.
