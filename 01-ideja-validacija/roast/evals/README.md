# Evals for roast

Prva eval-suita za `roast` (faza 05 sistematskog dodavanja eval pokrivenosti
skillovima, isti obrazac primenjen na 28 drugih skillova kroz 4 prethodne
faze). Prati kontrakt iz `evals.json` formata korišćen u ostatku biblioteke
(vidi npr. `skill-creator-pro/evals/evals.json`): `{"skill_name", "evals":
[{"id", "prompt", "expected_output", "expectations"}]}`.

## `evals.json` — 6 slučajeva

Svaki slučaj je samodovoljan hipotetički scenario koji svež agent može da
reši imajući isključivo tekst `SKILL.md` i sam prompt — bez pominjanja "ovog
razgovora", "juče", putanja na disku ili spoljašnjeg stanja. Svaki je
usidren u eksplicitno, imenovano pravilo ili prag iz `SKILL.md`, citirano u
`expected_output`, a ne u izmišljeno očekivanje.

Pokriveni mehanizmi, po redosledu slučajeva:

1. **Izbor režima (LITE vs FULL) + business weighting.** Jednolinijski,
   nisko-rizičan ulaz mora pokrenuti LITE ("3 most relevant personas + a
   short verdict, skip or compress the steelman"), a ne podrazumevani FULL —
   default-to-FULL pravilo važi samo "when unsure", što ovde nije slučaj.
2. **FULL režim, technical weighting, i pravilo da svih šest persona ipak
   govori.** Suštinski tehnički plan mora pokrenuti FULL; weighting favorizuje
   Operator/Researcher/Architect/Pre-mortem, ali "In FULL mode all six still
   speak, even if briefly" — weighting nije isključivanje. Testira se i hard
   rule o neslaganju i tačan redosled Faze 4.
3. **[fact]/[assumption] labeling + anti-fabrication pravilo.** Kad web
   pretraga nije dostupna, agent ne sme izmišljati veličine tržišta, imena
   konkurenata ili statistiku — mora ih označiti `[assumption]` i navesti šta
   treba proveriti.
4. **"Name a fatal flaw" hard rule + tačan redosled Faze 4 + GO je dozvoljen
   ishod.** Solidna, nisko-rizična ideja testira da li agent ćutke preskače
   obavezu da imenuje fatalnu manu ili eksplicitno argumentuje da je nema, i
   da li veruje da roast mora uvek da završi u NO-GO.
5. **Granica "when this runs".** Zahtev za čistu lekturu već objavljenog
   teksta, bez želje za strateškom kritikom — `SKILL.md` eksplicitno kaže da
   je to pogrešan alat i da agent treba to kratko da kaže umesto da ipak
   roastuje.
6. **Mirror-back + 3-7 skrivenih pretpostavki + disagreement rule na
   očigledno lošoj ideji.** Testira da li agent i dalje razdvaja personas na
   bar jednu tačku neslaganja čak i kad je ideja toliko loša da je lako pasti
   u "šest glasova, jedno mišljenje".

## Kako pokrenuti / tumačiti

Ovaj repozitorijum ne definiše poseban runner za `roast` (za razliku od
`skill-creator-pro`, koji ima `scripts/run_eval.py`). Dok takav runner ne
postoji za ovu skill-biblioteku, svaki slučaj se pokreće ručno:

1. Pokrenuti svež agent (bez istorije razgovora) sa `SKILL.md` sadržajem
   skilla `roast` učitanim i sa `prompt` poljem kao jedinim korisničkim
   unosom.
2. Prikupiti pun izlaz agenta.
3. Proveriti svaku stavku iz `expectations` nezavisno, kao da/ne — svaka
   stavka mora biti proverljiva bez subjektivnog čitanja između redova
   (npr. "svaka kritika je oblika 'X fails if/because Y'" se proverava
   pretragom teksta, ne utiskom).
4. Slučaj prolazi samo ako prođu sve stavke iz `expectations` za taj
   slučaj; `expected_output` je vodič za ocenjivača, ne string za tačno
   poklapanje.

Napomena: personas ostaju fiksne engleske oznake (Skeptic, Customer,
Operator, Researcher, Architect, Pre-mortem) čak i kad je ostatak izlaza na
srpskom, po pravilu iz `SKILL.md` ("Output language... Keep only the
internal persona labels... as fixed English tags"). Provere u
`expectations` koje pominju imena persona treba čitati doslovno, ne u
prevodu.
