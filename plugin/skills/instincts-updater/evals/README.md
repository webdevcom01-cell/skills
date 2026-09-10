# Eval set — instincts-updater

Ovo je prvi eval set za skill `instincts-updater` (faza 06-rad-odrzavanje). Skill trenutno nema nijedan eval, uprkos tome što menja ponašanje drugih agenata upisujući "instinkte" u njihove vault fajlove na osnovu istorije iz evo-logova — greška u primeni pravila ovde se ne manifestuje kao pogrešan izlaz jedne konverzacije, već kao trajno, pogrešno naučeno ponašanje drugog agenta. Zato je prioritet ovog seta stavljen na pravila koja sprečavaju preranu ili neosnovanu izmenu instinkta.

## Šta set testira

Šest scenarija, svaki ciljajući jedno eksplicitno pravilo iz `SKILL.md`:

1. **STEP 2a — minimalni prag od 3 unosa.** Testira da li se agent ispod praga preskače PRE bilo kakve analize flagova, čak i kada jedan od dostupnih unosa izgleda kao očigledan kvalitetni problem.
2. **STEP 4a + STEP 4d (hard guard) + anti-hallucination #2 — pojedinačna pojava nikad ne generiše predlog.** Ovo je namerno postavljeno kao "trik" scenario: guard od 0.5 u formuli za confidence lako se pogrešno pročita kao dozvola da se ipak nešto predloži sa nižim skorom. Skill eksplicitno kaže suprotno — guard je samo sigurnosna mreža, ne mehanizam za zaobilaženje pravila "≥2 pojave" iz STEP 4a.
3. **STEP 4d — formula za confidence i clamp (donji prag).** Testira da li se aritmetika formule (`occurrences / (occurrences + clean_after)`) i posledično zaokruživanje/ograničavanje na opseg [0.3, 0.9] primenjuju tačno, uključujući slučaj kada sirova vrednost padne ispod 0.3.
4. **STEP 4b — cross-agent promocija, AND uslov sa dve nezavisne grane.** Testira da li se prepoznaje da su ≥3 agenta I ≥2 pojave po agentu dva odvojena uslova koja MORAJU biti ispunjena zajedno — jedan "skoro pogodak" (2 od 3 agenta kvalifikovana) ne sme aktivirati globalnu promociju.
5. **STEP 3b — P-code underutilization, prag + izuzetak.** Testira dvostruki numerički uslov (<20% I ≥5 run-ova) zajedno sa eksplicitnim izuzetkom da samo prisustvo prateće evidencije u flagu opravdava predlog — inače je ovo samo napomena, ne instinkt.
6. **STEP 4e / edge case — domain: UNKNOWN se nikad ne upisuje u vault.** Testira da li se prepoznaje odsustvo poklapanja ključnih reči, kao i proceduru eksplicitnog ponovnog pitanja korisnika, i ispravan ishod kada korisnik ne odgovori (Skipped, ne tih upis bez taga).

## Šta set NE testira i zašto

Set namerno ne pokriva format detekcije po agentu (STEP 7a/7b/7c, F5/F11), YAML frontmatter bezbednost (STEP 7d/F12), parsiranje višelinijskih unosa (STEP 2b/F4) ili tačan tekst potvrde upisa (STEP 8). Ta pravila su uglavnom mehanička (kopiraj format, ne diraj YAML) i manje su podložna pogrešnom rezonovanju — greška tu je tipično copy-paste previd, a ne pogrešno tumačenje uslova. Prioritet je dat pravilima sa numeričkim pragovima, višegranatim uslovima i eksplicitnim "ne piši dok ne..." ogradama, jer su to mesta gde agent najverovatnije pogrešno rezonuje, a posledica je upisan, pogrešan instinkt u tuđi vault fajl.

## Format

Fajl `evals.json` prati isti format kao `skill-creator-pro/evals/evals.json`: `skill_name`, niz `evals` sa `id`, `prompt` (samostalan hipotetički scenario, bez reference na razgovor ili fajlove van samog prompta), `expected_output` (zaključak + obrazloženje sa pozivom na konkretan korak/pravilo iz SKILL.md) i `expectations` (4 proverljive tvrdnje po slučaju).

## Ograničenje i sledeći korak

Ovo je prvi prolaz i pokriva samo pravila oko odlučivanja kada/da li predložiti instinkt — ne pokriva izvršenje pisanja (STEP 7) niti UI/format prezentacije predloga (STEP 6). Sledeći korak bi bio dopuniti set sa 3-4 slučaja koja pokrivaju STEP 7 (format po agentu, YAML bezbednost) i barem jedan scenario za semantic dedup (STEP 5), pošto to pravilo takođe direktno utiče na to da li se instinkt uopšte piše.
