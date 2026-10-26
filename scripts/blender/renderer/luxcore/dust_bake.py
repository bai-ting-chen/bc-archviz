"""Dust bake; canonical implementation behind luxcore."""

import os, json

import bpy

import core.archviz as archviz

from renderer.luxcore.dust_config import DUST_PX

from renderer.luxcore.dust_shader import _dust_bake_material

from renderer.luxcore.dust_uv import _ctx, dust_uv

def bake_dust(objs, cache_dir, rebake=False, samples=64):
    """One dust mask per object into cache_dir/<object>.png (EMIT bake, GPU). Returns {name: path}."""
    os.makedirs(cache_dir, exist_ok=True)
    paths = {o.name: os.path.join(cache_dir, o.name + ".png") for o in objs}
    for o in objs: dust_uv(o)
    todo = [o for o in objs if rebake or not os.path.exists(paths[o.name])]
    if not todo: return paths
    sc = bpy.context.scene; eng = sc.render.engine
    sc.render.engine = "CYCLES"; sc.cycles.samples = samples; sc.cycles.use_denoising = False
    archviz.use_gpu(force=True)
    bm = _dust_bake_material(); tgt = bm.node_tree.nodes["target"]
    try:
        _bake_each(todo, bm, tgt, paths)
    finally:                                  # every object bakes under Cycles; engine back once
        sc.render.engine = eng
    return paths

def _bake_each(todo, bm, tgt, paths):
    for o in todo:
        img = bpy.data.images.new("dust_" + o.name, DUST_PX, DUST_PX, float_buffer=False, is_data=True)
        tgt.image = img
        saved = [s.material for s in o.material_slots]
        added = not o.material_slots          # an object without slots would bake nothing
        if added: o.data.materials.append(bm)
        for s in o.material_slots: s.material = bm
        me = o.data; keep = me.uv_layers.active.name; me.uv_layers.active = me.uv_layers["DustUV"]
        try:
            for x in bpy.context.view_layer.objects: x.select_set(False)
            bpy.context.view_layer.objects.active = o; o.select_set(True)
            with _ctx(o): bpy.ops.object.bake(type="EMIT", margin=8, use_clear=True)
            img.filepath_raw = paths[o.name]; img.file_format = "PNG"; img.save()
        finally:                              # a failed bake must not leave the scene on DustBake
            me.uv_layers.active = me.uv_layers[keep]
            if added: o.data.materials.clear()
            for s, mat in zip(o.material_slots, saved): s.material = mat
