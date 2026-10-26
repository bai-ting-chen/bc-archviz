"""Reference localise; implementation for blend_refs."""
import filecmp
import hashlib
import os
import shutil
import bpy
from reference_paths import files_of, references


def relink(study):
    """Repath missing references to a file of the same name found inside the study (outside _wip)."""
    index = {}
    for root, dirs, files in os.walk(study):
        dirs[:] = [x for x in dirs if x != '_wip']
        for n in files:
            index.setdefault(n.lower(), os.path.join(root, n))
    fixed = []
    for d, attr, path in list(references()):
        hit = index.get(os.path.basename(path).lower())
        if not os.path.exists(path) and hit and getattr(d, 'library', None) is None:
            setattr(d, attr, bpy.path.relpath(hit))
            fixed.append([path, hit])
    return fixed


outside_libs = []


def localise(study):
    """Copy outside-study (and _wip) references into <study>/library/local/<parent>/ and repath them."""
    moved = relink(study)
    global outside_libs
    for d, attr, path in list(references()):
        wip = os.path.join(study, '_wip') + os.sep
        if getattr(d, 'library', None) is not None:
            continue  # linked data is fixed in its own library .blend, which is listed itself
        if (path.startswith(study + os.sep) and not path.startswith(wip)) or not (
                os.path.exists(path) or any(os.path.exists(f) for f in files_of(d, path))):
            continue
        if isinstance(d, bpy.types.Library):
            outside_libs.append(path)  # its own dependencies would not follow; caller refuses --apply
            continue
        dest_dir = os.path.join(study, 'library', 'local', os.path.basename(os.path.dirname(path)))
        src_files = files_of(d, path)
        clash = any(os.path.exists(os.path.join(dest_dir, os.path.basename(f))) and os.path.isfile(f)
                    and not filecmp.cmp(f, os.path.join(dest_dir, os.path.basename(f)), shallow=False) for f in src_files)
        if clash:  # same name, different content: keep both, in a folder named by the source path
            dest_dir += '_' + hashlib.md5(os.path.dirname(path).encode()).hexdigest()[:8]
        dest = os.path.join(dest_dir, os.path.basename(path))
        if os.path.isdir(path):
            if not os.path.exists(dest):
                shutil.copytree(path, dest)
        else:
            os.makedirs(dest_dir, exist_ok=True)
            for f in src_files:
                t = os.path.join(dest_dir, os.path.basename(f))
                if os.path.exists(f) and not os.path.exists(t):
                    shutil.copy2(f, t)
        setattr(d, attr, bpy.path.relpath(dest))
        moved.append([path, dest])
    if moved:
        bpy.ops.wm.save_mainfile()
    return moved
