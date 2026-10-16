"""Independent tile layout, glazed face, rounded shoulder and grout shading."""
import math
import json
import warnings
import uuid
import inspect
from pathlib import Path

import bpy
import numpy as np
from archviz import read_meta
from study_materials import G
import tile_layout
import tile_mapping
import tile_damage
from tile_nodes import _Graph, _socket

FEATURES = ("profile", "variation", "tilt", "wave", "dust", "specks", "macro", "damage")
_LAYOUT = dict(tile_w="Tile W", tile_h="Tile H", joint="Joint", corner_radius="Corner Radius", row_offset="Row Offset",
               rotation="Rotation", origin="Origin", jitter_offset="Jitter Offset",
               jitter_rotation_deg="Jitter Rotation")
_OPTIONAL_LAYOUT = ("jitter_offset", "jitter_rotation_deg")
_REMOVED_DAMAGE = ('chip_reach', 'flake_margin', 'crack_wander', 'crack_branch_share',
                   'spall_share', 'spall_reach', 'kink_size', 'kink_amp', 'branch_share')
_FINISH = dict(body_albedo="Body Albedo", coat_ior="Coat IOR", coat_rough="Coat Rough",
               edge_radius="Edge Radius", recess="Recess", grout_albedo="Grout Albedo",
               grout_rough="Grout Rough", dust="Dust", dust_width="Dust Width",
               tint_var="Tint Var", rough_var="Rough Var", tilt_deg="Tilt Deg", lippage="Lippage",
               wave_amp="Wave Amp", specks="Specks", speck_size="Speck Size", macro="Macro", map_size="Map Size",
               face_contrast="Face Contrast", face_saturation="Face Saturation")


def _finish(defaults, owner):
    """Create an owned group exposing all editable finish parameters."""
    tree = bpy.data.node_groups.new(defaults['name'] + '.TileFinish', 'ShaderNodeTree')
    tree['tile_surface_owner'] = owner
    for key, label in _FINISH.items():
        kind = ('NodeSocketColor' if key.endswith('albedo') else
                'NodeSocketVector' if key == 'map_size' else 'NodeSocketFloat')
        socket = _socket(tree, label, kind=kind, default=defaults[key])
        if key == 'tilt_deg':
            socket.subtype = 'ANGLE'
        elif key in ('face_contrast', 'face_saturation'):
            socket.min_value, socket.max_value = 0., 1.
    for f in FEATURES:
        _socket(tree, f + ' On', default=1.0)
    # A parameter-only group keeps every dependency flowing outwards to the shader.
    # Images can stay outside groups without feeding any output back into TileFinish.
    inputs = [item for item in tree.interface.items_tree if item.in_out == 'INPUT']
    for item in inputs:
        _socket(tree, item.name, 'OUTPUT', item.socket_type)
    a = _Graph(tree)
    source = a.node('NodeGroupInput')
    target = a.node('NodeGroupOutput')
    target.is_active_output = True
    for item in inputs:
        a.put(source.outputs[item.name], target.inputs[item.name])
    return tree


def _gate(a, i, feature, value):
    """Remove a feature's whole contribution when its switch is zero."""
    return a.m('MULTIPLY', i[feature + ' On'], value)


def _desaturate(a, color, saturation):
    """Mix RGB toward Rec.709 luminance without changing its measured luminance."""
    luminance = a.v('DOT_PRODUCT', color, (.2126, .7152, .0722))
    gray = a.xyz(luminance, luminance, luminance)
    amount = a.xyz(saturation, saturation, saturation)
    return a.v('ADD', gray, a.v('MULTIPLY', a.v('SUBTRACT', color, gray), amount))


def _face_tone(a, i):
    """Reduce scan contrast and saturation, then normalize its adjusted linear mean."""
    contrast = a.xyz(i['Face Contrast'], i['Face Contrast'], i['Face Contrast'])
    color = a.v('ADD', i['Face Mean'], a.v('MULTIPLY',
                   a.v('SUBTRACT', i['Face Color'], i['Face Mean']), contrast))
    color = _desaturate(a, color, i['Face Saturation'])
    mean = _desaturate(a, i['Face Mean'], i['Face Saturation'])
    return a.v('MULTIPLY', color, a.v('DIVIDE', i['Body Albedo'], mean))


def _albedo(a, i, dust, pits, pinholes):
    """Build normalized face and grout albedos plus signed macro variation."""
    m, v = a.m, a.v
    cloud = m('ADD', 1, m('MULTIPLY', a.amplitude(i['World'], 18), .03))
    normalized = _face_tone(a, i)
    normalized = v('MINIMUM', normalized, (.9, .9, .9))
    # Vector mix expressed as add/multiply to avoid hidden Mix sockets.
    color = v('ADD', v('MULTIPLY', normalized, a.xyz(i['Has Face'], i['Has Face'], i['Has Face'])),
              v('MULTIPLY', i['Body Albedo'], a.xyz(
                  m('MULTIPLY', m('SUBTRACT', 1, i['Has Face']), cloud),
                  m('MULTIPLY', m('SUBTRACT', 1, i['Has Face']), cloud),
                  m('MULTIPLY', m('SUBTRACT', 1, i['Has Face']), cloud))))
    # Sum of two independent uniforms gives a triangular, mean-centered lightness spread.
    tint = m('SUBTRACT', m('ADD', a.rand(i['Cell'], (17, 31, 47)),
                           a.rand(i['Cell'], (349, 367, 389))), 1)
    tint_factor = m('ADD', 1, _gate(a, i, 'variation', m('MULTIPLY', i['Tint Var'], tint)))
    warmth = _gate(a, i, 'variation', m('MULTIPLY', m('MULTIPLY', i['Tint Var'], .25),
                      m('SUBTRACT', m('MULTIPLY', a.rand(i['Cell'], (401, 419, 439)), 2), 1)))
    color = v('MULTIPLY', color, a.xyz(m('ADD', 1, warmth), 1, m('SUBTRACT', 1, warmth)))
    macro_delta = _gate(a, i, 'macro', m('MULTIPLY', i['Macro'], a.amplitude(i['World'], 1/3)))
    macro = m('ADD', 1, macro_delta)
    darken = m('SUBTRACT', 1, m('MULTIPLY', dust, .5))
    # Iron spots darken; pinholes brighten instead, sharing the same final albedo cap.
    speck_tone = m('ADD', m('SUBTRACT', 1, m('MULTIPLY', m('SUBTRACT', pits, pinholes), .6)),
                   m('MULTIPLY', pinholes, .15))
    factor = m('MULTIPLY', m('MULTIPLY', tint_factor, macro), m('MULTIPLY', darken, speck_tone))
    color = v('MINIMUM', v('MULTIPLY', color, a.xyz(factor, factor, factor)), (.9, .9, .9))
    marker = a.node('ShaderNodeVectorMath', operation='MULTIPLY')
    marker.name = 'TileFaceAlbedo'
    a.put(color, marker.inputs[0]); marker.inputs[1].default_value = (1, 1, 1)
    grout_factor = m('MULTIPLY', darken, macro)
    grout_color = v('MULTIPLY', i['Grout Albedo'], a.xyz(grout_factor, grout_factor, grout_factor))
    return marker.outputs['Vector'], grout_color, macro_delta


def _dust(a, i):
    """Build patchy corner dust with independently varying physical width."""
    m, v = a.m, a.v
    # Dust reaches zero in broad clean patches.
    patch_noise = a.smooth(a.noise(i['World'], 2.5), .45, .65)
    width_noise = a.amplitude(v('ADD', i['World'], (13, 29, 43)), 2.)
    width = m('MULTIPLY', i['Dust Width'], m('ADD', .9, m('MULTIPLY', .6, width_noise)))
    dust_band = m('SUBTRACT', 1, a.smooth(m('ADD', i['Edge'], m('MULTIPLY', i['Joint Width'], .5)),
                                               0, m('MAXIMUM', width, 1e-9)))
    dust = _gate(a, i, 'dust', m('MULTIPLY', i['Dust'], m('MULTIPLY', dust_band, patch_noise)))
    return dust


def _specks(a, i):
    """Build clustered, irregular, varied-size iron spots and lighter pinhole masks."""
    m, v = a.m, a.v
    fraction = m('MAXIMUM', m('MULTIPLY', i['Specks'], .01), 0)
    # Diameter ratio = .3 + .7*U^2: most dots small; E[ratio^2] = .328.
    # The symmetric smooth noise field retains half the candidate dots on average.
    # Compensate both area losses in center density, preserving mean percent coverage.
    base_threshold = m('SQRT', m('DIVIDE', fraction, math.pi * .328 * .5))
    radius = m('MAXIMUM', m('MULTIPLY', i['Speck Size'], .5), 1e-9)
    scale = m('DIVIDE', base_threshold, radius)
    surface = v('MULTIPLY', i['Tile UV'], a.xyz(i['Tile W'], i['Tile H'], 0))
    phase = a.rand(i['Cell'], (229, 251, 269), True)
    surface = v('ADD', surface, phase)
    warp_noise = a.noise(surface, m('DIVIDE', 1, m('MAXIMUM', i['Speck Size'], 1e-9)))
    channels = a.split(warp_noise.node.outputs['Color'])
    warp = []
    for channel in channels[:2]:
        signed = m('MINIMUM', m('MAXIMUM', m('DIVIDE', m('SUBTRACT', channel, .5), .1), -1), 1)
        warp.append(m('MULTIPLY', signed, m('MULTIPLY', i['Speck Size'], .3)))
    warped = v('ADD', surface, a.xyz(warp[0], warp[1], 0))
    xy = a.split(warped)
    vor = a.node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature='F1', distance='EUCLIDEAN')
    a.put(a.xyz(xy[0], xy[1]), vor.inputs['Vector'])
    a.put(scale, vor.inputs['Scale'])
    random = a.split(vor.outputs['Color'])
    diameter_ratio = m('ADD', .3, m('MULTIPLY', .7, m('MULTIPLY', random[0], random[0])))
    threshold = m('MULTIPLY', base_threshold, diameter_ratio)
    density = a.smooth(a.noise(i['World'], 1/.15), .4, .6)
    # Thin whole dots with the independent blue hash: patchiness changes coverage,
    # rather than shrinking all dots in a sparse patch below their diameter range.
    retained = m('LESS_THAN', random[2], density)
    mask = _gate(a, i, 'specks', m('MULTIPLY', retained, m('LESS_THAN', vor.outputs['Distance'], threshold)))
    pinholes = m('MULTIPLY', mask, m('LESS_THAN', random[1], .2))
    return mask, pinholes


def _height(a, i, pits, pinholes):
    """Combine metre-valued shoulders, tilt, wave and pit relief."""
    m, v = a.m, a.v
    tile_size = a.xyz(i['Tile W'], i['Tile H'], 0)
    tilt = a.rand(i['Cell'], (113, 137, 157))
    direction = m('MULTIPLY', a.rand(i['Cell'], (179, 197, 211)), math.tau)
    # Round shoulder, clamped to the grout floor; turning profile off removes both.
    r = m('MAXIMUM', i['Edge Radius'], 0)
    e = m('MINIMUM', m('MAXIMUM', i['Edge'], 0), r)
    square = m('MULTIPLY', m('SUBTRACT', r, e), m('SUBTRACT', r, e))
    shoulder = m('SUBTRACT', m('SQRT', m('MAXIMUM', m('SUBTRACT', m('MULTIPLY', r, r), square), 0)), r)
    floor = m('MULTIPLY', i['Recess'], -1)
    shoulder = m('MAXIMUM', shoulder, floor)
    joint_mix = m('MAXIMUM', i['Joint'], m('SUBTRACT', 1, a.smooth(i['Edge'], 0, .0003)))
    profile = _gate(a, i, 'profile', a.mix(joint_mix, shoulder, floor))
    uv_center = v('MULTIPLY', v('SUBTRACT', i['Tile UV'], (.5, .5, 0)), tile_size)
    slope = m('TANGENT', m('MULTIPLY', i['Tilt Deg'], m('SUBTRACT', m('MULTIPLY', tilt, 2), 1)))
    tilt_height = _gate(a, i, 'tilt', m('MULTIPLY', v('DOT_PRODUCT', uv_center, a.xyz(m('COSINE', direction), m('SINE', direction))), slope))
    wave = _gate(a, i, 'wave', m('MULTIPLY', i['Wave Amp'], a.amplitude(i['World'], m('DIVIDE', 1, i['Tile H']))))
    face_height = m('ADD', m('ADD', tilt_height, wave),
                    m('SUBTRACT', m('MULTIPLY', m('MULTIPLY', i['Face Height'], i['Face Contrast']), .0002), m('ADD', m('MULTIPLY', pits, .0001), m('MULTIPLY', pinholes, .00005))))
    lippage = _gate(a, i, 'tilt', m('MULTIPLY', i['Lippage'],
                    m('SUBTRACT', m('MULTIPLY', a.rand(i['Cell'], (457, 479, 499)), 2), 1)))
    # The rounded shoulder interpolates from the fixed grout floor to the shifted face.
    rise = m('MINIMUM', m('MAXIMUM', m('DIVIDE', m('SUBTRACT', shoulder, floor),
                     m('MAXIMUM', i['Recess'], 1e-9)), 0), 1)
    rise = m('MAXIMUM', rise, m('LESS_THAN', i['Recess'], 1e-9))
    lip_weight = a.mix(i['profile On'], 1, rise)
    face_height = m('ADD', face_height, m('MULTIPLY', lippage, lip_weight))
    height = m('ADD', profile, m('MULTIPLY', m('SUBTRACT', 1, joint_mix), face_height))
    return height, joint_mix, face_height


def _bsdfs(a, i, color, grout_color, dust, macro_delta, height, joint_mix):
    """Mix coated clay and grout using a world-metre bump field."""
    m, v = a.m, a.v
    bump = a.node('ShaderNodeBump')
    bump.name = 'TileBump'
    bump.inputs['Strength'].default_value = 1; bump.inputs['Distance'].default_value = 1
    a.put(height, bump.inputs['Height'])
    face = a.node('ShaderNodeBsdfPrincipled')
    a.put(color, face.inputs['Base Color'])
    a.put(m('MINIMUM', m('MAXIMUM', m('ADD', .5, m('MULTIPLY', macro_delta, .5)), 0), 1), face.inputs['Roughness'])
    face.inputs['Specular IOR Level'].default_value = 0
    face.inputs['Coat Weight'].default_value = 1
    a.put(i['Coat IOR'], face.inputs['Coat IOR'])
    rough = a.rand(i['Cell'], (59, 83, 101))
    gloss = m('ADD', i['Coat Rough'], _gate(a, i, 'variation', m('MULTIPLY', i['Rough Var'], m('SUBTRACT', m('MULTIPLY', rough, 2), 1))))
    gloss = m('ADD', gloss, m('MULTIPLY', m('MULTIPLY', m('SUBTRACT', i['Face Rough'], i['Rough Mean']), i['Face Contrast']), .3))
    gloss = m('ADD', gloss, m('MULTIPLY', macro_delta, .5))
    a.put(m('MINIMUM', m('MAXIMUM', m('ADD', gloss, m('MULTIPLY', dust, .3)), 0), 1), face.inputs['Coat Roughness'])
    grout = a.node('ShaderNodeBsdfPrincipled')
    a.put(grout_color, grout.inputs['Base Color'])
    a.put(m('MINIMUM', m('MAXIMUM', m('ADD', m('ADD', i['Grout Rough'], m('MULTIPLY', dust, .1)), m('MULTIPLY', macro_delta, .5)), 0), 1), grout.inputs['Roughness'])
    grout.inputs['Coat Weight'].default_value = 0
    for bsdf in (face, grout):
        a.put(bump.outputs['Normal'], bsdf.inputs['Normal'])
    a.put(bump.outputs['Normal'], face.inputs['Coat Normal'])
    mix = a.node('ShaderNodeMixShader')
    for val, socket in zip((joint_mix, face.outputs['BSDF'], grout.outputs['BSDF']), mix.inputs):
        a.put(val, socket)
    return mix.outputs[0]



def _maps(folder):
    """Find supported face albedo, roughness and height maps by filename."""
    paths = sorted(p for p in Path(folder).rglob('*') if p.suffix.lower() in
                   ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.exr', '.hdr', '.webp'))
    result = {}
    for key, tokens in (('color', ('diff', 'col')), ('rough', ('rough',)), ('height', ('disp', 'height'))):
        result[key] = next((p for p in paths if any(t in p.stem.lower() for t in tokens)), None)
    result['arm'] = next((p for p in paths if '_arm_' in p.stem.lower() or p.stem.lower().endswith('_arm')), None) if result['rough'] is None else None
    if result['color'] is None:
        raise ValueError('Face folder needs a *diff* or *col* albedo map')
    return result


def _stats(image, color=False):
    """Cache linear RGB mean and maximum once per image and colour interpretation."""
    key = 'tile_surface_stats_' + ('color' if color else 'data')
    signature = json.dumps([list(image.size), image.channels, image.colorspace_settings.name, image.is_float])
    if image.get(key + '_signature') == signature and key in image:
        values = tuple(image[key])
        return values[:3], values[3:]
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    rgb = pixels.reshape(-1, image.channels)[:, :3].astype(np.float64)
    if rgb.shape[1] < 3:
        rgb = np.repeat(rgb[:, :1], 3, axis=1)
    if color and not image.is_float and image.colorspace_settings.name == 'sRGB':
        rgb = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    mean = tuple(float(max(x, 1e-8)) for x in rgb.mean(axis=0))
    maximum = tuple(float(x) for x in rgb.max(axis=0))
    image[key], image[key + '_signature'] = (*mean, *maximum), signature
    return mean, maximum


def _mean(image, color=False):
    """Return a cached linear RGB mean, including replicated single-channel maps."""
    return _stats(image, color)[0]


def _size(face, map_size):
    """Resolve physical map dimensions from metres or metadata in millimetres."""
    if map_size is None and face and (Path(face) / 'meta.json').exists():
        meta = read_meta(face)
        dimensions = meta.get('dimensions_mm') or meta.get('dimensions')
        if dimensions:
            if isinstance(dimensions, dict):
                dimensions = (dimensions['width'], dimensions['height'])
            map_size = tuple(float(x) / 1000 for x in dimensions[:2])
    if map_size is None:
        if face:
            warnings.warn('Face map dimensions missing; falling back to 1 x 1 m.', stacklevel=2)
        map_size = (1., 1.)
    size = tuple(map_size)
    if len(size) != 2 or any(not math.isfinite(x) or x <= 0 for x in size):
        raise ValueError('map_size must contain two positive finite metre dimensions')
    return (*size, 1.)


def _warn_albedo(image, body, contrast=1., saturation=1.):
    """Warn when target normalization would exceed the face albedo cap."""
    mean, maximum = (np.asarray(x) for x in _stats(image, True))
    maximum = mean + contrast * (maximum - mean)
    weights = np.asarray((.2126, .7152, .0722))
    mean = np.dot(mean, weights) * (1 - saturation) + mean * saturation
    maximum = np.dot(maximum, weights) * (1 - saturation) + maximum * saturation
    if any(peak * target / avg > .9 for peak, target, avg in zip(maximum, body, mean)):
        warnings.warn('Normalized face map exceeds 0.9; clamping can lower its mean albedo.', stacklevel=2)


def _settings(mat):
    """Read rebuild settings including live UI socket edits and feature switches."""
    saved = json.loads(mat['tile_surface_settings'])
    defaults = {key:p.default for key,p in inspect.signature(tile_material).parameters.items()
                if p.default is not inspect.Parameter.empty}
    unknown = set(saved)-set(defaults)-{'name'}-set(_REMOVED_DAMAGE)
    if unknown:
        raise ValueError(f'Cannot map legacy tile settings: {", ".join(sorted(unknown))}')
    values = {**defaults,**saved}
    for key in _REMOVED_DAMAGE:
        values.pop(key, None)
    values['name'] = mat.name
    for key, label in {**_LAYOUT, **_FINISH, **tile_damage.PARAMS}.items():
        node = mat.node_tree.nodes['TileDamage' if key in tile_damage.PARAMS else 'TileLayout' if key in _LAYOUT else 'TileFinish']
        socket = node.inputs.get(label)
        if socket is None:
            continue
        value = socket.default_value
        if key in ('tilt_deg', 'jitter_rotation_deg'):
            value = math.degrees(value)
        elif key in ('body_albedo', 'grout_albedo'):
            value = list(value[:3])
        elif key in ('origin', 'map_size'):
            value = list(value[:2])
        values[key] = value
    values['off'] = [f for f in FEATURES if not mat.node_tree.nodes['TileFinish'].inputs[f + ' On'].default_value]
    damage = mat.node_tree.nodes.get('TileDamage')
    piece = damage.outputs.get('Piece Height') if damage else None
    dirt = damage.outputs.get('Dirt') if damage else None
    needs_upgrade = (damage is None or not tile_damage._is_current(damage.node_tree) or
                     piece is None or not piece.is_linked or dirt is None or not dirt.is_linked)
    if needs_upgrade:
        try:
            tile_material(**values)
        except (TypeError,ValueError) as exc:
            raise ValueError(f'Cannot map legacy tile material {mat.name!r}: {exc}') from exc
    return values


def tile_material(name, uv="TileUV", tile_w=0.045, tile_h=0.145, joint=0.003, row_offset=0.0,
                  rotation=0.0, origin=(0.0, 0.0), face=None, map_size=None,
                  body_albedo=(0.65, 0.64, 0.61), coat_ior=1.5, coat_rough=0.25,
                  edge_radius=0.002, recess=0.0015, grout_albedo=(0.36, 0.36, 0.35),
                  grout_rough=0.9, dust=0.5, dust_width=0.004, tint_var=0.03, rough_var=0.05,
                  tilt_deg=0.4, wave_amp=0.0001, specks=0.3, macro=0.05, off=(),
                  corner_radius=0.003, speck_size=0.001, lippage=0.0003,
                  jitter_offset=0.0, jitter_rotation_deg=0.0, face_contrast=1.0, face_saturation=1.0,
                  damage=0.05, crack_share=0.45, chip_share=0.35,
                  step_height=0.00015, piece_tilt=0.0035, crack_width=0.00018, crack_depth=0.0008,
                  chip_size=0.004, chip_depth=0.0008,
                  spall_size=0.001, spall_density=0.25, glaze_thickness=0.0003,
                  engobe_thickness=0.0002, glaze_lip_width=0.0002, engobe_ring=0.0003,
                  force_kind=0, displacement=False, pixel_size=1.0,
                  shell_exponent=0.6, crack_dirt=0.85, dirt_width=0.004,
                  warp=0.004, warp_scale=0.02, crack_cell=0.03, crack_density=0.35, chip_density=0.5):
    """Build metre-scale tiles with rotation in radians, tilt/jitter_rotation_deg in degrees and lippage in metres."""
    values = locals().copy()
    if face is not None:
        values['face'] = face = str(face)
    settings = values.copy()
    if not math.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError('pixel_size must be positive and finite')
    unknown = set(off) - set(FEATURES)
    if unknown:
        raise ValueError(f'Unknown features: {sorted(unknown)}')
    values['map_size'] = _size(face, map_size)
    values['tilt_deg'] = math.radians(tilt_deg)
    values['jitter_rotation_deg'] = math.radians(jitter_rotation_deg)
    for key in ('body_albedo', 'grout_albedo'):
        values[key] = (*values[key][:3], 1)
    if tile_w <= 0 or tile_h <= 0 or joint < 0 or corner_radius < 0 or speck_size <= 0 or lippage < 0:
        raise ValueError('Tile dimensions must be positive and joint nonnegative')
    if not 0 <= face_contrast <= 1 or not 0 <= face_saturation <= 1:
        raise ValueError('face_contrast and face_saturation must lie in [0, 1]')
    for key in tile_damage.PARAMS:
        _validate_damage(key, values[key])
    maps = _maps(face) if face else {}
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    old_group = None
    if mat.node_tree and mat.node_tree.nodes.get('TileFinish'):
        old_group = mat.node_tree.nodes['TileFinish'].node_tree
    owner = mat.get('tile_surface_id') or uuid.uuid4().hex
    mat['tile_surface_id'] = owner
    G(mat)
    if old_group and old_group.get('tile_surface_owner') == owner and old_group.users == 0:
        bpy.data.node_groups.remove(old_group)
    mat['tile_surface_settings'] = json.dumps(settings)

    a = _Graph(mat.node_tree)
    vector = tile_mapping.layout_vector(mat.node_tree, uv, (-600, 300))
    layout = tile_layout.add_layout(mat.node_tree, vector, (-350, 300),
                                    **{k: values[k] for k in _LAYOUT if k not in _OPTIONAL_LAYOUT})
    for key in _OPTIONAL_LAYOUT:
        socket = layout.inputs.get(_LAYOUT[key])
        if socket is not None:
            socket.default_value = values[key]
    layout.name = 'TileLayout'
    finish = a.node('ShaderNodeGroup'); finish.node_tree = _finish(values, owner)
    finish.name = 'TileFinish'; finish.location = (350, 300)
    params = {socket.name: socket for socket in finish.outputs}
    params.update({key: layout.outputs[key] for key in ('Tile UV', 'Cell', 'Edge', 'Joint')})
    dimensions = a.split(layout.outputs['Tile Size'])
    params.update({'Tile W': dimensions[0], 'Tile H': dimensions[1],
                   'Joint Width': layout.outputs['Joint Width']})
    # Tile Size is (W,H,0); use a safe Z denominator while preserving map aspect.
    sizes = a.split(finish.outputs['Map Size'])
    map_scale = a.xyz(sizes[0], sizes[1], 1)
    patch = a.v('MULTIPLY', a.rand(layout.outputs['Cell'], (41, 73, 19), True), map_scale)
    coords = a.v('DIVIDE', a.v('ADD', a.v('MULTIPLY', layout.outputs['Tile UV'],
                                         layout.outputs['Tile Size']), patch), map_scale)
    coords.node.name = 'TileMapUV'
    geo = a.node('ShaderNodeNewGeometry')
    params.update({'World': geo.outputs['Position'], 'Face Color': (1, 1, 1),
                   'Face Mean': (1, 1, 1), 'Face Rough': 0., 'Rough Mean': 0.,
                   'Face Height': 0., 'Has Face': 0.})
    if face:
        for key, path in maps.items():
            if path is None:
                continue
            image = bpy.data.images.load(str(path), check_existing=True)
            if key != 'color':
                image.colorspace_settings.name = 'Non-Color'
            elif not image.is_float:
                image.colorspace_settings.name = 'sRGB'
            node = a.node('ShaderNodeTexImage'); node.image = image; node.extension = 'REPEAT'; node['tile_map_role'] = key
            a.put(coords, node.inputs['Vector'])
            if key == 'arm':
                separate = a.node('ShaderNodeSeparateColor', mode='RGB')
                separate.name = 'TileARMChannels'
                a.put(node.outputs['Color'], separate.inputs['Color'])
                params['Face Rough'] = separate.outputs['Green']
            else:
                params[{'color': 'Face Color', 'rough': 'Face Rough', 'height': 'Face Height'}[key]] = node.outputs['Color']
            if key == 'color':
                mean = _mean(image, True); mat['face_mean'] = mean
                _warn_albedo(image, body_albedo, face_contrast, face_saturation)
                params['Face Mean'] = mean
            elif key in ('rough', 'arm'):
                params['Rough Mean'] = _mean(image)[1] if key == 'arm' else float(np.mean(_mean(image)))
        params['Has Face'] = 1.
    else:
        mat['face_mean'] = (1., 1., 1.)
    dust_mask = _dust(a, params)
    pits, pinholes = _specks(a, params)
    color, grout_color, macro_delta = _albedo(a, params, dust_mask, pits, pinholes)
    height, joint_mix, face_height = _height(a, params, pits, pinholes)
    damage_node = a.node('ShaderNodeGroup'); damage_node.node_tree = tile_damage.damage_group()
    damage_node.name = 'TileDamage'; damage_node.location = (0, -500)
    for label in ('Tile ID', 'Cell', 'Tile UV', 'Edge', 'Tile Size'):
        a.put(layout.outputs[label], damage_node.inputs[label])
    for key, label in tile_damage.PARAMS.items():
        damage_node.inputs[label].default_value = values[key]
    a.put(finish.outputs['damage On'], damage_node.inputs['On'])
    d = damage_node.outputs
    piece_height = a.m('MULTIPLY', d['Piece Height'], a.m('GREATER_THAN', params['Edge'], 0))
    undamaged = height
    height = a.m('ADD', height, piece_height)
    face_height = a.m('ADD', face_height, piece_height)
    missing = a.m('ADD', d['Chip Depth Out'], d['Crack Depth Out'])
    cut = a.m('MINIMUM', height, a.m('SUBTRACT', face_height, missing))
    cut = a.m('MAXIMUM', cut, a.m('MULTIPLY', params['Recess'], -1))
    height = a.mix(a.m('GREATER_THAN', missing, 0), height, cut)
    marker = a.node('ShaderNodeMath', operation='ADD'); marker.name = 'TileTotalHeight'
    a.put(height, marker.inputs[0]); marker.inputs[1].default_value = 0
    height = marker.outputs[0]
    # Damage-only relief (piece steps + chip/crack cuts): what use_damage_displacement turns into geometry.
    # Bump then shades the rest (profile, joints, waviness), so the displaced part is not counted twice.
    damage_height = a.node('ShaderNodeMath', operation='SUBTRACT'); damage_height.name = 'TileDamageHeight'
    a.put(height, damage_height.inputs[0]); a.put(undamaged, damage_height.inputs[1])
    displaced_share = a.node('ShaderNodeValue'); displaced_share.name = 'DamageDisplacementOn'
    displaced_share.outputs[0].default_value = 0.
    bump_height = a.m('SUBTRACT', height, a.m('MULTIPLY', damage_height.outputs[0], displaced_share.outputs[0]))
    shader = _bsdfs(a, params, color, grout_color, dust_mask, macro_delta, bump_height, joint_mix)
    shader = tile_damage.damage_bsdfs(a, params, shader, color, bump_height, d)
    out = a.node('ShaderNodeOutputMaterial'); out.location = (900, 300)
    a.put(shader, out.inputs['Surface'])
    disp = a.node('ShaderNodeDisplacement'); disp.label = 'Metres; optional displacement'; disp.space = 'WORLD'
    disp.inputs['Midlevel'].default_value = 0; disp.inputs['Scale'].default_value = 1
    a.put(height, disp.inputs['Height'])
    disp.name = 'TileDisplacement'
    ddisp = a.node('ShaderNodeDisplacement'); ddisp.label = 'Metres; damage-only displacement'; ddisp.space = 'WORLD'
    ddisp.inputs['Midlevel'].default_value = 0; ddisp.inputs['Scale'].default_value = 1
    a.put(damage_height.outputs[0], ddisp.inputs['Height'])
    ddisp.name = 'DamageDisplacement'
    mat.displacement_method = 'BUMP'
    for feature in off:
        toggle(mat, feature, False)
    if displacement:
        objects = [o for o in bpy.data.objects if o.type == 'MESH' and
                   any(slot.material == mat for slot in o.material_slots)]
        use_displacement(mat, objects, pixel_size)
    return mat


def set_param(mat, name, value):
    """Set any tile_material keyword, rebuilding structural options in the same material."""
    if name in _REMOVED_DAMAGE:
        raise ValueError(f'{name} was removed; v7 parameters: {", ".join(tile_damage.PARAMS)}')
    settings = _settings(mat)
    if name not in settings:
        raise KeyError(name)
    if name == 'name':
        existing = bpy.data.materials.get(value)
        if existing is not None and existing != mat:
            raise ValueError(f'Material {value!r} already exists')
        mat.name = value
        settings['name'] = mat.name
    elif name in ('displacement', 'pixel_size'):
        if name == 'pixel_size' and (not math.isfinite(value) or value <= 0):
            raise ValueError('pixel_size must be positive and finite')
        settings[name] = value
        return tile_material(**settings)
    elif name in ('face', 'uv'):
        settings[name] = str(value) if name == 'face' and value is not None else value
        return tile_material(**settings)
    elif name == 'off':
        unknown = set(value) - set(FEATURES)
        if unknown:
            raise ValueError(f'Unknown tile features: {sorted(unknown)}')
        for feature in FEATURES:
            toggle(mat, feature, feature not in value)
        settings['off'] = list(value)
    else:
        node = mat.node_tree.nodes['TileDamage' if name in tile_damage.PARAMS else 'TileLayout' if name in _LAYOUT else 'TileFinish']
        label = ({**_LAYOUT, **_FINISH, **tile_damage.PARAMS})[name]
        if name in tile_damage.PARAMS:
            _validate_damage(name, value)
        settings[name] = value
        if name in ('tilt_deg', 'jitter_rotation_deg'):
            value = math.radians(value)
        elif name == 'map_size':
            value = _size(settings['face'], value)
        elif name in ('origin',) and len(value) == 2:
            value = (*value, 0.)
        elif name.endswith('albedo') and len(value) == 3:
            value = (*value, 1.)
        if name in ('face_contrast', 'face_saturation') and not 0 <= value <= 1:
            raise ValueError(f'{name} must lie in [0, 1]')
        if name in ('tile_w', 'tile_h', 'speck_size') and value <= 0:
            raise ValueError(f'{name} must be positive')
        if name in ('joint', 'corner_radius', 'lippage') and value < 0:
            raise ValueError(f'{name} must be nonnegative')
        socket = node.inputs.get(label)
        if socket is not None:
            socket.default_value = value
        elif name not in _OPTIONAL_LAYOUT:
            raise KeyError(label)
        if name in ('body_albedo', 'face_contrast', 'face_saturation'):
            image_node = next((n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.get('tile_map_role') == 'color'), None)
            if image_node:
                finish_inputs = mat.node_tree.nodes['TileFinish'].inputs
                _warn_albedo(image_node.image, finish_inputs['Body Albedo'].default_value[:3],
                             finish_inputs['Face Contrast'].default_value, finish_inputs['Face Saturation'].default_value)
    mat['tile_surface_settings'] = json.dumps(settings)
    mat.node_tree.update_tag(); mat.update_tag()
    return mat


def toggle(mat, feature, on):
    """Enable or remove a finish feature, preserving its parameter values."""
    if feature not in FEATURES:
        raise ValueError(f'Unknown tile feature: {feature}')
    mat.node_tree.nodes['TileFinish'].inputs[feature + ' On'].default_value = float(bool(on))
    mat.node_tree.update_tag(); mat.update_tag()



def _validate_damage(key, value):
    """Reject negative/nonfinite metre parameters and invalid probabilities."""
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'{key} must be finite and nonnegative')
    if key in ('damage', 'chip_share', 'crack_share', 'branch_share', 'spall_density', 'crack_dirt', 'crack_density', 'chip_density') and value > 1:
        raise ValueError(f'{key} must lie in [0, 1]')
    if key in ('warp_scale','crack_cell') and value <= 0:
        raise ValueError(f'{key} must be positive')
    if key == 'force_kind' and value not in (0, 1, 2, 3):
        raise ValueError('force_kind must be 0, 1, 2 or 3')
    if key == 'shell_exponent' and not .2 <= value <= 2:
        raise ValueError('shell_exponent must lie in [0.2, 2]')


def use_displacement(mat, objects, pixel_size=1.0):
    """Opt into world-metre displacement using the shared adaptive subdivision helper."""
    from study_materials import enable_true_displacement
    if not math.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError('pixel_size must be positive and finite')
    tree = mat.node_tree
    disp = tree.nodes['TileDisplacement']
    out = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    tree.links.new(disp.outputs['Displacement'], out.inputs['Displacement'])
    mat.displacement_method = 'BOTH'
    for name in ('TileBump', 'DamageBump'):
        tree.nodes[name].inputs['Strength'].default_value = 0
    settings = json.loads(mat['tile_surface_settings'])
    settings.update(displacement=True, pixel_size=pixel_size)
    mat['tile_surface_settings'] = json.dumps(settings)
    for obj in objects:
        enable_true_displacement(obj, pixel_size)
    return mat


def use_damage_displacement(mat, objects, pixel_size=1.0):
    """Displace only chips, cracks and piece steps; tile profile and joints stay bump, so wall edges never move."""
    from study_materials import enable_true_displacement
    if not math.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError('pixel_size must be positive and finite')
    tree = mat.node_tree
    out = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    tree.links.new(tree.nodes['DamageDisplacement'].outputs['Displacement'], out.inputs['Displacement'])
    tree.nodes['DamageDisplacementOn'].outputs[0].default_value = 1.
    for name in ('TileBump', 'DamageBump'):
        tree.nodes[name].inputs['Strength'].default_value = 1
    mat.displacement_method = 'BOTH'
    for obj in objects:
        enable_true_displacement(obj, pixel_size)
    return mat


def use_bump(mat):
    """Restore height bump shading and disconnect geometric displacement."""
    tree = mat.node_tree
    for node in tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            for link in list(node.inputs['Displacement'].links):
                tree.links.remove(link)
    if 'DamageDisplacementOn' in tree.nodes:
        tree.nodes['DamageDisplacementOn'].outputs[0].default_value = 0.
    for name in ('TileBump', 'DamageBump'):
        tree.nodes[name].inputs['Strength'].default_value = 1
    mat.displacement_method = 'BUMP'
    settings = json.loads(mat['tile_surface_settings'])
    settings['displacement'] = False
    mat['tile_surface_settings'] = json.dumps(settings)
    return mat
