"""One hybrid definition: procedural region multiplied by a full-range stochastic scan interior."""
from dataclasses import dataclass, replace
from effects.surface_wear_masks import asset_mask
from effects.surface_wear_fields import procedural_field
from effects.surface_wear_tiling import stochastic_mask

# Threshold and feather width are normalized procedural-field units, not metres.
REGION_EDGES = {'grunge': (.24, .20), 'dried-marks': (.07, .08), 'worn-through': (.30, .02)}
INTERIOR_ASSETS = {'grunge': (('uh4tfagc', 'Mask'), ('uh4uabdc', 'Mask')),
                   'dried-marks': (('uh4tdhic', 'Mask'), ('tjwtbgvc', 'Roughness'))}


@dataclass
class HybridSource:
    """Stochastic interiors, contrast/mean remap, normalized region edges and binary flake cutoff."""
    seed: int = 17
    blend_scale_m: float = 1.7
    scale_jitter: float = .12
    masks: tuple = ()
    region_threshold: float | None = None
    edge_width: float | None = None
    interior_black: float = 0.
    interior_white: float = 1.
    interior_gamma: float = 1.
    interior_gain: float = 1.
    flake_threshold: float = .5


def _interior_masks(kind, settings, override):
    if override is not None:
        return [override]
    if settings.masks:
        return list(settings.masks)
    if kind == 'worn-through':
        from effects.surface_wear_chips import flaked_paint_masks, WORN_SCAN_LEVELS
        masks = flaked_paint_masks()
        if any(mask is None for mask in masks):
            from effects.surface_wear_defaults import report_missing
            for asset_id, mask in zip(WORN_SCAN_LEVELS, masks):
                if mask is None:
                    report_missing(asset_id, 'flaked paint wall')
            return None
        return masks
    assets = INTERIOR_ASSETS[kind]
    masks = [asset_mask(asset_id, map_name) for asset_id, map_name in assets]
    if any(mask is None for mask in masks):
        from effects.surface_wear_defaults import report_missing
        for (asset_id, _), mask in zip(assets, masks):
            if mask is None:
                report_missing(asset_id, 'grunge' if kind == 'grunge' else 'stains')
        return None
    if kind == 'dried-marks':
        # Only the Roughness background needs removal; neither map needs a gamma compensation.
        return [replace(mask, black=.34) if map_name=='Roughness' else mask
                for mask,(_,map_name) in zip(masks,assets)]
    return masks


def hybrid_field(g, kind, layer, vector, extent, frame=None, amount=None):
    """Return region, scan interior, drying-edge rim and their exact region-times-interior product."""
    settings = layer.hybrid
    masks = _interior_masks(kind, settings, layer.mask)
    procedural = procedural_field(g, kind, vector, layer.scale_m, layer.scratch_width_m, frame,
                                  region=masks is not None)
    driver = g.math('MULTIPLY', procedural, extent, (-1400, -26000), frame)
    if masks is None:
        return dict(region=driver, interior=1., rim=0., factor=driver, fallback=True)
    threshold, width = REGION_EDGES[kind]
    threshold = threshold if settings.region_threshold is None else settings.region_threshold
    width = width if settings.edge_width is None else settings.edge_width
    region = g.range(driver, threshold-width/2, threshold+width/2,
                     (-1100, -26000), frame=frame, smooth=True)
    scan = stochastic_mask(g, masks, vector, settings, frame)
    interior = g.range(scan, settings.interior_black, settings.interior_white,
                       (-1400, -26800), frame=frame)
    interior = g.math('POWER', interior, settings.interior_gamma, (-1100, -26800), frame)
    interior = g.math('MULTIPLY', interior, settings.interior_gain, (-800, -26800), frame)
    interior = g.math('MINIMUM', interior, 1., (-500, -26800), frame)
    if kind == 'worn-through':
        # Amount selects chip coverage; it never makes a selected chip translucent.
        amount = layer.amount if amount is None else amount
        cutoff = g.math('SUBTRACT', settings.flake_threshold+.5, amount, (-1100, -27200), frame)
        region = g.math('GREATER_THAN', region, .5, (-800, -27200), frame)
        interior = g.math('GREATER_THAN', interior, cutoff, (-500, -27200), frame)
    factor = g.math('MULTIPLY', region, interior, (-800, -26000), frame)
    inverse = g.math('SUBTRACT', 1, region, (-1100, -26400), frame)
    rim = g.math('MULTIPLY', region, inverse, (-800, -26400), frame)
    rim = g.math('MULTIPLY', rim, 4, (-500, -26400), frame)
    return dict(region=region, interior=interior, rim=rim, factor=factor, scan=scan, driver=driver)


def scratch_hybrid(g, layer, vector, frame=None):
    """Keep the held scratch hybrid's existing 0.7–1.0 scan modulation unchanged."""
    mask = layer.mask or asset_mask('vdekdjrc')
    if mask is None:
        from effects.surface_wear_defaults import report_missing
        report_missing('vdekdjrc', 'scratched metal')
        return procedural_field(g, 'scratches', vector, layer.scale_m, layer.scratch_width_m, frame)
    texture = stochastic_mask(g, [mask], vector, layer.hybrid, frame)
    shape = procedural_field(g, 'scratches', vector, layer.scale_m, layer.scratch_width_m, frame)
    modulation = g.math('MULTIPLY', texture, .3, (-900, -16000), frame)
    modulation = g.math('ADD', modulation, .7, (-600, -16000), frame)
    return g.math('MULTIPLY', shape, modulation, (-300, -16000), frame)
