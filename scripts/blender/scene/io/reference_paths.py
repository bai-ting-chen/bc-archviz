"""Reference paths; implementation for blend_refs."""
import glob
import os
import re
import bpy


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
