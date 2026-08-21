# Advanced Techniques — Deep Reference

## Tree of Thoughts (ToT)

### Kada koristiti
- Problem ima više mogućih pristupa
- Treba evaluirati trade-off-ove
- Greška je skupa — treba biti siguran

### Pattern

```xml
<task>
  Reši sledeći problem koristeći Tree of Thoughts pristup:

  {{problem}}

  PROCES:
  1. Generiši 3 različita pristupa rešenju
  2. Za svaki pristup:
     a. Opiši pristup u 2-3 rečenice
     b. Navedi prednosti (2-3)
     c. Navedi mane (2-3)
     d. Oceni verovatnoću uspeha (Low/Medium/High)
  3. Izaberi najbolji pristup i obrazloži zašto
  4. Implementiraj izabrani pristup korak po korak
  5. Na kraju, verifikuj rešenje

  FORMAT:
  ## Pristup 1: [Naziv]
  ...
  ## Pristup 2: [Naziv]
  ...
  ## Pristup 3: [Naziv]
  ...
  ## Evaluacija
  [Tabela poređenja]
  ## Izabrani pristup: [N]
  [Razlog izbora]
  ## Implementacija
  [Korak po korak]
  ## Verifikacija
  [Provera da rešenje radi]
</task>
```

### Primer: Arhitekturalna Odluka

```
Problem: "Biramo između monolita i mikroservisa za e-commerce platformu"

Pristup 1: Monolit
+ Jednostavniji development, lakši debugging, manji ops overhead
- Teže skaliranje, jedan deployment za sve, tight coupling

Pristup 2: Mikroservisi
+ Nezavisno skaliranje, technology diversity, team autonomy
- Complexity overhead, network latency, distributed debugging

Pristup 3: Modularni monolit (hybrid)
+ Monolit simplicty + modular boundaries, lak prelaz na MS
- Zahteva disciplinu, manje poznati pattern

Evaluacija: Za tim od 5 developera sa 3 meseca do launch-a,
Pristup 3 daje najbolji balans. Monolit je prejednostavan za
dugoročni rast, mikroservisi su preoverkill za mali tim.
```

---

## ReAct (Reasoning + Acting)

### Kada koristiti
- Zadatak zahteva korišćenje alata (search, API, database)
- Multi-step istraživanje
- Treba razumeti zašto je Claude pozvao koji alat

### Pattern

```xml
<task>
  Odgovori na pitanje koristeći dostupne alate.

  Za svaki korak:
  1. THOUGHT: Razmisli šta treba da saznaš
  2. ACTION: Pozovi odgovarajući alat
  3. OBSERVATION: Analiziraj rezultat
  4. Ponovi dok nemaš dovoljno informacija
  5. ANSWER: Daj finalni odgovor

  PRAVILA:
  - Max 5 tool poziva po pitanju
  - Ako posle 3 poziva nemaš odgovor, daj best-effort sa napomenom
  - Ne pozivaj isti alat sa istim parametrima dva puta
</task>
```

### Primer u Tool Use

```python
# System prompt koji aktivira ReAct pattern
system = """
Kad odgovaraš na pitanja:
1. Razmisli šta treba da saznaš (ne govori ovo korisniku)
2. Koristi dostupne alate da nađeš informacije
3. Analiziraj rezultate
4. Ako treba više informacija, koristi alat ponovo
5. Kad imaš dovoljno, daj koncizan odgovor sa izvorom

Max 3 tool poziva po pitanju.
Ako nemaš dovoljno informacija, reci šta si našao i šta nedostaje.
"""
```

---

## Self-Consistency

### Kada koristiti
- Tačnost je kritična (medicinski, pravni, finansijski kontekst)
- Prompt daje nedosledne odgovore
- Treba veća pouzdanost

### Pattern

```xml
<task>
  Odgovori na sledeće pitanje 3 PUTA, svaki put nezavisno.
  
  Pitanje: {{question}}
  
  Za svaki pokušaj:
  1. Pristupi problemu iz drugačijeg ugla
  2. Daj odgovor sa obrazloženjem
  
  Na kraju:
  - Uporedi sva 3 odgovora
  - Ako se svi slažu → visoka pouzdanost
  - Ako se 2/3 slažu → srednja pouzdanost, navedi neslaganje
  - Ako se svi razlikuju → niska pouzdanost, navedi sve opcije
  
  FORMAT:
  ## Pokušaj 1: [Pristup]
  Odgovor: ...
  Obrazloženje: ...
  
  ## Pokušaj 2: [Drugi pristup]
  ...
  
  ## Pokušaj 3: [Treći pristup]
  ...
  
  ## Konsenzus
  Pouzdanost: [Visoka/Srednja/Niska]
  Finalni odgovor: ...
</task>
```

### Automatizovana Self-Consistency (API)

```python
import collections

def self_consistent_answer(question, model, n=5):
    """Pokreni prompt N puta i vrati majority answer."""
    answers = []
    for _ in range(n):
        response = client.messages.create(
            model=model,
            temperature=0.7,  # Malo viša za raznolikost
            messages=[{"role": "user", "content": question}]
        )
        answers.append(extract_answer(response))
    
    # Majority voting
    counter = collections.Counter(answers)
    best_answer, count = counter.most_common(1)[0]
    confidence = count / n
    
    return {
        "answer": best_answer,
        "confidence": confidence,
        "all_answers": dict(counter)
    }
```

---

## Chain of Thought (CoT) — Napredne Varijante

### Zero-shot CoT

```
"Razmisli korak po korak pre nego što odgovoriš."
```
Jednostavno ali efektivno za reasoning zadatke.

### Structured CoT

```xml
<instructions>
  Pre davanja odgovora, napravi analizu u sledećem formatu:

  GIVEN: [Šta znamo iz pitanja]
  FIND: [Šta treba da nađemo]
  APPROACH: [Koji pristup ćemo koristiti]
  STEPS:
    1. [Korak 1 sa rezultatom]
    2. [Korak 2 sa rezultatom]
    ...
  ANSWER: [Finalni odgovor]
  CHECK: [Verifikacija da odgovor ima smisla]
</instructions>
```

### CoT sa Extended Thinking

```python
# Umesto da tražiš CoT u outputu (troši output tokene),
# koristi extended thinking (troši thinking tokene — jeftinije)

response = client.messages.create(
    model="claude-sonnet-4-5-20250514",
    thinking={"type": "enabled", "budget_tokens": 5000},
    messages=[{
        "role": "user",
        "content": "Reši ovaj problem: ..."
        # NE treba "think step by step" — thinking mode to radi automatski
    }]
)
```

---

## RAG (Retrieval-Augmented Generation)

### Pattern za Document Q&A

```xml
<system>
  Ti si asistent koji odgovara na pitanja ISKLJUČIVO na osnovu
  datog konteksta.

  PRAVILA:
  1. Koristi SAMO informacije iz <context> tagova
  2. Ako odgovor nije u kontekstu, reci "Ova informacija nije
     dostupna u datom dokumentu"
  3. Citiraj relevantne delove: "Prema dokumentu: '...'"
  4. NE dodaj informacije iz svog znanja
  5. Ako je odgovor delimičan, napomeni šta nedostaje
</system>

<context>
  {{retrieved_documents}}
</context>

<question>
  {{user_question}}
</question>
```

### Chunk Strategy za Dugačke Dokumente

```python
# Pravilo palca za chunk size:
# - Preveliki chunk → Claude se "izgubi" u tekstu
# - Premali chunk → nema dovoljno konteksta

RECOMMENDED_CHUNK_SIZES = {
    "factual_qa": 500,      # Tačni podaci, kraći chunk
    "summarization": 2000,  # Treba širi kontekst
    "analysis": 1000,       # Balans
    "code_review": 1500,    # Treba videti okolni kod
}

# Overlap: 10-20% chunk size
# Primer: 1000 token chunk sa 150 token overlap
```

---

## Reflexion

### Kada koristiti
- Iterativno poboljšavanje outputa
- Kad prvi pokušaj nije dovoljno dobar
- Self-improvement loop

### Pattern

```xml
<task>
  {{original_task}}

  PROCES:
  1. Napravi prvi draft
  2. Kritikuj svoj draft:
     - Šta je dobro?
     - Šta nedostaje?
     - Šta je pogrešno?
  3. Na osnovu kritike, napravi poboljšanu verziju
  4. Ponovi korake 2-3 još jednom

  OUTPUT:
  ## Draft 1
  [Prvi pokušaj]

  ## Self-Critique 1
  [Šta poboljšati]

  ## Draft 2 (Final)
  [Poboljšana verzija]
</task>
```

---

## Kombinovanje Tehnika

```
SCENARIO: Kompleksna analiza za biznis odluku

KOMBINACIJA:
1. ToT → Generiši 3 pristupa analizi
2. CoT → Za izabrani pristup, analiziraj korak po korak
3. Self-Consistency → Proveri zaključke sa 3 nezavisna pokušaja
4. Reflexion → Poboljšaj finalni output na osnovu kritike

Ovo je "heavy-duty" pristup — koristi samo kad je odluka
zaista važna i vredna dodatnih tokena.
```
