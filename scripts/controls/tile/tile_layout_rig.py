"""Shared tile-layout emission probe, coordinates and fixed cases."""

import os as _os
import sys as _sys
_CONTROLS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in [_CONTROLS] + [_os.path.join(_CONTROLS, _t) for _t in ('archviz', 'tile', 'material', 'effects', 'water', 'lighting', 'environment', 'regression')]:
    if _d not in _sys.path:
        _sys.path.append(_d)
import bpy
import numpy as np
import _scene
import materials.tile.tile_layout as tile_layout

RES, SIZE = 400, 1.0                       # 400 px over 1 m: 2.5 mm per px
CASES = {
    "jitter": dict(tile_w=0.0375, tile_h=0.25, joint=0.004,
                   jitter_offset=0.0004, jitter_rotation=0.0044),
    "stack":   dict(tile_w=0.10, tile_h=0.05, joint=0.01),
    "rounded": dict(tile_w=0.10, tile_h=0.05, joint=0.01, corner_radius=0.012),
    "running": dict(tile_w=0.10, tile_h=0.05, joint=0.01, row_offset=0.5),
    "rotated": dict(tile_w=0.145, tile_h=0.045, joint=0.008, rotation=0.5236, origin=(0.013, -0.02)),
}
OUTS = ("Edge", "Joint", "Tile UV", "Tile ID")

def plane_with(output, params, RES=RES, SIZE=SIZE):
    """Render one layout output on the requested metre-sized plane."""
    sc = _scene.black_scene(samples=1, res=RES)
    sc.cycles.filter_width = 0.01
    bpy.ops.mesh.primitive_plane_add(size=SIZE)
    ob = bpy.context.object
    m = bpy.data.materials.new("probe"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grp = tile_layout.add_layout(nt, tc.outputs["Object"], **params)
    em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    src = grp.outputs[output]
    if output == "Edge":                      # map metres to a visible, positive range
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"
        mul.inputs[1].default_value, mul.inputs[2].default_value = 10.0, 0.5
        nt.links.new(src, mul.inputs[0]); src = mul.outputs[0]
    nt.links.new(src, em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
    ob.data.materials.append(m)
    _scene.ortho_camera(1.0, SIZE)
    return _scene.render_linear()

def pixel_coords(RES=RES, SIZE=SIZE):
    """Return pixel-centre metre coordinates in the emission probe plane."""
    c = (np.arange(RES) + 0.5) / RES * SIZE - SIZE / 2
    return np.meshgrid(c, c)

def stable(mask):                             # pixels whose 3x3 neighbourhood shares the value
    """Retain pixels whose neighbouring samples all share the mask value."""
    m = mask.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            m &= np.roll(np.roll(mask, dy, 0), dx, 1)
    return m
