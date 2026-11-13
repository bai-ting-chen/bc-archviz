"""Shared rig for the tile damage probes: the scene, the packed EXR probe and the aligned tile grids.

Every probe builds only the observed UV-metre window (no unrelated geometry is diced); the EXR
packs up to three material sockets into one render so one render reads three quantities.
"""

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import controls_import_paths  # noqa: E402,F401 -- every controls topic folder on sys.path
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'blender'))
import core.archviz as archviz  # noqa: E402
import materials.tile.tile_surface as tile_surface  # noqa: E402

TILE_WIDTH_M, TILE_HEIGHT_M, JOINT_WIDTH_M, METRES_PER_PIXEL, TILE_COUNT = .0375, .25, .003, .00025, 3
GLAZE_THICKNESS_M, ENGOBE_THICKNESS_M = .0003, .0002
SOLO = tuple(f for f in tile_surface.FEATURES if f != 'damage')


def render(folder, label):
    """Save and read one linear, float RGB evidence render."""
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.render.filepath = str(folder / (label + '.exr'))
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(sc.render.filepath, check_existing=False)
    try:
        data = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(data)
        return data.reshape(image.size[1], image.size[0], 4)[..., :3].copy()
    finally:
        bpy.data.images.remove(image)


def setup(width, height, nx, ny, origin=(0., 0.), **kwargs):
    """Build only the observed UV-metre window; no unrelated geometry is diced."""
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    archviz.use_gpu()            # --factory-startup alone renders on the CPU
    sc.cycles.samples = 1
    sc.cycles.use_denoising = sc.cycles.use_adaptive_sampling = False
    sc.cycles.seed = 17
    sc.cycles.filter_width = .01
    sc.render.resolution_x, sc.render.resolution_y = nx, ny
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'
    sc.world = bpy.data.worlds.new('ProbeWorld'); sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1
    x, y = origin
    mesh = bpy.data.meshes.new('ProbePlane')
    mesh.from_pydata([(x,y,0),(x+width,y,0),(x+width,y+height,0),(x,y+height,0)], [], [(0,1,2,3)])
    ob = bpy.data.objects.new('ProbePlane', mesh); sc.collection.objects.link(ob)
    uv = mesh.uv_layers.new(name='TileUV')
    for loop in mesh.loops:
        uv.data[loop.index].uv = mesh.vertices[loop.vertex_index].co[:2]
    base = dict(tile_w=TILE_WIDTH_M, tile_h=TILE_HEIGHT_M, joint=JOINT_WIDTH_M, corner_radius=0, jitter_offset=0,
                jitter_rotation_deg=0, damage=1, off=SOLO)
    base.update(kwargs)
    mat = tile_surface.tile_material('DamageControl', **base); mesh.materials.append(mat)
    cam = bpy.data.objects.new('ProbeCamera', bpy.data.cameras.new('ProbeCamera'))
    sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (x+width/2, y+height/2, 1)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(width, height)
    return sc, ob, mat


def tile_rig(**kw):
    """Three complete finger tiles at 0.25 mm per pixel."""
    return setup(TILE_COUNT*(TILE_WIDTH_M+JOINT_WIDTH_M), TILE_HEIGHT_M+JOINT_WIDTH_M, round(TILE_COUNT*(TILE_WIDTH_M+JOINT_WIDTH_M)/METRES_PER_PIXEL), round((TILE_HEIGHT_M+JOINT_WIDTH_M)/METRES_PER_PIXEL), **kw)


def probe_rgb(mat, folder, label, outputs, divisors=(1., 1., 1.)):
    """Pack three sockets into one EXR; signed heights/normals use a 0.5 offset."""
    tree = mat.node_tree
    target = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
    original = target.inputs['Surface'].links[0].from_socket
    created = []
    def node(kind):
        """Track probe-only nodes for guaranteed removal."""
        n = tree.nodes.new(kind); created.append(n); return n
    combine = node('ShaderNodeCombineXYZ')
    offsets = []
    for index, (name, divisor) in enumerate(zip(outputs, divisors)):
        signed = name in ('Piece Height', 'World Z', 'Normal X', 'Normal Y', 'Normal Z', 'Total Height',
                          'Damage Height')
        offsets.append(.5 if signed else 0.)
        if name is None: continue
        if name == 'World Z' or name.startswith('Normal '):
            separate = node('ShaderNodeSeparateXYZ')
            source = (node('ShaderNodeNewGeometry').outputs['Position'] if name == 'World Z'
                      else tree.nodes['TileBump'].outputs['Normal'])
            tree.links.new(source, separate.inputs[0])
            socket = separate.outputs['Z' if name == 'World Z' else name[-1]]
        elif name == 'Total Height':
            socket = tree.nodes['TileTotalHeight'].outputs[0]
        elif name == 'Damage Height':
            socket = tree.nodes['TileDamageHeight'].outputs[0]
        elif name in ('UV X', 'UV Y'):
            separate = node('ShaderNodeSeparateXYZ')
            tree.links.new(tree.nodes['TileLayout'].outputs['Tile UV'], separate.inputs[0])
            socket = separate.outputs[name[-1]]
        else:
            socket = tree.nodes['TileDamage'].outputs[name]
        encode = node('ShaderNodeMath'); encode.operation = 'MULTIPLY_ADD'
        tree.links.new(socket, encode.inputs[0])
        encode.inputs[1].default_value = 1/divisor
        encode.inputs[2].default_value = offsets[-1]
        tree.links.new(encode.outputs[0], combine.inputs[index])
    emission = node('ShaderNodeEmission')
    tree.links.new(combine.outputs[0], emission.inputs['Color'])
    tree.links.new(emission.outputs[0], target.inputs['Surface'])
    try:
        return (render(folder, label)-np.array(offsets))*np.array(divisors)
    finally:
        tree.links.new(original, target.inputs['Surface'])
        for n in created: tree.nodes.remove(n)


def tiles(shape):
    """Yield face masks and metre coordinates for the three-tile topology rig."""
    Y, X = np.meshgrid((np.arange(shape[0])+.5)*METRES_PER_PIXEL, (np.arange(shape[1])+.5)*METRES_PER_PIXEL, indexing='ij')
    for index in range(TILE_COUNT):
        x0 = index*(TILE_WIDTH_M+JOINT_WIDTH_M)+JOINT_WIDTH_M/2
        yield index, (X>x0)&(X<x0+TILE_WIDTH_M)&(Y>JOINT_WIDTH_M/2)&(Y<JOINT_WIDTH_M/2+TILE_HEIGHT_M), x0, X, Y


def grid_rig(count,cols,**kw):
    """Observe complete 37.5 x 250 mm cells at 0.25 mm/px."""
    rows=math.ceil(count/cols)
    return setup(cols*(TILE_WIDTH_M+JOINT_WIDTH_M),rows*(TILE_HEIGHT_M+JOINT_WIDTH_M),round(cols*(TILE_WIDTH_M+JOINT_WIDTH_M)/METRES_PER_PIXEL),round(rows*(TILE_HEIGHT_M+JOINT_WIDTH_M)/METRES_PER_PIXEL),**kw)


def grid_faces(data,count,cols):
    """Extract aligned face arrays; joints remain outside every face slice."""
    for index in range(count):
        col,row=index%cols,index//cols
        x0=round((col*(TILE_WIDTH_M+JOINT_WIDTH_M)+JOINT_WIDTH_M/2)/METRES_PER_PIXEL); y0=round((row*(TILE_HEIGHT_M+JOINT_WIDTH_M)+JOINT_WIDTH_M/2)/METRES_PER_PIXEL)
        yield index,data[y0:y0+round(TILE_HEIGHT_M/METRES_PER_PIXEL),x0:x0+round(TILE_WIDTH_M/METRES_PER_PIXEL)],(col*(TILE_WIDTH_M+JOINT_WIDTH_M)+JOINT_WIDTH_M/2,row*(TILE_HEIGHT_M+JOINT_WIDTH_M)+JOINT_WIDTH_M/2)
