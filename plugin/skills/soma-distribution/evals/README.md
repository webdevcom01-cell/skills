# Evals za soma-distribution

Ovo je prvi eval set za skill `soma-distribution` (faza 05-isporuka). Skill do sada
nije imao nijedan eval — ovih 6 slučajeva su polazna osnova, ne konačna pokrivenost.

## Šta set testira

`soma-distribution` je najkraći skill u ovoj fazi (samo SKILL.md, ~130 linija), pa
je set fokusiran isključivo na pravila koja SKILL.md eksplicitno navodi u sekciji
"Hard rules", u opisu Step-ova i u `do_not_use_when`. Svaki od 6 slučajeva cilja
tačno jedno pravilo:

1. **Hard rule 1** — odobrenje je obavezno, nikad podrazumevano; "objavi postove"
   ne znači automatsko "odobri sve".
2. **Hard rule 2 + Step 2** — nikad ne skraćuj copy; X hook limit ≤280 karaktera
   (Hook Writer KB) mora biti flagovan, ne tiho ispravljen, čak i uz unapred dato
   "odobravam".
3. **Hard rule 3** — verifikuj kanal pre tvrdnje da je objavljeno; prazan/nejasan
   odgovor alata nije potvrda uspeha.
4. **Step 5** — ne pretvaraj se da kanal postoji; bez povezanog MCP-a bundle je
   deliverable, ne izmišljen routing.
5. **`do_not_use_when`** — skill ne dira copy; zahtev da se hook "prepravi" ide na
   soma-run/CR, ne izvršava se ovde.
6. **Step 2, platform-specifični pragovi** — YouTube ≤150 karaktera vs TikTok ≤12
   reči; testira da se ova dva ne pomešaju (155 karaktera krši, 11 reči ne krši).

## Šta set namerno NE testira

Ne testira Step 1 (parsiranje CR outputa), Step 4 (format bloka/manifest.json
šeme), Step 6 (Obsidian logging) ni Step 0 (task list). Ne testira pravilo
"suggested_time nikad kao fiksan timestamp" — izostavljeno jer bi zahtevalo
izmišljen trend/cadence kontekst van onoga što SKILL.md daje. Nije procena
kvaliteta samih postova (to radi soma-score-analyzer) niti test KB sadržaja
(`format-templates.md`, Hook Writer agent-card) — pragovi u slučajevima 2 i 6
preuzeti su doslovno iz teksta SKILL.md, ne iz KB-a.

## Format

Isti format kao `skill-creator-pro/evals/evals.json`: svaki slučaj ima `prompt`
(samostalan hipotetički scenario), `expected_output` (tačan zaključak + referenca
na konkretno pravilo iz SKILL.md) i `expectations` (proverljive tvrdnje za ocenu).

## Ograničenje i sledeći korak

Skill u produkciji zavisi od živog stanja (KB pretraga, connector registry,
Obsidian, eventualni social MCP) kome ovaj set nema pristup — zato je svaki prompt
samodovoljan scenario sa svim brojevima i stanjem unetim u tekst, rešiv čistim
rezonovanjem iz SKILL.md, bez pristupa razgovoru, fajlovima ili spoljnim alatima.
Sledeći korak: pokrenuti set kroz soma-eval-harness i po potrebi dodati slučajeve
za Step 4/6 format i suggested-timing pravilo kada se odredi kako ih samostalno
hipotetizovati bez oslanjanja na spoljni KB sadržaj.
