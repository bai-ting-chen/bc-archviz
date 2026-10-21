"""Variation material helpers; canonical implementations."""
import bpy


def random_tone_material(name, c0, c1, roughness=0.6, translucent=0.0):
    """Base colour between c0 and c1 per instance (Object Info > Random); optional translucency
    for leaves."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    oi = N.new("ShaderNodeObjectInfo"); ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c0, 1); ramp.color_ramp.elements[1].color = (*c1, 1)
    L.new(oi.outputs["Random"], ramp.inputs[0])
    b = N.new("ShaderNodeBsdfPrincipled"); b.inputs["Roughness"].default_value = roughness
    L.new(ramp.outputs[0], b.inputs["Base Color"])
    o = N.new("ShaderNodeOutputMaterial")
    if translucent:
        t = N.new("ShaderNodeBsdfTranslucent"); L.new(ramp.outputs[0], t.inputs[0])
        mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = translucent
        L.new(b.outputs[0], mx.inputs[1]); L.new(t.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], o.inputs[0])
    else:
        L.new(b.outputs[0], o.inputs[0])
    return m
