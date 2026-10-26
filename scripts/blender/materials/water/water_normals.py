"""Water normals; canonical implementation behind water."""

import math

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
