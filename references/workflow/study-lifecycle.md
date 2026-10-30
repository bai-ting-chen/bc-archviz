# Study lifecycle


## AST_02 procedure

**Closing a study cleans it.** When the user calls a study finished, list its milestone
    scenes (every final plus real turning points) under `## Milestones` in study-notes.md, then run
    `scripts/workflow/study_close.py <study>` (plan) and `--apply`: it makes the milestones self-contained
    (copies outside or `_wip` files they use into `library/local/`), deletes `_wip/`, other .blend
    files, backups, library files no milestone uses and vendor/cache folders, and verifies every
    milestone reference still resolves. Finals, notes, scripts and .3dm stay. No asking per file.
