"""Tile uv planar; canonical implementation behind tile_mapping."""

import math

from mathutils import Vector

from materials.tile.tile_uv_mesh import _face_vectors, _world_vertices, _write_uv

def planar_uv(obj, origin=(0.0, 0.0), name="TileUV", facing=None):
    """UVs baked in world space: map after placing the object; tilted faces foreshorten by cos(theta), so use cylinder_uv for curved walls.

    facing is a world direction vector, or a world point supplied as a Blender
    object (such as a camera); U follows Z cross the normal facing that side.
    """
    vertices = _world_vertices(obj)
    mesh = obj.data
    horizontal, walls = [], []
    for area, center in _face_vectors(mesh, vertices):
        group = horizontal if abs(area.normalized().z) >= math.cos(math.pi / 6) else walls
        group.append((area, center))
    if sum(a.length for a, _ in horizontal) >= sum(a.length for a, _ in walls):
        tangent, vertical = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))
    else:
        reference = max(walls, key=lambda item: item[0].length_squared)[0]
        dominant = sum((a if a.dot(reference) >= 0 else -a for a, _ in walls), Vector()).normalized()
        if facing is not None:
            if hasattr(facing, 'matrix_world'):
                total = sum(a.length for a, _ in walls)
                center = sum((p * a.length for a, p in walls), Vector()) / total
                toward = facing.matrix_world.translation - center
            else:
                toward = Vector(facing)
            if dominant.dot(toward) < 0:
                dominant.negate()
        tangent = Vector((0.0, 0.0, 1.0)).cross(dominant).normalized()
        vertical = Vector((0.0, 0.0, 1.0))
    coords = [(point.dot(tangent) - origin[0], point.dot(vertical) - origin[1])
              for point in vertices]
    values = [value for loop in mesh.loops for value in coords[loop.vertex_index]]
    return _write_uv(mesh, values, name)
