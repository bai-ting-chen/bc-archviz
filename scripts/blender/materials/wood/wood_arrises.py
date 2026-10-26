"""Wood arrises; canonical implementation behind wood_wear."""

import math

import bmesh

def round_arrises(obj, width=0.0025, segments=2, min_angle_deg=30.0):
    """Real rounded arrises. Two segments keep each new edge at 45 deg, so the GN edge field
    (threshold 30 deg) still finds them."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    edges = [e for e in bm.edges if e.is_manifold and e.calc_face_angle(0) > math.radians(min_angle_deg)]
    bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, profile=0.5,
                    affect="EDGES", clamp_overlap=True)
    bm.to_mesh(obj.data)
    bm.free()
