"""Sparse short cracks running inward from clean outside edges."""
import bmesh
import math
import random
import bpy
from materials.shared.nodes import G
from mathutils import Vector
from effects.cracks import CRACK, apply_crack_masks
from effects.crack_ribbon import crooked_ribbon_masks
from effects.wear_nodes import frame_for


EDGE_CRACK = dict(CRACK, core=0.0016, halo=0.006, depth=0.0008)  # m, core/halo widths and groove depth


def edge_crack_edges(obj, min_angle_deg=30.0):
    """Collect world-space (start, end, inward) face edges before dicing or displacement."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    result = []
    transform = obj.matrix_world
    for edge in bm.edges:
        if not edge.is_manifold or edge.calc_face_angle_signed(0) <= math.radians(min_angle_deg):
            continue
        start, end = (transform @ v.co for v in edge.verts)
        direction = (end - start).normalized()
        for face in edge.link_faces:
            inward = transform @ face.calc_center_median() - (start + end) / 2
            inward -= direction * inward.dot(direction)
            if inward.length > 1e-6:
                result.append((tuple(start), tuple(end), tuple(inward.normalized())))
    bm.free()
    return result


def _ribbon_group(seed, length):
    name = 'Outside edge crack ribbon ' + str(seed) + '-' + format(length, '.9g')
    if existing := bpy.data.node_groups.get(name):
        return existing
    ng = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    for key, kind, default in [('Origin', 'NodeSocketVector', (0, 0, 0)),
                               ('Tangent', 'NodeSocketVector', (1, 0, 0)),
                               ('Inward', 'NodeSocketVector', (0, 0, 1)),
                               ('Plane', 'NodeSocketVector', (0, 1, 0)),
                               ('Length', 'NodeSocketFloat', 0.1),
                               ('Skew', 'NodeSocketFloat', 0.0)]:
        socket = ng.interface.new_socket(name=key, in_out='INPUT', socket_type=kind)
        socket.default_value = default
    for key in ('Core', 'Halo'):
        ng.interface.new_socket(name=key, in_out='OUTPUT', socket_type='NodeSocketFloat')
    g = G(ng)
    F = 'Edge crack ribbon'
    g.frame(F)
    inputs = g.node('NodeGroupInput', (-3000, 0))
    output = g.node('NodeGroupOutput', (600, 0))
    pos = g.node('ShaderNodeNewGeometry', (-2800, 0), F).outputs['Position']
    delta = g.node('ShaderNodeVectorMath', (-2600, 0), F)
    delta.operation = 'SUBTRACT'
    g.link(pos, delta.inputs[0])
    g.link(inputs.outputs['Origin'], delta.inputs[1])

    def dot(key, location):
        node = g.node('ShaderNodeVectorMath', location, F)
        node.operation = 'DOT_PRODUCT'
        g.link(delta.outputs['Vector'], node.inputs[0])
        g.link(inputs.outputs[key], node.inputs[1])
        return node.outputs['Value']

    along = dot('Inward', (-2400, 0))
    perp = dot('Tangent', (-2400, -150))
    plane = dot('Plane', (-2400, -300))
    plane = g.math('ABSOLUTE', plane, 0, (-2200, -300), F)
    on = g.range(plane, 0.004, 0.001, (-2000, -300), frame=F)
    phase = g.noise(pos, 180, (-2400, -500), F, detail=3)
    wob = g.math('MULTIPLY', g.math('SUBTRACT', phase, 0.5, (-2200, -500), F),
                 0.009, (-2050, -500), F)
    # Pin the ribbon to its actual edge, then wobble and drift into the face.
    wob = g.math('MULTIPLY', wob, g.range(along, 0, 0.025, (-2200, -650), frame=F),
                 (-1900, -500), F)
    wob = g.math('ADD', wob, g.math('MULTIPLY', along, inputs.outputs['Skew'], (-2050, -700), F),
                 (-1750, -650), F)
    core, halo = crooked_ribbon_masks(g, F, along, perp, wob, on, EDGE_CRACK,
                                      inputs.outputs['Length'], 0, seed=seed, physical_length=length)
    g.link(core, output.inputs['Core'])
    g.link(halo, output.inputs['Halo'])
    return ng


def add_edge_cracks(mat, edges, amount=1.0, seed=17):
    """Add sparse 5-20 cm core/halo cracks from clean (start, end, inward) outside edges."""
    g, F = frame_for(mat, 'Edge cracks')
    rnd = random.Random(seed)
    core = halo = None
    count = 0
    for start, end, inward in edges:
        start, end, inward = Vector(start), Vector(end), Vector(inward).normalized()
        tangent = (end - start).normalized()
        plane_normal = tangent.cross(inward).normalized()
        distance = rnd.uniform(0.18, 1.0)  # m; many short edges have no crack
        while distance < (end - start).length - 0.12:
            node = g.node('ShaderNodeGroup', (-1000, -count * 220), F)
            length = rnd.uniform(0.05, 0.20)
            skew = rnd.uniform(-0.20, 0.20)
            node.node_tree = _ribbon_group(seed * 1009 + count, length)
            node.inputs['Origin'].default_value = start + tangent * distance
            node.inputs['Tangent'].default_value = tangent
            node.inputs['Inward'].default_value = inward
            node.inputs['Plane'].default_value = plane_normal
            node.inputs['Length'].default_value = length  # m into the face
            node.inputs['Skew'].default_value = skew  # roughly perpendicular
            c, h = node.outputs['Core'], node.outputs['Halo']
            core = c if core is None else g.math('MAXIMUM', core, c, (-500, -count * 220), F)
            halo = h if halo is None else g.math('MAXIMUM', halo, h, (-300, -count * 220), F)
            count += 1
            distance += 0.30 + rnd.expovariate(1.1)  # irregular gaps; no dense periodic pattern
    if core is None:
        zero = g.node('ShaderNodeValue', (0, 0), F)
        core = halo = zero.outputs[0]
        zero.outputs[0].default_value = 0
    mat['edge_crack_count'] = count
    return apply_crack_masks(mat, g, F, core, halo, EDGE_CRACK, amount, 'Edge cracks')
