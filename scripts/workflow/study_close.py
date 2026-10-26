"""Close a study (RULES AST_02): keep milestones and finals, make them self-contained, delete the rest.

    python study_close.py <study> [--keep a.blend ...] [--apply] [--blender <exe>]

Milestones: --keep, else the `.blend` names listed under `## Milestones` in STUDY_NOTES.md (the closing
agent writes that list: every final scene plus real milestones). Without a list only the plan runs
(newest .blend assumed). Without --apply it only prints the plan. With --apply it (1) copies files the milestones
use from outside the study into library/local/ and repaths them (scripts/blender/scene/io/blend_refs.py),
(2) deletes: _wip/, other .blend, *.blend1/*.3dmbak, library files no milestone uses, and top-level
folders holding nothing a milestone uses and no .py/.md/.3dm (vendor copies, sim caches),
(3) checks every milestone reference still resolves and logs the result in STUDY_NOTES.md.
Kept always: finals/, STUDY_NOTES.md, scripts, .3dm, loose top-level files. Never touches anything
outside the study.
"""
import argparse
import datetime
import os
import sys

from study_files import norm, size, remove
from study_milestones import milestones
from study_refs import refs, HERE
from study_prune import plan, KEEP_DIRS, KEEP_EXT

BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"


def main():
    """Plan, and with --apply carry out, the close of one study."""
    ap = argparse.ArgumentParser()
    ap.add_argument('study')
    ap.add_argument('--keep', nargs='*', default=[])
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--blender', default=BLENDER)
    a = ap.parse_args()
    study = norm(a.study)
    keep = [norm(k) for k in milestones(study, a.keep, a.apply)]
    data = [refs(b, study, a.blender, False) for b in keep]  # read-only pass first
    used = {norm(r[1]) for d in data for r in d['refs']}
    outside = sorted({r[1] for d in data for r in d['refs'] if not norm(r[1]).startswith(study + os.sep)})
    libs = sorted({lib for d in data for lib in d.get('outside_libraries', [])})
    if libs:
        sys.exit('milestones link .blend libraries outside the study; make them local or move them in first: '
                 + ', '.join(libs))
    if a.apply:  # relink, copy outside/_wip files in, then plan from the updated references
        data = [refs(b, study, a.blender, True) for b in keep]
        used = {norm(r[1]) for d in data for r in d['refs']}
    cands = plan(study, set(keep), used)
    total = sum(size(p) for p in cands)
    print('keep:', *[os.path.basename(k) for k in keep], sep='\n  ')
    missing = sorted({r[1] for d in data for r in d['refs'] if not r[2]})
    if missing and not a.apply:
        print('missing now (relinked by name from inside the study on --apply if found):', *missing, sep='\n  ')
    if outside and not a.apply:
        print('outside the study (copied into library/local on --apply):', *outside, sep='\n  ')
    print(f'delete ({total / 1e9:.2f} GB):', *[os.path.relpath(p, study) for p in cands], sep='\n  ')
    if not a.apply:
        return
    for p in cands:
        remove(p)
    for root, dirs, files in os.walk(os.path.join(study, 'library'), topdown=False):
        if not dirs and not files and root != os.path.join(study, 'library'):
            os.rmdir(root)
    after = [refs(b, study, a.blender, False) for b in keep]
    broken = [r[1] for d in after for r in d['refs'] if not r[2]]
    stamp = datetime.date.today().isoformat()
    log = (f'\n## Closed {stamp} (study_close.py)\nMilestones kept: '
           + ', '.join(f'`{os.path.basename(k)}`' for k in keep)
           + f'. Deleted {len(cands)} items ({total / 1e9:.2f} GB): _wip, other .blend, unused library'
           f' files, vendor/cache folders. Files copied in from outside: {sum(len(d["localised"]) for d in data)}.'
           f' Broken references after close: {len(broken)}.\n')
    with open(os.path.join(study, 'STUDY_NOTES.md'), 'a', encoding='utf-8') as f:
        f.write(log)
    print(log)
    if broken:
        sys.exit(f'BROKEN references: {broken}')


if __name__ == '__main__':
    main()
