# Review checklist

What a reviewer of a bc-archviz change checks. Read SKILL.md, RULES.md, references/workflow/skill-maintaining.md and
references/scene/blender-api-traps.md first. Report each finding with file:line and a concrete
failure scenario:

1. **Correctness bugs in the code:** wrong Blender 5.2 API use (see blender-api-traps.md), broken
   node links, unit errors (mm vs m, lux, lumens, EV), paths that only work on one machine.
2. **Breaks of the skill's own rules:** a project, study, client or user-folder name in the skill;
   a scene-specific number presented as a rule (RULES GOV_01); a rule stated outside RULES.md
   instead of pointed to; a change that can break another clone but has no MIGRATE.md; a second
   builder for a job that already has one; a new public helper without a one-line docstring.
3. **Docs that no longer match the code:** SKILL.md tables, references, blender-python-helpers.md.
