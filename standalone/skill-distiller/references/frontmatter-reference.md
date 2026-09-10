# Frontmatter reference (adversarially verified)

Source: agentskills.io/specification, cross-checked against anthropics/skills,
huggingface/skills, and the (now-deprecated) openai/skills repo. Every field
below reflects a verified status, not an assumption — see the note on each row.

## Required (only two — everything else is optional)

| Field | Type / rules |
|---|---|
| `name` | String, 1–64 chars. Lowercase unicode alphanumeric (`a-z`, `0-9`) and hyphens only. Cannot start/end with a hyphen or contain `--`. **Must exactly match the parent folder's name.** |
| `description` | String, 1–1,024 chars, non-empty. Must describe both what the skill does and when to use it — this is the entire triggering mechanism, not documentation (see `quality-checks.md`). |

## Formally optional — defined by the spec, but not required

These four fields each have their own sub-section in the specification. Use
them when they add real value; never invent a fixed schema for `metadata`
since every implementation studied uses it differently.

| Field | Type / rules | Notes |
|---|---|---|
| `license` | String — a license name or a reference to a bundled license file | Present in most anthropics/skills and huggingface/skills entries; openai/skills keeps licensing in a separate `LICENSE.txt` instead of this field — both are valid, this field is never required. |
| `compatibility` | String, 1–500 chars | Describes environment requirements (platform, system packages, network access). The spec itself notes most skills don't need this field — only add it when there's a real, specific requirement. |
| `metadata` | Free-form string→string map | No fixed schema across implementations — HuggingFace uses a structured object (author/version/category/tags), OpenAI's legacy usage (`short-description`) was later disavowed by that repo's own authoring guide. Don't assume any particular key is standard. |
| `allowed-tools` | Space-separated string of pre-approved tool names | Explicitly marked experimental by the spec itself — support varies between client implementations. Don't rely on this being enforced anywhere. |

## Pure convention — not formal spec fields at all

These are **not** defined anywhere in the specification, not even as optional
fields. They only ever appear as ad-hoc keys inside the free-form `metadata`
map, when an author chooses to put them there.

| Convention | Where it actually lives |
|---|---|
| `version` | Only ever seen as `metadata.version` (e.g. `metadata: {version: "1.0"}`) — never a top-level field. |
| `platforms` | Same — only as an ad-hoc `metadata` key in specific implementations (e.g. Hermes Agent), never part of the base spec. |
| `author` | Same — the spec's own example shows `metadata: {author: example-org}`, explicitly as an example of free-form usage, not a defined field. |

**Why this distinction matters in practice:** treating `license` as "just a
convention like `version`" undersells it — it's worth setting correctly and
consistently because the spec gives it a defined shape. Conversely, don't
invent structure for `version`/`platforms`/`author` beyond what `metadata`
naturally offers; there's no standard to be compliant *with* for those three.

## Bundled folders (convention, not spec-mandated structure)

The specification does not mandate any particular bundled-folder layout — it
only defines what goes inside `SKILL.md`. The following are conventions
observed consistently across real implementations, safe to treat as the
de-facto standard:

| Folder | Convention |
|---|---|
| `scripts/` | Executable code for deterministic/repetitive sub-tasks. Should be self-contained or clearly document its own dependencies. |
| `references/` | Documentation loaded on demand — organize by *topic*, not by session or event (see `quality-checks.md`, references-sprawl). |
| `assets/` | Static resources used in output: templates, images, data files. |

`templates/` and `examples/` additionally appear in more than one independent
implementation (Hermes Agent, and at least one skill in huggingface/skills)
— convergent practice worth supporting, but still not part of the formal
specification. Don't require them.

Keep cross-references from `SKILL.md` to bundled files at most one directory
level deep — avoid chains of references pointing to other references.
