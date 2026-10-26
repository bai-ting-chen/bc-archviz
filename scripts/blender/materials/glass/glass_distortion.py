"""Glass distortion; canonical implementation behind glass."""

from materials.shared.dielectric import dielectric
from materials.shared.principled import _principled

def glass_distortion(mat, obj, wave_period=0.30, wave_amp_mm=0.05, pillow_mm=2.0, roughness=0.01):
    """Bump on a dielectric so reflections wobble like real glazing: roller wave (~0.1 mm p-v over ~0.3 m) + pane bow (pillowing, a few mm) centred on `obj`'s bounding box; thin axis has no dome."""
    import math

    from materials.shared.nodes import G
    # dome over the pane in its own Generated coordinates (0..1 over the local bounding box, so it
    # follows any rotation/position and works on every pane sharing the material); the thinnest
    # local axis is the glass thickness - masked out
    dims = obj.dimensions
    thin = min(range(3), key=lambda i: dims[i])
    mask = [0.0 if i == thin else 2.0 for i in range(3)]
    nt = mat.node_tree
    p = _principled(mat)
    p.inputs["Roughness"].default_value = roughness
    g = G(nt)
    geo = g.node("ShaderNodeNewGeometry", (-900, -300))
    sp = g.node("ShaderNodeSeparateXYZ", (-750, -300)); g.link(geo.outputs["Position"], sp.inputs[0])
    warp = g.noise(geo.outputs["Position"], 0.8, (-750, -550), detail=2)
    ph = g.math("MULTIPLY", g.math("ADD", sp.outputs["Z"], g.math("MULTIPLY", warp, 0.15, (-600, -550)), (-500, -400)),
                2 * math.pi / wave_period, (-350, -400))
    h = g.math("ADD", g.math("SINE", ph, 0.0, (-200, -400)),
               g.math("MULTIPLY", g.noise(geo.outputs["Position"], 2.5, (-350, -650), detail=3), 1.2, (-200, -650)), (-50, -500))
    tc = g.node("ShaderNodeTexCoord", (-900, -850))
    rel = g.n("ShaderNodeVectorMath", (-750, -850), operation="SUBTRACT")
    g.link(tc.outputs["Generated"], rel.inputs[0]); rel.inputs[1].default_value = (0.5, 0.5, 0.5)
    nrm = g.n("ShaderNodeVectorMath", (-600, -850), operation="MULTIPLY")
    g.link(rel.outputs[0], nrm.inputs[0]); nrm.inputs[1].default_value = mask
    r2 = g.n("ShaderNodeVectorMath", (-450, -850), operation="DOT_PRODUCT")
    g.link(nrm.outputs[0], r2.inputs[0]); g.link(nrm.outputs[0], r2.inputs[1])
    dome = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, r2.outputs["Value"], (-300, -850)), pillow_mm / wave_amp_mm, (-150, -850))
    bump = g.node("ShaderNodeBump", (150, -400), label="roller wave + pillowing", Strength=1.0)
    bump.inputs["Distance"].default_value = wave_amp_mm * 1e-3
    g.link(g.math("ADD", h, dome, (0, -650)), bump.inputs["Height"])
    g.link(bump.outputs["Normal"], p.inputs["Normal"])
    return mat
