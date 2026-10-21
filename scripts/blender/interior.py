"""Night-interior recipes: artificial lights in real lumens, polished
stone, stone tiles, steel, pool water with depth tint, steam.

Photometry follows archviz.LM_PER_W (683 lm per Blender W), the same constant the physical camera
uses, so light power and exposure stay consistent. Measured in Cycles 5.2 (scripts/controls/light_units.py):
  * point / spot: power is for the FULL sphere; the spot cone only masks it
    -> a fixture putting F lm into a cone of full angle a needs P = F/683 * 4pi / (2pi(1 - cos a/2)).
  * area: Lambert emitter, P = total emitted flux (E on axis = P / (pi d^2)); `spread` focuses it.
  * IES: Cycles uses 177.83 lm/W internally -> point light power 177.83/683 (ies_light, IES_POWER).
"""
import math
import os

import bpy

from archviz import LM_PER_W
from materials.nodes import G
from materials.nodes import sock

# --- lights ---------------------------------------------------------------------------------


def _light_obj(name, kind, loc, rot=(0.0, 0.0, 0.0), coll=None):
    ob = bpy.data.objects.get(name)
    if ob is not None and ob.type != "LIGHT":
        raise ValueError(f"'{name}' is a {ob.type} object (e.g. imported from Rhino): give the light another name")
    ld = ob.data if ob is not None else (bpy.data.lights.get(name) or bpy.data.lights.new(name, kind))
    if ld.type != kind:
        ld.type = kind                        # re-run with another kind: switch, keep the datablock
        ld = bpy.data.lights[ld.name]         # re-fetch: the old handle keeps the old subclass
    ob = ob or bpy.data.objects.new(name, ld)
    coll = coll or bpy.context.scene.collection
    if ob.name not in coll.objects:
        coll.objects.link(ob)
    ob.location, ob.rotation_euler = loc, rot
    return ob, ld


def _warm(ld, kelvin):
    ld.color = (1.0, 1.0, 1.0)
    ld.use_temperature, ld.temperature = True, kelvin


def downlight(name, loc, lumens=800.0, beam_deg=24.0, kelvin=3000, radius=0.02, blend=0.3, coll=None):
    """Recessed spot pointing straight down. `lumens` = flux inside the beam."""
    ob, ld = _light_obj(name, "SPOT", loc, coll=coll)
    a = math.radians(beam_deg)
    omega = 2 * math.pi * (1 - math.cos(a / 2))
    ld.energy = lumens / LM_PER_W * 4 * math.pi / omega
    ld.spot_size, ld.spot_blend, ld.shadow_soft_size = a, blend, radius
    _warm(ld, kelvin)
    return ob


def led_strip(name, p0, p1, lm_per_m=1000.0, kelvin=2700, width=0.012, normal=(0, 0, -1),
              spread_deg=120.0, coll=None):
    """Linear LED (cove) as a thin rectangular area light from p0 to p1 facing `normal`."""
    from mathutils import Matrix, Vector
    p0, p1, n = Vector(p0), Vector(p1), Vector(normal).normalized()
    length = (p1 - p0).length
    x = (p1 - p0).normalized()
    n = (n - x * n.dot(x)).normalized()                       # aim orthogonal to the strip
    y = (-n).cross(x).normalized()
    m = Matrix((x, y, -n)).transposed()                       # local X along strip, emits along local -Z
    ob, ld = _light_obj(name, "AREA", (p0 + p1) / 2, m.to_euler(), coll=coll)
    ld.shape, ld.size, ld.size_y = "RECTANGLE", length, width
    ld.energy = lm_per_m * length / LM_PER_W
    ld.spread = math.radians(spread_deg)
    _warm(ld, kelvin)
    return ob


def panel_light(name, loc, rot, size=(0.2, 0.2), lumens=500.0, kelvin=3000, spread_deg=180.0, coll=None):
    """Rectangular area light emitting `lumens` (Lambert, `spread_deg` like a louvre)."""
    ob, ld = _light_obj(name, "AREA", loc, rot, coll=coll)
    ld.shape, ld.size, ld.size_y = "RECTANGLE", size[0], size[1]
    ld.energy = lumens / LM_PER_W
    ld.spread = math.radians(spread_deg)
    _warm(ld, kelvin)
    return ob


# --- IES photometry (scripts/controls/ies_units.py) ---------------------------------------------
# Cycles converts the file's candela with 4pi/177.83 (D65 efficacy, intern/cycles/util/ies.cpp),
# including its multiplier and ballast factors, then multiplies by the light's power/(4pi). On a
# POINT or SPOT light, power 177.83/683 W therefore reproduces the file's candela in the 683 lm/W
# convention (measured 0.999). On an AREA light the profile multiplies a Lambert emitter: 4x on
# axis and cosine-weighted, so it is no longer the measured distribution -- use a point/spot.
# Orientation: nadir (V 0) = light -Z, C0 plane = light -Y, C90 = light -X.
IES_POWER = 177.83 / LM_PER_W


def ies_read(path):
    """Parse an LM-63 type C file. Returns header lumens, integrated luminaire lumens, peak cd,
    beam (50 % of peak) and field (10 %) full angles in degrees, and the [MANUFAC]/[LUMCAT] tags."""
    with open(path, errors="replace") as f:
        txt = f.read()
    head, _, rest = txt.partition("TILT=")
    tags = {}
    for line in head.splitlines():
        if line.startswith("[") and "]" in line:
            k, v = line[1:].split("]", 1)
            tags.setdefault(k.strip(), v.strip())
    tok = rest.split()
    tilt = tok.pop(0)
    if tilt == "INCLUDE":
        tok.pop(0); n = int(tok.pop(0)); del tok[:2 * n]
    nums = [float(t) for t in tok]
    lamps, lm_lamp, mult, nv, nh, ptype = nums[0], nums[1], nums[2], int(nums[3]), int(nums[4]), int(nums[5])
    ballast, blp = nums[10], nums[11]
    if ptype != 1:
        raise ValueError(f"{path}: photometric type {ptype}, only type C is handled")
    i = 13
    va, ha = nums[i:i + nv], nums[i + nv:i + nv + nh]
    i += nv + nh
    k = mult * ballast * blp
    cd = [[k * c for c in nums[i + h * nv:i + (h + 1) * nv]] for h in range(nh)]
    # flux = sum over C planes of  integral I(theta) sin(theta) dtheta, weighted by each plane's share of 2pi
    def plane_flux(row):
        return sum((row[j] * math.sin(math.radians(va[j])) + row[j + 1] * math.sin(math.radians(va[j + 1])))
                   / 2 * math.radians(va[j + 1] - va[j]) for j in range(nv - 1))
    if nh == 1:
        flux = 2 * math.pi * plane_flux(cd[0])
    else:
        span = ha[-1] - ha[0]
        flux = sum((plane_flux(cd[h]) + plane_flux(cd[h + 1])) / 2 * math.radians(ha[h + 1] - ha[h])
                   for h in range(nh - 1)) * 360.0 / span
    mean = [sum(cd[h][j] for h in range(nh)) / nh for j in range(nv)]   # plane-averaged profile
    peak = max(max(r) for r in cd)

    def cut(frac):
        for j in range(1, nv):
            if mean[j] < frac * mean[0] <= mean[j - 1]:
                t = (mean[j - 1] - frac * mean[0]) / (mean[j - 1] - mean[j])
                return 2 * (va[j - 1] + t * (va[j] - va[j - 1]))
        return None
    return {"lumens_header": lamps * lm_lamp if lm_lamp > 0 else None, "absolute": lm_lamp < 0,
            "lumens": flux, "peak_cd": peak, "beam_deg": cut(0.5), "field_deg": cut(0.1),
            "manufacturer": tags.get("MANUFAC"), "catalog": tags.get("LUMCAT"),
            "luminaire": tags.get("LUMINAIRE"), "lamp": tags.get("LAMP")}


def ies_light(name, path, loc, rot=(0.0, 0.0, 0.0), lumens=None, kelvin=3000, radius=0.02,
              kind="POINT", coll=None):
    """A light with the manufacturer's measured distribution. Unscaled (`lumens=None`) it emits
    exactly the file's candela; `lumens` rescales it to another lumen package or a dimmed level.
    The file is embedded (Internal mode) so the .blend stays self-contained. Aim with `rot`: the
    profile's nadir is the light's -Z, C0 its -Y, a linear fixture's length its -X. `radius` sets the
    shadow/highlight softness of the emitting lens; place `loc` at least radius + 2 mm from any
    surface -- the part of the sphere inside a ceiling or housing is shadowed (0.57x measured)."""
    info = ies_read(path)
    ob, ld = _light_obj(name, kind, loc, rot, coll=coll)
    ld.shadow_soft_size = radius
    if kind == "SPOT":
        ld.spot_size, ld.spot_blend = math.pi, 0.0        # cone off: the profile shapes the beam
    ld.energy = IES_POWER * (lumens / info["lumens"] if lumens else 1.0)
    _warm(ld, kelvin)
    ld.use_nodes = True
    nt = ld.node_tree
    em = next(n for n in nt.nodes if n.type == "EMISSION")
    ies = next((n for n in nt.nodes if n.type == "TEX_IES"), None) or nt.nodes.new("ShaderNodeTexIES")
    txt_name = "IES_" + os.path.basename(path)
    txt = bpy.data.texts.get(txt_name) or bpy.data.texts.new(txt_name)
    with open(path, errors="replace") as f:
        txt.from_string(f.read())
    ies.mode, ies.ies = "INTERNAL", txt
    ies.location = (em.location.x - 250, em.location.y)
    nt.links.new(ies.outputs["Fac"], em.inputs["Strength"])
    ob["ies_file"], ob["ies_lumens"] = os.path.basename(path), round(lumens or info["lumens"], 1)
    return ob


def lens_luminance(lumens, area_m2):
    """Luminance of a Lambertian lens of area A emitting `lumens` into its half-space: L = F / (pi A)."""
    return lumens / (math.pi * area_m2)


def lit_once(objs):
    """Decorative lenses whose flux is carried by an analytic light: keep them visible to the camera
    and in reflections, but out of diffuse AND transmission paths -- a diffuse bounce that then
    passes through water continues as a transmission ray and would see the lens again."""
    for o in objs:
        o.visible_diffuse = False
        o.visible_transmission = False


def emitter(name, luminance_cd, kelvin=3000, color=None):
    """Visible light source surface (LED lens, lit panel) with a luminance in cd/m2.
    Cycles emission strength S is radiance in W/m2/sr, so S = L / 683."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    em = g.node("ShaderNodeEmission", (-200, 0), label="%d cd/m2" % luminance_cd,
                Strength=luminance_cd / LM_PER_W)
    if color:
        em.inputs["Color"].default_value = (*color, 1)
    else:
        bb = g.node("ShaderNodeBlackbody", (-400, 0), label="%d K" % kelvin, Temperature=kelvin)
        g.link(bb.outputs["Color"], em.inputs["Color"])
    out = g.node("ShaderNodeOutputMaterial", (0, 0))
    g.link(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def emitter_dots(name, luminance_cd, n=4, radius=0.22, kelvin=3000, housing=(0.02, 0.02, 0.02)):
    """Multi-head downlight face: n round LED lenses along the object's long (generated X) axis,
    black housing around them. Generated coords span 0..1 over the box."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    tc = g.node("ShaderNodeTexCoord", (-1100, 0))
    sep = g.node("ShaderNodeSeparateXYZ", (-900, 0))
    g.link(tc.outputs["Generated"], sep.inputs["Vector"])
    cell = g.node("ShaderNodeMath", (-700, 100), label="cell x")
    cell.operation, cell.inputs[1].default_value = "MULTIPLY", float(n)
    g.link(sep.outputs["X"], cell.inputs[0])
    fr = g.node("ShaderNodeMath", (-550, 100))
    fr.operation = "FRACT"
    g.link(cell.outputs[0], fr.inputs[0])
    comb = g.node("ShaderNodeCombineXYZ", (-400, 0))
    g.link(fr.outputs[0], comb.inputs["X"])
    g.link(sep.outputs["Y"], comb.inputs["Y"])
    d = g.node("ShaderNodeVectorMath", (-250, 0), label="distance to lens centre")
    d.operation = "DISTANCE"
    d.inputs[1].default_value = (0.5, 0.5, 0.0)
    g.link(comb.outputs["Vector"], d.inputs[0])
    m = g.node("ShaderNodeMath", (-100, 0), label="lens mask")
    m.operation, m.inputs[1].default_value = "LESS_THAN", radius
    g.link(d.outputs["Value"], m.inputs[0])
    em = g.node("ShaderNodeEmission", (50, 150), label="%d cd/m2" % luminance_cd, Strength=luminance_cd / LM_PER_W)
    bb = g.node("ShaderNodeBlackbody", (-100, 250), Temperature=kelvin)
    g.link(bb.outputs["Color"], em.inputs["Color"])
    hb = g.node("ShaderNodeBsdfPrincipled", (50, -200), label="housing", Roughness=0.4)
    hb.inputs["Base Color"].default_value = (*housing, 1)
    mix = g.node("ShaderNodeMixShader", (300, 0))
    g.link(m.outputs[0], mix.inputs["Fac"])
    g.link(hb.outputs["BSDF"], mix.inputs[1])
    g.link(em.outputs["Emission"], mix.inputs[2])
    out = g.node("ShaderNodeOutputMaterial", (500, 0))
    g.link(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


# --- materials ------------------------------------------------------------------------------
