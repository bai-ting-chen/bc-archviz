"""Allow-list only known-safe study deletions; every unknown file stays."""
import re
from study_files import entries, is_link, size


def is_image(path):
    """Recognise Blender image-file extensions eligible for unused-library cleanup."""
    return path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.exr', '.hdr', '.webp', '.bmp', '.tga', '.dds', '.jp2'}


def plan(study, keep, used, moves):
    """Return leaf deletions and empty-directory removals, preserving used numbered siblings."""
    tree = entries(study)
    protected = set(used)
    for path in used:
        match = re.match(r'(.*?)(\d+)(\.[^.]+)$', path.name)
        if match and path.parent.is_dir():
            pattern = re.compile(re.escape(match[1]) + r'\d+' + re.escape(match[3]), re.I)
            protected.update(p for p in path.parent.iterdir() if pattern.fullmatch(p.name))
    sources = {source for source, _ in moves}
    links = [p for p in tree if is_link(p)]
    delete = {}
    for path in tree:
        relative = path.relative_to(study)
        parts = [p.lower() for p in relative.parts]
        if is_link(path) or any(link.is_relative_to(path) for link in links):
            continue
        process = parts[0] == '_wip' or '__pycache__' in parts[:-1] or (path.is_dir() and parts[-1] == '__pycache__')
        unused = parts[0] == 'library' and is_image(path) and path not in protected and not any(
            p.is_dir() and path.is_relative_to(p) for p in used)
        version = path.suffix.lower() in {'.blend1', '.3dmbak'} or (path.parent == study and path.suffix.lower() == '.blend' and path not in keep)
        if path not in sources and (process or (not path.is_dir() and (unused or version))):
            if path in protected:
                raise ValueError(f'used reference would be deleted: {path}')
            delete[relative.as_posix() + ('/' if path.is_dir() else '')] = 0 if path.is_dir() else size(path)
    return dict(sorted(delete.items()))


def large_folders(study):
    """List otherwise unaccounted top-level folders larger than 100 MB without deleting them."""
    return [(p.name, n) for p in study.iterdir() if p.is_dir() and not is_link(p)
            and p.name.lower() not in {'_wip', 'library', 'milestones', 'finals', '__pycache__'}
            and not p.name.lower().startswith('reference') if (n := size(p)) > 100_000_000]
