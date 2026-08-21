# Claude API Patterns — Deep Reference

## System Prompt Architecture

### Layered System Prompts

Za kompleksne aplikacije, system prompt ima slojeve:

```
Layer 1: IDENTITY (ko je Claude u ovom kontekstu)
Layer 2: KNOWLEDGE (šta zna — statički sadržaj)
Layer 3: RULES (šta sme/ne sme — behavioral constraints)
Layer 4: TOOLS (definicije alata)
Layer 5: FORMAT (output structure)
Layer 6: EXAMPLES (few-shot demonstrations)
Layer 7: DYNAMIC CONTEXT (per-request info — user history, session data)
```

**Zašto ovaj redosled?**
- Identity i knowledge su najstabilniji → keširaj ih
- Rules pre tools → Claude zna ograničenja pre nego što vidi alate
- Examples na kraju → poslednje pročitano ima largest impact
- Dynamic context poslednji → nikad se ne kešira

### Caching Strategy

```python
import anthropic

client = anthropic.Anthropic()

# Layer 1-6: Stabilan deo — keširaj
STATIC_SYSTEM = """
<role>...</role>
<knowledge>...</knowledge>
<rules>...</rules>
<tools>...</tools>
<format>...</format>
<examples>...</examples>
"""

# Layer 7: Dinamičan deo — ne keširaj
def get_dynamic_context(user_id):
    return f"""
    <session>
      <user_id>{user_id}</user_id>
      <previous_interactions>...</previous_interactions>
      <current_time>2025-02-10T14:30:00Z</current_time>
    </session>
    """

response = client.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": STATIC_SYSTEM,
            "cache_control": {"type": "ephemeral"}
        },
        {
            "type": "text",
            "text": get_dynamic_context("user_123")
        }
    ],
    messages=[{"role": "user", "content": "Pitanje korisnika"}]
)
```

### Token Budgeting

```
Tipičan API poziv budget:
┌────────────────────────────────────┐
│ System prompt:  1,000 - 4,000 tok  │ ← Keširaj (90% ušteda)
│ User context:     200 - 1,000 tok  │
│ User message:     100 - 500 tok    │
│ ─────────────────────────────────  │
│ INPUT TOTAL:    1,300 - 5,500 tok  │
│ ─────────────────────────────────  │
│ Output:           200 - 2,000 tok  │
│ ─────────────────────────────────  │
│ UKUPNO:         1,500 - 7,500 tok  │
└────────────────────────────────────┘

Cena po pozivu (Sonnet):
  Bez cache:  ~$0.008 - $0.04
  Sa cache:   ~$0.002 - $0.02  (60-75% ušteda)
```

---

## Tool Use — Advanced Patterns

### Tool Routing Pattern

Kad imaš 5+ alata, dodaj routing layer:

```xml
<tool_routing>
  Pre nego što pozoveš bilo koji alat, klasifikuj korisnikov zahtev:

  INFORMACIONI (korisnik traži podatak):
  → search_knowledge_base ili get_user_info

  AKCIONI (korisnik traži da se nešto uradi):
  → create_ticket, update_record, send_notification

  DIJAGNOSTIČKI (korisnik prijavljuje problem):
  → check_status, run_diagnostic, search_logs

  Ako zahtev ne pripada nijednoj kategoriji, odgovori bez alata.
</tool_routing>
```

### Error Handling u Tool Use

```xml
<tool_error_handling>
  Ako alat vrati grešku:
  1. NE pokušavaj isti poziv ponovo sa istim parametrima
  2. Ako je 404/Not Found → objasni korisniku da resurs ne postoji
  3. Ako je 500/Server Error → reci "Došlo je do tehničkog problema,
     pokušajte ponovo za par minuta"
  4. Ako je validation error → ispravi parametre i pokušaj ponovo JEDNOM
  5. Ako 2 uzastopna poziva ne uspe → eskalriaj korisniku

  NIKAD ne ulazi u beskonačni loop pokušavanja.
</tool_error_handling>
```

### Parallel Tool Calls

```python
# Claude može da pozove više alata odjednom
# Dodaj u system prompt:
"""
Kad trebaš podatke iz više izvora, pozovi sve relevantne alate
ISTOVREMENO umesto sekvencijalno. Na primer:
- Korisnik pita "Kakvo je stanje mog porudžbe #123 i imam li popust?"
- Pozovi get_order(123) I check_discounts(user_id) paralelno
"""
```

### Structured Output sa Tool Use

```python
# Koristi tool_choice za garantovan strukturiran output
response = client.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    tools=[{
        "name": "classify_intent",
        "description": "Klasifikuj korisnikov intent",
        "input_schema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["question", "complaint", "request", "feedback"]
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"]
                },
                "summary": {
                    "type": "string",
                    "description": "Jednolinijski rezime u max 10 reči"
                }
            },
            "required": ["intent", "urgency", "summary"]
        }
    }],
    tool_choice={"type": "tool", "name": "classify_intent"},
    messages=[{"role": "user", "content": user_message}]
)
# Garantovano vraća strukturiran JSON kroz tool call
```

---

## Streaming Patterns

### Streaming sa Tool Use

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    tools=tools,
    messages=messages
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "tool_use":
                print(f"Pozivam alat: {event.content_block.name}")
        elif event.type == "content_block_delta":
            if hasattr(event.delta, "text"):
                print(event.delta.text, end="")
```

### Conversation History Management

```python
# Efikasno upravljanje istorijom konverzacije
def manage_history(messages, max_tokens=8000):
    """Drži istoriju u budgetu tokena."""
    # Uvek zadrži system prompt (keširan)
    # Uvek zadrži poslednje 2 poruke
    # Sumarizuj starije poruke
    
    if estimate_tokens(messages) > max_tokens:
        # Zadrži prvu (kontekst) i poslednje 2 poruke
        summary = summarize_old_messages(messages[1:-2])
        return [
            messages[0],  # original context
            {"role": "user", "content": f"[Rezime prethodne konverzacije: {summary}]"},
            {"role": "assistant", "content": "Razumem, nastavljamo."},
            *messages[-2:]  # poslednje 2 poruke
        ]
    return messages
```

---

## Production Checklist

```
Pre deploy-a API prompta:

□ System prompt testiran na 20+ različitih inputa
□ Tool definitions imaju description za svako polje
□ Error handling za svaki tool definisan
□ Rate limiting implementiran
□ Caching uključen za system prompt
□ Streaming implementiran za UX
□ Fallback za kad API nije dostupan
□ Logging za debugging (bez PII!)
□ Cost monitoring postavljen
□ Prompt version tracking (git ili database)
```
