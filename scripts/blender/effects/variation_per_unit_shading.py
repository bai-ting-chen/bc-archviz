"""Unit keys and independently hashed material variations."""
from collections import namedtuple
import hashlib
import math
import bpy
from materials.shared.node_graph import layer_frame, layer_switch

MESH_HASH_SALT = 17  # independent namespace for combining a per-mesh key with the object key
TILT_AXIS_Z = 0.5  # keep the reference axis non-horizontal before its tangent-plane projection
HASH_AXIS_RATIO = 1.618033989  # irrational spacing between hash coordinates

UnitValues = namedtuple('UnitValues', 'tint roughness bump offset normal')


def _hash(graph, key, salt, frame, row):
    y = -700 * row
    vector = graph.combine_xyz(key, salt, salt * HASH_AXIS_RATIO, (-2100, y), frame)
    node = graph.node('ShaderNodeTexWhiteNoise', (-1800, y), frame)
    graph.link(vector, node.inputs['Vector'])
    return node.outputs['Value']


def _instancer_key(graph, attribute, frame):
    key = graph.attribute(attribute, (-2100, 0), frame)
    key.node.attribute_type = 'INSTANCER'
    return key


def _with_object(graph, local, frame):
    """A per-mesh key repeats in every copy of the mesh; the object key separates the copies."""
    obj = graph.node('ShaderNodeObjectInfo', (-2700, 0), frame).outputs['Random']
    key = graph.math('ADD', local, obj, (-2400, 0), frame)
    return _hash(graph, key, MESH_HASH_SALT, frame, 0)


def _island_key(graph, frame):
    island = graph.node('ShaderNodeNewGeometry', (-2700, -700), frame).outputs['Random Per Island']
    return _with_object(graph, island, frame)


def _cell_key(graph, vector, size, frame):
    scaled = graph.node('ShaderNodeVectorMath', (-3300, -700), frame)
    scaled.operation = 'DIVIDE'
    graph.link(vector, scaled.inputs[0])
    scaled.inputs[1].default_value = (size,) * 3 if isinstance(size, (int, float)) else size
    cell = graph.node('ShaderNodeVectorMath', (-3000, -700), frame)
    cell.operation = 'FLOOR'
    graph.link(scaled.outputs[0], cell.inputs[0])
    noise = graph.node('ShaderNodeTexWhiteNoise', (-2700, -700), frame)
    graph.link(cell.outputs[0], noise.inputs['Vector'])
    return _with_object(graph, noise.outputs['Value'], frame)


def unit_key(graph, source='object', attribute='unit_key', vector=None, size=1.0):
    """Read a unit key from its source. instancer needs set_unit_keys on the parents; geometry reads
    a face attribute stored by the build; cell hashes floor(vector / size), size per axis or one number."""
    frame = layer_frame(graph, 'VARIATION: UNIT KEY')
    builders = {
        'object': lambda: graph.node('ShaderNodeObjectInfo', (-2100, 0), frame).outputs['Random'],
        'instancer': lambda: _instancer_key(graph, attribute, frame),
        'island': lambda: _island_key(graph, frame),
        'geometry': lambda: _with_object(graph, graph.attribute(attribute, (-2700, -700), frame), frame),
        'cell': lambda: _cell_key(graph, vector, size, frame),
    }
    key = builders[source]()
    aov = graph.node('ShaderNodeOutputAOV', (key.node.location.x+300, 0), frame)
    aov.aov_name = aov.name = 'var_unit_key'
    graph.link(key, aov.inputs['Value'])
    return key


def set_unit_keys(objects, attribute='unit_key', seed=0):
    """Store deterministic keys on the supplied objects or collection instancers."""
    for obj in objects:
        digest = hashlib.sha256(f'{seed}:{obj.name_full}'.encode()).digest()
        obj[attribute] = int.from_bytes(digest[:8], 'big') / (2**64 - 1)


def unit_values(graph, key, tint=0.035, roughness=0.05, bump=0.3, offset=1.0,
                tilt_deg=0.0, amount=1.0):
    """Independently hash tint, roughness, bump, lookup-coordinate offsets and optional normal tilt."""
    frame = layer_frame(graph, 'VARIATION: PER UNIT')
    values = []
    for salt, (name, span, neutral) in enumerate((('tint', tint, 1),
            ('roughness', roughness, 0), ('bump', bump, 1)), 1):
        raw = graph.map_range(_hash(graph, key, salt, frame, salt-1), 0, 1, (-1500, -700*(salt-1)),
                      target_min=neutral-span, target_max=neutral+span, frame=frame)
        values.append(layer_switch(graph, 'unit_' + name, raw, amount, neutral, frame))
    xyz = [graph.map_range(_hash(graph, key, salt, frame, salt-1), 0, 1, (-1500, -700*(salt-1)),
                   target_min=-offset, target_max=offset, frame=frame) for salt in (4, 5, 6)]
    offset_value = layer_switch(graph, 'unit_offset', graph.combine_xyz(*xyz, (-1200, -3500), frame),
                     amount, (0, 0, 0), frame)
    normal = _tilt(graph, key, tilt_deg, amount, frame) if tilt_deg else None
    return UnitValues(*values, offset_value, normal)


def _tilt(graph, key, tilt_deg, amount, frame):
    angle = graph.map_range(_hash(graph, key, 7, frame, 6), 0, 1, (-1500, -4200),
                    target_min=-math.radians(tilt_deg), target_max=math.radians(tilt_deg), frame=frame)
    angle = layer_switch(graph, 'unit_tilt', angle, amount, 0, frame)
    azimuth = graph.math('MULTIPLY', _hash(graph, key, 8, frame, 7), math.tau, (-1500, -4900), frame)
    axis = graph.combine_xyz(graph.math('COSINE', azimuth, 0, (-1200, -4900), frame),
                     graph.math('SINE', azimuth, 0, (-1200, -5600), frame),
                     TILT_AXIS_Z, (-900, -4900), frame)
    normal = graph.node('ShaderNodeNewGeometry', (-900, -6300), frame).outputs['Normal']
    tangent = graph.node('ShaderNodeVectorMath', (-600, -4900), frame)
    tangent.operation = 'CROSS_PRODUCT'
    graph.link(normal, tangent.inputs[0])
    graph.link(axis, tangent.inputs[1])
    rotate = graph.node('ShaderNodeVectorRotate', (-300, -4900), frame)
    rotate.rotation_type = 'AXIS_ANGLE'
    graph.link(normal, rotate.inputs['Vector'])
    graph.link(tangent.outputs[0], rotate.inputs['Axis'])
    graph.link(angle, rotate.inputs['Angle'])
    return rotate.outputs['Vector']


def random_tone_material(name, color_min, color_max, roughness=0.6, translucent=0.0):
    """Base colour between color_min and color_max per instance (Object Info > Random); optional translucency
    for leaves."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    oi = N.new("ShaderNodeObjectInfo")
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*color_min, 1)
    ramp.color_ramp.elements[1].color = (*color_max, 1)
    L.new(oi.outputs["Random"], ramp.inputs[0])
    b = N.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = roughness
    L.new(ramp.outputs[0], b.inputs["Base Color"])
    o = N.new("ShaderNodeOutputMaterial")
    if translucent:
        t = N.new("ShaderNodeBsdfTranslucent")
        L.new(ramp.outputs[0], t.inputs[0])
        mx = N.new("ShaderNodeMixShader")
        mx.inputs[0].default_value = translucent
        L.new(b.outputs[0], mx.inputs[1])
        L.new(t.outputs[0], mx.inputs[2])
        L.new(mx.outputs[0], o.inputs[0])
    else:
        L.new(b.outputs[0], o.inputs[0])
    return m
