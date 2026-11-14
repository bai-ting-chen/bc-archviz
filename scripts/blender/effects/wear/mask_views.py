"""Edge masks as an emission view: one edge-detection method at a time, for side-by-side comparison
(pointiness, inside ambient occlusion, bevel normal, the GN edge distance, the chip mask, damage).
"""
import bpy

from materials.concrete import concrete as _mat_concrete
from materials.shared.node_graph import NodeGraph
from effects.wear.chipping import chip_exposed_mask


def mask_material(name, method, radius=0.035):
    """Emission view of one edge-detection method, for side-by-side comparison."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NodeGraph(mat)
    g.frame("mask", None)
    F = "mask"
    if method == "pointiness":
        geo = g.node("ShaderNodeNewGeometry", (-800, 0), F)
        val = g.map_range(geo.outputs["Pointiness"], 0.5, 0.56, (-500, 0), frame=F)
    elif method == "ao_inside":
        ao = g.node("ShaderNodeAmbientOcclusion", (-800, 0), F, Distance=radius)
        ao.inside, ao.only_local, ao.samples = True, True, 16
        val = g.map_range(ao.outputs["AO"], 1.0, 0.6, (-500, 0), frame=F)
    elif method == "bevel":
        val = _mat_concrete._edge_mask(g, radius, (-500, 0), F, "bevel")
    elif method == "edge_dist":
        val = g.map_range(g.attribute("edge_dist", (-800, 0), F), 0.0, radius, (-500, 0), 1.0, 0.0, frame=F)
    elif method == "chip":
        val = chip_exposed_mask(g, 0.0003, frame=F)
    elif method == "damage":  # chips + breaks (wood)
        val = chip_exposed_mask(g, 0.0003, 0.00015, F, chip_mask_location=(-600, 0))
    em = g.node("ShaderNodeEmission", (-200, 0))
    g.link(val, em.inputs["Color"])
    o = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(em.outputs["Emission"], o.inputs["Surface"])
    return mat
