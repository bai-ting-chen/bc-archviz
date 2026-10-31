"""Read new-study final scenes and ordered milestone image list items."""
import re
from pathlib import Path
from study_files import checked
from study_prune import is_image


def listed(study, heading):
    """Read backtick list items from a notes section ending at the next heading."""
    text = (study / 'study-notes.md').read_text(encoding='utf-8')
    match = re.search(r'^## ' + re.escape(heading) + r'[^\S\n]*\n(.*?)(?=^#{1,6}\s|\Z)', text, re.M | re.S)
    return [value for line in match[1].splitlines() if re.match(r'^\s*(?:[-*+]|\d+\.)\s+', line)
            for value in re.findall(r'`([^`]+)`', line)] if match else []


def final_scenes(study):
    """Require the listed final scenes to exist in the study root."""
    scenes = [checked(study / name, study) for name in listed(study, 'Final scene')]
    if not scenes or any(p.parent != study or p.suffix.lower() != '.blend' or not p.is_file() for p in scenes):
        raise ValueError('list existing root .blend files under ## Final scene')
    return scenes


def milestone_images(study):
    """Resolve ordered _wip image moves, accepting targets already moved by a partial apply."""
    moves = []
    for number, name in enumerate(listed(study, 'Milestones'), 1):
        source = checked(study / name, study)
        if Path(name).is_absolute() or not source.is_relative_to(study / '_wip') or not is_image(source):
            raise ValueError(f'milestone must be an image under _wip/: {name}')
        target = checked(study / 'milestones' / f'milestone-{number}{source.suffix.lower()}', study)
        if source in [s for s, _ in moves] or (source.exists() and target.exists()):
            raise ValueError(f'duplicate milestone or existing target: {name}')
        if not source.is_file() and not target.is_file():
            raise ValueError(f'milestone not found: {name}')
        moves.append((source, target))
    return moves
