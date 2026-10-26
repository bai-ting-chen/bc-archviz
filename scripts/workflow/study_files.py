"""Study-local path, size and deletion operations."""
import os
import shutil
import stat


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
