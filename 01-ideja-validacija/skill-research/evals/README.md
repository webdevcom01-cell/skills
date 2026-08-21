# Evals for skill-research

Prvi eval set za ovaj skill. Deo pete faze sistematskog dodavanja eval pokrivenosti
biblioteci skillova (faza `01-ideja-validacija`), po istom obrascu koji je već primenjen
na 28 skillova kroz četiri prethodne faze.

## Šta ovaj set testira, i šta namerno ne testira

`skill-research` u produkciji zavisi od žive pretrage weba (`WebSearch`/`WebFetch`) —
nijedan od ta dva alata nije dostupan iz ove sesije, pa set ne pokreće stvarno
istraživanje end-to-end i ne proverava kvalitet pretraga ili tačnost pronađenih izvora.

Umesto toga testira sloj koji je nezavisan od žive pretrage a podjednako kritičan: da li
agent, kad mu se da konkretan hipotetički scenario (rezultati pretrage već opisani kao
činjenice u promptu), ispravno primenjuje sopstvena pravila za verdikte iz SKILL.md.
Sekcija "Verdicts" je najgušći i najlakše-pogrešiv deo skilla, pa joj je posvećena većina
seta. Svih 6 slučajeva cilja eksplicitno pravilo iz SKILL.md:

1. **Tool-access gate na samom početku** — ako ni `WebSearch` ni `WebFetch` nisu
   dostupni, agent mora to reći korisniku direktno i STATI, ne odgovoriti iz memorije
   trening podataka predstavljajući to kao istraženo.
2. **REFUTED zahteva pozitivan dokaz, ne samo neuspelu pretragu** — "pretražio sam
   temeljno i nisam ništa našao" je UNCONFIRMED, ne REFUTED, bez obzira koliko tvrdnja
   deluje sumnjivo. REFUTED zahteva da se imenuje konkretan artefakt ili izjava koja
   tvrdnju direktno demantuje.
3. **MISLEADING vs. REFUTED vs. UNCONFIRMED — pravilo "dokazane veze"** — MISLEADING
   znači da je osnovna stvar stvarna ali je bitna činjenica pogrešna, ALI to zahteva
   dokazanu vezu (deljena formulacija, citatni trag, poklapanje datuma, neko ko
   imenuje vezu). Pronalazak nečeg stvarnog na istu temu nije ta veza — bez nje je
   verdikt UNCONFIRMED, a stvarna stvar se prijavljuje kao odvojen kontekst.
4. **"Verdict the propositions, not the sentence"** — višedelna tvrdnja (osoba +
   poslodavac + skorašnjost + format/dužina + suština) ima nezavisno proverljive
   elemente; svaki dobija svoj verdikt, a ukupan verdikt prati suštinsku tvrdnju i mora
   ostati vidljivo odvojen od verdikta pojedinačnih elemenata.
5. **Lista slabosti "odsustva dokaza"** — mrtav link nije dokaz nepostojanja artefakta
   (prvo probati arhivirani snapshot), a region-specifičan/ne-engleski izvor zahteva
   pretragu na tom jeziku i lokalnim domenima pre bilo kakvog zaključka.
6. **"Never assign REFUTED" unutar korisnikovog sopstvenog sveta + struktura izveštaja**
   — tvrdnja o korisnikovoj sopstvenoj firmi/klijentu/porodici nikad ne sme dobiti
   REFUTED; a UNCONFIRMED tvrdnja ide u odeljak "Claims checked" sa svojim verdiktom,
   ne (dodatno) u "What could not be confirmed", koji je rezervisan za praznine koje
   nikad nisu formulisane kao konkretna tvrdnja, plus greške pristupa.

## Format

Isti format kao `skill-creator-pro/evals/evals.json`: svaki slučaj ima `id`, `prompt`
(samostalan hipotetički scenario sa svim činjenicama/rezultatima pretrage potrebnim za
jednoznačno rešenje — bez reference na "ovaj razgovor", vreme poput "juče", putanje na
disku ili bilo kakvo spoljno stanje, tako da ga svež agent može rešiti isključivo na
osnovu SKILL.md teksta i samog prompta), `expected_output` (tačan zaključak/verdikt i
zašto, sa doslovnim ili parafraziranim citatom konkretnog pravila iz SKILL.md koje ga
opravdava) i `expectations` (3-5 konkretnih, nezavisno proverljivih tvrdnji o tome šta
agent mora — ili ne sme — da kaže; ne opšti utisci).

## Kako pokrenuti i tumačiti

Ovo je "logic-only" sloj bez izvršnog harnessa u ovom repou — svaki slučaj se pokreće
tako što se agentu (bez pristupa ovom razgovoru) da tačno `prompt` polje kao jedini
unos, uz SKILL.md kao dostupni skill. Odgovor se zatim ručno ili programski proverava
protiv svake stavke u `expectations`: svaka stavka je da/ne provera, ne opisna ocena.
Slučaj prolazi samo ako su ispunjene sve njegove stavke — delimično tačan verdikt
(npr. ispravan zaključak UNCONFIRMED ali sa REFUTED-tipom obrazloženja, ili ispravan
verdikt ali smešten u pogrešan odeljak izveštaja) treba brojati kao promašaj tog
slučaja, ne kao delimičan uspeh, jer upravo ta razlika (verdikt naspram obrazloženja i
mesta u izveštaju) je ono što set testira.

## Ograničenje / sledeći korak

Ovaj set proverava samo da li agent ispravno rezonuje o pravilima za verdikte kad su mu
rezultati pretrage već dati kao gotove činjenice u promptu — ne testira samu veštinu
pretrage (formulisanje upita iz više uglova, prepoznavanje da je tvrdnja "cirkulišuća"
i zahteva `claim-forensics.md`, čitanje izvora dovoljno pažljivo da se tačno predstave)
niti izlazni format izveštaja u celini (Executive summary, Key findings, Sources kao
markdown linkovi). Kad bude dostupan pristup `WebSearch`/`WebFetch` iz test okruženja,
set treba proširiti drugim slojem koji pokreće stvarno istraživanje nad poznatim,
unapred verifikovanim tvrdnjama (mešavina istinitih, lažnih i MISLEADING primera) i
proverava da li agent sam, bez pomoći datih "činjenica" u promptu, stigne do istog
verdikta i strukture.
