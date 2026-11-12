"""Real scan-mask comparisons on the shared surface-wear rig; project manifests own asset choices."""
from dataclasses import replace
import json
import numpy as np
from surface_wear_match import fit_levels, statistics, prefilter_mask as _prefilter
from surface_wear_runoff import runoff_fixture as _runoff_fixture

MATCHING_TOLERANCE = dict(mean_relative=.03, sd_relative=.03, coverage_absolute=.01)


def _assets(manifest, project):
    from effects.surface_wear_masks import asset_mask, mask_dimensions_m
    result = {}
    for kind, candidates in json.loads(manifest.read_text()).items():
        result[kind] = []
        for row in candidates:
            mask = asset_mask(row['id'], row['map'], project)
            if mask is None:
                raise ValueError('Missing comparison mask: ' + row['id'])
            width_m, height_m = mask_dimensions_m(mask.size_m)
            result[kind].append(dict(row, path=mask.path, size_m=mask.size_m,
                                     scan=f'{width_m:g}x{height_m:g} m'))
    return result


def _roi(field, rectangle):
    x0, y0, x1, y1 = rectangle
    return field[y0:y1, x0:x1]


def _subpixels(field, rectangle, factor):
    x0, y0, x1, y1 = rectangle
    block = field[y0 * factor:y1 * factor, x0 * factor:x1 * factor]
    return block.reshape(y1 - y0, factor, x1 - x0, factor).transpose(0, 2, 1, 3).reshape(-1, factor * factor)


def _matching(measured, target):
    errors = {key: measured[key] - target[key] for key in target}
    tolerances = _tolerances(target)
    matched = all(abs(errors[key]) <= tolerances[key] for key in target)
    return dict(errors=errors, matched=matched)


def _tolerances(target):
    return dict(mean=max(1e-12, target['mean'] * MATCHING_TOLERANCE['mean_relative']),
                sd=max(1e-12, target['sd'] * MATCHING_TOLERANCE['sd_relative']),
                coverage=MATCHING_TOLERANCE['coverage_absolute'])


def _set_levels(material, kind, parameters):
    from effects.surface_wear_masks import MASK_LEVELS_LABEL, MASK_GAMMA_LABEL
    frame = next(n for n in material.node_tree.nodes if n.type == 'FRAME' and n.label == 'surface-wear: ' + kind)
    nodes = [n for n in material.node_tree.nodes if n.parent == frame]
    for levels in (n for n in nodes if n.label == MASK_LEVELS_LABEL):
        levels.inputs['From Min'].default_value = parameters['black']
        levels.inputs['From Max'].default_value = parameters['white']
    for gamma in (n for n in nodes if n.label == MASK_GAMMA_LABEL):
        gamma.inputs[1].default_value = parameters['gamma']
    amount = next(n for n in nodes if n.label == 'surface-' + kind + ' amount')
    amount.outputs[0].default_value = parameters['amount']


def _calibration_fields(material, kind):
    """Export the scan before location weighting and the fixed extent used by the actual graph."""
    from materials.shared.nodes import G, sock
    graph = G(material.node_tree)
    switch = next(n for n in graph.nt.nodes if n.label == 'surface-' + kind)
    source = sock(switch.inputs, 'B').links[0].from_socket
    if kind == 'run-off':
        scan, extent = source, 1.
    else:
        product = source.node
        assert product.type == 'MATH' and product.operation == 'MULTIPLY'
        scan = product.inputs[0].links[0].from_socket
        extent = product.inputs[1].links[0].from_socket if product.inputs[1].is_linked else product.inputs[1].default_value
    for name, value in (('scan', scan), ('extent', extent)):
        aov = graph.node('ShaderNodeOutputAOV', (900, -29000))
        aov.aov_name = 'var_surface-' + kind + '-calibration-' + name
        graph._in(aov.inputs['Value'], value)


def _candidate(out, args, kind, candidate, targets, regions):
    import bpy
    import OpenImageIO as oiio
    import surface_wear_lab as lab
    from effects.surface_wear import MaskSource
    # All downloaded maps in this control are grayscale RGB; verify that rather than infer a channel.
    image = oiio.ImageBuf(candidate['path']).get_pixels()
    assert image.shape[:2] == (4096, 4096)
    assert np.max(abs(image[..., 0] - image[..., 1])) < 1e-6
    assert np.max(abs(image[..., 0] - image[..., 2])) < 1e-6
    if candidate.get('invert'):
        raise ValueError('Calibrate positive grayscale marks; invert the source polarity before levels fitting')
    mask = MaskSource(candidate['path'], size_m=candidate['size_m'])
    settings = replace(lab._settings(kind), source='mask', mask=mask)
    fixture = _fixture(args, kind)
    sc, materials, _ = fixture(args.project, args.samples, kind, settings)
    lab.render(out, candidate['id'] + '-unmodified')
    # A hard coating mask needs coherent patches before thresholding; its micrograin otherwise
    # leaves too many partially covered final pixels to match the procedural solid-patch SD.
    sigma_pixels = 1.5 if kind == 'worn-through' else .5
    width_m = sc.camera.data.ortho_scale
    filtered_path, filtering = _prefilter(out, candidate, image[..., 0],
                                         width_m / lab.FRAME_PIXELS[0], sigma_pixels)
    del image
    filtered_image = bpy.data.images.load(str(filtered_path), check_existing=True)
    filtered_image.colorspace_settings.name = 'Non-Color'
    for material in materials:
        for texture in (n for n in material.node_tree.nodes if n.type == 'TEX_IMAGE'):
            texture.image = filtered_image
        _calibration_fields(material, kind)
    # A calibration image samples each final pixel at 4×4 locations before nonlinear levels.
    # Beauty frames below retain the requested camera, resolution and sample count.
    subpixel_grid = 4
    sc.render.resolution_x *= subpixel_grid
    sc.render.resolution_y *= subpixel_grid
    sc.cycles.samples = 1
    calibration = lab.render(out, candidate['id'] + '-calibration')
    raw = lab._aov(calibration, kind + '-calibration-scan')
    extent = lab._aov(calibration, kind + '-calibration-extent')
    samples = {name: _subpixels(raw, rect, subpixel_grid) for name, rect in regions.items()}
    extents = {name: _subpixels(extent, rect, subpixel_grid) for name, rect in regions.items()}
    del raw, extent, calibration
    sc.render.resolution_x, sc.render.resolution_y = lab.FRAME_PIXELS
    sc.cycles.samples = args.samples
    goals = {name: dict(target) for name, target in targets.items()}
    history = []
    for iteration in range(5):
        parameters = {}
        for material, name in zip(materials, targets):
            parameters[name] = fit_levels(samples[name], goals[name], hard=kind == 'worn-through',
                                          extent=extents[name])
            _set_levels(material, kind, parameters[name])
        passes = lab.render(out, candidate['id'] + '-fit-' + str(iteration))
        field = lab._aov(passes, kind)
        actual = {name: statistics(_roi(field, rect)) for name, rect in regions.items()}
        checks = {name: _matching(actual[name], targets[name]) for name in targets}
        history.append(dict(parameters=parameters, measured=actual, checks=checks))
        print('MASK_FIT', kind, candidate['id'], iteration, json.dumps(actual), flush=True)
        if all(row['matched'] for row in checks.values()):
            break
        for name in goals:
            goals[name] = {key: max(.0001, min(.999, goals[name][key] + .5 * (targets[name][key] - actual[name][key])))
                           for key in targets[name]}
    # Keep the best measured fit per material, rather than publishing an iteration that regressed.
    chosen = {}
    for material, name in zip(materials, targets):
        def score(row):
            actual = row['measured'][name]
            target = targets[name]
            tolerance = _tolerances(target)
            return sum(((actual[k] - target[k]) / tolerance[k]) ** 2 for k in target)
        best = min(history, key=lambda row: (not row['checks'][name]['matched'], score(row)))
        chosen[name] = best['parameters'][name]
        _set_levels(material, kind, chosen[name])
    final = lab.render(out, candidate['id'])
    field = lab._aov(final, kind)
    actual = {name: statistics(_roi(field, rect)) for name, rect in regions.items()}
    checks = {name: _matching(actual[name], targets[name]) for name in targets}
    result = dict(candidate=candidate, filtering=filtering, rendered_mask=str(filtered_path),
                  parameters=chosen, tiles=actual, checks=checks, fitting=history)
    if args.scratch_glints:
        from surface_wear_scratch_lab import measure_glints
        result['glints'] = measure_glints(out, candidate['id'], field, regions)
    return result



def _display_measurements(out, layer):
    import OpenImageIO as oiio
    keys = ['off', 'procedural', 'noise-floor'] + [row['candidate']['id'] for row in layer['candidates']]
    pixels = {key: oiio.ImageBuf(str(out / (key + '.png'))).get_pixels()[..., :3] for key in keys}
    result = {}
    for name, rectangle in layer['regions'].items():
        noise = float(abs(_roi(pixels['procedural'], rectangle) - _roi(pixels['noise-floor'], rectangle)).mean())
        result[name] = dict(noise_png_mae=noise, sources={})
        for key in keys:
            if key in ('off', 'noise-floor'):
                continue
            change = float(abs(_roi(pixels[key], rectangle) - _roi(pixels['off'], rectangle)).mean())
            result[name]['sources'][key] = dict(png_mae=change, whole_tile_signal_over_noise=change / max(noise, 1e-12))
    return result


def compare(args):
    """Render procedural baselines and real candidates; publish measured matching residuals."""
    import surface_wear_lab as lab
    assets = _assets(args.masks, args.project)
    results = dict(samples=args.samples, coverage_threshold=.01, layers={},
                   matching_tolerance=MATCHING_TOLERANCE)
    kinds = [kind for kind in lab.LAYERS if kind in assets] + (['run-off'] if 'run-off' in assets else [])
    if args.scratch_glints:
        kinds = ['scratches']
    for kind in kinds:
        out = args.out / kind
        out.mkdir(exist_ok=True)
        fixture = _fixture(args, kind)
        sc, materials, regions = fixture(args.project, args.samples, kind, lab._settings(kind))
        proc = lab.render(out, 'procedural')
        field = lab._aov(proc, kind)
        targets = {name: statistics(_roi(field, rect)) for name, rect in regions.items()}
        lab._amount(materials, kind, 0)
        off = lab.render(out, 'off')
        assert np.max(abs(lab._aov(off, kind))) == 0
        lab._amount(materials, kind, 1)
        sc.cycles.seed = 79
        lab.render(out, 'noise-floor')
        layer = dict(procedural=targets, regions=regions, candidates=[])
        if args.scratch_glints:
            from surface_wear_scratch_lab import measure_glints
            layer['procedural_glints'] = measure_glints(out, 'procedural', field, regions)
        for candidate in assets[kind]:
            layer['candidates'].append(_candidate(out, args, kind, candidate, targets, regions))
        layer['display'] = _display_measurements(out, layer)
        results['layers'][kind] = layer
        (args.out / 'measurements.json').write_text(json.dumps(results, indent=2))
        print('LAYER_COMPLETE', kind, flush=True)
    (args.out / 'measurements.json').write_text(json.dumps(results, indent=2))
    checks = [check for layer in results['layers'].values() for candidate in layer['candidates']
              for check in candidate['checks'].values()]
    matched = sum(check['matched'] for check in checks)
    print('MATCHED_TILES', matched, '/', len(checks), flush=True)
    assert matched == len(checks), 'See measurements.json for unmatched tiles'


def _fixture(args, kind):
    if args.scratch_glints:
        from surface_wear_scratch_lab import scratch_fixture
        return scratch_fixture
    if kind == 'run-off':
        return _runoff_fixture
    import surface_wear_lab as lab
    return lab._fixture


