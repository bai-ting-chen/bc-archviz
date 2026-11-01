"""Bake the shared cross-object corner masks into R=line, G=dust, B=0."""
import bpy
from effects.edge_dirt import corner_dirt_masks
from materials.shared.nodes import G


def _dust_bake_material():
    mat = bpy.data.materials.get('DustBake') or bpy.data.materials.new('DustBake')
    g = G(mat)
    line, dust = corner_dirt_masks(g)
    packed = g.combine(line, dust, 0.0, (1000, 0))
    em = g.node('ShaderNodeEmission', (1200, 0), label='R line / G dust')
    out = g.node('ShaderNodeOutputMaterial', (1400, 0))
    g.link(packed, em.inputs['Color'])
    g.link(em.outputs[0], out.inputs['Surface'])
    target = g.node('ShaderNodeTexImage', (1200, -300))
    target.name = 'target'
    g.nt.nodes.active = target
    return mat
