"""Close a study (RULES 10e): keep milestones and finals, make them self-contained, delete the rest.

    python study_close.py <study> [--keep a.blend ...] [--apply] [--blender <exe>]

Milestones: --keep, else the `.blend` names listed under `## Milestones` in STUDY_NOTES.md (the closing
agent writes that list: every final scene plus real milestones). Without a list only the plan runs
(newest .blend assumed). Without --apply it only prints the plan. With --apply it (1) copies files the milestones
use from outside the study into library/local/ and repaths them (scripts/blender/blend_refs.py),
(2) deletes: _wip/, other .blend, *.blend1/*.3dmbak, library files no milestone uses, and top-level
folders holding nothing a milestone uses and no .py/.md/.3dm (vendor copies, sim caches),
(3) checks every milestone reference still resolves and logs the result in STUDY_NOTES.md.
Kept always: finals/, STUDY_NOTES.md, scripts, .3dm, loose top-level files. Never touches anything
outside the study.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
KEEP_DIRS = {'finals', 'library'}
KEEP_EXT = {'.py', '.md', '.3dm'}


def norm(p):
    """Case-normalised absolute path."""
    return os.path.normcase(os.path.normpath(os.path.abspath(p)))


def size(p):
    """Bytes of a file or folder."""
    if os.path.isfile(p):
        return os.path.getsize(p)
    return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)


def remove(p):
    """Delete a file or folder, clearing read-only flags (vendor files often carry them)."""
    def unlock(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if os.path.isdir(p):
        shutil.rmtree(p, onerror=unlock)
    else:
        os.chmod(p, stat.S_IWRITE)
        os.remove(p)


def milestones(study, keep, apply=False):
    """Milestone .blend paths: --keep, else STUDY_NOTES `## Milestones`, else the newest .blend."""
    blends = sorted((f for f in os.listdir(study) if f.lower().endswith('.blend')),
                    key=lambda f: os.path.getmtime(os.path.join(study, f)))
    if not keep:
        notes = os.path.join(study, 'STUDY_NOTES.md')
        if os.path.exists(notes):
            m = re.search(r'^## Milestones\s*$(.*?)(?=^## |\Z)', open(notes, encoding='utf-8').read(), re.M | re.S)
            if m:
                keep = re.findall(r'[\w\-. ]+?\.blend\b', m.group(1))
    keep = [k.strip() for k in keep]
    if not keep and apply:
        sys.exit('no milestones: list them under "## Milestones" in STUDY_NOTES.md or pass --keep')
    keep = keep or blends[-1:]
    missing = [k for k in keep if k not in blends]
    if missing:
        sys.exit(f'milestone not found in study root: {missing}')
    return [os.path.join(study, k) for k in keep]


def refs(blend, study, blender, localise):
    """Run blend_refs.py in Blender; return its JSON."""
    out = os.path.join(study, '_close_refs.json')
    cmd = [blender, '-b', blend, '--factory-startup', '--python',
           os.path.join(HERE, 'blender', 'blend_refs.py'), '--', '--study', study, '--out', out]
    if localise:
        cmd.append('--localise')
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = json.load(open(out, encoding='utf-8'))
    os.remove(out)
    return data


def plan(study, keep, used):
    """List deletion candidates; nothing a milestone uses is ever listed."""
    def holds_used(p):
        p = norm(p)
        return any(u == p or u.startswith(p + os.sep) for u in used)

    out = []
    for f in os.listdir(study):
        p = os.path.join(study, f)
        low = f.lower()
        if os.path.isdir(p):
            if f == '_wip' or (f not in KEEP_DIRS and not holds_used(p) and not any(
                    os.path.splitext(n)[1].lower() in KEEP_EXT for _, _, ns in os.walk(p) for n in ns)):
                out.append(p)
        elif (low.endswith('.blend') and norm(p) not in keep) or low.endswith(('.blend1', '.3dmbak')):
            out.append(p)
    lib = os.path.join(study, 'library')
    for root, _, files in os.walk(lib):
        dir_used = any(norm(os.path.join(root, n)) in used for n in files)
        for n in files:
            p = os.path.join(root, n)
            if norm(p) in used or (n == 'meta.json' and dir_used) or holds_used(p):
                continue
            out.append(p)
    return [p for p in out if not holds_used(p)]


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
    data = [refs(b, study, a.blender, a.apply) for b in keep]
    used = {norm(r[1]) for d in data for r in d['refs']}
    outside = sorted({r[1] for d in data for r in d['refs'] if not norm(r[1]).startswith(study + os.sep)})
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
