"""World-metre UV coordinates for planar and cylindrical tile surfaces."""
import math

import bpy
from mathutils import Vector


def _world_vertices(obj):
    if obj.type != 'MESH':
        raise TypeError("Tile mapping requires a mesh object")
    if obj.mode != 'OBJECT':
        raise ValueError("Tile mapping requires Object Mode")
    if obj.data.users > 1:
        raise ValueError("Tile mapping refuses shared meshes; make the mesh single-user first")
    bpy.context.view_layer.update()
    return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]


def _write_uv(mesh, values, name):
    layer = mesh.uv_layers.get(name)
    if layer is None:
        layer = mesh.uv_layers.new(name=name)
    if layer is None:
        raise ValueError("Cannot create UV map: mesh has reached the 8-layer UV limit")
    layer.data.foreach_set("uv", values)
    mesh.update()
    return layer.name


def _face_vectors(mesh, vertices):
    for face in mesh.polygons:
        indices = list(face.vertices)
        if len(indices) < 3:
            continue
        base = vertices[indices[0]]
        area = Vector((0.0, 0.0, 0.0))
        for i in range(1, len(indices) - 1):
            area += (vertices[indices[i]] - base).cross(vertices[indices[i + 1]] - base)
        if area.length_squared:
            center = sum((vertices[i] for i in indices), Vector()) / len(indices)
            yield area * 0.5, center


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


def cylinder_uv(obj, center_xy, radius, origin=(0.0, 0.0), name="TileUV", inward=None,
                seam_angle=None):
    """UVs baked in world space: map after placing the object; write oriented arc-length/Z UVs.

    seam_angle is the world cut angle in radians, default opposite the mean angle.
    On a full ring the cut column is a fraction of a tile unless 2*pi*R/pitch
    is whole; put the cut out of view.
    """
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("Tile face radius must be finite and positive")
    vertices = _world_vertices(obj)
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
    if inward is None:
        inward = sum(area.dot(Vector((p.x - center_xy[0], p.y - center_xy[1], 0.0)))
                     for area, p in _face_vectors(obj.data, vertices)) < 0
    direction = -1.0 if inward else 1.0
    values = [0.0] * (2 * len(obj.data.loops))
    for face in obj.data.polygons:
        loops = list(face.loop_indices)
        if not loops:
            continue
        first = angles[obj.data.loops[loops[0]].vertex_index]
        cut = mean - math.pi
        unwrapped = [first + (angles[obj.data.loops[index].vertex_index] - first
                             + math.pi) % math.tau - math.pi for index in loops]
        # Choose the face's turn from its interior, not a float32 vertex on the
        # cut: rounding that vertex below the cut must not shift its whole face.
        face_angle = math.fsum(unwrapped) / len(unwrapped)
        turn = math.floor((face_angle - cut) / math.tau) * math.tau
        for index, angle in zip(loops, unwrapped):
            vertex = obj.data.loops[index].vertex_index
            angle -= turn
            values[2 * index] = direction * radius * angle - origin[0]
            values[2 * index + 1] = vertices[vertex].z - origin[1]
    return _write_uv(obj.data, values, name)


def layout_vector(node_tree, name="TileUV", loc=(0, 0), obj=None):
    """Add a named UV Map node and return its layout vector output socket."""
    if obj is not None and (obj.type != 'MESH' or obj.data.uv_layers.get(name) is None):
        raise ValueError(f"Object {obj.name!r} has no UV layer {name!r}")
    node = node_tree.nodes.new("ShaderNodeUVMap")
    node.uv_map = name
    node.location = loc
    return node.outputs["UV"]
