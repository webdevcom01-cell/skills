# plugin-sync-guard

Git pre-commit hook that blocks a commit if `plugin/skills/` has drifted from
the 01-08 phase folders — the exact failure mode that let 28+ skills (and,
separately, 2 more later) go unsynced for weeks until a manual audit caught it.

This is NOT a Skill package (no SKILL.md) and NOT a Claude Code hook — it's a
plain git hook, same mechanism as `tools/pr-reviewer`'s guard but for `git
commit` instead of a Claude Code tool call.

It only ever runs `sync_plugin.py` in check mode (no `--apply`, no
`--prune-orphans`) — it reports and blocks, it never modifies files on its
own.

## Install (per clone/machine)

Git hooks live in `.git/hooks/`, which is never tracked by git — so this
script is kept here and symlinked in:

```bash
ln -sf ../../tools/plugin-sync-guard/pre-commit .git/hooks/pre-commit
chmod +x tools/plugin-sync-guard/pre-commit
```

Bypass for one commit if you genuinely need to: `git commit --no-verify`
(git's own standard escape hatch — this hook doesn't add a separate one).
