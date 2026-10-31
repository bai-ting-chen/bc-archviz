"""Reference paths; implementation for blend_refs."""
import glob
import os
import re
import bpy


def _abs(path, owner=None):
    """Absolute normalised path; '//' is relative to the .blend that owns the datablock (linked data: its library)."""
    return os.path.normpath(bpy.path.abspath(path, library=owner_library(owner)))


def files_of(d, path):
    """Concrete files behind a path: UDIM tiles and all numbered image, volume or mesh-cache sequence frames."""
    src = getattr(d, 'source', '')
    if src == 'TILED' and '<UVTILE>' in path:
        return [path.replace('<UVTILE>', f'u{(t.number - 1001) % 10 + 1}_v{(t.number - 1001) // 10 + 1}') for t in d.tiles]
    if src == 'TILED' and '<UDIM>' in path:
        return [path.replace('<udim>', str(t.number)).replace('<UDIM>', str(t.number)) for t in d.tiles]
    if src == 'SEQUENCE' or getattr(d, 'is_sequence', False):
        head, tail = os.path.split(path)
        m = re.match(r'(.*?)(\d+)(\.[^.]+)$', tail)
        if m:
            pattern = re.compile(re.escape(m.group(1)) + r'\d+' + re.escape(m.group(3)), re.I)
            found = sorted(f for f in glob.glob(os.path.join(glob.escape(head), '*'))
                           if pattern.fullmatch(os.path.basename(f)) and os.path.isfile(f))
            if os.path.normcase(path) not in {os.path.normcase(f) for f in found}:
                found.append(path)  # A missing configured frame must still fail verification.
            return sorted(found)
    return [path]


def references():
    """Yield (datablock, attribute, absolute path) for every external file the .blend needs."""
    for coll in (bpy.data.images, bpy.data.libraries, bpy.data.cache_files, bpy.data.volumes,
                 bpy.data.sounds, bpy.data.fonts, bpy.data.movieclips):
        for d in coll:
            fp = getattr(d, 'filepath', '')
            if fp and not getattr(d, 'packed_file', None) and not fp.startswith('<'):
                yield d, 'filepath', _abs(fp, d).replace('<udim>', '<UDIM>')
    trees = list(bpy.data.node_groups)
    trees += [tree for coll in (bpy.data.materials, bpy.data.worlds, bpy.data.lights)
              for data in coll if (tree := getattr(data, 'node_tree', None)) is not None]
    seen = set()
    for tree in trees:
        for node in tree.nodes:
            if (node.bl_idname == 'ShaderNodeTexIES' and node.mode == 'EXTERNAL'
                    and node.filepath and node.as_pointer() not in seen):
                seen.add(node.as_pointer())
                yield node, 'filepath', _abs(node.filepath, node)
    for scene in bpy.data.scenes:
        for strip in (scene.sequence_editor.strips_all if scene.sequence_editor else ()):
            if strip.type == 'IMAGE':
                for element in strip.elements:
                    yield strip, 'directory', _abs(os.path.join(strip.directory, element.filename), strip)
            elif strip.type == 'MOVIE' and strip.filepath:
                yield strip, 'filepath', _abs(strip.filepath, strip)
    for ob in bpy.data.objects:
        for m in ob.modifiers:
            dom = getattr(m, 'domain_settings', None)
            if dom is not None and dom.cache_directory:
                yield dom, 'cache_directory', _abs(dom.cache_directory)


def owner_library(owner):
    """Return the library owning a datablock or shader node, if linked."""
    return getattr(owner, 'library', None) or getattr(getattr(owner, 'id_data', None), 'library', None)
