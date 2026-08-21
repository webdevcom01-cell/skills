---
name: obsidian-knowledge-logger
description: Structured knowledge capture into an Obsidian vault via any available Obsidian MCP server or REST API. Saves typed notes (concept, resource, insight, decision, project-log, question) with consistent frontmatter, tags, folder placement, and wikilinks. Use whenever the user wants to save, log, capture, archive, or remember something — phrases like "save this to Obsidian", "log this", "add to my vault", "capture this idea", "note this down", "remember this", or Serbian equivalents "sačuvaj u Obsidian", "zapiši ovo", "dodaj u vault", "zabeleži", "logiraj". ALSO trigger proactively, without waiting to be asked, whenever the user shares a useful resource, makes a clear decision in conversation, or arrives at a real insight worth preserving — offer to save it as a one-line question. Do NOT use for one-off scratch notes the user doesn't want preserved, or when no Obsidian tool (MCP, REST API, or filesystem access to a vault) is available.
---

# Obsidian Knowledge Logger

Capture knowledge into an Obsidian vault as structured, typed notes with consistent frontmatter, sensible folder placement, and bidirectional links where possible.

## Core idea

The vault is a long-lived knowledge base. Every note should be retrievable later by *type*, *topic*, or *date*, and connected to related notes via tags and wikilinks. This skill enforces just enough structure to make that possible without locking the user into a rigid system.

---

## Workflow

0. **On first use in a session, peek at the vault structure.** List the top-level folders (via whatever tool is available). If the user already has folders like `Permanent Notes/` or `2-Areas/Knowledge/`, adapt to them — the suggested folders in this skill are defaults for *empty* vaults, not commandments. Remember the structure for the rest of the session; don't re-check on every note.
1. **Identify the note type** from what the user is saving (see Note Types below)
2. **Confirm with the user** if the type is ambiguous — one short question, max. When asking, narrow to the **2–3 most likely types** based on what context you have (the message itself, recent conversation, the user's project). Listing all six types reads as a menu dump and signals you didn't try to infer. If there's truly zero context (e.g. user just says "save this" with nothing to save), ask for the content first, then propose types.
3. **Propose the filename and folder** (don't write yet)
4. **Write the note** with the right template
5. **Confirm what was saved** and where, in one sentence

**Shortcuts:**
- Skip step 2 when the type is obvious from the content
- Skip step 3 when the user explicitly said "just save it" or "don't ask, just do it" — pick reasonable defaults and proceed
- Skip step 5 in the same case

---

## Note Types

Six types. Each maps to a suggested folder and a frontmatter template. The folders below are defaults for *empty* vaults — if step 0 of the workflow showed an existing structure, use that instead.

| Type | Suggested folder | When to use |
|------|------------------|-------------|
| `concept` | `Concepts/` | Definition of a term, technology, framework, pattern |
| `resource` | `Resources/` | External content (article, video, repo, paper) + your summary |
| `insight` | `Insights/` | Personal realization, lesson learned, "aha" moment |
| `decision` | `Decisions/` | Choice between options, with reasoning preserved |
| `project-log` | `Projects/<project-name>/` | Status update or work log for an ongoing project |
| `question` | `Questions/` | Open question to research later |

If the content doesn't fit cleanly into one type, ask the user. Don't invent a seventh type silently.

---

## Templates

All notes share these frontmatter fields: `type`, `created`, `tags`. Each type adds its own. Use ISO date format (`YYYY-MM-DD`) — replace the `<YYYY-MM-DD>` placeholder in templates with today's actual date, not the literal string.

### concept

```markdown
---
type: concept
created: <YYYY-MM-DD>
tags: [<topic-tag>, <domain-tag>]
aliases: [<alternative-names>]
---

# <Concept name>

## Definition
<One or two sentences, plain language.>

## Why it matters
<Why this concept is useful or important in context.>

## Related
- [[<related-concept-1>]]
- [[<related-concept-2>]]
```

### resource

```markdown
---
type: resource
created: <YYYY-MM-DD>
tags: [<topic-tag>]
source: <url>
author: <author-or-org>
format: <article|video|repo|paper|podcast>
---

# <Resource title>

## Summary
<2-4 sentences capturing the core idea.>

## Key takeaways
- <Point 1>
- <Point 2>
- <Point 3>

## My notes
<Personal commentary, why you saved it, how you might use it.>
```

### insight

```markdown
---
type: insight
created: <YYYY-MM-DD>
tags: [<topic-tag>]
context: <where-this-came-from>
---

# <Insight in one line>

## What I noticed
<Description of the observation.>

## Why it matters
<Implication or application.>

## Related
- [[<related-note>]]
```

### decision

```markdown
---
type: decision
created: <YYYY-MM-DD>
tags: [<topic-tag>]
status: <decided|revisiting>
---

# Decision: <What was decided>

## Context
<Situation forcing the decision.>

## Options considered
- **<Option A>** — <pros/cons>
- **<Option B>** — <pros/cons>

## Choice
<What was chosen.>

## Reasoning
<Why. The honest reason, not the post-hoc justification.>

## Revisit when
<Trigger that should make you reconsider.>
```

### project-log

```markdown
---
type: project-log
created: <YYYY-MM-DD>
tags: [<project-name>]
project: <project-name>
status: <in-progress|blocked|done>
---

# <Project>: <short description of session>

## What I did
<Concrete actions taken.>

## What I learned
<Anything new, surprising, or worth remembering.>

## Next
<What comes next, or what's blocking.>
```

### question

```markdown
---
type: question
created: <YYYY-MM-DD>
tags: [<topic-tag>]
status: open
---

# <The question itself>

## Why I'm asking
<Context — what prompted it.>

## What I've tried / know so far
<Partial answers, dead ends, related reading.>

## Where to look next
<Sources, people to ask, experiments to run.>
```

---

## Filename convention

`<short-kebab-case-title>.md` — no date prefix (frontmatter already has `created`). Keep it under ~50 characters. Examples:

- `mcp-protocol-overview.md` (concept)
- `cyanheads-obsidian-mcp-server.md` (resource)
- `why-flat-folder-structure-fails.md` (insight)
- `use-typescript-for-agent-orchestration.md` (decision)

If a file with that name already exists, don't overwrite silently. Tell the user: *"Već postoji `<name>.md` — da li želiš da apendujem novi sadržaj na postojeću notu, da sačuvam kao `<name>-2.md`, ili da je preimenujem?"* Default action if they don't specify: save as `-2`.

---

## Updating an existing note

When the user says things like *"dopiši ovo u moj note o X"*, *"add this to my X note"*, or *"update the X decision"*, the flow is different from creating a new note.

1. **Find the note first.** Search the vault for the note name or topic. If multiple candidates come back, list 2–3 with their folder paths and ask which one.
2. **Read it before editing.** Never blind-write to an existing note — you might overwrite something the user wrote in a different session. Read, then propose the change.
3. **Choose how to merge:**
   - **Append** — new content goes at the bottom under a new `## Update <YYYY-MM-DD>` section. Default for project-log and insight notes.
   - **Edit in place** — for fixing/expanding a specific section (e.g. updating the `Choice` field of a decision). Show the user the diff in chat before writing.
   - **Convert type** — rare. If user says *"this question got answered, turn it into a concept"*, save a new note with the new type and link back to the original.
4. **Update frontmatter.** Add or update a `modified: <YYYY-MM-DD>` field. Don't change `created` — that's historical.
5. **For decisions specifically:** if the user is changing their mind, don't silently rewrite. Either add a `## Reversal <YYYY-MM-DD>` section explaining the change, or set `status: revisiting` so the original reasoning is preserved.

---

## Tagging guidelines

- Lowercase, kebab-case (`agent-orchestration`, not `AgentOrchestration`)
- 2–5 tags per note; more becomes noise
- In YAML frontmatter, write tags without the `#` prefix: `tags: [ai, agent-orchestration]`. The `#` is Obsidian's inline tag syntax for the note body, not frontmatter — using it in frontmatter creates broken tags.
- Reuse existing tags when possible — if the user has previously used `agent-orchestration`, don't introduce `agentorchestration` or `agent_orchestration`
- One tag should be the broad domain (`ai`, `dev`, `personal`), the rest more specific

---

## Linking

Wikilinks (`[[Note Name]]`) connect notes in the vault. The catch: Claude doesn't know which notes exist unless it checks. Procedure:

1. **If the Obsidian tool supports vault search**, search for plausible link targets before writing. Use real note names that come back from search.
2. **If search isn't available or returns nothing**, don't invent links — invented links create orphaned `[[Made Up Note]]` references that look real but go nowhere, which is worse than no link. Instead, write the link target as plain text and tell the user: "You may want to link this to your *X* note if you have one — I couldn't verify it exists."
3. **Always prefer 1–2 verified links over 4–5 speculative ones.** Quality over quantity.

---

## Choosing the tool at runtime

This skill doesn't hardcode an MCP server. At the moment of writing:

1. Check available tools for anything Obsidian-related (search tool names containing "obsidian", "vault", or "note")
2. If multiple options exist, prefer in this order: dedicated Obsidian MCP server > Local REST API > direct filesystem
3. If nothing is available, tell the user clearly — don't simulate the save

---

## Edge cases

**User pastes a long article and says "save this":** classify as `resource`. Ask for the source URL if it's not in the paste.

**User gives only a URL (no pasted content) and asks to save it:** do not fabricate `Summary` or `Key takeaways` from the URL alone — that produces plausible-sounding notes that may misrepresent the source, which is worse than no note. Options, in order of preference: (1) fetch the page if a web tool is available and read it before writing, (2) ask the user for a one-line summary and 2–3 takeaways, (3) save a stub note with the URL and frontmatter, leaving `Summary` and `Key takeaways` empty with a `TODO` marker. Whichever path you take, tell the user what you did and why.

**User describes a decision they already made:** classify as `decision`. The "Options considered" can be brief if they don't remember alternatives — note that explicitly.

**User says "save this conversation":** ambiguous. Ask whether they want it as an `insight` (key takeaway), `project-log` (work session), or `resource` (full transcript).

**Multiple things worth saving in one message:** offer to create multiple linked notes rather than one giant note. Each note stays focused on one idea.

**User wants a custom type not in the list:** use the closest match and add a custom tag, OR ask if they want to extend the skill. Don't silently invent new types — that breaks the retrieval contract.

---

## What good looks like

A successful save means: a few weeks later, the user can find this note by searching for the type, a tag, or a phrase from the title — and the note is self-contained enough to make sense without the original conversation.
