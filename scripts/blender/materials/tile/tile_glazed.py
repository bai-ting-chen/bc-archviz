"""Procedural glazed ceramic tiles (Poly Haven has no pool mosaic).

A Brick Texture with zero offset gives a square grid at real size (UVs in metres), with per-tile
colour variation, a glossy glaze, rough grout, and rounded tile edges as bump from the mortar mask.
Separate from the layered tile_material builder: this one is a single flat material.
"""
import bpy

from materials.shared.nodes import G


def glazed_tiles(name="POOL_TILES", tile=0.10, grout=0.003, glaze=(0.60, 0.79, 0.83),
                 glaze_var=0.06, grout_col=(0.50, 0.51, 0.50), uv="BoxUV"):
    """Procedural glazed ceramic tiles (Poly Haven has no pool mosaic): Brick Texture with zero
    offset = square grid at real size (UVs in metres), per-tile colour variation, glossy glaze,
    rough grout, rounded tile edges as bump from the mortar mask."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Tile grid (Brick Texture, offset 0)", (0.20, 0.24, 0.30))
    g.frame("Glaze / grout", (0.22, 0.28, 0.22))
    F_GRID, F_BRDF = list(g.frames)
    coords = g.uv(uv, (-1200, 0), F_GRID)
    br = g.node("ShaderNodeTexBrick", (-950, 0), F_GRID, label="tiles %d mm, grout %d mm" % (tile * 1000, grout * 1000),
                Scale=1.0)
    br.offset, br.squash = 0.0, 1.0
    br.inputs["Brick Width"].default_value = tile
    br.inputs["Row Height"].default_value = tile
    br.inputs["Mortar Size"].default_value = grout
    br.inputs["Mortar Smooth"].default_value = 0.35
    br.inputs["Bias"].default_value = 0.0
    lo = tuple(max(0.0, c - glaze_var) for c in glaze)
    br.inputs["Color1"].default_value = (*lo, 1)
    br.inputs["Color2"].default_value = (*glaze, 1)
    br.inputs["Mortar"].default_value = (*grout_col, 1)
    g.link(coords, br.inputs["Vector"])
    tile_b = g.node("ShaderNodeBsdfPrincipled", (-500, 200), F_BRDF, label="glaze", Roughness=0.05, IOR=1.52)
    g.link(br.outputs["Color"], tile_b.inputs["Base Color"])
    grout_b = g.node("ShaderNodeBsdfPrincipled", (-500, -200), F_BRDF, label="grout", Roughness=0.9)
    grout_b.inputs["Base Color"].default_value = (*grout_col, 1)
    bump = g.node("ShaderNodeBump", (-700, -400), F_BRDF, label="rounded tile edges", Distance=0.0015)
    inv = g.node("ShaderNodeMath", (-850, -400), F_BRDF)
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    g.link(br.outputs["Fac"], inv.inputs[1])
    g.link(inv.outputs[0], bump.inputs["Height"])
    g.link(bump.outputs["Normal"], tile_b.inputs["Normal"])
    g.link(bump.outputs["Normal"], grout_b.inputs["Normal"])
    mix = g.node("ShaderNodeMixShader", (-200, 0), F_BRDF, label="grout where mortar")
    g.link(br.outputs["Fac"], mix.inputs["Fac"])
    g.link(tile_b.outputs["BSDF"], mix.inputs[1])
    g.link(grout_b.outputs["BSDF"], mix.inputs[2])
    out = g.node("ShaderNodeOutputMaterial", (100, 0))
    g.link(mix.outputs["Shader"], out.inputs["Surface"])
    return mat
