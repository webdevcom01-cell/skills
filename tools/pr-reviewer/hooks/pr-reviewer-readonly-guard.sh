#!/bin/bash
# .claude/hooks/pr-reviewer-readonly-guard.sh (v3)
#
# Mechanically enforces pr-reviewer's "read-only" guarantee via a PreToolUse hook,
# instead of relying only on prose in the agent's Guardrails section.
#
# Design: ALLOWLIST, not denylist. Only commands matching a known-safe inspection
# pattern are permitted; everything else is denied by default (fail-closed).
#
# History — why this is v3, not v1: v1 only checked whether a command STARTED WITH
# an allowed prefix, and allowlisted subcommand *names* without checking their flags.
# Direct testing (piping fake tool-call JSON into this script — see the punch-list
# doc for the full test log) surfaced five real bypasses before this was ever
# handed off:
#   1. "git diff; rm -rf ."          -- command chaining via ;
#   2. "git diff && git push"        -- command chaining via &&
#   3. "find . -delete"              -- allowlisted command name, destructive flag
#   4. "git branch -D main"          -- allowlisted command name, destructive flag
#   5. "git diff --output=/tmp/x"    -- git's own --output flag writes a file with
#                                        no shell redirection character at all
# v3 fixes all five: it denies outright on any chaining/redirection/substitution
# metacharacter, drops subcommands that have a destructive-flag surface (find,
# git branch, git remote) instead of trying to enumerate every dangerous flag on
# them, and denies any --output/-o flag specifically on git/gh commands (where it
# means "write to this file"), while leaving grep/rg's own unrelated -o flag alone.
#
# Honest limit: this is a regex-based defense-in-depth layer over the model's own
# prose Guardrails, tested against the bypasses above — it is NOT a formally
# verified sandbox. A sufficiently creative bypass this testing didn't think of may
# still exist. If the stakes ever justify it, pair this with running pr-reviewer
# against a credential-less checkout or an isolated container, rather than relying
# on command-string pattern matching alone.
#
# Requires `jq` on PATH.

COMMAND=$(jq -r '.tool_input.command // empty')

deny() {
  jq -n --arg reason "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
}

if [ -z "$COMMAND" ]; then
  deny "pr-reviewer read-only guard: could not read tool_input.command; denying by default."
  exit 0
fi

# 1) Reject embedded newlines (multi-line command strings) outright.
if [[ "$COMMAND" == *$'\n'* ]]; then
  deny "pr-reviewer is read-only: multi-line command rejected outright: $COMMAND"
  exit 0
fi

# 2) Reject any chaining / redirection / substitution operator outright, BEFORE
#    the allowlist check. Without this, "git diff; rm -rf ." or "git diff > file"
#    would match the allowlist prefix and slip through with the dangerous part
#    unchecked.
if echo "$COMMAND" | grep -qE '[;&|`<>]|\$\('; then
  deny "pr-reviewer is read-only: command contains a chaining/redirection/substitution operator (; & | \` < > \$() and is blocked regardless of allowlist: $COMMAND"
  exit 0
fi

# 3) Reject git/gh's own --output/-o flag family, which writes to a file without
#    needing a shell redirection character at all (git diff/log/show/blame all
#    support --output=<file>). Scoped to git/gh only, so grep/rg's own unrelated
#    -o (--only-matching) flag isn't caught by mistake.
if echo "$COMMAND" | grep -qE '^(git|gh) ' && echo "$COMMAND" | grep -qE -- '--output(=| )|(^| )-o( |$)'; then
  deny "pr-reviewer is read-only: command uses --output/-o, which can write to a file directly: $COMMAND"
  exit 0
fi

# 4) Allowlist of inspection-only commands. Only command NAMES whose entire flag
#    surface is read-only are included here — deliberately no "find" (-delete,
#    -exec), no "git branch" (-d/-D/-m/-M), no "git remote" (add/remove/set-url):
#    rather than chase every dangerous flag on those, they're left off entirely.
ALLOWLIST_REGEX='^(git (diff|log|show|status|blame)|gh (pr|issue) (view|diff|list)|cat |grep |rg |ls |head |tail |wc )'

if echo "$COMMAND" | grep -qE "$ALLOWLIST_REGEX"; then
  exit 0  # Allowed — falls through to normal permission flow (no decision).
else
  deny "pr-reviewer is read-only: command is not on the inspection allowlist: $COMMAND"
fi
