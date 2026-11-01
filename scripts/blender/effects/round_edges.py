"""Shared scene-sized rounded edges: shader normals or real bevel geometry."""
import math
import bmesh
import bpy

ROUND_RADIUS = 0.0025  # m, shared scene default


def set_round_radius(radius=ROUND_RADIUS):
    """Set the scene's shared radius in metres before building rounded materials."""
    bpy.context.scene['round_edge_radius'] = radius


def round_shader(g, normal=None, rounded_edges=True, loc=(-650, -250), frame=None,
                 label='Round edges (TexEdges)', samples=8):
    """Build a rounded shader normal using the shared scene radius."""
    if not rounded_edges:
        return normal
    node = g.node('ShaderNodeBevel', loc, frame, label=label,
                  Radius=bpy.context.scene.get('round_edge_radius', ROUND_RADIUS))
    node.samples = samples
    if normal is not None:
        g.link(normal, node.inputs['Normal'])
    return node.outputs['Normal']


def round_geometry(obj, rounded_edges=True, segments=2, min_angle_deg=30.0):
    """Bevel a mesh's real edges using the shared scene radius."""
    if not rounded_edges:
        return obj
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    edges = [e for e in bm.edges if e.is_manifold and e.calc_face_angle(0) > math.radians(min_angle_deg)]
    bmesh.ops.bevel(bm, geom=edges, offset=bpy.context.scene.get('round_edge_radius', ROUND_RADIUS),
                    segments=segments, profile=0.5, affect="EDGES", clamp_overlap=True)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def switch_rounding(mat, rounded_edges=True):
    """Switch an existing material's shared rounded-normal layer on or off."""
    for node in mat.node_tree.nodes:
        if node.type == 'BEVEL' and node.label in ('Round edges (TexEdges)', 'Round edges'):
            node.mute = not rounded_edges
    return mat
