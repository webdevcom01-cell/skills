# pr-reviewer

Read-only Claude Code subagent for PR/diff review, sa mehanicki forsiranim
read-only guard hook-om (v3, blokira chaining/redirection/destructive flags).

Ovo NIJE Skill paket (SKILL.md) - to je Claude Code subagent + hook konfiguracija
(.claude/agents, .claude/hooks, .claude/commands konvencija), drugaciji mehanizam
od skillova u ostatku ovog repoa. Zadrzano ovde jer je funkcionalan i dobro
testiran alat (vidi komentare u hooks/pr-reviewer-readonly-guard.sh za istoriju
5 otkrivenih bypass-ova i njihovih fixeva).

Da bi radio, agents/pr-reviewer.md i hooks/pr-reviewer-readonly-guard.sh treba
da budu pod `.claude/` u korenu projekta gde se koristi (kopiraj ih tamo, ne
referenciraj odavde).
