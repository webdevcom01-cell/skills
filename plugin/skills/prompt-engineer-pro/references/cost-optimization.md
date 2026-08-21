# Cost Optimization — Deep Reference

## Model Selection Matrix

```
┌────────────────────────────────────────────────────────────────┐
│                    COST PER 1M TOKENS (USD)                     │
├────────────┬──────────┬───────────┬─────────────────────────────┤
│ Model      │ Input    │ Output    │ Best For                    │
├────────────┼──────────┼───────────┼─────────────────────────────┤
│ Opus 4     │ $15.00   │ $75.00    │ Complex reasoning, planning │
│ Sonnet 4   │ $3.00    │ $15.00    │ Coding, analysis, general   │
│ Haiku 4    │ $0.25    │ $1.25     │ Classification, extraction  │
├────────────┼──────────┼───────────┼─────────────────────────────┤
│ Sa cache   │ -90%     │ (isto)    │ Repetitivni system promptovi│
│ Batch      │ -50%     │ -50%      │ Ne-hitni bulk zadaci        │
└────────────┴──────────┴───────────┴─────────────────────────────┘
```

## Strategija 1: Model Routing

Umesto jednog modela za sve, rutiramo po kompleksnosti:

```python
def select_model(task):
    """Cost-optimalni model routing."""
    
    # Tier 1: Haiku ($0.25/$1.25 per M)
    if task.type in ["classification", "extraction", "routing", "formatting"]:
        return "claude-haiku-4-5-20251001"
    
    # Tier 2: Sonnet ($3/$15 per M)
    if task.type in ["coding", "analysis", "summarization", "general_qa"]:
        return "claude-sonnet-4-5-20250929"
    
    # Tier 3: Opus ($15/$75 per M)
    if task.type in ["complex_reasoning", "planning", "creative_writing", "review"]:
        return "claude-opus-4-6"
    
    # Default: Sonnet (best balance)
    return "claude-sonnet-4-5-20250929"
```

**Ušteda:** 40-60% na mešovitim workloads

## Strategija 2: Prompt Caching

```python
# BEZ cachinga: Plaćaš punu cenu system prompta SVAKI PUT
# Primer: 2000 token system prompt × 1000 poziva = 2M input tokena

# SA cachingom: Plaćaš 10% za keširane tokene
# Isti primer: 2000 × 0.1 × 1000 + 2000 × 1 (prvi poziv) = 202K ekvivalent

# PRAVILA:
# 1. Cache se drži 5 minuta (ephemeral)
# 2. Min 1024 tokena za caching (Haiku), 2048 (Sonnet/Opus)
# 3. Keširaj STABILNE delove (system prompt, primere)
# 4. NE keširaj DINAMIČKE delove (user data, session info)

client.messages.create(
    model="claude-sonnet-4-5-20250929",
    system=[
        {
            "type": "text",
            "text": LONG_SYSTEM_PROMPT,  # 2000+ tokena
            "cache_control": {"type": "ephemeral"}
        },
        {
            "type": "text",
            "text": FEW_SHOT_EXAMPLES,  # 1000+ tokena
            "cache_control": {"type": "ephemeral"}
        },
        {
            "type": "text",
            "text": dynamic_context  # Ovo se NE kešira
        }
    ],
    messages=[...]
)
```

**Ušteda:** 60-90% na input tokenima za repetitivne pozive

## Strategija 3: Batch Processing

```python
# Za zadatke koji ne trebaju realtime odgovor:
# - Analiza dokumenata
# - Klasifikacija velikih datasetova
# - Generisanje sadržaja unapred
# - Evaluacija promptova

batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": f"item-{i}",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": item}]
            }
        }
        for i, item in enumerate(dataset)
    ]
)

# Rezultati za 24h, 50% popusta
results = client.messages.batches.results(batch.id)
```

**Ušteda:** 50% na svim tokenima

## Strategija 4: Token Reduction

### Kraći promptovi, isti kvalitet

```
VERBOSE (85 tokena):
"I would like you to please carefully analyze the following
piece of text and provide me with a detailed summary that
captures all the important points while being concise."

OPTIMIZED (20 tokena):
"Summarize this text. Include all key points. Max 3 paragraphs."

Ušteda: 76%
```

### Structured Output umesto Prose

```
PROSE OUTPUT (~200 tokena):
"The analysis reveals that the product has strong market fit
in the European market, particularly in Germany and France.
The main competitors are Company A and Company B. The estimated
market size is approximately $2.5 billion..."

JSON OUTPUT (~80 tokena):
{"market_fit": "strong", "regions": ["DE", "FR"],
 "competitors": ["Company A", "Company B"],
 "market_size_usd": 2500000000}

Ušteda: 60% na output tokenima
```

### Prefill za Format Control

```python
# Bez prefill: Claude piše preamble → troši tokene
messages = [
    {"role": "user", "content": "Klasifikuj: 'Proizvod ne radi'"},
    {"role": "assistant", "content": '{"category":"'}
]
# Claude nastavlja direktno: technical_issue", "urgency": "high"}
# Ušteda: 20-50 tokena po odgovoru (nema "Sure, I'll classify...")
```

## Strategija 5: Architect + Builder

```
SCENARIO: Razvoj feature-a sa 5 taskova

OPCIJA A: Opus za sve
  Planning:  3K input × $15/M  = $0.045, 1.5K output × $75/M = $0.113
  Task 1-5:  12K input × $15/M = $0.180, 6K output × $75/M   = $0.450
  TOTAL: $0.788

OPCIJA B: Opus plan + Sonnet execute
  Planning:  3K × $15/M = $0.045, 1.5K × $75/M  = $0.113
  Task 1-5:  12K × $3/M = $0.036, 6K × $15/M    = $0.090
  TOTAL: $0.284

OPCIJA C: Opus plan + Haiku execute (simple tasks only)
  Planning:  3K × $15/M  = $0.045, 1.5K × $75/M  = $0.113
  Task 1-5:  12K × $0.25/M = $0.003, 6K × $1.25/M = $0.008
  TOTAL: $0.169

SAVINGS: B = 64% vs A, C = 79% vs A
```

## Monthly Cost Calculator

```
VARIJABLE:
  daily_requests = 100
  avg_input_tokens = 2000
  avg_output_tokens = 500
  working_days = 22

MONTHLY TOKENS:
  input  = 100 × 2000 × 22 = 4.4M
  output = 100 × 500  × 22 = 1.1M

MONTHLY COST BY MODEL:
  Opus:    4.4M × $15/M + 1.1M × $75/M = $148.50
  Sonnet:  4.4M × $3/M  + 1.1M × $15/M = $29.70
  Haiku:   4.4M × $0.25/M + 1.1M × $1.25/M = $2.48

WITH OPTIMIZATIONS (Sonnet + cache + routing):
  Sonnet cached: 4.4M × $0.30/M + 1.1M × $15/M = $17.82
  + 20% Haiku routing for simple tasks: -$3.00
  OPTIMIZED TOTAL: ~$14.82 (50% savings vs base Sonnet)
```

## Decision Framework

```
Pitanje                               → Strategija
─────────────────────────────────────────────────────
Pozivam isti system prompt 100×/dan?  → Caching
Imam bulk zadatak koji nije hitan?    → Batch (50% off)
Koristim Opus za sve?                 → Model routing
Moji odgovori su previše dugački?     → Structured output + prefill
Razvijam feature sa 5+ fajlova?      → Architect+Builder
Sve od navedenog?                     → Kombinuj sve za 70-80% uštede
```
