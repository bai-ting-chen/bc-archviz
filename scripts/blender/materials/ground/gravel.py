"""Gravel; canonical implementation behind ground."""

import bpy

from materials.shared.node_graph import NodeGraph, active_socket

from materials.shared.pbr_maps import _ph_maps, box_maps

def displaced_ground(name="GRAVEL", tex_id="gray_rocks", relief_m=0.12, shift_m=-0.049):
    """Gravel ground with true displacement.
    Displacement: Scale = relief_m, Midlevel = -shift_m / relief_m."""
    maps, meta = _ph_maps(tex_id)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = NodeGraph(mat)
    g.frame("Maps (BoxUV)", (0.20, 0.24, 0.30))
    g.frame("Displacement (GeomDisplacedMesh, 2D)", (0.30, 0.25, 0.18))
    F_MAP, F_DISP = list(g.frames)
    m = box_maps(g, maps, F_MAP, (-1300, 0), height_frame=F_DISP)
    diff, hgt, sep, nmap = m["diff"], m["hgt"], m["sep"], m["nmap"]
    bsdf = g.node("ShaderNodeBsdfPrincipled", (-400, 200))
    g.link(diff.outputs["Color"], bsdf.inputs["Base Color"])
    g.link(sep.outputs["Green"], bsdf.inputs["Roughness"])
    g.link(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    disp = g.node("ShaderNodeDisplacement", (-700, -600), F_DISP,
                  Midlevel=-shift_m / relief_m, Scale=relief_m)
    g.link(hgt.outputs["Color"], disp.inputs["Height"])
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    g.link(disp.outputs["Displacement"], out.inputs["Displacement"])
    mat.displacement_method = "BOTH"  # true displacement + bump for sub-dice detail
    return mat
