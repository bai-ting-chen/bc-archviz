"""Study file traversal and guarded filesystem operations (Python 3.12+)."""
import os
import stat
from pathlib import Path


def is_link(path):
    """Identify symlinks and junctions without traversing them."""
    return path.is_symlink() or path.is_junction()


def checked(path, study):
    """Require a path strictly inside the study with no link or junction in its ancestry."""
    path, study = Path(os.path.abspath(path)), Path(os.path.abspath(study))
    if path == study or not path.resolve().is_relative_to(study.resolve()):
        raise ValueError(f'path outside study: {path}')
    for parent in (path, *path.parents):
        if is_link(parent):
            raise ValueError(f'link or junction is not allowed: {parent}')
        if parent == study:
            return path
    raise ValueError(f'path outside study: {path}')


def entries(folder):
    """List files, directories and opaque links without walking through links."""
    found = []
    for root, dirs, files in os.walk(folder, followlinks=False):
        found.extend(Path(root) / n for n in dirs + files)
        dirs[:] = [n for n in dirs if not is_link(Path(root) / n)]
    return found


def size(path):
    """Count file bytes without following links."""
    if is_link(path):
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in entries(path) if not is_link(p) and p.is_file())


def remove(path, study):
    """Delete a checked file or empty directory; propagate failures for a forward-only retry."""
    path = checked(path, study)
    path.chmod(stat.S_IWRITE)  # Windows refuses to delete read-only items.
    if path.is_dir():
        path.rmdir()
    else:
        path.unlink()
