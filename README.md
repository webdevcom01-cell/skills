# skills

Biblioteka profesionalnih skillova organizovana po fazama razvoja: **ideja -> projekat -> gotovo resenje**. Fokus je na AI-agent/SOMA pipeline projektima (dogovoreni obim), sa jasnim handoff-om izmedju faza.

> Ovo je snapshot skillova iz Claude naloga (webdevcom01@gmail.com), organizovan radi verzionisanja i pregleda. Izvor istine za AKTIVNO koriscenje ostaje Claude nalog - kad se skill izmeni tamo (npr. preko skill-creator-pro), ovaj repo treba rucno osveziti (re-export + commit) da ne zastari.

## Mapa pipeline-a

### 01-ideja-validacija/ -- Ideja / validacija

Pre nego sto se posveti vreme i novac gradnji - istrazi, izbusi i validiraj ideju.

| Skill | Sta radi |
|---|---|
| [`brainstorming-buddy`](01-ideja-validacija/brainstorming-buddy/SKILL.md) | Interactive brainstorming companion for exploring ideas, projects, and solutions |
| [`roast`](01-ideja-validacija/roast/SKILL.md) | Adversarial "council of personas" that stress-tests an idea, plan, business concept, strategy, or technical/architecture proposal to find... |
| [`market-research-navigator`](01-ideja-validacija/market-research-navigator/SKILL.md) | Guided market research assistant that provides structure, frameworks, and helps find data for any business research |
| [`deep-research`](01-ideja-validacija/deep-research/SKILL.md) | Conducts systematic, multi-step web research on a target topic, filters for high-quality primary and authoritative secondary sources, syn... |
| [`skill-research`](01-ideja-validacija/skill-research/SKILL.md) | Research or verify anything about the real world — from a quick "is this true?" check to a full sourced report |

### 02-dizajn/ -- Dizajn / arhitektura

Pretvori validiranu ideju u konkretnu arhitekturu i spec pre nego sto se pise prvi red koda.

| Skill | Sta radi |
|---|---|
| [`agent-architect`](02-dizajn/agent-architect/SKILL.md) | Savetnik za dizajn i audit AI agenata, baziran na Anthropic engineering principima i SOMA pipeline arhitekturi |
| [`system-teardown`](02-dizajn/system-teardown/SKILL.md) | Reconstruct how an existing system works when documentation is missing, then produce an as-built spec or a rebuild plan |
| [`prompt-engineer-pro`](02-dizajn/prompt-engineer-pro/SKILL.md) | Write, audit and shrink production prompts for Claude — API system prompts, tool descriptions, CLAUDE.md files, and agent prompts |

### 03-izrada/ -- Izrada

Skafolduju i grade novi agent, skill, MCP server ili menjaju bezbednosni sloj baze.

| Skill | Sta radi |
|---|---|
| [`agent-scaffolder`](03-izrada/agent-scaffolder/SKILL.md) | Fully scaffolds a new AgentStack agent from spec to live deployment using SOMA-standard architecture |
| [`safe-agent-builder`](03-izrada/safe-agent-builder/SKILL.md) | Scaffolds a NEW AgentStack agent with a DETERMINISTIC quality gate and anti-hallucination input-guard baked in by default — not the promp... |
| [`mcp-builder`](03-izrada/mcp-builder/SKILL.md) | Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-des... |
| [`skill-creator-pro`](03-izrada/skill-creator-pro/SKILL.md) | Create new skills, modify and improve existing skills, and measure skill performance |
| [`rls-rollout`](03-izrada/rls-rollout/SKILL.md) | Audits, plans, and orchestrates a phased Postgres Row-Level Security (RLS) rollout for the agent-studio multi-tenant database (61 Prisma ... |
| [`session-start-hook`](03-izrada/session-start-hook/SKILL.md) | Creating and developing startup hooks for Claude Code on the web |

### 04-test-qa/ -- Testiranje / QA

Pre-flight provere, health checkovi, eval harness i debug kad nesto ne radi kako treba.

| Skill | Sta radi |
|---|---|
| [`pipeline-input-validator`](04-test-qa/pipeline-input-validator/SKILL.md) | Pre-flight validator for SOMA pipeline inputs |
| [`soma-model-preflight`](04-test-qa/soma-model-preflight/SKILL.md) | Pre-run guard for AgentStack model/API-key mismatches |
| [`agent-health-check`](04-test-qa/agent-health-check/SKILL.md) | Runs a structured health check across the Agent Studio AgentStack system and produces a scored report with prioritized fixes |
| [`soma-eval-harness`](04-test-qa/soma-eval-harness/SKILL.md) | Evaluates SOMA pipeline reliability (TI → HW → CR) by re-running real logged trends k times, grading each trial with structural + quality... |
| [`enterprise-agent-readiness`](04-test-qa/enterprise-agent-readiness/SKILL.md) | Audits an Agent Studio / AgentStack agent against an enterprise readiness bar (8 dimensions A–H, mapped to OWASP Agentic Top 10 2026, Ant... |
| [`pipeline-debug`](04-test-qa/pipeline-debug/SKILL.md) | Reactive diagnostic skill for the SOMA pipeline (TI → HW → CR → Score Analyzer) |
| [`soma-agent-debugger`](04-test-qa/soma-agent-debugger/SKILL.md) | Specijalizovan skill za debug, fix i deploy production AgentStack agenata (SOMA pipeline) |

### 05-isporuka/ -- Isporuka klijentu

Od gotovog agenta do dokumentacije, prijemnog testa i programa za klijentski tim.

| Skill | Sta radi |
|---|---|
| [`agent-delivery-pack`](05-isporuka/agent-delivery-pack/SKILL.md) | Turns an agent you have already built into something a client can accept, own and be handed — five client-facing documents plus the recei... |
| [`soma-distribution`](05-isporuka/soma-distribution/SKILL.md) | Takes SOMA Content Repurposer output (5 platform posts marked READY_FOR_REVIEW) through a human approval gate and turns approved posts in... |
| [`prospect-discovery`](05-isporuka/prospect-discovery/SKILL.md) | Researches a company from a URL or name and produces a consultant-ready discovery pack — a sourced dossier where every claim carries a ci... |
| [`team-enablement-program`](05-isporuka/team-enablement-program/SKILL.md) | Builds a client-ready 14-week AI enablement program (Week 0 baseline, 12 training weeks, Week 13 handoff) tailored to a company's real to... |

### 06-rad-odrzavanje/ -- Rad i odrzavanje

Pokretanje, monitoring, ucenje iz logova i ciscenje nakon lansiranja.

| Skill | Sta radi |
|---|---|
| [`soma-run`](06-rad-odrzavanje/soma-run/SKILL.md) | End-to-end SOMA pipeline runner: validates input, runs Trend Intelligence, captures the output, writes evo-logs to Obsidian, and logs win... |
| [`soma-performance-review`](06-rad-odrzavanje/soma-performance-review/SKILL.md) | Generates a SOMA pipeline performance report by reading all 4 agent logs from the Obsidian vault (TI evo-log, HW evo-log, CR evo-log, win... |
| [`instincts-updater`](06-rad-odrzavanje/instincts-updater/SKILL.md) | Extracts patterns from SOMA agent evo-logs, proposes new instincts, and — after human approval — appends them to the correct instincts.md... |
| [`agent-dependency-mapper`](06-rad-odrzavanje/agent-dependency-mapper/SKILL.md) | Maps agent-to-agent call dependencies in an AgentStack / Agent Studio system and derives blast radius, single points of failure (SPOF), o... |
| [`soma-agent-cleanup`](06-rad-odrzavanje/soma-agent-cleanup/SKILL.md) | Finds and safely removes duplicate or abandoned AgentStack agents |
| [`memory-integrity-gate`](06-rad-odrzavanje/memory-integrity-gate/SKILL.md) | Adds a DETERMINISTIC, fail-closed Memory Integrity Gate to any agent or loop that promotes its own outputs into LEARNED MEMORY (winners-l... |
| [`kb-sync`](06-rad-odrzavanje/kb-sync/SKILL.md) | Syncs Obsidian vault files into Agent Studio knowledge bases using True-Sync (ADD new, wait READY, DELETE old) |
| [`soma-score-analyzer`](06-rad-odrzavanje/soma-score-analyzer/SKILL.md) | Restores the missing 4th stage of the SOMA pipeline (TI → HW → CR → Score Analyzer) |
| [`soma-memory-fix`](06-rad-odrzavanje/soma-memory-fix/SKILL.md) | Audits AgentStack agents for unwired kb_search nodes (missing knowledgeBaseId), proposes a fix plan, and — after confirmation — patches e... |
| [`evo-log-writer`](06-rad-odrzavanje/evo-log-writer/SKILL.md) | Logs SOMA agent run results into the correct evo-log.md file in the Obsidian vault |
| [`winners-log-logger`](06-rad-odrzavanje/winners-log-logger/SKILL.md) | Logs a winning hook (score ≥ 17/20) into the Hook Writer winners-log in the Obsidian vault |
| [`automation-triage`](06-rad-odrzavanje/automation-triage/SKILL.md) | Decides which of a client's repeated tasks are worth automating, which to teach a person instead, and which to tell them not to touch — c... |
| [`obsidian-knowledge-logger`](06-rad-odrzavanje/obsidian-knowledge-logger/SKILL.md) | Structured knowledge capture into an Obsidian vault via any available Obsidian MCP server or REST API |
| [`plugin-sync`](06-rad-odrzavanje/plugin-sync/SKILL.md) | Proverava i sinhronizuje `plugin/skills/` sa izvornim faznim folderima (01-08) i pakuje `plugin/` u distributable `.plugin` fajl |

### 07-izlazni-formati/ -- Izlazni formati / finalni materijal

Format u kom gotovo resenje stize do citaoca - dokument, prezentacija, tabela, artifact, dizajn.

| Skill | Sta radi |
|---|---|
| [`canvas-design`](07-izlazni-formati/canvas-design/SKILL.md) | Create beautiful visual art in .png and .pdf documents using design philosophy |
| [`theme-factory`](07-izlazni-formati/theme-factory/SKILL.md) | Toolkit for styling artifacts with a theme |
| [`web-artifacts-builder`](07-izlazni-formati/web-artifacts-builder/SKILL.md) | Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind C... |
| [`internal-comms`](07-izlazni-formati/internal-comms/SKILL.md) | A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use |
| [`doc-coauthoring`](07-izlazni-formati/doc-coauthoring/SKILL.md) | Guide users through a structured workflow for co-authoring documentation |
| [`slack-gif-creator`](07-izlazni-formati/slack-gif-creator/SKILL.md) | Knowledge and utilities for creating animated GIFs optimized for Slack |
| [`algorithmic-art`](07-izlazni-formati/algorithmic-art/SKILL.md) | Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration |
| [`brand-guidelines`](07-izlazni-formati/brand-guidelines/SKILL.md) | Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthropic's look-and-feel |

### 08-drugi-projekti/ -- Drugi / samostalni projekti

Nisu deo AI-agent pipeline-a - samostalni proizvodi izgradjeni istom disciplinom.

| Skill | Sta radi |
|---|---|
| [`tender-projekat`](08-drugi-projekti/tender-projekat/SKILL.md) | Radni protokol i kontinuitet projekta "tender-sistem" — anti-halucinacionog sistema za praćenje tendera za vodu/kanalizaciju u Srbiji (Po... |
| [`geo-prompt-library`](08-drugi-projekti/geo-prompt-library/SKILL.md) | Generiše kvota-validiranu biblioteku kupčevih upita (30–50 intenata, SR+EN par) iz URL-a firme, vertikale i lokalea — verzionisan JSON ka... |
| [`morning`](08-drugi-projekti/morning/SKILL.md) | Render the user's morning brief as a styled HTML artifact, or set it up as a recurring weekday task |

## tools/

Pomocni Claude Code alati koji NISU Skill paketi (subagenti, hooks, komande) - npr. `pr-reviewer` read-only code-review subagent.
