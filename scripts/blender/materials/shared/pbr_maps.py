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
    from core.archviz import library, read_meta
    folder = library("polyhaven", "textures", tex_id)
    meta = read_meta(folder)
    return {k: os.path.join(folder, v) for k, v in meta["maps"].items()}, meta


def box_maps(graph, maps, frame, origin, arm_label="arm", normal_frame=None, normal_strength=1.0,
             height_frame=None):
    """BoxUV, the Poly Haven diffuse / arm / normal images (and height when height_frame is given),
    Separate Color on arm and a Normal Map on BoxUV. Returns the nodes by key:
    uv (socket), diff, arm, nor, hgt, sep, nmap."""
    x, y = origin
    uv = graph.uv_map("BoxUV", (x, y), frame)
    nodes = {"uv": uv,
             "diff": graph.image_texture(maps["diff"], "sRGB", (x + 250, y + 300), frame, uv, "diffuse"),
             "arm": graph.image_texture(maps["arm"], "Non-Color", (x + 250, y), frame, uv, arm_label),
             "nor": graph.image_texture(maps["nor_gl"], "Non-Color", (x + 250, y - 300), frame, uv, "normal (GL)")}
    if height_frame is not None:
        nodes["hgt"] = graph.image_texture(maps["disp"], "Non-Color", (x + 250, y - 600), height_frame, uv, "height")
    sep = graph.node("ShaderNodeSeparateColor", (x + 550, y), frame)
    graph.link(nodes["arm"].outputs["Color"], sep.inputs["Color"])
    nmap = graph.node("ShaderNodeNormalMap", (x + 550, y - 300), normal_frame or frame, Strength=normal_strength)
    nmap.uv_map = "BoxUV"
    graph.link(nodes["nor"].outputs["Color"], nmap.inputs["Color"])
    nodes.update(sep=sep, nmap=nmap)
    return nodes
