<!-- Part of a derivative work of anthropics/skills@b29e7cf6 (skills/skill-creator), by buky <webdevcom01@gmail.com>, 2026-07-31. Apache-2.0; see LICENSE.txt. Changes: CHANGELOG.md. -->

# Skill Writing Guide

Moved out of SKILL.md body by T-04 (finding N-08): the body was 7,597 tokens against a 5,000-token recommendation, and Claude Code re-attaches only the first 5,000 after auto-compaction — so everything past that point was silently dropped in exactly the long sessions this skill is built for. The text below is unchanged.

---

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 tokens)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

These counts are approximate and you can feel free to go longer if needed — but note
that the spec measures level 1 in **tokens**, not words, and that the two body limits are
**conjunctive**: under 500 lines *and* under 5,000 tokens. The token one is the harsher
of the pair and the easy one to miss, because no validator checks it. It matters most
after auto-compaction: Claude Code re-attaches only the **first 5,000 tokens** of each
skill, so anything past that point is silently dropped in exactly the long sessions where
you most need the instructions. Measure both before you decide the body is finished.

**Key patterns:**
- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>100 lines), include a table of contents

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude reads only the relevant reference file.

#### Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

#### Writing Patterns

Prefer using the imperative form in instructions.

**Defining output formats** - You can do it like this:
```markdown
## Report structure
Use this template, adapting sections as needed:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern** - It's useful to include examples. You can format them like this (but if "Input" and "Output" are in the examples you might want to deviate a little):
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Writing Style

Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples. Start by writing a draft and then look at it with fresh eyes and improve it.

**Voice of the `description` field — the guidance is not settled.** Two sources of
comparable standing disagree, and this skill does not hide that:

- `platform.claude.com/…/best-practices`: "Always write in **third person**. The
  description is injected into the system prompt, and inconsistent point-of-view can
  cause discovery problems."
- `agentskills.io/skill-creation/optimizing-descriptions`: "Use **imperative** phrasing.
  Frame the description as an instruction to the agent: 'Use this skill when…' rather
  than 'This skill does…'"

They agree on the substance even where they differ on grammar: state **what** the skill
does and **when** to use it, and avoid first person (`I`, `we`, `my`) and second person
(`you`) self-description. Pick either voice and hold it across the whole description —
mixing them is the failure both sources actually warn about. Do not treat the choice as
resolved just because a validator accepts it; no validator in this skill checks voice.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: [you don't have to use this exact language] "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions in the next step while the runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema (including the `assertions` field, which you'll add later).
