"""Clean edge fields, scene rounding and location extents for wear."""
from effects.wear.layer_names import canonical_layer
from dataclasses import dataclass
import math
import bmesh
import bpy
from materials.shared.node_graph import active_socket


@dataclass
class WearExtent:
    """World-metre wear location; edge_distance is a clean-mesh distance socket when available."""
    enabled: bool = True
    floor_z_m: float = 0.
    foot_height_m: float = .7
    soffit_edge_m: float = .18
    patch_scale_m: float = 2.3
    edge_distance: object = None
    foot_full_m: float = .02
    patch_black: float = .46
    patch_white: float = .66
    drip_top_m: float | None = None
    drip_length_m: float = 1.


def face_z(g, frame=None):
    """Return world shading-normal Z, independent of the projected mask coordinates."""
    geometry = g.node('ShaderNodeNewGeometry', (-6000, -9000), frame)
    xyz = g.node('ShaderNodeSeparateXYZ', (-5800, -9000), frame)
    g.link(geometry.outputs['Normal'], xyz.inputs[0])
    return xyz.outputs['Z']


def patch_extent(g, vector, scale_m, frame=None, black=.46, white=.66):
    """Return a slow patch field with real zero regions, rather than uniform modulation."""
    noise = g.noise_texture(vector, 1/scale_m, (-5600, -10000), frame, detail=2, rough=.55)
    return g.map_range(noise, black, white, (-5300, -10000), frame=frame, smooth=True)


def location_extent(g, kind, settings, frame=None):
    """Gate feet, floor patches and supplied soffit-edge distances; dried marks exclude undersides."""
    kind = canonical_layer(kind)
    nz = face_z(g, frame)
    eligible = g.math('GREATER_THAN', nz, -.001, (-5500, -9200), frame) if kind == 'dried-marks' else 1
    if not settings.enabled:
        return eligible
    geo = g.node('ShaderNodeNewGeometry', (-6000, -10500), frame)
    pos = g.node('ShaderNodeSeparateXYZ', (-5800, -10500), frame)
    g.link(geo.outputs['Position'], pos.inputs[0])
    height = g.math('SUBTRACT', pos.outputs['Z'], settings.floor_z_m, (-5500, -10500), frame)
    foot = g.map_range(height, settings.foot_full_m, settings.foot_height_m, (-5200, -10500), tmin=1, tmax=0,
                   frame=frame, smooth=True)
    absz = g.math('ABSOLUTE', nz, 0, (-5500, -10800), frame)
    vertical = g.map_range(absz, .1, .55, (-5200, -10800), tmin=1, tmax=0, frame=frame)
    up = g.map_range(nz, .35, .85, (-5200, -11100), frame=frame)
    wall_foot = g.math('MULTIPLY', foot, vertical, (-4900, -10500), frame)
    drips = 0
    if settings.drip_top_m is not None:
        drips = g.map_range(pos.outputs['Z'], settings.drip_top_m-settings.drip_length_m,
                        settings.drip_top_m, (-4900,-11700), frame=frame, smooth=True)
        below = g.math('LESS_THAN',pos.outputs['Z'],settings.drip_top_m,(-5200,-11700),frame)
        drips = g.math('MULTIPLY',drips,below,(-4600,-11700),frame)
        drips = g.math('MULTIPLY',drips,vertical,(-4300,-11700),frame)
    if kind == 'chipping':
        location = wall_foot
    elif kind == 'grunge':
        edge = 0
        if settings.edge_distance is not None:
            band = g.map_range(settings.edge_distance, .015, settings.soffit_edge_m,
                           (-5200, -11400), tmin=1, tmax=0, frame=frame, smooth=True)
            down = g.math('LESS_THAN', nz, -.5, (-5500, -11400), frame)
            edge = g.math('MULTIPLY', band, down, (-4900, -11400), frame)
        floor = g.math('MULTIPLY', up, .16, (-4900, -11100), frame)  # faint floor dirt
        location = g.math('MAXIMUM', wall_foot, floor, (-4600, -10500), frame)
        location = g.math('MAXIMUM', location, edge, (-4300, -10500), frame)
        location = g.math('MAXIMUM', location, drips, (-4000,-11700), frame)
    elif kind == 'dried-marks':
        wall = g.math('MAXIMUM', foot, .12, (-4900, -10800), frame)  # occasional wall marks above feet
        wall = g.math('MULTIPLY', wall, vertical, (-4600, -10800), frame)
        floor = g.math('MULTIPLY', up, .45, (-4900, -11100), frame)
        location = g.math('MAXIMUM', wall, floor, (-4300, -10800), frame)
        location = g.math('MAXIMUM',location,drips,(-4000,-11700),frame)
    else:
        location = g.math('MAXIMUM', wall_foot, .15, (-4300, -10800), frame)
    patch = patch_extent(g, geo.outputs['Position'], settings.patch_scale_m, frame,
                         settings.patch_black, settings.patch_white)
    extent = g.math('MULTIPLY', location, patch, (-4000, -10500), frame)
    return g.math('MULTIPLY', extent, eligible, (-3700, -10500), frame)


def edge_field(b, gi, x0, vertex_junctions=False):
    """Distance to the nearest convex arris -> `edge_dist`, and the rest position offset by the
    group's Seed -> `rest_pos` (noise lookups; a per-object Seed decorrelates repeated objects).
    Measured on outward-normal meshes: convex arrises give a POSITIVE signed angle, inner
    corners a negative one."""
    L = b.link
    ang = b.node_with_props("GeometryNodeInputMeshEdgeAngle", (x0, -300))
    cmp = b.node_with_props("FunctionNodeCompare", (x0 + 200, -300), data_type="FLOAT", operation="GREATER_THAN")
    L(ang.outputs["Signed Angle"], active_socket(cmp.inputs, "A"))
    L(gi.outputs["Sharp Angle"], active_socket(cmp.inputs, "B"))
    m2c = b.node_with_props("GeometryNodeMeshToCurve", (x0 + 400, -200))
    L(gi.outputs["Geometry"], m2c.inputs["Mesh"])
    L(cmp.outputs[0], m2c.inputs["Selection"])
    c2m = b.node_with_props("GeometryNodeCurveToMesh", (x0 + 600, -200))
    L(m2c.outputs["Curve"], c2m.inputs["Curve"])
    prox = b.node_with_props("GeometryNodeProximity", (x0 + 800, -200), target_element="EDGES")
    L(c2m.outputs["Mesh"], prox.inputs["Geometry"])
    pos = b.node_with_props("GeometryNodeInputPosition", (x0 + 800, -450))
    seed_v = b.node_with_props("ShaderNodeVectorMath", (x0 + 950, -450), operation="ADD")
    L(pos.outputs["Position"], seed_v.inputs[0])
    L(gi.outputs["Seed"], seed_v.inputs[1])
    g = b.store_attribute(gi.outputs["Geometry"], "edge_dist", "FLOAT", prox.outputs["Distance"], (x0 + 1050, 0))
    if vertex_junctions:
        # Sharp-edge valence distinguishes a junction from diced points along a straight arris.
        sharp = b.node_with_props('GeometryNodeSeparateGeometry', (x0 + 400, -700), domain='EDGE')
        L(gi.outputs['Geometry'], sharp.inputs['Geometry'])
        L(cmp.outputs[0], sharp.inputs['Selection'])
        neighbours = b.node_with_props('GeometryNodeInputMeshVertexNeighbors', (x0 + 600, -900))
        junction = b.node_with_props('FunctionNodeCompare', (x0 + 800, -900), data_type='INT', operation='GREATER_THAN')
        L(neighbours.outputs['Vertex Count'], active_socket(junction.inputs, 'A'))
        active_socket(junction.inputs, 'B').default_value = 2
        points = b.node_with_props('GeometryNodeMeshToPoints', (x0 + 1000, -700), mode='VERTICES')
        L(sharp.outputs['Selection'], points.inputs['Mesh'])
        L(junction.outputs[0], points.inputs['Selection'])
        vertex = b.node_with_props('GeometryNodeProximity', (x0 + 1200, -700), target_element='POINTS')
        L(points.outputs['Points'], vertex.inputs['Geometry'])
        size = b.node_with_props('GeometryNodeAttributeDomainSize', (x0 + 1200, -1000), component='POINTCLOUD')
        L(points.outputs['Points'], size.inputs['Geometry'])
        valid = b.math('GREATER_THAN', size.outputs['Point Count'], 0.0, (x0 + 1400, -1000))
        g = b.store_attribute(g, 'edge_vertex_dist', 'FLOAT', vertex.outputs['Distance'], (x0 + 1400, 0))
        g = b.store_attribute(g, 'edge_vertex_valid', 'FLOAT', valid, (x0 + 1600, 0))
    return b.store_attribute(g, "rest_pos", "FLOAT_VECTOR", seed_v.outputs["Vector"], (x0 + 1250, 0))



ROUND_RADIUS_M = 0.0025  # m, shared scene default

def set_round_radius(radius=ROUND_RADIUS_M):
    """Set the scene's shared radius in metres before building rounded materials."""
    bpy.context.scene['round_edge_radius'] = radius


def round_shader(g, normal=None, rounded_edges=True, loc=(-650, -250), frame=None,
                 label='Round edges (TexEdges)', samples=8):
    """Build a rounded shader normal using the shared scene radius."""
    if not rounded_edges:
        return normal
    node = g.node('ShaderNodeBevel', loc, frame, label=label,
                  Radius=bpy.context.scene.get('round_edge_radius', ROUND_RADIUS_M))
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
    bmesh.ops.bevel(bm, geom=edges, offset=bpy.context.scene.get('round_edge_radius', ROUND_RADIUS_M),
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
