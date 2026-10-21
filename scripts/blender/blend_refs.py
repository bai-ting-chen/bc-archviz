"""Inside Blender: list a .blend's external files and optionally copy outside-study files into the study.

    blender -b scene.blend --factory-startup --python blend_refs.py -- --study <dir> --out refs.json [--localise]

--localise first relinks missing files by name from inside the study, then copies every referenced file that lies outside <study> (or in its _wip/) into <study>/library/local/<parent folder>/,
repaths it relative and saves the .blend (RULES AST_03). Packed files are skipped.
"""
import filecmp
import glob
import hashlib
import json
import os
import re
import shutil
import sys

import bpy


def _args():
    """Parse the arguments after '--'."""
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = dict(study=None, out=None, localise=False)
    while a:
        k = a.pop(0)
        if k == '--localise':
            out['localise'] = True
        else:
            out[k.lstrip('-')] = a.pop(0)
    return out


def _abs(path, owner=None):
    """Absolute normalised path; '//' is relative to the .blend that owns the datablock (linked data: its library)."""
    lib = getattr(owner, 'library', None)
    return os.path.normcase(os.path.normpath(bpy.path.abspath(path, library=lib)))


def files_of(d, path):
    """Concrete files behind a path: every UDIM tile and every frame of an image sequence."""
    src = getattr(d, 'source', '')
    if src == 'TILED' and '<UDIM>' in path:
        return [path.replace('<udim>', str(t.number)).replace('<UDIM>', str(t.number)) for t in d.tiles]
    if src == 'SEQUENCE':
        head, tail = os.path.split(path)
        m = re.match(r'(.*?)(\d+)(\.[^.]+)$', tail)
        if m:
            return sorted(os.path.normcase(f) for f in glob.glob(os.path.join(head, glob.escape(m.group(1)) + '*' + m.group(3))))
    return [path]


def references():
    """Yield (datablock, attribute, absolute path) for every external file the .blend needs."""
    for coll in (bpy.data.images, bpy.data.libraries, bpy.data.cache_files, bpy.data.volumes,
                 bpy.data.sounds, bpy.data.fonts, bpy.data.movieclips):
        for d in coll:
            fp = getattr(d, 'filepath', '')
            if fp and not getattr(d, 'packed_file', None) and not fp.startswith('<'):
                yield d, 'filepath', _abs(fp, d).replace('<udim>', '<UDIM>')
    for ob in bpy.data.objects:
        for m in ob.modifiers:
            dom = getattr(m, 'domain_settings', None)
            if dom is not None and dom.cache_directory:
                yield dom, 'cache_directory', _abs(dom.cache_directory)


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


def main():
    """Dump references (after optional localising) to JSON."""
    a = _args()
    study = os.path.normcase(os.path.normpath(a['study']))
    moved = localise(study) if a['localise'] else []
    refs = [[type(d).__name__, f, os.path.exists(f)] for d, _, p in references() for f in files_of(d, p)]
    with open(a['out'], 'w', encoding='utf-8') as f:
        json.dump(dict(blend=bpy.data.filepath, refs=refs, localised=moved, outside_libraries=sorted(set(outside_libs) | {p for d, _, p in references() if isinstance(d, bpy.types.Library) and not p.startswith(study + os.sep)})), f, indent=1)


if __name__ == '__main__':
    main()
