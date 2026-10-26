"""Plan unused study files while retaining milestone dependencies."""
import os
from study_files import norm

KEEP_DIRS = {'finals', 'library'}
KEEP_EXT = {'.py', '.md', '.3dm'}


def plan(study, keep, used):
    """List deletion candidates; nothing a milestone uses is ever listed."""
    used_dirs = [u for u in used if os.path.isdir(u)]

    def holds_used(p):
        p = norm(p)
        return any(u == p or u.startswith(p + os.sep) for u in used) or any(
            p.startswith(d + os.sep) for d in used_dirs)

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
