"""Night-interior recipes: artificial lights in real lumens, polished
stone, stone tiles, steel, pool water with depth tint, steam.

Photometry follows archviz.LM_PER_W (683 lm per Blender W), the same constant the physical camera
uses, so light power and exposure stay consistent. Measured in Cycles 5.2 (_wip/light_units_test.py):
  * point / spot: power is for the FULL sphere; the spot cone only masks it
    -> a fixture putting F lm into a cone of full angle a needs P = F/683 * 4pi / (2pi(1 - cos a/2)).
  * area: Lambert emitter, P = total emitted flux (E on axis = P / (pi d^2)); `spread` focuses it.
"""
import math

import bpy

from archviz import LM_PER_W
from study_materials import G, sock

# --- lights ---------------------------------------------------------------------------------


def _light_obj(name, kind, loc, rot=(0.0, 0.0, 0.0), coll=None):
    ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, kind)
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, ld)
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
    ob, ld = _light_obj(name, "AREA", loc, rot, coll=coll)
    ld.shape, ld.size, ld.size_y = "RECTANGLE", size[0], size[1]
    ld.energy = lumens / LM_PER_W
    ld.spread = math.radians(spread_deg)
    _warm(ld, kelvin)
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


def _ramp(g, loc, frame, stops, label=None, interp="LINEAR"):
    r = g.node("ShaderNodeValToRGB", loc, frame, label)
    cr = r.color_ramp
    cr.interpolation = interp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    for pos, col in stops[1:]:
        e = cr.elements.new(pos)
        e.color = (*col, 1)
    return r


def polished_granite(name="GRANITE_POLISHED", grain_m=0.006, roughness=0.04, ior=1.55,
                     base=((0.010, 0.008, 0.007), (0.026, 0.019, 0.015)),
                     flecks=((0.62, (0.055, 0.037, 0.026)), (0.80, (0.13, 0.12, 0.11)),
                             (0.91, (0.34, 0.28, 0.21)))):
    """Procedural speckled granite in 3-D world space (a solid texture: cut faces and edges agree).
    Crystals = Voronoi cells of ~grain_m, each coloured by its random value through a constant
    ramp (black mica / brown feldspar / grey quartz / cream feldspar); a coarse noise drifts the
    base. Polished = one smooth dielectric (no coat). No Bevel node: the pool lining is a caustic
    receiver -- round edges come from a geometric Bevel modifier instead."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Crystals (Voronoi, world space)", (0.22, 0.20, 0.18))
    g.frame("Polish", (0.20, 0.24, 0.30))
    F_C, F_P = list(g.frames)
    pos = g.node("ShaderNodeNewGeometry", (-1500, 0), F_C).outputs["Position"]
    warp = g.node("ShaderNodeTexNoise", (-1300, -250), F_C, label="crystal shape warp",
                  Scale=1.0 / (grain_m * 2.5), Detail=2.0)
    g.link(pos, warp.inputs["Vector"])
    vadd = g.node("ShaderNodeVectorMath", (-1100, 0), F_C, label="warped position")
    vadd.operation = "MULTIPLY_ADD"
    vadd.inputs[1].default_value = (grain_m * 0.6,) * 3
    g.link(warp.outputs["Color"], vadd.inputs[0])
    g.link(pos, vadd.inputs[2])
    vor = g.node("ShaderNodeTexVoronoi", (-900, 100), F_C, label="crystals %.0f mm" % (grain_m * 1000),
                 Scale=1.0 / grain_m, Randomness=1.0)
    g.link(vadd.outputs["Vector"], vor.inputs["Vector"])
    stops = [(0.0, base[0])] + list(flecks)
    cr = _ramp(g, (-650, 150), F_C, stops, "mineral palette", interp="CONSTANT")
    sepv = g.node("ShaderNodeSeparateColor", (-780, 150), F_C)
    g.link(vor.outputs["Color"], sepv.inputs["Color"])
    g.link(sepv.outputs["Red"], cr.inputs["Fac"])
    drift = g.node("ShaderNodeTexNoise", (-900, -250), F_C, label="base drift", Scale=3.0, Detail=6.0)
    g.link(vadd.outputs["Vector"], drift.inputs["Vector"])
    dr = _ramp(g, (-650, -200), F_C, [(0.35, base[0]), (0.65, base[1])], "dark matrix")
    g.link(drift.outputs["Fac"], dr.inputs["Fac"])
    is_matrix = g.node("ShaderNodeMath", (-450, -50), F_C, label="cell is matrix")
    is_matrix.operation = "LESS_THAN"
    is_matrix.inputs[1].default_value = flecks[0][0]
    g.link(sepv.outputs["Red"], is_matrix.inputs[0])
    col = g.node("ShaderNodeMix", (-250, 100), F_C, label="matrix vs crystal")
    col.data_type = "RGBA"
    g.link(is_matrix.outputs[0], col.inputs["Factor"])
    g.link(cr.outputs["Color"], sock(col.inputs, "A"))
    g.link(dr.outputs["Color"], sock(col.inputs, "B"))
    rnoise = g.node("ShaderNodeTexNoise", (-650, -500), F_P, label="polish variation", Scale=1.5, Detail=3)
    g.link(vadd.outputs["Vector"], rnoise.inputs["Vector"])
    rr = g.node("ShaderNodeMapRange", (-400, -450), F_P, label="roughness %.2f +-0.02" % roughness)
    rr.inputs["To Min"].default_value = max(0.0, roughness - 0.02)
    rr.inputs["To Max"].default_value = roughness + 0.02
    g.link(rnoise.outputs["Fac"], rr.inputs["Value"])
    b = g.node("ShaderNodeBsdfPrincipled", (0, 0), F_P, label="polished granite", IOR=ior)
    g.link(sock(col.outputs, "Result"), b.inputs["Base Color"])
    g.link(rr.outputs["Result"], b.inputs["Roughness"])
    out = g.node("ShaderNodeOutputMaterial", (300, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


def stone_tiles(name="LIMESTONE", tile=(1.2, 0.6), grout=0.002, albedo=(0.46, 0.41, 0.33),
                var=0.05, roughness=0.35, coat=0.0, coat_rough=0.08, uv="BoxUV"):
    """Large-format stone/porcelain on real-metre BoxUV: Brick Texture (offset 0) for the joints,
    per-tile tone from the brick colour pair, cloudy limestone mottling + fine specks, a soft coat
    for a honed-and-sealed floor. Grout darker and matte, joints slightly recessed (bump)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Tiles %.1f x %.1f m" % tile, (0.20, 0.24, 0.30))
    g.frame("Stone body", (0.26, 0.24, 0.20))
    g.frame("Finish", (0.22, 0.28, 0.22))
    F_T, F_S, F_F = list(g.frames)
    co = g.uv(uv, (-1500, 0), F_T)
    br = g.node("ShaderNodeTexBrick", (-1250, 0), F_T, Scale=1.0)
    br.offset, br.squash = 0.0, 1.0
    br.inputs["Brick Width"].default_value, br.inputs["Row Height"].default_value = tile
    br.inputs["Mortar Size"].default_value, br.inputs["Mortar Smooth"].default_value = grout, 0.2
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (1 - var, 1 - var, 1 - var, 1)
    br.inputs["Color2"].default_value = (1 + var, 1 + var, 1 + var, 1)
    br.inputs["Mortar"].default_value = (0.75, 0.75, 0.75, 1)
    g.link(co, br.inputs["Vector"])
    cloud = g.node("ShaderNodeTexNoise", (-1250, -350), F_S, label="cloudy body", Scale=2.5, Detail=8.0,
                   Roughness=0.6)
    g.link(co, cloud.inputs["Vector"])
    cr = _ramp(g, (-1000, -350), F_S, [(0.3, tuple(c * 0.90 for c in albedo)), (0.7, tuple(min(1, c * 1.08) for c in albedo))],
               "limestone tone")
    g.link(cloud.outputs["Fac"], cr.inputs["Fac"])
    speck = g.node("ShaderNodeTexVoronoi", (-1250, -650), F_S, label="fossil specks 3 mm", Scale=330.0)
    g.link(co, speck.inputs["Vector"])
    sp = g.node("ShaderNodeMapRange", (-1000, -650), F_S, label="speck mask")
    sp.inputs["From Min"].default_value, sp.inputs["From Max"].default_value = 0.0, 0.12
    sp.inputs["To Min"].default_value, sp.inputs["To Max"].default_value = 0.88, 1.0
    g.link(speck.outputs["Distance"], sp.inputs["Value"])
    m1 = g.node("ShaderNodeMix", (-750, -350), F_S, label="x specks")
    m1.data_type, m1.blend_type = "RGBA", "MULTIPLY"
    m1.inputs["Factor"].default_value = 1.0
    g.link(cr.outputs["Color"], sock(m1.inputs, "A"))
    g.link(sp.outputs["Result"], sock(m1.inputs, "B"))
    m2 = g.node("ShaderNodeMix", (-550, -150), F_S, label="x per-tile tone / grout")
    m2.data_type, m2.blend_type = "RGBA", "MULTIPLY"
    m2.inputs["Factor"].default_value = 1.0
    g.link(sock(m1.outputs, "Result"), sock(m2.inputs, "A"))
    g.link(br.outputs["Color"], sock(m2.inputs, "B"))
    rough = g.node("ShaderNodeMapRange", (-550, 250), F_F, label="grout matte")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = roughness, 0.85
    g.link(br.outputs["Fac"], rough.inputs["Value"])
    bump = g.node("ShaderNodeBump", (-550, 500), F_F, label="recessed joints", Distance=0.001)
    bump.invert = True
    g.link(br.outputs["Fac"], bump.inputs["Height"])
    b = g.node("ShaderNodeBsdfPrincipled", (-200, 0), F_F, label="stone", IOR=1.5)
    g.link(sock(m2.outputs, "Result"), b.inputs["Base Color"])
    g.link(rough.outputs["Result"], b.inputs["Roughness"])
    g.link(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rough
    out = g.node("ShaderNodeOutputMaterial", (100, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    return mat


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


def pool_water(name="POOL_WATER", tint=(0.45, 0.85, 0.72), density=1.0, ripple_scale=2.0,
               ripple_m=0.0015, ior=1.333):
    """Water as a closed volume: refractive surface (IOR 1.333) + Volume Absorption, so colour
    grows with path length (shallow steps stay clear, depth turns green). Absorption coefficient
    = density * (1 - tint) per metre. Gentle ripples as bump on the surface only."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    g.frame("Surface", (0.20, 0.24, 0.30))
    g.frame("Body", (0.18, 0.28, 0.26))
    F_S, F_B = list(g.frames)
    geo = g.node("ShaderNodeNewGeometry", (-900, 0), F_S)
    nz = g.node("ShaderNodeTexNoise", (-700, 0), F_S, label="ripples", Scale=ripple_scale, Detail=4.0)
    g.link(geo.outputs["Position"], nz.inputs["Vector"])
    bump = g.node("ShaderNodeBump", (-500, 0), F_S, label="ripple height %.1f mm" % (ripple_m * 1000),
                  Distance=ripple_m, Strength=1.0)
    g.link(nz.outputs["Fac"], bump.inputs["Height"])
    b = g.node("ShaderNodeBsdfPrincipled", (-250, 0), F_S, label="water surface", IOR=ior, Roughness=0.0)
    b.inputs["Transmission Weight"].default_value = 1.0
    g.link(bump.outputs["Normal"], b.inputs["Normal"])
    va = g.node("ShaderNodeVolumeAbsorption", (-250, -300), F_B, label="depth tint", Density=density)
    va.inputs["Color"].default_value = (*tint, 1)
    out = g.node("ShaderNodeOutputMaterial", (100, 0))
    g.link(b.outputs["BSDF"], out.inputs["Surface"])
    g.link(va.outputs["Volume"], out.inputs["Volume"])
    return mat


def smooth_flat(obj, sharp_deg=30.0):
    """Shade smooth but keep edges sharper than `sharp_deg` split: a box stays geometrically flat
    (top normals exactly vertical) while counting as 'smooth normals' -- required by MNEE casters."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for f in bm.faces:
        f.smooth = True
    lim = math.radians(sharp_deg)
    for e in bm.edges:
        e.smooth = not (e.is_manifold and e.calc_face_angle(0.0) > lim) and e.is_manifold
    bm.to_mesh(obj.data)
    bm.free()


def water_surface(obj, cell=0.1):
    """Turn a closed water box into its top surface, diced to `cell` metres and smooth -- the build
    MNEE needs (control: scripts/controls/mnee_water.py): a one-quad flat caster delivers NO light, the
    same plane diced 40x40 does; a closed box adds a degenerate bottom interface. The volume still
    works: rays enter it crossing the surface downward and leave crossing it upward (opaque basin)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < 0.5], context="FACES")
    bm.faces.ensure_lookup_table()
    f = bm.faces[0]
    xs = [v.co.x for v in f.verts]
    ys = [v.co.y for v in f.verts]
    nx = max(1, round((max(xs) - min(xs)) / cell))
    ny = max(1, round((max(ys) - min(ys)) / cell))
    z = f.verts[0].co.z
    bm.clear()
    bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=0.5)
    for v in bm.verts:
        v.co.x = min(xs) + (v.co.x + 0.5) * (max(xs) - min(xs))
        v.co.y = min(ys) + (v.co.y + 0.5) * (max(ys) - min(ys))
        v.co.z = z
    for fc in bm.faces:
        fc.smooth = True
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    if bm.faces[0].normal.z < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()
    return nx * ny


def steam(name="STEAM", density=0.6, z0=0.4, height=0.9, scale=3.0):
    """Wisps over a hot tub: Principled Volume, density = noise ramp x fade with height above z0."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    geo = g.node("ShaderNodeNewGeometry", (-1100, 0))
    stretch = g.node("ShaderNodeVectorMath", (-900, 0))
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (1.0, 1.0, 0.45)              # wisps elongate upward
    g.link(geo.outputs["Position"], stretch.inputs[0])
    nz = g.node("ShaderNodeTexNoise", (-700, 0), label="wisps", Scale=scale, Detail=6.0, Roughness=0.6)
    g.link(stretch.outputs["Vector"], nz.inputs["Vector"])
    cr = _ramp(g, (-500, 0), None, [(0.52, (0, 0, 0)), (0.72, (1, 1, 1))], "wisp threshold")
    g.link(nz.outputs["Fac"], cr.inputs["Fac"])
    sep = g.node("ShaderNodeSeparateXYZ", (-700, -300))
    g.link(geo.outputs["Position"], sep.inputs["Vector"])
    fade = g.node("ShaderNodeMapRange", (-500, -300), label="fade with height")
    fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = z0, z0 + height
    fade.inputs["To Min"].default_value, fade.inputs["To Max"].default_value = 1.0, 0.0
    g.link(sep.outputs["Z"], fade.inputs["Value"])
    mul = g.node("ShaderNodeMath", (-300, -100))
    mul.operation = "MULTIPLY"
    g.link(cr.outputs["Color"], mul.inputs[0])
    g.link(fade.outputs["Result"], mul.inputs[1])
    dens = g.node("ShaderNodeMath", (-150, -100), label="density %.2f" % density)
    dens.operation = "MULTIPLY"
    dens.inputs[1].default_value = density
    g.link(mul.outputs[0], dens.inputs[0])
    pv = g.node("ShaderNodeVolumePrincipled", (50, 0), label="steam", Anisotropy=0.5)
    pv.inputs["Color"].default_value = (0.95, 0.95, 0.95, 1)
    g.link(dens.outputs[0], pv.inputs["Density"])
    out = g.node("ShaderNodeOutputMaterial", (300, 0))
    g.link(pv.outputs["Volume"], out.inputs["Volume"])
    return mat
