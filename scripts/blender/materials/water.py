"""Water material helpers; canonical implementations."""
import math
import bpy
from .nodes import G, sock


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
