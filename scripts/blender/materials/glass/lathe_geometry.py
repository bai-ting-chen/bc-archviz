"""Lathe geometry; implementation for glassware."""
import math
import bpy


def lathe(name, profile, centre, segments=256, normal_hint=None):
    """Revolve an (r, z) polyline about the Z axis through `centre`. Points with r == 0 become a
    single pole vertex. `normal_hint(p)` -> desired normal direction at point p (to orient)."""
    import bmesh
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-9:
            rings.append([bm.verts.new((centre[0], centre[1], z))])
        else:
            rings.append([bm.verts.new((centre[0] + r * math.cos(2 * math.pi * k / segments),
                                        centre[1] + r * math.sin(2 * math.pi * k / segments), z))
                          for k in range(segments)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segments):
            k1 = (k + 1) % segments
            if len(a) == 1:
                bm.faces.new((a[0], b[k], b[k1]))
            elif len(b) == 1:
                bm.faces.new((a[k], b[0], a[k1]))
            else:
                bm.faces.new((a[k], b[k], b[k1], a[k1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)   # closed profiles: weld the seam ring
    bm.normal_update()
    if normal_hint:  # area-weighted vote over all faces (lathe winding is consistent)
        vote = sum(f.calc_area() * f.normal.dot(normal_hint(f.calc_center_median())) for f in bm.faces)
        if vote < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob
