"""Photon shading; implementation for caustic_photons."""
import math
from effects.caustics.photon_grid import GRID, _load_grid


def add_caustic_light(mat, exr_path, scale=1.0, albedo_label="Pine + satin varnish coat"):
    """Adds Emission = albedo * E / pi on up-facing faces, E sampled at world XY from the map.
    `albedo_label`: label of the receiver's BSDF whose Base Color input carries the albedo (the
    default is materials.wood.wood.coated_wood's)."""
    import bpy
    from materials.shared.nodes import G
    from materials.shared.nodes import sock
    _load_grid(exr_path)
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    old_add = next((n for n in nt.nodes if n.label == "caustic map: surface + caustic"), None)
    if old_add is not None:                   # re-run: the surface is what the old Add received
        surf_src = old_add.inputs[0].links[0].from_socket
    else:
        surf_src = out.inputs["Surface"].links[0].from_socket
    for n in [n for n in nt.nodes if n.label.startswith("caustic map")]:
        nt.nodes.remove(n)
    albedo_src = next(n for n in nt.nodes if n.label == albedo_label).inputs["Base Color"].links[0].from_socket
    g = G(nt, clear=False)
    N = lambda kind, loc, label: g.node(kind, loc, label="caustic map: " + label)
    geo = N("ShaderNodeNewGeometry", (-400, -1600), "position")
    mp = N("ShaderNodeMapping", (-200, -1600), "world XY -> map UV")
    mp.inputs["Location"].default_value = (-GRID["x0"] / GRID["size"], -GRID["y0"] / GRID["size"], 0)
    mp.inputs["Scale"].default_value = (1 / GRID["size"], 1 / GRID["size"], 1)
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    tex = N("ShaderNodeTexImage", (0, -1600), "irradiance W/m2")
    tex.image = bpy.data.images.load(exr_path, check_existing=True)
    tex.image.colorspace_settings.name = "Non-Color"
    tex.extension, tex.interpolation = "CLIP", "Cubic"
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    up = N("ShaderNodeSeparateXYZ", (0, -1850), "normal z")
    nt.links.new(geo.outputs["Normal"], up.inputs["Vector"])
    upm = N("ShaderNodeMapRange", (200, -1850), "up-facing only")
    upm.inputs["From Min"].default_value, upm.inputs["From Max"].default_value = 0.85, 0.95
    nt.links.new(up.outputs["Z"], upm.inputs["Value"])
    rad = N("ShaderNodeMath", (250, -1600), "E / pi x scale")
    rad.operation = "MULTIPLY"
    rad.inputs[1].default_value = scale / math.pi
    nt.links.new(tex.outputs["Color"], rad.inputs[0])
    m2 = N("ShaderNodeMath", (420, -1700), "on top only")
    m2.operation = "MULTIPLY"
    nt.links.new(rad.outputs[0], m2.inputs[0])
    nt.links.new(upm.outputs["Result"], m2.inputs[1])
    col = N("ShaderNodeMix", (600, -1550), "albedo x E/pi")
    col.data_type, col.blend_type = "RGBA", "MULTIPLY"
    col.inputs["Factor"].default_value = 1.0
    nt.links.new(albedo_src, sock(col.inputs, "A"))
    em = N("ShaderNodeEmission", (800, -1550), "reflected caustic light")
    nt.links.new(sock(col.outputs, "Result"), em.inputs["Color"])
    nt.links.new(m2.outputs[0], em.inputs["Strength"])
    # the Mix colour's B is driven by a grey value = 1 (albedo * 1), strength carries E/pi
    sock(col.inputs, "B").default_value = (1, 1, 1, 1)
    add = N("ShaderNodeAddShader", (1000, -300), "surface + caustic")
    nt.links.new(surf_src, add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    return mat
