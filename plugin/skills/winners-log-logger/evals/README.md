# Eval set: winners-log-logger

## (a) Šta je ovo

Ovo je prvi eval set za skill `winners-log-logger` (faza `06-rad-odrzavanje`), koja trenutno ima 13 skillova i nijedan eval — najveća i strukturno najslabija faza u biblioteci. Set sadrži **6 hipotetičkih, samostalnih scenarija** (`evals.json`, format usklađen sa `skill-creator-pro/evals/evals.json`), od kojih svaki testira jedno eksplicitno pravilo iz `SKILL.md`, bez pristupa spoljnom stanju, fajlovima ili prethodnom razgovoru — svaki prompt agent mora rešiti čisto rezonovanjem iz teksta skilla.

## (b) Šta testira, a šta ne testira, i zašto

Testira se **razumevanje pravila**, ne izvršenje alata — nijedan eval ne pretpostavlja da agent stvarno ima pristup Obsidian vaultu ili `as_chat_with_agent` alatu. Svaki scenario je formulisan tako da agent može da zaključi ispravan odgovor isključivo čitanjem `SKILL.md`: koji korak se primenjuje, koji gate blokira upis, i zašto.

Ne testira se: format finalne linije unosa, tačan tekst poruka na srpskom (SKILL.md daje primere fraza, ne stroge šablone), niti ponašanje opcionog `## Reference` update-a — ovi bi zahtevali izvršno okruženje (stvarni fajl, stvarni tool-pozivi), što nije u domenu čisto tekstualnog rezonovanja.

## (c) Koje pravilo svaki slučaj cilja

1. **Score gate — celobrojnost i minimum** (`score` polje, Korak 1, Edge case "Score 17.5"): decimalna ocena je INVALID, agent ne sme da zaokruži, mora da pita.
2. **Dva apsolutna gate-a spojena sa AND, ne OR** (uvod skilla, Korak 7.5): visok score sam po sebi nije dovoljan — QUARANTINE odluka Memory Integrity Gate-a blokira upis čak i uz score 19/20, fail-closed, bez izuzetka na insistiranje korisnika.
3. **Obavezno paginirano čitanje pre `mode: replace`** (Korak 2, upozorenje o `obsidian_read_note`): najkritičniji edge case u celom skillu — upis na osnovu delimičnog reada trajno briše ostatak fajla jer replace prepisuje ceo body.
4. **Nepoznata platforma → pitaj, ne nagađaj** (`platform` normalizacija + Edge case "Nepoznata platforma"): "Threads" je eksplicitno naveden primer koji ne sme biti automatski mapiran ni na jednu od 5 kanonskih vrednosti.
5. **Zabrana izmišljanja P-kodova** (Anti-hallucination pravilo #3): jedino P1 i P3 su poznati kodovi; sve ostalo mora biti opisni tekst, nikad novi P-kod.
6. **Deduplikacija sa normalizacijom `.trim().toLowerCase()`** (Korak 4): razlike u velikim/malim slovima i razmacima ne smeju sakriti duplikat.

Namerno su izostavljeni "Multiple winners" (Korak 3) i "corrupted file" edge case — vredni budućih evala, ali preskočeni da set ostane fokusiran na 6 najlakše promašivih pravila.

## (d) Format

Standardni format sa poljima `skill_name` i niz `evals`, svaki sa `id`, `prompt` (samostalan scenario), `expected_output` (zaključak + obrazloženje sa referencom na konkretno pravilo/korak iz SKILL.md), i `expectations` (4-5 konkretnih, proverljivih tvrdnji po slučaju).

## (e) Ograničenje i sledeći korak

Ovaj set proverava da li model *zna* pravila kada mu se daju u tekstualnom obliku, bez izvršavanja alata. Sledeći korak: funkcionalni eval sloj koji pokreće skill sa simuliranim `obsidian_read_note`/`obsidian_update_note`/`as_chat_with_agent` odgovorima i proverava da agent zaista poziva alate u ispravnom redosledu (posebno petlju za paginirano čitanje iz slučaja 3), a ne samo da to opisno tvrdi. Vredi dodati i evale za preostala dva edge case-a i za Korak 10 (post-write verifikacija).
