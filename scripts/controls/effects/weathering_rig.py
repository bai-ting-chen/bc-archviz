"""Weathering wall, emission rig and fixed review camera."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import bpy
import core.archviz as archviz
from materials.shared.nodes import G

def scene():
    """Build the flat-wall lab and canonical graph builder."""
    sc = bpy.context.scene
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    W, H = 8.0, 4.0
    bpy.ops.mesh.primitive_plane_add(size=1); wall = bpy.context.object
    wall.scale = (W, H, 1); wall.rotation_euler = (1.5708, 0, 0); wall.location = (W / 2, 0, H / 2)
    m = bpy.data.materials.new('lab'); b = G(m)   # canonical node builder (materials.shared.nodes.G)
    out = b.node('ShaderNodeOutputMaterial', (900, 0)); em = b.node('ShaderNodeEmission', (700, 0))
    b.link(em.outputs[0], out.inputs[0])
    pos = b.node('ShaderNodeNewGeometry', (-900, 0)).outputs['Position']   # world metres: x along wall, z up
    sep = b.node('ShaderNodeSeparateXYZ', (-700, 0)); b.link(pos, sep.inputs[0])
    return sc, W, H, wall, m, b, em, sep

def render(sc, W, H, O, TAG):
    """Render the lab with its original camera and settings."""
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = W; cam.location = (W / 2, -10, H / 2); cam.rotation_euler = (1.5708, 0, 0)
    sc.render.resolution_x, sc.render.resolution_y = 1200, 600
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; archviz.use_gpu(); sc.cycles.device = 'GPU'
    sc.view_settings.view_transform = 'Standard'; sc.world = None
    sc.render.filepath = str(O / f'lab_{TAG}.png'); bpy.ops.render.render(write_still=True)
