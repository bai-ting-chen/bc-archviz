"""Tile uv polar; canonical implementation behind tile_mapping."""

import math

from mathutils import Vector

from materials.tile.tile_uv_mesh import _face_vectors, _world_vertices, _write_uv

def _polar_angles(mesh, vertices, center_xy, seam_angle):
    angles = [math.atan2(point.y - center_xy[1], point.x - center_xy[0])
              for point in vertices]
    sine = math.fsum(math.sin(angle) for angle in angles)
    cosine = math.fsum(math.cos(angle) for angle in angles)
    # A complete symmetric cylinder has no preferred mean direction: use zero.
    mean = math.atan2(sine, cosine) if math.hypot(sine, cosine) > 1e-12 * len(angles) else 0.0
    if seam_angle is not None:
        if not math.isfinite(seam_angle):
            raise ValueError("Seam angle must be finite")
        mean = seam_angle + math.pi
    cut = mean - math.pi
    result = []
    for face in mesh.polygons:
        loops = list(face.loop_indices)
        if not loops:
            continue
        first = angles[mesh.loops[loops[0]].vertex_index]
        unwrapped = [first + (angles[mesh.loops[index].vertex_index] - first
                             + math.pi) % math.tau - math.pi for index in loops]
        # Choose the face's turn from its interior, not a float32 vertex on the
        # cut: rounding that vertex below the cut must not shift its whole face.
        face_angle = math.fsum(unwrapped) / len(unwrapped)
        turn = math.floor((face_angle - cut) / math.tau) * math.tau
        result.extend((index, angle - turn) for index, angle in zip(loops, unwrapped))
    return result, cut

def cylinder_uv(obj, center_xy, radius, origin=(0.0, 0.0), name="TileUV", inward=None,
                seam_angle=None):
    """UVs baked in world space: map after placing the object; write oriented arc-length/Z UVs.

    seam_angle is the world cut angle in radians, default opposite the mean angle.
    On a full ring the cut column is a fraction of a tile unless 2*pi*R/pitch
    is whole; put the cut out of view. Stores tile_uv_sign and tile_uv_seam
    on obj for annulus_uv(like=obj).
    """
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("Tile face radius must be finite and positive")
    vertices = _world_vertices(obj)
    loop_angles, cut = _polar_angles(obj.data, vertices, center_xy, seam_angle)
    if inward is None:
        inward = sum(area.dot(Vector((p.x - center_xy[0], p.y - center_xy[1], 0.0)))
                     for area, p in _face_vectors(obj.data, vertices)) < 0
    direction = -1.0 if inward else 1.0
    values = [0.0] * (2 * len(obj.data.loops))
    for index, angle in loop_angles:
        vertex = obj.data.loops[index].vertex_index
        values[2 * index] = direction * radius * angle - origin[0]
        values[2 * index + 1] = vertices[vertex].z - origin[1]
    result = _write_uv(obj.data, values, name)
    obj["tile_uv_sign"] = direction
    obj["tile_uv_seam"] = cut
    return result

def annulus_uv(obj, center_xy, radius, origin=(0.0, 0.0), name="TileUV",
               seam_angle=None, sign=None, like=None):
    """Polar metre UVs for a flat ring: wall-radius arc length U and absolute radial offset V.

    UVs baked in world space: map after placing the object. Use like=wall for a
    concave well: it copies the sign and cut cylinder_uv used on that wall.
    Explicit sign/seam_angle override copied values. Without like, sign defaults
    to +1 (convex); a flat ring cannot infer the adjoining wall's facing.
    Use the same center_xy, radius and origin as the wall to continue its joints.
    """
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("Tile face radius must be finite and positive")
    vertices = _world_vertices(obj)
    if like is not None:
        if "tile_uv_sign" not in like or "tile_uv_seam" not in like:
            raise ValueError("The like object must first be mapped with cylinder_uv")
        if sign is None:
            sign = like["tile_uv_sign"]
        if seam_angle is None:
            seam_angle = like["tile_uv_seam"]
    if sign is None:
        sign = 1.0
    if sign not in (-1, 1):
        raise ValueError("Tile UV sign must be +1 or -1")
    loop_angles, _ = _polar_angles(obj.data, vertices, center_xy, seam_angle)
    values = [0.0] * (2 * len(obj.data.loops))
    for index, angle in loop_angles:
        point = vertices[obj.data.loops[index].vertex_index]
        values[2 * index] = sign * radius * angle - origin[0]
        values[2 * index + 1] = abs(math.hypot(point.x - center_xy[0],
                                             point.y - center_xy[1]) - radius) - origin[1]
    return _write_uv(obj.data, values, name)
