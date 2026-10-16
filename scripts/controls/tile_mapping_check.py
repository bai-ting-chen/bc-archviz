"""Control: TileUV distances = true surface distances (planar wall, rotated wall, floor,
cylinder crossing the ±pi cut). Run: blender -b --factory-startup --python <this>"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blender"))
import bpy, bmesh, numpy as np
import tile_mapping

def uv_vs_world(ob, uvname, metric):
    """Max |uv edge length - metric edge length| over all face edges, metres."""
    me = ob.data; uvl = me.uv_layers[uvname].data
    worst = 0.0
    for poly in me.polygons:
        li = list(poly.loop_indices)
        for a, b in zip(li, li[1:] + li[:1]):
            va = ob.matrix_world @ me.vertices[me.loops[a].vertex_index].co
            vb = ob.matrix_world @ me.vertices[me.loops[b].vertex_index].co
            du = (uvl[a].uv - uvl[b].uv).length
            worst = max(worst, abs(du - metric(va, vb)))
    return worst

bpy.ops.wm.read_homefile(use_empty=True)
fails = []
# planar wall, rotated 37 deg about Z, 3 x 2.6 m, subdivided
bpy.ops.mesh.primitive_grid_add(x_subdivisions=7, y_subdivisions=5, size=1)
w = bpy.context.object; w.scale = (3, 2.6, 1); w.rotation_euler = (math.pi/2, 0, math.radians(37))
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
n = tile_mapping.planar_uv(w)
e = uv_vs_world(w, n, lambda a, b: (a - b).length)
if e > 1e-4: fails.append(f"planar wall err {e:.6f}")
# floor
bpy.ops.mesh.primitive_grid_add(x_subdivisions=4, y_subdivisions=4, size=4)
f = bpy.context.object
n = tile_mapping.planar_uv(f)
if uv_vs_world(f, n, lambda a, b: (a - b).length) > 1e-4: fails.append("floor err")
# cylinder R 1.8 spanning 150..250 deg (crosses +-pi), 2.6 m tall
R, verts, faces = 1.8, [], []
angs = [math.radians(a) for a in range(150, 251, 2)]
for z in (0.0, 1.3, 2.6):
    verts += [(R*math.cos(t), R*math.sin(t), z) for t in angs]
N = len(angs)
for r in range(2):
    for i in range(N - 1):
        faces.append((r*N+i, r*N+i+1, (r+1)*N+i+1, (r+1)*N+i))
me = bpy.data.meshes.new("cyl"); me.from_pydata(verts, [], faces)
c = bpy.data.objects.new("cyl", me); bpy.context.scene.collection.objects.link(c)
n = tile_mapping.cylinder_uv(c, (0.0, 0.0), R)
arc = lambda a, b: math.hypot(R * abs(math.atan2(math.sin(math.atan2(a.y,a.x)-math.atan2(b.y,b.x)),
                                          math.cos(math.atan2(a.y,a.x)-math.atan2(b.y,b.x)))), a.z - b.z)
if uv_vs_world(c, n, arc) > 1e-4: fails.append("cylinder arc err")
us = [l.uv.x for l in c.data.uv_layers[n].data]
if max(us) - min(us) > R * math.radians(100) + 1e-3: fails.append("seam: U jumps across the cut")
def continuity(ob, name, cut_vertices=()):
    """Check per-vertex loop UV continuity except at explicitly identified cut vertices."""
    samples = {}
    for loop in ob.data.loops:
        samples.setdefault(loop.vertex_index, []).append(ob.data.uv_layers[name].data[loop.index].uv.copy())
    for vertex, values in samples.items():
        for axis in (0, 1):
            if axis == 0 and vertex in cut_vertices:
                continue
            if max(v[axis] for v in values) - min(v[axis] for v in values) >= 1e-6:
                fails.append(f"{ob.name}: vertex {vertex} axis {axis} discontinuity")


def orientation(ob, name, u_axis, v_axis):
    """Check signed UV increments against the requested world basis on every edge."""
    from mathutils import Vector
    u_axis, v_axis = Vector(u_axis), Vector(v_axis)
    uv = ob.data.uv_layers[name].data
    for poly in ob.data.polygons:
        li = list(poly.loop_indices)
        for a, b in zip(li, li[1:] + li[:1]):
            delta = (ob.matrix_world @ ob.data.vertices[ob.data.loops[b].vertex_index].co
                     - ob.matrix_world @ ob.data.vertices[ob.data.loops[a].vertex_index].co)
            duv = uv[b].uv - uv[a].uv
            if abs(duv.x - delta.dot(u_axis)) > 1e-5 or abs(duv.y - delta.dot(v_axis)) > 1e-5:
                fails.append(f"{ob.name}: orientation err")
                return


from mathutils import Vector
room_normal = Vector((math.sin(math.radians(37)), -math.cos(math.radians(37)), 0))
wall_u = Vector((0, 0, 1)).cross(room_normal)
n = tile_mapping.planar_uv(w, facing=room_normal)
continuity(w, n)
orientation(w, n, wall_u, (0, 0, 1))
camera = bpy.data.objects.new("facing_camera", bpy.data.cameras.new("facing_camera"))
bpy.context.scene.collection.objects.link(camera)
camera.location = room_normal * 5
n = tile_mapping.planar_uv(w, facing=camera)
orientation(w, n, wall_u, (0, 0, 1))
n = tile_mapping.planar_uv(f)
continuity(f, n)
orientation(f, n, (1, 0, 0), (0, 1, 0))
continuity(c, c.data.uv_layers.active.name)

# An unapplied transform must produce world-metre distances, including translation.
bpy.ops.mesh.primitive_grid_add(x_subdivisions=7, y_subdivisions=5, size=1)
transformed = bpy.context.object
transformed.name = "unapplied_wall"
transformed.scale = (3, 2.6, 0.7)
transformed.rotation_euler = (math.pi/2, 0, math.radians(37))
transformed.location = (4.2, -3.1, 0.8)
n = tile_mapping.planar_uv(transformed, facing=room_normal)
if uv_vs_world(transformed, n, lambda a, b: (a-b).length) > 1e-4:
    fails.append("unapplied world lengths err")
continuity(transformed, n)
orientation(transformed, n, wall_u, (0, 0, 1))

# Full rings share vertices at the cut, with deliberately opposed normal directions.
for R, concave in ((2.6, True), (1.8, False)):
    count, seam = 180, 0.37
    verts = [(R*math.cos(seam+i*math.tau/count), R*math.sin(seam+i*math.tau/count), z)
             for z in (0.0, 2.6) for i in range(count)]
    faces = [(i, (i+1) % count, count+(i+1) % count, count+i) for i in range(count)]
    if concave:
        faces = [tuple(reversed(face)) for face in faces]
    me = bpy.data.meshes.new("ring_mesh")
    me.from_pydata(verts, [], faces)
    ring = bpy.data.objects.new("concave_ring" if concave else "convex_ring", me)
    bpy.context.scene.collection.objects.link(ring)
    n = tile_mapping.cylinder_uv(ring, (0, 0), R, seam_angle=seam)
    if uv_vs_world(ring, n, arc) > 1e-4:
        fails.append(f"{ring.name}: arc err")
    continuity(ring, n, {0, count})
    # Z cross the surface normal is rightward from its visible side.
    for poly in me.polygons:
        li = list(poly.loop_indices)
        for a, b in zip(li, li[1:]+li[:1]):
            pa = me.vertices[me.loops[a].vertex_index].co
            pb = me.vertices[me.loops[b].vertex_index].co
            angle_delta = math.atan2(math.sin(math.atan2(pb.y,pb.x)-math.atan2(pa.y,pa.x)),
                                     math.cos(math.atan2(pb.y,pb.x)-math.atan2(pa.y,pa.x)))
            delta = me.uv_layers[n].data[b].uv - me.uv_layers[n].data[a].uv
            if abs(delta.x - (-1 if concave else 1)*R*angle_delta) > 1e-4 or abs(delta.y-(pb.z-pa.z)) > 1e-5:
                fails.append(f"{ring.name}: rightward orientation err")
                break

# A slab's subdivided front must outweigh its individually larger top face.
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1)
bm.normal_update()
for vertex in bm.verts:
    vertex.co.x *= 3
    vertex.co.y *= 0.2
    vertex.co.z *= 2.6
front = next(face for face in bm.faces if face.normal.y < -0.9)
bmesh.ops.subdivide_edges(bm, edges=list(front.edges), cuts=15, use_grid_fill=True)
me = bpy.data.meshes.new("slab_mesh")
bm.to_mesh(me)
bm.free()
slab = bpy.data.objects.new("subdivided_slab", me)
bpy.context.scene.collection.objects.link(slab)
n = tile_mapping.planar_uv(slab, facing=(0, -1, 0))
continuity(slab, n)
orientation(slab, n, (1, 0, 0), (0, 0, 1))

# Shared geometry and missing requested maps must fail before mutation.
shared = bpy.data.objects.new("shared_slab", me)
bpy.context.scene.collection.objects.link(shared)
for mapper in (lambda: tile_mapping.planar_uv(slab),
               lambda: tile_mapping.cylinder_uv(slab, (0, 0), 1.0)):
    try:
        mapper()
    except ValueError:
        pass
    else:
        fails.append("shared mesh accepted")
tree = bpy.data.node_groups.new("mapping_control", "ShaderNodeTree")
try:
    tile_mapping.layout_vector(tree, name="missing", obj=f)
except ValueError:
    pass
else:
    fails.append("missing UV layer accepted")
socket = tile_mapping.layout_vector(tree, obj=f)
if socket.node.uv_map != "TileUV":
    fails.append("layout_vector map err")

bpy.ops.mesh.primitive_plane_add()
limited = bpy.context.object
for i in range(8):
    if len(limited.data.uv_layers) < 8:
        limited.data.uv_layers.new(name=f"occupied_{i}")
try:
    tile_mapping.planar_uv(limited, name="ninth_map")
except ValueError:
    pass
else:
    fails.append("UV layer limit accepted")

# The concave well's bottom cut pieces must continue its vertical joints.
R, count, seam = 2.6, 180, 0.37
angles = [seam + i * math.tau / count for i in range(count)]
wall_verts = [(R*math.cos(a), R*math.sin(a), z) for z in (2.6, 4.0) for a in angles]
wall_faces = [(count+i, count+(i+1) % count, (i+1) % count, i) for i in range(count)]
me = bpy.data.meshes.new("well_wall_mesh")
me.from_pydata(wall_verts, [], wall_faces)
wall = bpy.data.objects.new("well_wall", me)
bpy.context.scene.collection.objects.link(wall)
wall_map = tile_mapping.cylinder_uv(wall, (0, 0), R, seam_angle=seam)
if wall["tile_uv_sign"] != -1 or abs(wall["tile_uv_seam"] - seam) > 1e-12:
    fails.append("well wall sign/seam metadata err")
continuity(wall, wall_map, {0, count})
ring_verts = [(r*math.cos(a), r*math.sin(a), 2.6) for r in (R, 2.65) for a in angles]
# Clockwise from above: exposed bottom face has -Z normal.
ring_faces = [(i, (i+1) % count, count+(i+1) % count, count+i) for i in range(count)]
me = bpy.data.meshes.new("well_bottom_mesh")
me.from_pydata(ring_verts, [], ring_faces)
bottom = bpy.data.objects.new("well_bottom", me)
bpy.context.scene.collection.objects.link(bottom)
bottom_map = tile_mapping.annulus_uv(bottom, (0, 0), R, like=wall)
continuity(bottom, bottom_map, {0, count})
wall_uv = wall.data.uv_layers[wall_map].data
bottom_uv = me.uv_layers[bottom_map].data
for wall_face, ring_face in zip(wall.data.polygons, me.polygons):
    # Compare corresponding faces so the two sheets of the seam stay distinct.
    wall_u = {wall.data.loops[i].vertex_index: wall_uv[i].uv.x
              for i in wall_face.loop_indices if wall.data.loops[i].vertex_index < count}
    face_uv = {me.loops[i].vertex_index: bottom_uv[i].uv.copy() for i in ring_face.loop_indices}
    for vertex, uv in face_uv.items():
        p = bottom.matrix_world @ me.vertices[vertex].co
        expected_v = math.hypot(p.x, p.y) - R
        if abs(uv.y - expected_v) > 1e-6:
            fails.append("annulus radial V err")
        if vertex < count:
            outer = face_uv[vertex + count]
            if abs(uv.x - wall_u[vertex]) > 1e-6:
                fails.append("annulus/wall joint continuation err")
            if abs(outer.x - uv.x) > 1e-6:
                fails.append("annulus radial U err")
            if outer.y <= uv.y:
                fails.append("annulus V does not increase outward")

print("TILE_MAPPING_CHECK", "FAIL" if fails else "PASS", *fails, sep="\n  ")
sys.exit(1 if fails else 0)
