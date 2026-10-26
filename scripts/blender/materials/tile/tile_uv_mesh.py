"""Tile uv mesh; canonical implementation behind tile_mapping."""

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
