"""Weathering wall, emission rig and fixed review camera."""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import bpy
import core.archviz as archviz
from materials.shared.node_graph import NodeGraph

def scene():
    """Build the flat-wall lab and canonical graph builder."""
    sc = bpy.context.scene
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    W, H = 8.0, 4.0
    bpy.ops.mesh.primitive_plane_add(size=1); wall = bpy.context.object
    wall.scale = (W, H, 1); wall.rotation_euler = (1.5708, 0, 0); wall.location = (W / 2, 0, H / 2)
    m = bpy.data.materials.new('lab'); b = NodeGraph(m)   # canonical node builder (materials.shared.node_graph.NodeGraph)
    out = b.node('ShaderNodeOutputMaterial', (900, 0)); em = b.node('ShaderNodeEmission', (700, 0))
    b.link(em.outputs[0], out.inputs[0])
    pos = b.node('ShaderNodeNewGeometry', (-900, 0)).outputs['Position']   # world metres: x along wall, z up
    sep = b.node('ShaderNodeSeparateXYZ', (-700, 0)); b.link(pos, sep.inputs[0])
    return sc, W, H, wall, m, b, em, sep

def render(scene, wall_width_m, wall_height_m, output_dir, variant_name):
    """Render the lab with its original camera and settings."""
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = wall_width_m; cam.location = (wall_width_m / 2, -10, wall_height_m / 2); cam.rotation_euler = (1.5708, 0, 0)
    scene.render.resolution_x, scene.render.resolution_y = 1200, 600
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 4; archviz.use_gpu(); scene.cycles.device = 'GPU'
    scene.view_settings.view_transform = 'Standard'; scene.world = None
    scene.render.filepath = str(output_dir / f'lab_{variant_name}.png'); bpy.ops.render.render(write_still=True)
