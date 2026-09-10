# Secrets exclusion patterns

Load this when publishing, reviewing, or scanning a manifest/config that
references credentials, or when deciding how a schema should represent a
required secret.

## The rule

A manifest may declare that a secret is required. It must never be able to
declare what that secret's value is. Everything in this file is really
about how strongly each of five ecosystems actually enforces that one
sentence — the gap between "there's a field for it" and "the value cannot
end up there" is where every real leak in this comparison originated.

## Enforcement, ranked from strongest to weakest

**Hermes Agent — enforced at two layers.** The schema itself only accepts a
secret *name*, a `description`, and a `required` flag; a `value` key isn't
a valid field at all, so a literal secret can't be structurally placed in
the manifest by mistake. Separately, Hermes's publish tooling independently
sweeps every file in the bundle for credential-shaped, high-entropy strings
— not just the manifest file — and refuses to finish the publish if it
finds one. That second layer is what catches the case a schema check alone
would miss: a leftover template file, say an `.env.example`, that someone
accidentally filled in with a real value before committing it.

**CrewAI — convention plus a plain string field.** Credentials are meant to
be referenced through `${ENV_VAR}` interpolation, resolved by the runtime
at crew-run time. But the field holding that string is just YAML text —
the schema has no way to tell an interpolation reference apart from a
literal value sitting in the same spot. A validator that only checks
"does this parse and match the schema" cannot catch a hardcoded key here;
only a raw-text scan for secret-shaped strings can.

**LangChain Hub — convention only, no schema involvement at all.** The
expected practice is that a serialized object should never embed a value
read out of `os.environ`; instead, whatever credential it depends on gets
*named* in the object's free-text `readme`. Because that field is ordinary
prose, there's no technical barrier keeping someone from typing an actual
credential straight into the same spot — the whole scheme depends entirely
on the person writing it choosing not to, and nothing downstream checks
that choice.

**OpenAI Assistants — mostly out of scope, with one reintroduced risk.**
The assistant object itself doesn't typically declare model-provider
secrets, since the caller's own API key authenticates the request rather
than the assistant object holding one. But third-party `tool_resources`
extensions that wire in custom tool integrations carry their own separate
configuration, and that configuration reintroduces the same class of risk
this file is about — it just lives outside the assistant manifest proper.

**MCP Registry — weakest of the five.** There is no schema field for
secrets at all in `server.json`. Required environment variables are
documented only in prose, in the `description` or an external README. There
isn't even a structured place to *name* a required secret, let alone
anything that could stop a value from being committed next to it.

## The lesson behind the worst observed case

A forked starter template that used `${ENV_VAR}`-style interpolation as its
only convention for credentials ended up, in one real case, with a literal
API key value sitting in the same field a reference belonged in — because
nothing in the schema forced the distinction, and the mistake wasn't caught
before the fork was widely cloned. The generalizable lesson: whenever a
secret reference and a secret value can both legally occupy the same plain
field, a schema check alone cannot tell you the file is clean. Run a
raw-text, high-entropy-string scan over the *entire* file being published or
merged — not only the lines that changed since the last scan — because a
literal value can sit untouched in a part of the file an incremental scan
already marked clean from an earlier pass.

## Practical checklist before publishing anything that references credentials

- Does the schema have a `value`-shaped field at all for secrets? If yes,
  that's already a structural risk — the fix is removing the field, not
  documenting "please don't fill this in."
- If credentials are represented as plain interpolation strings, is there a
  raw-text secret scan in the publish path — run over the whole file, not
  a diff — independent of schema validation?
- Does the *scan* run every time, including on forks and template reuse,
  not only on the original author's own commits?
- Is there anywhere in this ecosystem to name a required secret in a
  structured way (a real field, not prose) — and if not, is that itself
  worth flagging as a gap before adopting this ecosystem for anything
  handling real credentials?
