"""Inside Blender: list a .blend's external files and optionally copy outside-study files into the study.

    blender -b scene.blend --factory-startup --python blend_refs.py -- --study <dir> --out refs.json [--localise]

--localise first relinks missing files by name from inside the study, then copies every referenced file that lies outside <study> (or in its _wip/) into <study>/library/local/<parent folder>/,
repaths it relative and saves the .blend (RULES AST_03). Packed files are skipped.
"""

# Compatibility imports; each implementation has one owner (GOV_04).
from reference_paths import _abs, files_of, references  # noqa: F401
from reference_localise import relink, outside_libs, localise  # noqa: F401
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
