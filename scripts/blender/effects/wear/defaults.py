"""Per-layer source choices and local default assets; missing-id logs are deduplicated per process."""
from effects.wear.layers import canonical_layer
from effects.wear.masks import asset_mask, mask_field
from effects.wear.patterns import procedural_field
from materials.shared.nodes import sock

DEFAULT_SOURCES = {'grunge': 'hybrid', 'dried-marks': 'hybrid',
                   'chipping': 'hybrid', 'scratches': 'hybrid'}
DEFAULT_MASKS = {'grunge': ('uh4tfagc', 'Mask', 'grunge'),
                 'dried-vertical': ('tjwtbgvc', 'Roughness', 'window stains'),
                 'dried-up': ('uh4tdhic', 'Mask', 'stains'),
                 'scratches': ('vdekdjrc', 'Mask', 'scratched metal'),
                 'chipping': ('uh4tbdhc', 'Mask', 'stains')}
_missing_reported = set()


def report_missing(asset_id,search):
    """Log a named default's procedural fallback and Fab search once per missing id."""
    if asset_id not in _missing_reported:
        print('surface-wear: missing ' + asset_id + '; procedural fallback; Fab search: '
              + 'fabSearch({q:"' + search + '",max:48}) (match id ' + asset_id + ')',flush=True)
        _missing_reported.add(asset_id)


def default_field(g, kind, settings, vector, frame):
    """Load the layer's default mask, blend dried-mark zones, or use the procedural fallback."""
    kind = canonical_layer(kind)
    fallback = None
    def value(key, row):
        nonlocal fallback
        asset_id, map_name, search = DEFAULT_MASKS[key]
        mask = asset_mask(asset_id, map_name)
        if mask is not None:
            return mask_field(g, mask, vector, frame, crossed=kind == 'scratches', row=row)
        report_missing(asset_id,search)
        if fallback is None:
            fallback = procedural_field(g, kind, vector, settings.scale_m, settings.scratch_width_m, frame)
        return fallback
    if kind != 'dried-marks':
        return value(kind, 0)
    vertical = value('dried-vertical', 0)
    up = value('dried-up', 1)
    geometry = g.node('ShaderNodeNewGeometry', (-1000, -7000), frame)
    normal = g.node('ShaderNodeSeparateXYZ', (-800, -7000), frame)
    g.link(geometry.outputs['Normal'], normal.inputs[0])
    zone = g.range(normal.outputs['Z'], .25, .75, (-600, -7000), frame=frame,
                   smooth=True, label='dried marks up-facing zone')
    mix = g.node('ShaderNodeMix', (-300, -7000), frame)
    mix.data_type = 'FLOAT'
    g.link(zone, mix.inputs[0])
    g.link(vertical, sock(mix.inputs, 'A'))
    g.link(up, sock(mix.inputs, 'B'))
    return sock(mix.outputs, 'Result')
