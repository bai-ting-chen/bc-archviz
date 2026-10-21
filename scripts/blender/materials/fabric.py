"""Fabric material helpers; canonical implementations."""
import bpy


def sheer(name="CURTAIN_SHEER", color=(0.80, 0.78, 0.75), translucency=0.5):
    """Sheer curtain: Mix(Diffuse, Translucent) — a lit room behind glows through it."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    d = N.new("ShaderNodeBsdfDiffuse"); d.inputs["Color"].default_value = (*color, 1)
    t = N.new("ShaderNodeBsdfTranslucent"); t.inputs["Color"].default_value = (*color, 1)
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = translucency
    o = N.new("ShaderNodeOutputMaterial")
    L.new(d.outputs[0], mx.inputs[1]); L.new(t.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], o.inputs[0])
    return m
