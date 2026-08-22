# evo-log-writer — eval set

Ovo je prvi eval set za skill `evo-log-writer` (faza `06-rad-odrzavanje`), koja trenutno ima 13 skillova i nijedan evo do sada nije imao svoje evalove. Set sadrži 6 slučajeva u `evals.json`, u istom formatu kao `skill-creator-pro/evals/evals.json` (polja `id`, `prompt`, `expected_output`, `expectations`).

## Šta set testira

Svaki slučaj cilja jedno eksplicitno pravilo, prag ili edge case iz SKILL.md, ne izmišljene situacije:

1. **Confidence — anti-hallucination pravilo #2 + required polje.** Agentu se daju sirovi signali koji na prvi pogled odgovaraju ⭐⭐⭐ formuli, ali confidence je procena SOMA agenta, ne evo-log-writer-a, i to je required polje za Trend Intelligence — pa se ne sme ni izračunati samostalno ni popuniti sa `-`, već se mora pitati korisnik. Ovo je najsuptilnija zamka: tabela zvezdica u SKILL.md izgleda kao formula za primenu, a zapravo je referenca za validaciju već dobijene vrednosti.
2. **Tačan format i sanitizacija polja (Hook Writer).** Testira zamenu `|` → `—`, zamenu newline-a razmakom, zabranu skraćivanja teksta, format `N/20` umesto golog broja, `lowercase` za platformu, i tačan redosled polja.
3. **"Every run gets logged — no exceptions" + halted run edge case.** Trend Intelligence je haltovao (VAGUE_INPUT) — testira da li agent ipak loguje run, ispravno postavlja `hook_writer_triggered: no`, `-` za nullable polje, i ne izmišlja required polja koja realno nedostaju.
4. **Content Repurposer partial completion.** Testira eksplicitno propisan format `linkedin,x (partial: instagram)`, obaveznu vrednost `PARTIAL_OUTPUT` (ne `none`, ne izmišljena zastavica), i redosled svih 7 polja — najbogatiji format u skillu.
5. **Append vs. replace write mode.** Testira da li agent prepoznaje kad NE sme koristiti `section_heading` (kvari strukturu fajla) i da ne meša replace-only first-entry granu sa običnim append-om.
6. **File not found — zabrana kreiranja fajla.** Testira da li agent staje i prijavljuje grešku umesto da kreira nov evo-log.md, što bi pokvarilo SOMA vault strukturu.

## Šta set NE testira i zašto

Set namerno ne testira: čitanje/paginaciju stvarnog Obsidian fajla (Step 2 napomena o `has_more`/`next_line_offset`), scope-boundary rutiranje ka `winners-log-logger` ili `obsidian-knowledge-logger`, i punu pipeline sekvencu za sva 3 agenta. Ovi slučajevi ili zahtevaju simulaciju stvarnog stanja alata (paginacija) što bi kršilo ograničenje samostalnosti, ili testiraju granice IZMEĐU skillova (bolje mesto za integracioni eval kasnije, ne za prvi set jednog skilla).

## Format i ograničenje

Svaki prompt je samostalan hipotetički scenario — ne referencira konkretan razgovor, fajl na disku niti spoljno stanje; agent koji rešava eval treba samo tekst SKILL.md i rezonovanje. `expected_output` uvek referencira tačno pravilo/citat iz SKILL.md, a `expectations` su proverljive, atomske tvrdnje pogodne za automatsku ili ručnu proveru.

**Sledeći korak:** dodati drugi set koji pokriva scope-boundary rutiranje (npr. hook sa skorom ≥17/20 — da li agent zna da to NIJE njegov posao da upiše u winners-log) i paginaciju pri `mode: replace`, ali ti slučajevi zahtevaju ili pristup drugim skillovima ili simulirano tool stanje, pa su van dometa ovog prvog, čisto-rezonovanjem-rešivog seta.
