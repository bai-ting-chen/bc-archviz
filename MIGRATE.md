# MIGRATE — run before anything else, then delete

## 261018 — Research loop for an agent working alone
Pull-only. New `references/research-loop.md`: the order of work when one agent (Claude or Codex)
runs research, studies and experiments without the user or the other model — question, physics,
proof plan, build, prove, judge, record, loop log, skill promotion — plus what it decides alone and
what it never does alone. Pointers in SKILL.md (references table) and RULES 15. No code changed.

### 1. Read the new reference
Check: this machine's session has read `references/research-loop.md` (or the user says so).
Do: read it before the next unattended study; nothing to install.

### Last. Delete this file
Only after the steps above changed something here: delete MIGRATE.md, commit, pull --rebase, push.
