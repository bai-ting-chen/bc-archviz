"""Water mesh; canonical implementation behind water."""

def water_surface(obj, cell=0.1):
    """Turn a closed water box into its top surface, diced to `cell` metres and smooth -- the build
    MNEE needs (control: scripts/controls/water/mnee_water.py): a one-quad flat caster delivers NO light, the
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
