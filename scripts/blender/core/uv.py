"""UV projections for archviz materials: real-world box, directional (grain follows one axis), and
the once-per-object span set used by stains.

1 UV unit = `size` metres everywhere, so a texture keeps its scale across objects.
"""


def directional_uv(obj, size, name="BoxUV", axis=None, along="U"):
    """Box UVs for DIRECTIONAL textures (wood grain, boards, brushed metal, vein-cut or banded
    stone, ribbed/corrugated sheet, woven fabric, long-format tiles): U follows one direction on
    every face — the object's longest dimension, or world `axis` ("X"/"Y"/"Z", e.g. "Z" for
    vertical cladding). Plain box_uv projects each face along its own dominant axis, which turns
    the image 90 deg between faces (grain along the top of a plank, across its side). Faces whose
    normal lies along that direction (end grain) get the other two axes. along="V" for textures
    whose direction runs up the image. 1 UV unit = `size` metres. Returns the axis used."""
    import bmesh
    dims = obj.dimensions
    grain = "XYZ".index(axis) if axis else max(range(3), key=lambda i: dims[i])
    mw, rot = obj.matrix_world, obj.matrix_world.to_3x3()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.get(name) or bm.loops.layers.uv.new(name)
    for f in bm.faces:
        n = (rot @ f.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        plane = [i for i in range(3) if i != ax]
        u_ax = grain if grain in plane else plane[0]
        v_ax = next(i for i in plane if i != u_ax)
        for lp in f.loops:
            p = mw @ lp.vert.co
            uv_ = (p[u_ax] / size, p[v_ax] / size)
            lp[uv].uv = uv_ if along == "U" else (uv_[1], uv_[0])
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.uv_layers.active = obj.data.uv_layers[name]
    return "XYZ"[grain]


def box_uv(obj, size=1.0, name="BoxUV"):
    """Real-world box UVs in world space: 1 UV unit = `size` metres. Each face is projected
    along its dominant world axis, so tangent-space normal maps and UV-based displacement
    behave (unlike shader box projection, which has no tangents)."""
    import bmesh
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.get(name) or bm.loops.layers.uv.new(name)
    mw = obj.matrix_world
    rot = mw.to_3x3()
    for f in bm.faces:
        n = (rot @ f.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            p = mw @ lp.vert.co
            if ax == 2:
                u, v = p.x * (1 if n.z > 0 else -1), p.y
            elif ax == 0:
                u, v = p.y * (1 if n.x > 0 else -1), p.z
            else:
                u, v = -p.x * (1 if n.y > 0 else -1), p.z
            lp[uv].uv = (u / size, v / size)
    bm.to_mesh(me)
    bm.free()
    me.uv_layers.active = me.uv_layers[name]
    me.uv_layers[name].active_render = True


def height_span_uv(obj, u_size=4.0, v_repeat=1.0, name="SpanUV"):
    """Second UV set for once-per-object maps (leak stains): u tiles every `u_size` metres
    along the face, v runs 0..v_repeat from the object's bottom to its top."""
    import bmesh
    mw = obj.matrix_world
    zs = [(mw @ v.co).z for v in obj.data.vertices]
    z0, h = min(zs), max(max(zs) - min(zs), 1e-6)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.get(name) or bm.loops.layers.uv.new(name)
    rot = mw.to_3x3()
    for f in bm.faces:
        n = (rot @ f.normal).normalized()
        for lp in f.loops:
            p = mw @ lp.vert.co
            horiz = p.y if abs(n.x) > abs(n.y) else p.x
            lp[uv].uv = (horiz / u_size, (p.z - z0) / h * v_repeat)
    bm.to_mesh(obj.data)
    bm.free()
