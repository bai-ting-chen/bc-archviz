"""Metal material helpers; canonical implementations."""
import bpy
from materials.shared.nodes import G


def polished_steel(name="STEEL_POLISHED", color=(0.67, 0.64, 0.60), edge=(0.80, 0.80, 0.80), roughness=0.05):
    """Mirror-polished stainless (physicallybased.info 0.67/0.64/0.60 linear). Metallic BSDF with
    F82 tint -- the edge colour of the conductor Fresnel."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    m = g.node("ShaderNodeBsdfMetallic", (-200, 0), label="stainless F82", Roughness=roughness)
    m.fresnel_type = "F82"
    m.inputs["Base Color"].default_value = (*color, 1)
    m.inputs["Edge Tint"].default_value = (*edge, 1)
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(m.outputs["BSDF"], out.inputs["Surface"])
    return mat
