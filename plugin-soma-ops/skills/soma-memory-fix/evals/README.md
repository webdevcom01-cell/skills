# Evals za soma-memory-fix

## (a) Zašto je ovo prioritet

Ovo je prvi eval set za bilo koji od 13 skillova u fazi "06-rad-odrzavanje" — do sada
nijedan nije imao svoj eval. `soma-memory-fix` je odabran kao jedan od dva
najprioritetnija (uz `memory-integrity-gate`) jer direktno dodiruje **živu memoriju
agenata u produkciji**: piše u `knowledgeBaseId` polje na kb_search čvorovima
produkcionih agenata (SOMA pipeline i AI Nekretnine CG). Ako skill pogrešno zaključi
kada je bezbedno da patch-uje, prepiše postojeću vezu ili "izmisli" ID koji nije
potvrđen live pozivom, posledica nije kozmetička — agent u produkciji ili ostaje bez
memorije, ili počinje da čita iz pogrešne baze znanja. Cilj ovog seta je da uhvati
tačno te greške pre nego što se skill ikad pusti na stvarne agente.

## (b) Šta testira, šta ne testira, i zašto

Test set namerno **ne** testira formatiranje izveštaja (📋 plan/rezultati blokovi),
task-listu iz STEP 0, niti tačan tekst log poruka — to su kozmetički detalji koji ne
ugrožavaju integritet memorije ako su malo drugačije formulisani. Umesto toga, svih 6
slučajeva cilja isključivo na **odluke koje, ako se pogreše, ili oštete memoriju ili
sakriju stvaran problem**: kada je auto-patch dozvoljen, kada se sme prepisati
postojeća vrednost, kada se sme verovati korisnikovom navodu o ID-ju, i kada uslov za
preskakanje agenta važi iako na prvi pogled ne izgleda tako. Svaki prompt je
samostalan hipotetički scenario — sadrži sve potrebne "izlaze" alata (as_inspect_flow,
as_list_knowledge_bases, as_get_recent_executions) direktno u tekstu, tako da ga
agent bez pristupa razgovoru, fajlovima ili live MCP okruženju može rešiti čisto
rezonovanjem iz pravila u SKILL.md.

## (c) Šta svaki slučaj cilja

1. **No-name-inference / AMBIGUOUS** — testira "CRITICAL: Do NOT attempt to match
   KBs by name similarity... count >= 2 → halt and report — never guess." Scenario
   namerno stavlja KB čiji naziv gotovo identično odgovara imenu agenta, da proveri
   da agent ne popusti pred očiglednim ali zabranjenim prečicama. Greška ovde =
   pogrešna baza tiho povezana sa agentom.
2. **Idempotentnost / zabrana prepisivanja** — testira pravilo da se već WIRED čvor
   nikad ne prepisuje, čak ni na eksplicitan zahtev korisnika da se "ispravi" na
   drugu bazu. Greška ovde = skill postaje alat za nekontrolisano menjanje postojećih
   memorijskih veza, što nije njegova namena i nema post-patch bezbednosne korake za
   taj put.
3. **Incident Guard, OR uslov** — testira da su "status == running" i "started_at u
   poslednjih 60s" nezavisne grane; pogrešno tumačenje kao AND bi dozvolilo
   patch-ovanje agenta koji je upravo završio izvršavanje, sa rizikom od race
   condition-a nad živim stanjem.
4. **VERIFY_MISMATCH posle patch-a** — testira da se neočekivana vrednost posle
   patch-a nikad automatski ne "ispravlja" ponovnim pisanjem, nego ide na ručni
   pregled. Greška ovde = skill bi mogao da nadjača nešto što je u međuvremenu
   promenio drugi proces, dupliranjem problema.
5. **Poreklo ID-ja / zero-hallucination** — testira otpornost na socijalni pritisak
   korisnika da se preskoči live poziv i upotrebi ID "iz sećanja". Ovo je srž
   "zero-hallucination" garancije skilla; greška ovde direktno krši centralni hard
   rule.
6. **do_not_use_when (kreiranje KB-a)** — testira granicu nadležnosti: skill sme
   samo da poveže postojeću bazu, nikad da je kreira. Greška ovde = skill pokušava
   zadatak van svog opsega umesto da preusmeri na agent-scaffolder.

## (d) Format

Fajl prati isti format kao `skill-creator-pro/evals/evals.json`: `skill_name` i niz
`evals`, svaki sa `id`, `prompt` (samostalan scenario), `expected_output` (tačan
zaključak i pravilo iz SKILL.md na koje se oslanja) i `expectations` (5 konkretnih,
proverljivih tvrdnji o odgovoru).

## (e) Ograničenje i sledeći korak

Ovih 6 slučajeva pokriva integritetno-kritične grane eksplicitno navedene u
SKILL.md, ali ne pokriva sve — na primer `NO_KB` (count == 0) granu, `PATCH_FAILED`
grešku alata, ili dry-run/confirm parsiranje fraza ("da"/"ne" varijante) nisu
posebno testirani. Sledeći korak je pokretanje ovog seta kroz eval harness (npr.
`soma-eval-harness`) nad stvarnim odgovorima agenta koji ima učitan `soma-memory-fix`,
i eventualno proširenje seta na `memory-integrity-gate` kao drugi prioritetni skill
iz iste faze, pošto se dva skilla direktno dodiruju (memory-integrity-gate verovatno
proverava upravo ono što ovaj skill menja).
