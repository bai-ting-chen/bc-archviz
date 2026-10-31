r"""Close a new study using known-safe deletions only; never write the scene.

Usage (Python 3.12+): %LOCALAPPDATA%\BlenderMCP\venv\Scripts\python.exe scripts/workflow/study_close.py <study> [--apply]
"""
import argparse
import datetime
import json
import os
from pathlib import Path
from study_files import checked, is_link, remove
from study_milestones import final_scenes, milestone_images
from study_prune import plan, large_folders
from study_refs import scan


def check_plan(saved, current, study):
    """Require unchanged references, choices and deletions, accepting only items already gone."""
    for key in ('references', 'finals', 'milestones'):
        if saved[key] != current[key]:
            raise ValueError(f'{key} changed; run the plan first')
    added = set(current['delete']) - set(saved['delete'])
    retained = [name for name in set(saved['delete']) - set(current['delete']) if (study / name).exists()]
    if added or retained:
        raise ValueError(f'delete list changed; run the plan first: {sorted(added) + retained}')


def apply(study, saved, moves, scenes, blender):
    """Move milestones, delete planned items and recheck references; failed deletions are retryable."""
    for source, target in moves:
        if source.exists():
            target.parent.mkdir(exist_ok=True)
            checked(source, study).rename(checked(target, study))
    order = sorted(saved['delete'], key=lambda name: (name.endswith('/'), -name.count('/'), name))
    try:
        for name in order:
            path = study / name
            if path.exists():
                remove(path, study)
    except OSError as error:
        left = [name for name in order if (study / name).exists()]
        raise ValueError(f'delete failed: {error}\nleft to delete:\n' + '\n'.join(left)) from error
    after, _ = scan(scenes, study, blender)
    if after != saved['references']:
        raise ValueError('references changed after deletion; closure record not written')
    stamp = datetime.date.today().isoformat()
    log = (f'# Closed {stamp}\nFinal scene: {saved["finals"]}\nMilestones: {saved["milestones"]}'
           f'\nDeleted {len(saved["delete"])} items ({sum(saved["delete"].values()) / 1e9:.6f} GB):'
           + '\n' + '\n'.join(saved['delete']) + '\nBroken references: 0.\n')
    remove(study / 'close-plan.txt', study)
    notes = checked(study / 'study-notes.md', study)
    if 'see closed.md.' not in notes.read_text(encoding='utf-8'):  # a rerun after a failed write adds it once
        with notes.open('a', encoding='utf-8') as stream:
            stream.write(f'\nClosed {stamp}: see closed.md.\n')
    checked(study / 'closed.md', study).write_text(log, encoding='utf-8')  # last: it marks the study closed


def main():
    """Read final scenes, print an allow-listed plan and optionally apply its unchanged contents."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--blender', default=str(Path(os.environ['PROGRAMFILES']) / 'Blender Foundation/Blender 5.2/blender.exe'))
    args = parser.parse_args()
    study = Path(os.path.abspath(args.study))
    if is_link(study) or not study.is_dir():
        raise ValueError('study must be an existing directory, not a link')
    if (study / 'closed.md').exists():
        raise ValueError('already closed: closed.md exists')
    checked(study / 'study-notes.md', study)
    plan_file = checked(study / 'close-plan.txt', study)
    if args.apply and not plan_file.is_file():
        raise ValueError('run the plan first: close-plan.txt is missing')
    scenes, moves = final_scenes(study), milestone_images(study)
    references, used = scan(scenes, study, args.blender)
    current = dict(finals=[p.name for p in scenes], milestones=[[s.relative_to(study).as_posix(), t.relative_to(study).as_posix()]
                   for s, t in moves], references=references, delete=plan(study, set(scenes), used, moves))
    print('milestone renames:', current['milestones'])
    print(f'delete ({sum(current["delete"].values())} bytes):', *current['delete'], sep='\n  ')
    for name, count in large_folders(study):
        print(f'unknown folder kept: {name} ({count / 1e6:.1f} MB)')
    if args.apply:
        saved = json.loads(plan_file.read_text(encoding='utf-8'))
        check_plan(saved, current, study)
        apply(study, saved, moves, scenes, args.blender)
    else:
        plan_file.write_text(json.dumps(current, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
