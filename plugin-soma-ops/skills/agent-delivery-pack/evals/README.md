# Evals za agent-delivery-pack

Ovo je prvi eval set za skill `agent-delivery-pack`. Do sada skill nije imao
nijedan eval — ovih 6 slučajeva je polazna tačka, ne konačan skup.

## Šta set testira, i šta namerno NE testira

Set namerno testira **pravila rezonovanja iz teksta SKILL.md**, ne izvršavanje
skilla protiv žive Agent Studio MCP instance. Svaki prompt je samostalan
hipotetički scenario sa svim brojevima i stanjima potrebnim da se pravilo
primeni — bez referenci na "ovaj razgovor", konkretne fajlove na disku, ili
pristup alatima kao što su `as_chat_with_agent`, `as_get_recent_executions`
ili `scripts/check_pack.py`. Razlog: sam skill zavisi od žive agent instance,
konfiguracije klijenta i fajlova evidencije kojima ova okolina nema pristup —
pa evaluacija ovde ne može (i ne treba da pokušava da) proveri da li skill
STVARNO pokreće agenta ili STVARNO parsira markdown fajlove. Umesto toga,
proverava da li agent koji čita SKILL.md pravilno primenjuje pravila koja
tekst eksplicitno postavlja, uključujući suptilne razlike koje se lako
pomešaju.

Ono što set NE pokriva (i zašto): ne testira pravilan format `record_evidence.py`
poziva (sintaksa `contains:`/`regex:`/`json_has_key:` pravila), ne testira sve
kategorije checkera iz Koraka 5 (npr. VERDICT_MISMATCH, DANGLING, DUPLICATE,
CLAIM nisu pokriveni — svaki bi zaslužio sopstveni scenario, ali 6 slučajeva
je namerno uzak prvi prolaz), i ne testira sadržaj `references/acceptance.md`,
`references/pack-contents.md` ili `references/maintenance.md` jer ti fajlovi
nisu bili dostupni/uključeni u ovaj pregled — samo SKILL.md.

## Šta svaki slučaj cilja

1. **Zabranjene tvrdnje nadjačavaju citiran dokaz.** Drugo od "dva pravila
   koja upravljaju svime": legal/compliance/security/outcome tvrdnje su
   zabranjene bezuslovno — "a tag does not buy them" — čak i uz validan
   `[EV:...]` citat.
2. **Korak 0, drugo pitanje nije opciono.** Ako agent piše bilo gde (šalje
   poruke, menja KB, troši novac), mora se pitati korisnik pre pokretanja; ako
   je odgovor ne, mora se stati — "a delivery pack without runs is not a
   delivery pack."
3. **Dva nezavisna uslova u Koraku 2.** Opseg 4-7 ukupnih slučajeva i "najmanje
   dva moraju biti refusal (block)" slučajevi su odvojeni uslovi — zadovoljenje
   jednog ne kompenzuje kršenje drugog.
4. **Pinovan exec-id ne znači potvrđen zapis.** "`--exec-id` chooses which
   execution is written down. It does not prove which one ran." — kad se dva
   izvršenja poklapaju, record ostaje `ambiguous` i uz pinovanje.
5. **Tačan format INTERNAL markera.** Marker mora biti sam na svojoj liniji u
   prvih 400 karaktera; "INTERNAL REF: ..." je referenca, ne marker, i ne
   isključuje gate.
6. **PLACEHOLDER je AND uslov sa pragom od 1000 karaktera.** `[TO AGREE]` bez
   DRAFT markera UNUTAR prvih 1000 karaktera i dalje puca, čak i ako DRAFT
   postoji kasnije u fajlu.

## Format

Isti format kao `skill-creator-pro/evals/evals.json`: `skill_name`, i niz
`evals` gde svaki element ima `id`, `prompt` (samostalan scenario), `expected_output`
(tačan zaključak i pravilo iz SKILL.md koje ga opravdava) i `expectations`
(lista konkretnih, proverljivih tvrdnji o tome šta agentov odgovor mora i ne
sme da sadrži — pogodno za automatsku ili ručnu proveru odgovora).

## Ograničenje i sledeći korak

Ovaj set proverava rezonovanje o pravilima, ne ponašanje samog skilla u
produkciji (nema pokretanja `check_pack.py`, `record_evidence.py` ili prave
Agent Studio MCP sesije). Sledeći korak je end-to-end prolaz: napraviti
fiktivnog test-agenta u Agent Studio-u, stvarno provesti Korake 0-6, i
proveriti da li `check_pack.py` zaista prijavljuje kategorije (VERDICT_MISMATCH,
DANGLING, DUPLICATE, CONFIG_CLAIM, FIGURE_OUTSIDE, itd.) koje ovaj set ne
dotiče — to zahteva pristup živoj MCP instanci koji ova okolina trenutno nema.
