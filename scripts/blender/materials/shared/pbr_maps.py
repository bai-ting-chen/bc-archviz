"""Pbr maps; canonical implementation behind pbr."""

import os

import bpy

def _img(nodes, path, colorspace, loc):
    n = nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(path, check_existing=True)
    n.image.colorspace_settings.name = colorspace
    n.projection = "BOX"  # world-space box mapping: no UVs needed on Rhino meshes
    n.projection_blend = 0.2
    n.location = loc
    return n

def _ph_maps(tex_id):
    import core.archviz as archviz
    from core.archviz import library, read_meta
    folder = library("polyhaven", "textures", tex_id)
    meta = read_meta(folder)
    return {k: os.path.join(folder, v) for k, v in meta["maps"].items()}, meta
