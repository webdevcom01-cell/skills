# Provenance: idea-to-project

`manifest-snapshot.json` in this folder is a **verbatim, byte-for-byte copy** of the
Claude Desktop session-cache plugin manifest that was the source of truth when this
skill was recovered into this repo.

- **Snapshot taken:** 2026-09-10
- **Exact source path at time of capture:**
  `/Users/buda007/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/8e0b9915-0af4-446a-b8ff-61e474ed90e6/d62e3a41-a44b-4f88-86f1-809bfd40b157/manifest.json`
- **Relevant entry within the snapshot** (this manifest lists every skill in that
  session-cache plugin bundle, not just this one):

  ```json
  {
    "skillId": "skill_01J1axx1yhp2nNrUex19QwUm",
    "name": "idea-to-project",
    "description": "Use when someone has a raw idea and wants a real deliverable built through Idea→Spec→Build→Test→Deploy; hands off React/Next/Vite UI decisions to react-design:director first.",
    "creatorType": "user",
    "updatedAt": "2026-09-03T20:28:01.913132Z",
    "enabled": true,
    "backingPluginId": "plugin_01Cys6njBnnBmfwYFh8U66DR"
  }
  ```

- **Verification:** `sha256sum` of this file matches the source manifest.json exactly
  at time of capture (see the session transcript / commit message for the hash pair).

This snapshot documents where the skill came from. It does not imply the session-cache
original has been deleted — it has not.

**A note on the checksum proof:** the SHA-256 hash recorded for this snapshot proves that
`manifest-snapshot.json` was byte-for-byte faithful to the source `manifest.json` **at the
moment this snapshot was taken** (commit `18ec284`). It is not a permanently-holding
invariant against the source — the session-cache `manifest.json` is a live, shared
registry that changes on its own from time to time (e.g. its top-level `lastUpdated`
epoch field), without necessarily changing any individual skill entry. If a future
sha256 recheck against the current live source does not match this snapshot, that only
means the source has since been touched — it does not mean this snapshot is corrupt or
wrong. To verify the integrity of the snapshot file itself, use `git log`/`git diff` on
this file (should be empty since it was committed), not a comparison against the
source's current state.
