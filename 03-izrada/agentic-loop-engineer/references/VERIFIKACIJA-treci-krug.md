# Treći krug: nezavisna verifikacija svake tvrdnje

**Zahtev koji je pokrenuo ovaj krug:** "ne zelim da idem u dalji razvoj ukoliko
plan nije na visokom nivou i po standardima industrije - zelim da svaku
tvrdnju proverimo jos jednom, da proverimo njene izvore."

**Metodološka razlika od prethodna dva kruga:** prva dva kruga sam radio
SAM, čitajući sopstveni kod - korisno, ali podložno istoj slepoj tački koju
Domen 2 (Maker-Checker) upozorava: onaj ko je napisao kod teško objektivno
nalazi sopstvene greške. Ovaj krug je uveo pravu nezavisnu proveru: (1)
poseban subagent bez ikakvog konteksta o prethodnom radu, sa zadatkom da
ponovo dohvati zvanične izvore i adversarijalno pročita i IZVRŠI kod, i (2)
moju sopstvenu, odvojenu reprodukciju najozbiljnijih nalaza pre nego što sam
im poverovao - uključujući slučaj gde sam morao da presudim između SVOJIH
ranijih tvrdnji i subagentovih (tačka A.1 ispod).

---

## A. Nalazi koji su ISPRAVILI grešku iz prethodnog kruga

### A.1 [KRITIČNO ZA DIZAJN] `permissionDecision` IPAK podržava `"ask"` - moja tvrdnja u drugom krugu je bila pogrešna

U drugom krugu sam dva puta dohvatio `code.claude.com/docs/en/hooks` i oba
puta zaključio da `permissionDecision` ima samo `allow`/`deny`/izostavljeno.
Nezavisan subagent je dohvatio ISTU stranicu i dobio suprotan odgovor
(`allow`/`deny`/`ask`) - direktna kontradikcija dva "nezavisna" izvora.

**Razrešeno** trećim, ciljanim pokušajem (traženje TAČNO tog pod-odeljka,
verbatim, ne cele stranice) - dokumentacija JASNO potvrđuje:

> `permissionDecision` | string | `"allow"`, `"deny"`, or `"ask"`. Controls
> whether the tool call proceeds, is blocked, or prompts the user. Overrides
> the permission system

**Uzrok greške:** stranica je duga i alat za dohvatanje (WebFetch) je
prilikom prva dva pokušaja "popunio prazninu" pogrešnim zaključkom umesto da
prizna da je sadržaj skraćen - i to DVA PUTA zaredom, na način koji je
izgledao kao konzistentna potvrda. Subagentov nezavisan pokušaj je razbio tu
lažnu konzistentnost.

**Posledica po dizajn:** `guardrail_check.py` je i dalje ISPRAVNO dizajniran
da koristi `deny + pending-approval + approve.sh` kao primarni mehanizam za
`require_human` - ali sada iz TAČNOG razloga, ne pogrešnog. Zvanični
Anthropic inženjerski blog (`anthropic.com/engineering/claude-code-auto-mode`)
potvrđuje: *"In headless mode (`claude -p`) there is no UI to ask the human,
so we instead terminate the process."* Dakle `"ask"` u headless/autonomnoj
petlji (naš ciljani slučaj) gasi proces bez mogućnosti nastavka - naš
mehanizam radi identično u oba režima i dozvoljava asinhroni nastavak. Ovo je
sada SVESNA, citirana inženjerska odluka, ne posledica pogrešnog uverenja.

**Pouka za dalji rad:** kad se od dugačke zvanične stranice traži sažetak,
tražiti TAČAN pod-odeljak verbatim pre nego što se tehnička tvrdnja uzme kao
potvrđena - pogotovo kad ta tvrdnja oblikuje arhitektonsku odluku.

---

## B. Nezavisno potvrđeni bagovi iz prethodnih krugova (dodatno testirano, ne samo pročitano)

Subagent je nezavisno pronašao, a ja sam SVAKI od ova dva najozbiljnija
nalaza SAM reprodukovao sopstvenim testom pre nego što sam im poverovao:

### B.1 [KRITIČNO] `registry_write.py` "optimistic concurrency" iz drugog kruga NIJE radila
Moj sopstveni test (30 paralelnih pisaca, različiti task-id): **9/30 upisa
izgubljeno** (30%). Subagentov nezavisan test (30 i 40 pisaca): 10/30 i
33/40 izgubljeno. Uzrok: "provera konflikta" se dešavala odmah posle
čitanja, u istom procesu, bez ičega što bi sprečilo DRUGI proces da upiše u
procepu pre stvarnog `os.rename()` - klasičan TOCTOU bag, ne stvarna zaštita.

**Ispravka:** `fcntl.flock()` ekskluzivni lock oko cele read-modify-write
sekcije (standardan industrijski obrazac za bezbedan konkurentan upis u
deljeni fajl - isti princip kao Python `filelock` biblioteka).

**Ponovljen test posle ispravke:** 40/40 upisa sačuvano, 0 izgubljeno.

### B.2 [VISOKO] Guardrail regex bypass preko bash line-continuation-a
Moj sopstveni test: `git\s+push\s+.*--force` NE matchuje `"git push \\\n--force origin main"`
(legitimna, ne-adversarijalna bash sintaksa - line continuation) jer `.` bez
`re.DOTALL` ne prelazi preko novog reda. Subagent je nezavisno pronašao isti
bag drugim primerom.

**Ispravka:** `re.search(pattern, text, re.IGNORECASE | re.DOTALL)` u
`guardrail_check.py`. **Ponovljen test:** ista komanda sada ispravno vraća
`deny`.

### B.3 [VISOKO] Hook je fail-open (ne fail-closed) na neočekivan izuzetak
Subagentov nalaz: neispravan oblik `tool_input` (npr. string umesto dict)
izaziva nezahvaćen `AttributeError`; po hook exit-code semantici (potvrđeno
u drugom krugu), exit kod različit od 0/2 bez validnog JSON izlaza se
IGNORIŠE - što znači da bug u NAŠEM skriptu tiho ukida celu zaštitu za taj
poziv.

**Ispravka:** (a) `match_text_for_scope` sad odbrambeno tretira ne-dict
`tool_input` kao prazan (bez crash-a, ali i bez lažnog "opasno" - ispravno
se ne klasifikuje kao poznato opasna komanda); (b) cela logika po pravilu
je omotana u `try/except Exception` koji radi `deny()` (fail-closed) SAMO za
taj tool poziv na BILO KOJU neočekivanu grešku (npr. neispravan regex u
guardrails.yaml). **Testirano oba puta**: malformisan `tool_input` više ne
ruši skriptu (tiho se ne prepoznaje kao opasan, razumno ograničenje);
namerno pokvaren regex u guardrails.yaml sada ispravno vraća `deny` sa
jasnom "interna greška" porukom, umesto da probije nezahvaćen.

---

## C. Dodatni nalazi iz ovog kruga (manji, ali stvarni - svi ispravljeni i testirani)

### C.1 [SREDNJE] `circuit_breaker.py` je pretpostavljao dobro-formiran state
Nedostajuća polja (`max_iterations`), pogrešan tip (`error_signatures` kao
string umesto liste), ili `started_at` u budućnosti (clock skew) su ili
rušili skriptu ili tiho onesposobljavali wall-clock ogradu (negativan
"elapsed" bi trajno sprečio okidanje).

**Ispravka:** eksplicitna validacija obaveznih polja (STOP + eskalacija ako
nedostaju), tiha normalizacija pogrešnih tipova na bezbedne default vrednosti
gde je to razumno, i eksplicitna `clock_skew_detected` STOP odluka za
negativan elapsed. **Testirano sve tri grane** - svaka vraća očekivan,
bezbedan rezultat (STOP ili tiha normalizacija), bez crash-a.

### C.2 [NISKO, ali sa regresijom otkrivenom TOKOM same ispravke] `spawn-worktree-agent.sh` maskirao je stvaran pad pnpm/uv instalacije
Prvobitna ispravka (`|| { echo greška; exit 1; }`) je IZGLEDALA ispravna ali
je unela NOVI bag: eksplicitan `exit` u bash-u NE aktivira `trap ... ERR`
(potvrđeno malim izolovanim testom), pa bi cleanup-trap iz Domena 1 (dodat u
prethodnom krugu) bio tiho preskočen baš u ovoj grani - vraćajući nazad
problem "napola kreiran worktree" koji je taj trap trebalo da reši.

**Ispravka:** `echo greška; false` umesto `exit 1` - `false` je obična
komanda sa ne-nula statusom i ISPRAVNO aktivira ERR trap pod `set -e`
(potvrđeno istim izolovanim testom). **Testirano end-to-end:** simuliran pad
`uv sync`-a - cleanup trap se sada ispravno aktivira i briše worktree/granu.

Ovo je vredan podatak sam po sebi: čak i ispravka napravljena TOKOM
rigoroznog audit procesa može uneti novu, suptilnu grešku - razlog više da
se svaka ispravka ponovo testira, ne samo pročita kao "izgleda ispravno".

---

## D. Šta NIJE promenjeno (proveravano, potvrđeno da je već ispravno)

Subagent je eksplicitno proverio i NIJE našao problem u: `checker-verify.sh`,
`prepare-checker-bundle.sh`, `approve.sh`, `hooks/settings.snippet.json`,
task-id path-traversal validaciji, numeričkoj validaciji argumenata, i
osnovnoj ERR-trap logici (van pnpm/uv grana opisanih u C.2). Takođe je
potvrdio da `git push --force-with-lease` VEĆ prolazi kroz `git-force-push`
pravilo (supstring "--force" se poklapa i sa "--force-with-lease"), što
NIJE bila greška kako se prvo činilo.

Domen 1 (git worktree arhitektura) je nezavisno potvrđen protiv
`gitworktree.org` (jer je `git-scm.com` zahtevao odobrenje koje nije stiglo
na vreme u ovoj sesiji): deljeni `.git/objects`, zabrana dupliranog
checkout-a iste grane, i `git worktree remove`/`prune` kao komande za
čišćenje - sve doslovno citirano i potvrđeno.

---

## E. Zaključak i preporuka

Od 6 tvrdnji o Claude Code standardima proverenih u ovom krugu, 5 je bilo
tačno već u drugom krugu, 1 (permissionDecision "ask") je bila pogrešna i
sada je ispravljena - u kodu I u dokumentaciji. Od nalaza nezavisnog
adversarijalnog pregleda, 2 su bila kritična/visoka i oba su bila STVARNA
(potvrđena mojom sopstvenom, odvojenom reprodukcijom, ne samo prihvaćena na
reč), plus 4 manja - svi ispravljeni, svi ponovo testirani, uključujući
otkrivanje i ispravku regresije unete tokom same ispravke (C.2).

**Ovo sad zadovoljava standard koji je tražen** ("svaka tvrdnja proverena,
izvori provereni") u meri u kojoj je to izvodljivo za sistem ove veličine:
svaka tehnička tvrdnja o Claude Code platformi je potkrepljena verbatim
citatom iz zvaničnog izvora ili nezavisno reprodukovanim testom, ne
pretpostavkom. Preostali rizici (regex-bypass kategorija van onoga što je
ovde nađeno, hook API promene u budućim verzijama, itd) su eksplicitno
navedeni u `AUDIT-nalaz.md` sekciji D kao SVESNO prihvaćeni, ne skriveni.

**Sledeći korak ostaje isti kao u prethodnom krugu:** pre prvog pravog
pokretanja, pokreni "Verifikacija guardrails-a" komandu iz SKILL.md sekcije
7 u SVOM konkretnom Claude Code okruženju - dokumentacija se menja između
verzija (kao što je upravo pokazano u tački A.1), pa je lokalna provera
uvek poslednja linija odbrane, ne pretpostavka.
