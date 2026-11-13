"""Canonical grayscale image loader for surface-wear masks."""
from dataclasses import dataclass, replace
import math
from pathlib import Path
import re

MASK_LEVELS_LABEL = 'surface-mask levels'
MASK_GAMMA_LABEL = 'surface-mask gamma'


def mask_dimensions_m(size_m):
    """Return width and height in metres from a square scalar or rectangular pair."""
    return tuple(size_m) if isinstance(size_m, (tuple, list)) else (size_m, size_m)


@dataclass
class MaskSource:
    """Grayscale data image, levels and real-world mapping (size_m in metres per tile)."""
    path: str
    size_m: float | tuple = 2.0
    mapping: str = 'world'
    uv_map: str = 'surface-wear-uv'
    black: float = 0.0
    white: float = 1.0
    gamma: float = 1.0
    invert: bool = False
    rotation_deg: float = 0.0
    offset_uv: tuple = (0.0, 0.0)


def image_mask(g, mask, vector=None, frame=None, row=0, mapped_vector=None):
    """Load a Non-Color mask in surface metres or named real-world box/directional UVs."""
    sizes = mask_dimensions_m(mask.size_m)
    if min(sizes) <= 0 or mask.white <= mask.black or mask.gamma <= 0:
        raise ValueError('Mask size/gamma must be positive and white must exceed black')
    y = -1600 - row * 3000
    if mapped_vector is not None:
        uv = mapped_vector  # already in tile units; stochastic UV lookups share the same loader
    elif mask.mapping == 'uv':
        # Author with box_uv/directional_uv(size=mask.size_m); do not scale UVs twice.
        uv = g.uv_map(mask.uv_map, (-2800, y), frame)
    elif mask.mapping == 'world':
        if vector is None:
            vector = surface_coordinates(g, frame)
        scale = g.node('ShaderNodeVectorMath', (-2800, y), frame)
        scale.operation = 'MULTIPLY' if isinstance(mask.size_m, (tuple, list)) else 'SCALE'
        g.link(vector, scale.inputs[0])
        if isinstance(mask.size_m, (tuple, list)):
            scale.inputs[1].default_value = (1/sizes[0], 1/sizes[1], 1)
        else:
            scale.inputs['Scale'].default_value = 1 / mask.size_m
        uv = scale.outputs[0]
    else:
        raise ValueError('Mask mapping must be world or uv')
    if mask.rotation_deg or any(mask.offset_uv):
        rotation = g.node('ShaderNodeVectorRotate', (-2700, y - 500), frame)
        rotation.rotation_type = 'AXIS_ANGLE'
        rotation.inputs['Axis'].default_value = (0, 0, 1)
        rotation.inputs['Angle'].default_value = math.radians(mask.rotation_deg)
        g.link(uv, rotation.inputs['Vector'])
        offset = g.node('ShaderNodeVectorMath', (-2500, y - 500), frame)
        offset.operation = 'ADD'
        g.link(rotation.outputs[0], offset.inputs[0])
        offset.inputs[1].default_value = (*mask.offset_uv, 0)
        uv = offset.outputs[0]
    tex = g.image_texture(str(mask.path), 'Non-Color', (-2500, y), frame, uv, 'surface-wear mask')
    tex.interpolation = 'Linear'
    value = g.map_range(tex.outputs['Color'], mask.black, mask.white, (-2200, y), frame=frame,
                    label=MASK_LEVELS_LABEL)
    value = g.math('POWER', value, mask.gamma, (-1900, y), frame)
    value.node.label = MASK_GAMMA_LABEL
    if mask.invert:
        value = g.math('SUBTRACT', 1, value, (-1600, y), frame)
    return value


def mask_field(g, mask, vector=None, frame=None, crossed=False, row=0):
    """Return one image field, or its union with a rotated/offset copy for crossing scratches."""
    first = image_mask(g, mask, vector, frame, row)
    if not crossed:
        return first
    second = replace(mask, rotation_deg=mask.rotation_deg + 90,
                     offset_uv=(mask.offset_uv[0] + .37, mask.offset_uv[1] + .19))
    second = image_mask(g, second, vector, frame, row + 1)
    return g.math('MAXIMUM', first, second, (-1200, -1600 - row * 3000), frame)


def asset_mask(asset_id, map_name='Mask', project=None):
    """Resolve a local 4K scan mask at its metadata scan size; return None when its map is missing."""
    asset = asset_maps(asset_id, (map_name,), project)
    if asset is None:
        return None
    maps, metadata = asset
    width, height = scan_size_m(metadata)
    return MaskSource(str(maps[map_name]), size_m=width if width == height else (width, height))


def asset_maps(asset_id, map_names, project=None):
    """Resolve named local 4K maps and their metadata once; return None for a missing map."""
    from core.assets import project_root, read_meta
    folder = Path(project if project is not None else project_root()) / 'library/local' / asset_id
    maps = {name:next(folder.glob('*_4K_' + name + '.*'), None) for name in map_names}
    if any(path is None for path in maps.values()):
        return None
    return maps, read_meta(str(folder))


def scan_size_m(metadata):
    """Read square or rectangular scan dimensions, converting m/cm/mm metadata to metres."""
    number = r'([0-9]+(?:\.[0-9]+)?)'
    unit = r'(mm|cm|m)?'
    match = re.fullmatch(r'\s*'+number+r'\s*'+unit+r'(?:\s*[x×]\s*'+number+r'\s*'+unit+r')?\s*',
                         metadata['scan'], re.IGNORECASE)
    if match is None:
        raise ValueError('Unsupported scan dimensions: ' + metadata['scan'])
    width, width_unit, height, height_unit = match.groups()
    common_unit = (height_unit or width_unit or 'm').lower()
    metres = {'m': 1., 'cm': .01, 'mm': .001}
    return (float(width)*metres[(width_unit or common_unit).lower()],
            float(height or width)*metres[(height_unit or common_unit).lower()])


def surface_coordinates(g, frame=None):
    """Project world metres onto the dominant face plane for walls, tops and soffits."""
    geometry = g.node('ShaderNodeNewGeometry', (-5200, -300), frame)
    position = g.node('ShaderNodeSeparateXYZ', (-5000, -300), frame)
    normal = g.node('ShaderNodeSeparateXYZ', (-5000, -800), frame)
    g.link(geometry.outputs['Position'], position.inputs[0])
    g.link(geometry.outputs['Normal'], normal.inputs[0])
    normals = [g.math('ABSOLUTE', normal.outputs[axis], 0, (-4700, -800 - i * 250), frame)
               for i, axis in enumerate('XYZ')]
    x_face = g.math('GREATER_THAN', normals[0], normals[1], (-4400, -800), frame)
    xy_max = g.math('MAXIMUM', normals[0], normals[1], (-4400, -1100), frame)
    z_face = g.math('GREATER_THAN', normals[2], xy_max, (-4100, -1100), frame)
    vectors = [g.combine_xyz(position.outputs[a], position.outputs[b], 0, (-4400, i * 250), frame)
               for i, (a, b) in enumerate((('X', 'Z'), ('Y', 'Z'), ('X', 'Y')))]
    wall = g.mix(vectors[0], vectors[1], x_face, (-4000, -300), frame, data_type='VECTOR')
    return g.mix(wall, vectors[2], z_face, (-3600, -300), frame, data_type='VECTOR')
