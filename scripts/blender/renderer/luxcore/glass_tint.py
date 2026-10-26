"""Glass tint; canonical implementation behind luxcore."""

import bpy

def glass_instance_tint(name="Glass_rand", tint=(0.985, 0.996, 0.99), ior=1.52):
    """Clear glass; Object Info Random mixes white -> `tint` per instance (per face crossed, so a
    hollow block's 4 faces give ~tint^4)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    info = N("ShaderNodeObjectInfo"); mix = N("ShaderNodeMixRGB"); mix.blend_type = "MIX"
    mix.inputs["Color1"].default_value = (1, 1, 1, 1); mix.inputs["Color2"].default_value = (*tint, 1)
    g = N("ShaderNodeBsdfGlass"); g.inputs["IOR"].default_value = ior; g.inputs["Roughness"].default_value = 0
    o = N("ShaderNodeOutputMaterial")
    L(info.outputs["Random"], mix.inputs["Fac"]); L(mix.outputs["Color"], g.inputs["Color"]); L(g.outputs[0], o.inputs["Surface"])
    m.luxcore.use_cycles_nodes = True
    return m
