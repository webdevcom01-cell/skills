---
name: transport-native-distribution
description: Design principle for shipping a bundle of related artifacts (agent configuration, personas, tool wiring, scheduled jobs, dotfiles, infrastructure templates, etc.) without standing up a dedicated package registry, build pipeline, or publish step. Applies whenever the artifacts are plain files that can live inside a system that already combines versioned history with a transport channel — most commonly a git repository. Use when scoping how a new kind of "profile" or config bundle should be packaged, released, installed, and kept up to date.
---

# Let the Transport Carry the Package

## The core move

Most distribution systems are assembled from four separate concerns: a
registry (where packages are listed and discovered), a build/release
pipeline (how a package gets produced and cut), a transport (how bytes
move from producer to consumer), and a versioning layer (how history and
rollback work). When the thing being shipped is just a directory of plain
files — configuration, prompts, scripts, connector wiring,
scheduled-task definitions — those four concerns don't need four
separate systems. A version-control tool already combines transport and
history into one piece of software, so building anything on top of it is
frequently pure overhead.

Concretely: treat the bundle itself as a repository. Adding a capability
or fixing a config value becomes a commit. Cutting a new release is
whatever you already do to send a commit to the shared remote. A
consumer's first install is however that tool fetches a full working
copy. Picking up the latest changes is however that tool merges upstream
commits into a local copy. There's no separate catalog service, no
artifact store, and nothing that has to be compiled or assembled before
it can be handed off — the commit log doubles as the release notes, and
the remote doubles as the registry.

## Lifecycle mapping (generic pattern)

| Traditional distribution concern | What it becomes when the version-control tool absorbs it |
|---|---|
| Package registry / index | The shared remote itself — its branches, tags, or file tree stand in for a catalog |
| Build step | Skipped — the checked-in files already are the runnable artifact |
| Release / publish | Committing, then sending that commit to the shared remote |
| Install | A full checkout of the repo onto the consumer's machine |
| Keeping current | Fetching and merging upstream changes into the local copy |
| Version history / rollback | The commit log itself — checking out an earlier commit or tag *is* the rollback path |
| Access control | Whatever the hosting platform already offers for repo-level permissions |

## Preconditions for this to work

- The bundle is made of text or otherwise diffable, mergeable content —
  no compiled binaries, no artifacts that must be built per target
  platform.
- Every consumer already has, or can easily get, the version-control
  client; you are not trying to reach people who have never touched it.
- One bundle stays small enough that a full working-copy transfer is
  cheap, since there's no mechanism to fetch only the changed piece.
- You're comfortable exposing the entire change history to anyone who can
  read the repo — unlike a registry that serves only the current release,
  there's no way to hide earlier states.

## When to reach for a dedicated registry/build system instead

- The artifact needs compilation, bundling, or platform-specific builds
  before it's usable.
- You need independent versioning and dependency resolution across many
  interdependent pieces, rather than one bundle versioned as a whole.
- Consumers must never see history — only the current approved state
  (secret rotation, compliance redaction, and similar cases).
- You're reaching non-technical end users with no appetite for
  version-control tooling.
- Scale demands content-addressed storage, partial/delta fetches, or a
  CDN in front of the artifact — moving the whole repository every time
  becomes the bottleneck.

## How to apply this pattern to something new

1. List everything the bundle has to carry. (In the motivating example: an
   agent's persona, its skill definitions, any scheduled or cron-style
   jobs, its external tool/connector wiring, and its configuration
   values.)
2. Check whether each of those pieces can be represented as files the
   version-control tool can track and diff sensibly.
3. If yes, stop designing a registry. Define the repo layout, decide what
   counts as a "release" (a tag convention, changelog-by-commit-message,
   or similar), and document install/update as plain checkout/fetch
   instructions instead of building separate tooling for them.
4. If some pieces resist that treatment — a compiled binary, a secret
   that must never sit in history, a large media asset — carve those out
   into whatever specialized system fits, and keep only the diffable,
   shareable material inside the version-control-backed bundle.

## Beyond one specific tool

The same move works with any store that already pairs a transport channel
with built-in history: a versioned object-storage bucket used as both the
drop location and the audit trail, a cluster whose state is reconciled
straight from committed manifests, or a database table with row-level
history serving as both the live config and its own changelog. Before
building a dedicated distribution system, ask whether something already
sits between producer and consumer that keeps a history *and* moves
bytes. If it does, that's your distribution stack — there's no need to
build a second one beside it.
