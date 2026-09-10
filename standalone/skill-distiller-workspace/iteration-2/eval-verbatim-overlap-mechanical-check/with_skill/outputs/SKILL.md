---
name: vcs-native-distribution
description: Explains and applies the pattern of using an existing version-control system (typically git) as the entire distribution channel for a bundle of heterogeneous artifacts — instead of building a separate package registry plus a build/publish pipeline. Covers mapping product lifecycle verbs (publish, install, update) onto the VCS's own operations (push, clone, pull), and the tradeoffs that choice implies. Use when designing how to ship a bundle of related-but-different pieces (agent config/personality, automation jobs, tool or service connections, settings, dotfiles, IaC modules, plugin bundles) to many installations, when someone asks "do we need a package registry for this" or "how should updates get distributed", or when reviewing a distribution design that already leans on git and you want to check it's using the pattern deliberately rather than accidentally. Do NOT use for general package-manager or registry design that has nothing to do with reusing a VCS, and not for ordinary git branching/workflow questions unrelated to how a product distributes itself to end users.
license: Apache-2.0
---

# VCS-native distribution

## Core idea

A version-control system already solves two hard problems at once: moving a
set of files to another machine, and tracking how that set of files changed
over time. A distribution mechanism needs exactly those two things. So a
bundle of artifacts that all need to travel and evolve together can often be
distributed by simply living in a VCS repository — with no registry, no
build step, and no separate publish pipeline layered on top.

This is not "git happens to be involved somewhere." It means the VCS's own
commands *are* the product's install/update commands, unmediated:

| Product lifecycle step | VCS operation that performs it |
|---|---|
| Publish a new or updated bundle | commit + push to the repo |
| Install the bundle for the first time | clone the repo |
| Pick up the latest changes | pull / fetch + merge |

No extra layer translates between "what the product calls this step" and
"what the VCS calls this step" — they're the same step.

## The bundle can be heterogeneous, not just code

The artifact being versioned doesn't have to be a single kind of thing. A
repo used this way commonly bundles several different categories that all
need to move and version together as one unit — for example, an AI agent
profile might combine a personality/behavior definition, a set of skills,
scheduled (cron-style) jobs, connections to external tools or MCP servers,
and general settings, all committed to one repo so that installing or
updating the agent means installing or updating all of it at once, atomically.
The same shape shows up in dotfiles repos, infrastructure-as-code modules,
and editor/IDE plugin bundles: unrelated-looking pieces, kept together
because they only make sense installed and versioned as a set.

## Why this is worth doing

- **No parallel infrastructure to build or run.** A registry server, a build
  step, and a publish pipeline are each a system with its own uptime,
  auth, and maintenance burden. Reusing the VCS's transport means none of
  that has to be built at all.
- **Versioning comes for free.** History, diffs, rollback, and branching
  already exist in the VCS — a bespoke package format would have to
  reinvent some subset of them.
- **The install verb is already familiar.** Anyone who can clone a repo
  already knows how to install the bundle; there's no new client tool to
  learn.

## What you give up, or have to solve separately

The source pattern is silent on these — they aren't automatic just because
the VCS is doing the transport, so treat them as open questions to answer
explicitly for your own case rather than assumptions the pattern resolves:

- **Discovery and curation.** A registry usually gives you search, listings,
  and ratings; a bare repo does not. If people need to find bundles they
  don't already know the URL for, that's a separate concern to design.
- **Granularity of versioning.** The whole repo versions together. If two
  parts of the bundle need independent version numbers or independent
  release cadences, a single repo doesn't give you that split for free —
  you'd need submodules, subdirectories with their own tags, or multiple
  repos.
- **Access control and trust.** Who can push, and whether a consumer should
  trust what they're pulling, is whatever the VCS host's permission model
  already provides — nothing about the pattern itself adds a review or
  signing step on top of that.

## Decision checklist

Before building a dedicated registry/build/publish pipeline for something,
check:

1. Is the thing being distributed already a set of files (config, code,
   definitions) rather than a compiled binary artifact that needs a build
   step to produce?
2. Do the consumers already have the VCS tool installed and know its basic
   commands?
3. Would "install = clone" and "update = pull" actually match how consumers
   want to receive changes (whole-bundle, in order), rather than needing
   selective/partial updates?

If all three hold, reusing the VCS as the full distribution channel is worth
trying before reaching for heavier tooling. If any one clearly doesn't hold —
e.g. consumers need to install only part of the bundle, or the artifact must
be compiled before use — the pattern still may apply to part of the problem,
but expect to layer something on top rather than relying on push/clone/pull
alone.
