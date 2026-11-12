"""Headless Cycles surface-wear comparison: --out DIR --project DIR [--samples 64]."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(SCRIPTS / 'blender'), str(SCRIPTS / 'controls'), str(Path(__file__).parent),
                str(SCRIPTS / 'controls/regression')]
from edge_lab_common import scene_setup, box, board_views

# Like edge_wear_lab, sheet assembly runs in the host measurement venv (Pillow).
if '--analyze' not in sys.argv:
    import bpy
    import numpy as np
    from effects.surface_wear import LAYERS, MaskSource, WearLayer, WearExtent, apply_surface_wear, image_mask, wear_factor
    from materials.shared.nodes import G
    from variation_lab import render, emission, plane
    from _scene import black_scene, ortho_camera
    import core.archviz as archviz

SURFACES = ('brushed-metal', 'painted-metal', 'concrete-wall')
TILE_M = 2.0
FRAME_WIDTH_M = 5.8
FRAME_PIXELS = (1008, 420)


def _settings(kind):
    # At 5.8 m / 1008 px, a 3-pixel scratch is about 17 mm wide in this shot.
    return WearLayer(source='procedural', scale_m=.45 if kind == 'scratches' else .35,
                     scratch_width_m=3 * FRAME_WIDTH_M / FRAME_PIXELS[0])


def _bake(out, kind):
    """Sample the actual procedural factor to a non-colour EXR placeholder tile."""
    import OpenImageIO as oiio
    resolution_px = 1024  # round-A placeholder, not production mask quality
    black_scene(samples=1, res=resolution_px)
    mat = bpy.data.materials.new('placeholder-' + kind)
    g = G(mat)
    factor, _ = wear_factor(g, kind, replace(_settings(kind), extent=WearExtent(enabled=False)))
    emission(g, factor)
    ob = plane(mat, TILE_M)
    ob.location = (TILE_M / 2, TILE_M / 2, 0)
    ortho_camera(5, TILE_M, xy=(TILE_M / 2, TILE_M / 2))
    passes = render(out, 'bake-' + kind)
    field = next(v for k, v in passes.items() if k.endswith('.var_surface-' + kind))[..., :1]
    path = out / ('placeholder-' + kind + '.exr')
    writer = oiio.ImageOutput.create(str(path))
    writer.open(str(path), oiio.ImageSpec(resolution_px, resolution_px, 1, oiio.FLOAT))
    writer.write_image(field)
    writer.close()
    assert float(field.max()) > .1 and float(field.min()) == 0, (kind, field.min(), field.max())
    return path


def _mask_controls(out):
    """Prove loader levels/gamma/invert and both disabled switches on constant data."""
    import OpenImageIO as oiio
    path = out / 'mask-levels.exr'
    writer = oiio.ImageOutput.create(str(path))
    writer.open(str(path), oiio.ImageSpec(8, 8, 1, oiio.FLOAT))
    writer.write_image(np.full((8, 8, 1), .5, dtype=np.float32))
    writer.close()
    black_scene(samples=1, res=32)
    mat = bpy.data.materials.new('mask-controls')
    g = G(mat)
    identity = image_mask(g, MaskSource(str(path)))
    remapped = image_mask(g, MaskSource(str(path), black=.2, white=.8, gamma=2, invert=True))
    disabled_mask, _ = wear_factor(g, 'grunge', WearLayer(enabled=False, source='mask', mask=MaskSource(str(path))))
    wear_factor(g, 'scratches', WearLayer(enabled=False))
    emission(g, g.combine(identity, remapped, disabled_mask, (4000, 0)))
    plane(mat)
    ortho_camera(5, 2)
    passes = render(out, 'mask-controls')
    data = next(v for k, v in passes.items() if k.endswith('.Combined'))[4:-4, 4:-4, :3]
    error = float(np.max(abs(data - np.array([.5, .75, 0]))))
    assert error < 1e-6, error
    assert float(np.max(abs(_aov(passes, 'scratches')))) == 0
    (out / 'mask-controls.json').write_text(json.dumps(dict(levels_gamma_invert_max_error=error,
                                                          disabled_factors_zero=True), indent=2))


def _surface_vector(g, centre_x):
    position = g.node('ShaderNodeNewGeometry', (-5000, 0)).outputs['Position']
    local = g.node('ShaderNodeVectorMath', (-4700, 0))
    local.operation = 'SUBTRACT'
    g.link(position, local.inputs[0])
    local.inputs[1].default_value = (centre_x - 1, -.1, -1)
    axes = g.node('ShaderNodeSeparateXYZ', (-4400, 0))
    g.link(local.outputs[0], axes.inputs[0])
    return g.combine(axes.outputs['X'], axes.outputs['Z'], 0, (-4100, 0))


def _base_shader(g, kind):
    shader = g.node('ShaderNodeBsdfPrincipled', (5000, 0))
    color, metallic, roughness = {
        'brushed-metal': ((.5, .53, .57, 1), 1, .3),
        'painted-metal': ((.12, .25, .38, 1), 0, .35),
        'concrete-wall': ((.52, .49, .43, 1), 0, .65),
    }[kind]
    shader.inputs['Base Color'].default_value = color
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    if kind == 'brushed-metal':
        shader.inputs['Anisotropic'].default_value = .75
        tangent = g.node('ShaderNodeTangent', (4700, -800))
        tangent.direction_type = 'UV_MAP'
        tangent.uv_map = 'surface-wear-uv'
        g.link(tangent.outputs[0], shader.inputs['Tangent'])
    under = g.node('ShaderNodeBsdfPrincipled', (5000, -1800))
    under.inputs['Base Color'].default_value = (.28, .3, .32, 1) if metallic or kind == 'painted-metal' else (.25, .23, .2, 1)
    under.inputs['Metallic'].default_value = 1 if kind != 'concrete-wall' else 0
    under.inputs['Roughness'].default_value = .42 if kind != 'concrete-wall' else .9
    return shader, under.outputs[0]


def _fixture(project, samples, kind, settings):
    sc, cam = scene_setup(archviz, project, samples, (0, -9, .15), (0, 0, 0), FRAME_WIDTH_M)
    sc.render.resolution_x, sc.render.resolution_y = FRAME_PIXELS
    sc.cycles.seed = 43
    # A broad softbox gives scratches and brushing a readable highlight.
    light = bpy.data.lights.new('wear-softbox', 'AREA')
    light.energy, light.shape, light.size = 450, 'DISK', 3
    ob = bpy.data.objects.new('wear-softbox', light)
    sc.collection.objects.link(ob)
    ob.location = (0, -4, 1)
    ob.rotation_euler.x = 1.57079632679
    materials = []
    regions = {}
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    for i, name in enumerate(SURFACES):
        x = (i - 1) * 1.9
        slab = box(name, (x, 0, 0), (1.65, .2, 1.65))
        if kind == 'scratches':
            archviz.directional_uv(slab, TILE_M, name='surface-wear-uv', axis='X')
        else:
            archviz.box_uv(slab, TILE_M, name='surface-wear-uv')
        # Tile origin matches the local metre coordinates used by the procedural branch.
        for loop in slab.data.uv_layers['surface-wear-uv'].data:
            loop.uv.x += (1 - x) / TILE_M
            loop.uv.y += 1 / TILE_M
        mat = bpy.data.materials.new(name)
        g = G(mat)
        vector = _surface_vector(g, x)
        shader, under = _base_shader(g, name)
        layer_settings = settings[name] if isinstance(settings, dict) else settings
        surface = apply_surface_wear(g, shader, {kind: layer_settings}, under, vector)
        output = g.node('ShaderNodeOutputMaterial', (5600, 0))
        g.link(surface, output.inputs['Surface'])
        slab.data.materials.append(mat)
        materials.append(mat)
        bpy.context.view_layer.update()
        points = [world_to_camera_view(sc, cam, Vector((x + dx, -.1, dz)))
                  for dx, dz in ((-.72, -.72), (.72, .72))]
        xs = [round(p.x * FRAME_PIXELS[0]) for p in points]
        ys = [round((1 - p.y) * FRAME_PIXELS[1]) for p in points]
        regions[name] = [min(xs), min(ys), max(xs), max(ys)]
    return sc, materials, regions


def _amount(materials, kind, amount):
    for mat in materials:
        node = next(n for n in mat.node_tree.nodes if n.label == 'surface-' + kind + ' amount')
        node.outputs[0].default_value = amount


def _stack_control(out, project, samples, masks):
    """Render all four layers together, mixing source choices on the same materials."""
    _, materials, _ = _fixture(project, samples, 'grunge', _settings('grunge'))
    for i, mat in enumerate(materials):
        g = G(mat.node_tree)
        shaders = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
        layers = {}
        for kind in LAYERS[1:]:
            settings = _settings(kind)
            if kind != 'dried-marks':
                settings = replace(settings, source='mask', mask=MaskSource(str(masks[kind])))
            layers[kind] = settings
        surface = apply_surface_wear(g, shaders[0], layers, shaders[1].outputs[0],
                                     _surface_vector(g, (i - 1) * 1.9))
        output = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
        g.link(surface, output.inputs['Surface'])
    passes = render(out, 'all-layers')
    for kind in LAYERS:
        field = _aov(passes, kind)
        assert np.isfinite(field).all() and field.max() > .1


def _aov(passes, kind):
    return next(v[..., 0] for k, v in passes.items() if k.endswith('.var_surface-' + kind))


def _measure(out, kind, passes, regions):
    import OpenImageIO as oiio
    images = {key: oiio.ImageBuf(str(out / (key + '.png'))).get_pixels()[..., :3]
              for key in ('off', 'procedural', 'mask', 'noise-floor', 'mask-off')}
    stats = {}
    for name, (x0, y0, x1, y1) in regions.items():
        roi = np.s_[y0:y1, x0:x1]
        noise = float(np.mean(abs(images['procedural'][roi] - images['noise-floor'][roi])))
        row = {'noise_png_mae': noise, 'sources': {}}
        for source in ('procedural', 'mask'):
            field = _aov(passes[source], kind)[roi]
            half = _aov(passes[source + '-half'], kind)[roi]
            change = float(np.mean(abs(images[source][roi] - images['off'][roi])))
            active = field > .05
            signal = abs(images[source][roi] - images['off'][roi])[active]
            local_noise = abs(images['procedural'][roi] - images['noise-floor'][roi])[active]
            row['sources'][source] = dict(png_mae=change, factor_mean=float(field.mean()),
                factor_sd=float(field.std()), coverage=float(np.mean(field > .01)),
                active_pixels=int(active.sum()), active_png_mae=float(signal.mean()),
                active_noise_mae=float(local_noise.mean()),
                half_amount_max_error=float(np.max(abs(half - .5 * field))))
            assert active.sum() > 20 and signal.mean() > local_noise.mean(), (kind, name, source, signal.mean(), local_noise.mean())
            assert float(np.max(abs(half - .5 * field))) < 1e-6
            assert field.min() >= 0 and field.max() <= 1 and field.std() > .005
        row['source_factor_mae'] = float(np.mean(abs(_aov(passes['procedural'], kind)[roi] - _aov(passes['mask'], kind)[roi])))
        row['source_png_mae'] = float(np.mean(abs(images['procedural'][roi] - images['mask'][roi])))
        assert row['source_factor_mae'] < .035, row
        stats[name] = row
    for key in ('off', 'mask-off'):
        assert float(np.max(abs(_aov(passes[key], kind)))) == 0
    # Different compiled source graphs can round at an 8-bit PNG boundary even at factor zero.
    off_delta = abs(images['off'] - images['mask-off'])
    off_error = dict(max_code_difference=int(round(float(off_delta.max()) * 255)),
                     differing_pixels=int(np.count_nonzero(np.any(off_delta > 0, axis=-1))))
    assert off_error['max_code_difference'] <= 1 and off_error['differing_pixels'] < 100, off_error
    stats['off_comparison'] = off_error
    (out / 'measurements.json').write_text(json.dumps(stats, indent=2))
    return stats


def _boards(out):
    from PIL import Image, ImageChops, ImageEnhance, ImageDraw
    images = {key: Image.open(out / (key + '.png')).convert('RGB')
              for key in ('off', 'procedural', 'mask')}
    images['all-on'] = images['procedural']
    for key in ('procedural', 'mask'):
        difference = ImageChops.difference(images[key], images['off'])
        ImageEnhance.Brightness(difference).enhance(6).save(out / (key + '-off-diff-x6.png'))
    difference = ImageChops.difference(images['procedural'], images['mask'])
    ImageEnhance.Brightness(difference).enhance(6).save(out / 'source-diff-x6.png')
    for key in ('off', 'procedural', 'mask'):
        labels = ImageDraw.Draw(images[key])
        for i, name in enumerate(SURFACES):
            labels.text((32 + i * 330, 25), name, fill='black')
    (out / 'regions.json').write_text(json.dumps({'crop': [360, 65, 650, 355]}))
    list(board_views(out, images, 3, ('off', 'procedural', 'mask'), 8))


def main():
    """Render all source/amount controls, measure AOVs and build native-pixel sheets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--analyze', action='store_true')
    parser.add_argument('--masks', type=Path, help='Project JSON: layer -> candidate id/map/invert rows')
    parser.add_argument('--scratch-glints', action='store_true', help='Two-metal grazing reflection control')
    parser.add_argument('--samples', type=int, default=64, choices=range(1, 257))
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
    if not args.analyze:
        if args.project is None:
            parser.error('--project is required for rendering')
        archviz.set_project(str(args.project))
    args.out.mkdir(parents=True, exist_ok=True)
    if args.masks:
        from surface_wear_compare import compare
        from surface_wear_boards import boards
        if args.analyze:
            boards(args.out)
        else:
            compare(args)
        return
    if args.analyze:
        for kind in json.loads((args.out / 'measurements.json').read_text()):
            _boards(args.out / kind)
        return
    _mask_controls(args.out)
    masks = {kind: _bake(args.out, kind) for kind in LAYERS}
    results = {}
    for kind in LAYERS:
        out = args.out / kind
        out.mkdir(exist_ok=True)
        passes = {}
        for source in ('procedural', 'mask'):
            mapping = 'uv' if kind in ('grunge', 'scratches') else 'world'
            settings = replace(_settings(kind), source=source,
                               mask=MaskSource(str(masks[kind]), mapping=mapping))
            sc, materials, regions = _fixture(args.project, args.samples, kind, settings)
            for suffix, amount in (('', 1), ('-half', .5), ('-off', 0)):
                _amount(materials, kind, amount)
                key = 'off' if source == 'procedural' and suffix == '-off' else source + suffix
                passes[key] = render(out, key)
            if source == 'procedural':
                _amount(materials, kind, 1)
                sc.cycles.seed = 79
                passes['noise-floor'] = render(out, 'noise-floor')
        results[kind] = _measure(out, kind, passes, regions)
        (args.out / 'measurements.json').write_text(json.dumps(results, indent=2))
        print('LAYER_PASS', kind, flush=True)
    _stack_control(args.out, args.project, args.samples, masks)
    print('STACK_PASS', flush=True)


if __name__ == '__main__':
    main()
