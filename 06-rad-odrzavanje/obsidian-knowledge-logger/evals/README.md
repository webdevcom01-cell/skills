# Evals for obsidian-knowledge-logger

Prvi eval set za ovaj skill otkad je uveden u biblioteku. Faza 06 (Rad i održavanje) je
najveća faza u celoj biblioteci (13 od 53 skilla) i strukturno najslabija — do sada nijedan
od njenih 13 skillova nije imao sopstveni `evals/` folder. Ovaj set je prvi korak u
popunjavanju te praznine, počevši od `obsidian-knowledge-logger`.

## Šta ovaj set testira, i šta namerno ne testira

`obsidian-knowledge-logger` nema izvršni kod (nema `scripts/`) — sav njegov "logic" živi u
proznom tekstu SKILL.md: radni tok od 5 koraka sa uslovnim preskakanjima, šest tipova nota sa
šablonima, konvencija imenovanja fajlova, pravila tagovanja, procedura za ažuriranje
postojećih nota, i posebna sekcija "Edge cases". Ovaj set testira isključivo taj sloj —
da li agent, kad dobije konkretan hipotetički scenario sa svim potrebnim detaljima već datim
u tekstu, ispravno primenjuje pravila skilla čistim rezonovanjem, bez pristupa pravom
Obsidian vault-u, pravom MCP serveru ili istoriji razgovora.

Namerno se NE testira: stvarno izvršavanje tool-poziva prema pravom Obsidian MCP serveru ili
REST API-ju, tačan format frontmatter-a koji bi validator parsirao (npr. da li je YAML
sintaksno ispravan), ponašanje pri stvarnoj pretrazi vaulta za wikilink kandidate (sekcija
"Linking"), niti scenario sa više nota koje treba sačuvati odjednom (sekcija "Multiple things
worth saving"). Sve to zahteva stvaran vault i stvaran MCP alat — ovde nije dostupno, pa bi
test morao da simulira tool-output umesto da proveri stvarno ponašanje.

Svih 6 slučajeva cilja pravilo koje SKILL.md eksplicitno navodi, ne izmišljenu situaciju:

1. **Redosled prioriteta alata** (sekcija "Choosing the tool at runtime"): kad je dostupno
   više načina pisanja u vault, mora se poštovati rang dedicated MCP server > Local REST API
   > direct filesystem — lako se pogrešno posegne za "jednostavnijim" filesystem pristupom
   samo zato što je pri ruci.
2. **Default akcija pri konfliktu imena fajla** (sekcija "Filename convention"): kad korisnik
   ne precizira izbor nakon što je obavešten o postojećem fajlu istog imena, podrazumevana
   akcija je eksplicitno propisana (`-2` varijanta) — a tiho prepisivanje je izričito
   zabranjeno u svakom slučaju.
3. **Tagging guidelines, tri pravila u jednom scenariju**: numerički prag od 2-5 tagova po
   noti, zabrana `#` prefiksa u YAML frontmatter-u (razlika između frontmatter i inline
   sintakse), i obaveza ponovne upotrebe postojećeg oblika taga umesto uvođenja varijante
   pravopisa — sve tri se lako preskoče pojedinačno, pa su namerno spojene u jedan zahtevan
   slučaj.
4. **Zabrana fabrikacije iz eksplicitne sekcije "Edge cases"**: kad korisnik da samo URL bez
   sadržaja i fetch alat nije dostupan, agent ne sme da "pogodi" Summary/Key takeaways —
   mora birati između ostala dva ponuđena puta (pitati korisnika, ili stub nota sa TODO) i to
   objasniti korisniku.
5. **Procedura za reversal odluke** (sekcija "Updating an existing note", tačka 5): kad
   korisnik menja mišljenje o već sačuvanoj odluci, tiho prepisivanje Choice/Reasoning je
   zabranjeno — mora se pronaći, pročitati, pa dodati Reversal sekcija ili `status:
   revisiting`, uz očuvano originalno obrazloženje i netaknuto `created` polje.
6. **Dva nezavisna uslova za preskakanje koraka** (radni tok, sekcija "Shortcuts"): uslov za
   preskakanje koraka 2 (tip note očigledan iz sadržaja) i uslov za preskakanje koraka 3 i 5
   (eksplicitna korisnikova fraza "samo sačuvaj"/"ne pitaj") su potpuno nezavisni — ispunjenje
   jednog ne povlači ispunjenje drugog, a upravo ta nezavisnost je najlakše mesto za grešku.

## Format

`evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `id`, `prompt`
(samostalan hipotetički scenario sa svim potrebnim detaljima već datim u tekstu, rešiv
čistim rezonovanjem bez pristupa razgovoru, fajlovima ili spoljnom stanju), `expected_output`
(tačan zaključak i konkretno pravilo/sekcija iz SKILL.md na koje se oslanja), i
`expectations` (konkretne, proverljive tvrdnje koje grejder može da potvrdi ili ospori, ne
opšti utisci o kvalitetu odgovora).

## Ograničenje i sledeći korak

Ovo je "logic-only" sloj — proverava da li agent razume i ispravno primenjuje pravila iz
proznog teksta, ne da li stvarno ume da pozove Obsidian MCP server, upiše validan fajl u
pravi vault, ili pronađe stvarne kandidate za wikilink pretragom. Kad bude dostupan sandbox
Obsidian vault (ili mock MCP server), ovaj set treba proširiti pravim end-to-end run-ovima
koji pokrivaju "Linking" proceduru, scenario sa više povezanih nota u jednoj poruci, i korak 0
(peek at vault structure) na stvarnoj, unapred pripremljenoj strukturi foldera. Ovih 6
slučajeva je jeftina početna provera razumevanja pravila, ne zamena za pravi eval skilla u
radu.
