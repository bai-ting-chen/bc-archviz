"""GPU variation controls: blender -b --factory-startup --python variation_lab.py -- --out DIR [--only CASE]."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np

SCRIPTS = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(SCRIPTS / 'blender'), str(SCRIPTS / 'controls'),
                str(SCRIPTS / 'controls/regression')]
from _scene import black_scene, ortho_camera
from materials.shared.nodes import G
from effects.variation_tiling import anti_tile
from effects.variation_per_unit_shading import unit_key, unit_values, set_unit_keys, random_tone_material
from effects.variation_surface_marks import macro_tone, grunge, patchy_extent, _field, _moments
from regress_graph import graph


def material(name):
    mat = bpy.data.materials.new(name)
    return mat, G(mat)


def emission(g, value):
    node = g.node('ShaderNodeEmission', (900, 0))
    g.link(value, node.inputs['Color'])
    g.link(node.outputs[0], g.node('ShaderNodeOutputMaterial', (1100, 0)).inputs['Surface'])


def plane(mat, size=64):
    bpy.ops.mesh.primitive_plane_add(size=size)
    bpy.context.object.data.materials.append(mat)
    return bpy.context.object


def render(out, name):
    import OpenImageIO as oiio
    sc = bpy.context.scene
    for mat in bpy.data.materials:
        if not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == 'OUTPUT_AOV' and node.aov_name not in sc.view_layers[0].aovs:
                aov = sc.view_layers[0].aovs.add()
                aov.name = node.aov_name
                aov.type = 'COLOR' if node.inputs['Color'].is_linked else 'VALUE'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    (out/'gpu.json').write_text(json.dumps(dict(device=sc.cycles.device, backend=prefs.compute_device_type,
        enabled=[device.name for device in prefs.devices if device.use]), indent=2))
    bpy.ops.render.render()
    fmt = sc.render.image_settings
    fmt.media_type = 'MULTI_LAYER_IMAGE'
    fmt.file_format = 'OPEN_EXR_MULTILAYER'
    fmt.color_depth = '32'
    path = out / (name + '.exr')
    bpy.data.images['Render Result'].save_render(str(path))
    reader = oiio.ImageInput.open(str(path))
    passes = {}
    i = 0
    while reader.seek_subimage(i, 0):
        spec = reader.spec()
        passes[spec.getattribute('name')] = np.asarray(reader.read_image()).copy()
        i += 1
    reader.close()
    fmt.media_type = 'IMAGE'
    fmt.file_format = 'PNG'
    fmt.color_depth = '8'
    bpy.data.images['Render Result'].save_render(str(out / (name + '.png')))
    return passes


def channel(passes, name):
    key = next(key for key in passes if key.split('.')[-1] == name or key.endswith('.' + name))
    return passes[key][4:-4, 4:-4, 0]


def _tiling_fixture():
    from materials.shared.pbr_maps import _ph_maps
    black_scene(samples=4, res=256)
    mat, g = material('wall')
    texs = []
    position = g.node('ShaderNodeTexCoord', (-1200, 0)).outputs['Object']
    maps, _ = _ph_maps('concrete_wall_003')
    for key, color in (('diff', 'sRGB'), ('arm', 'Non-Color'), ('disp', 'Non-Color')):
        path = next(v for v in maps.values() if ('_' + key + '_') in Path(v).name)
        tex = g.node('ShaderNodeTexImage', (-900, 0))
        tex.image = bpy.data.images.load(path, check_existing=True)
        tex.image.colorspace_settings.name = color
        tex.projection, tex.projection_blend = 'BOX', 0.15
        g.link(position, tex.inputs['Vector'])
        texs.append(tex)
    emission(g, texs[0].outputs['Color'])
    wall = plane(mat, 4)
    wall.rotation_euler.x = math.pi/2
    cam = ortho_camera(0, 4)
    cam.location = (0, -8, 0)
    cam.rotation_euler = (math.pi/2, 0, 0)
    return g, texs


def tiling(out):
    g, texs = _tiling_fixture()
    baseline = channel(render(out, 'tiling-plain'), 'Combined')
    anti_tile(g, texs, amount=0)
    _layout_evidence(out, 'tiling')
    off_passes = render(out, 'tiling-off')
    off = channel(off_passes, 'Combined')
    assert np.max(np.abs(channel(off_passes, 'var_anti_tile'))) == 0
    node = next(n for n in g.nt.nodes if n.label == 'anti_tile amount')
    node.outputs[0].default_value = 1
    on = channel(render(out, 'tiling-on'), 'Combined')
    error = float(np.max(np.abs(baseline-off)))
    change = float(np.mean(np.abs(on-off)))
    phase = float(np.mean(np.abs(on[64:] - on[:-64])))
    plain_phase = float(np.mean(np.abs(baseline[64:] - baseline[:-64])))
    import OpenImageIO as oiio
    pngs = [oiio.ImageBuf(str(out/(name+'.png'))).get_pixels()
            for name in ('tiling-plain', 'tiling-off')]
    metrics = dict(off_linear_max=error, off_png_identical=bool(np.array_equal(*pngs)),
                   off_png_differing_pixels=int(np.count_nonzero(np.any(pngs[0] != pngs[1], axis=-1))),
                   off_png_max_code_difference=int(round(float(np.max(abs(pngs[0]-pngs[1])))*255)),
                   on_mae=change, plain_row_period_mae=plain_phase, row_period_mae=phase)
    (out/'tiling-metrics.json').write_text(json.dumps(metrics, indent=2))
    assert metrics['off_png_identical'] and change > .001 and phase > 1.1*plain_phase, metrics
    copies = [n for n in g.nt.nodes if n.type == 'TEX_IMAGE']
    for tex in texs:
        assert sum(n.image == tex.image for n in copies) == 3
        assert all(n.projection == tex.projection and n.projection_blend == tex.projection_blend
                   and n.interpolation == tex.interpolation and n.extension == tex.extension
                   for n in copies if n.image == tex.image)
    return metrics


def coordinates(out):
    from materials.shared.pbr_maps import _ph_maps
    black_scene(samples=4, res=128)
    mat, g = material('default_coordinates')
    maps, _ = _ph_maps('concrete_wall_009')
    path = next(v for v in maps.values() if '_diff_' in Path(v).name)
    texs = []
    for _ in range(3):
        node = g.node('ShaderNodeTexImage', (-800, 0))
        node.image = bpy.data.images.load(path, check_existing=True)
        node.projection = 'BOX'
        texs.append(node)
    generated = g.node('ShaderNodeTexCoord', (-1000, 0)).outputs['Generated']
    g.link(generated, texs[2].inputs['Vector'])
    emission(g, g.combine(*(node.outputs['Color'] for node in texs), (800, 0)))
    anti_tile(g, [texs[1]], amount=0)
    ob = plane(mat, 4)
    for uv in ob.data.uv_layers.active.data:
        uv.uv.x = uv.uv.x * 2 + .17
        uv.uv.y = uv.uv.y * 2 + .31
    ortho_camera(8, 4)
    passes = render(out, 'coordinates-packed')
    data = next(value for key, value in passes.items() if key.endswith('Combined'))[4:-4, 4:-4]
    uv_error = float(np.max(abs(data[..., 0]-data[..., 1])))
    generated_error = float(np.mean(abs(data[..., 0]-data[..., 2])))
    assert uv_error < 1e-6 and generated_error > .001, (uv_error, generated_error)
    return dict(default_uv_max=uv_error, generated_mae=generated_error)


def _marks_fixture():
    black_scene(samples=4, res=512)
    mat, g = material('marks')
    tone, _ = macro_tone(g)
    dirt = grunge(g)
    patch = patchy_extent(g)
    noise, _ = _field(g, 'calibration', .5)
    raw_aov = g.node('ShaderNodeOutputAOV', (900, 600))
    raw_aov.aov_name = raw_aov.name = 'noise_calibration'
    g.link(noise, raw_aov.inputs['Value'])
    # Pack the three appearance probes into RGB; exact values also travel through AOVs.
    dirt_preview = g.range(dirt, .8, 1.2, (600, 200))
    tone_preview = g.range(tone, .97, 1.03, (600, 400))
    emission(g, g.combine(dirt_preview, tone_preview, patch, (800, 0)))
    macro_tone(g, amount=0)
    grunge(g, amount=0)
    patchy_extent(g, amount=0)
    unit_values(g, unit_key(g), tilt_deg=2, amount=0)
    for node in g.nt.nodes:
        if node.type == 'OUTPUT_AOV':
            node.aov_name = node.name.replace('.001', '_off')
    patchy_extent(g, coverage=.2)
    patchy_extent(g, coverage=.8)
    for node in g.nt.nodes:
        if node.type == 'OUTPUT_AOV' and node.name.endswith(('.002', '.003')):
            node.aov_name = node.name.replace('.002', '_20').replace('.003', '_80')
    plane(mat)
    ortho_camera(80, 64)
    return g


def marks(out):
    g = _marks_fixture()
    _layout_evidence(out, 'marks')
    passes = render(out, 'marks-packed')
    sd = float(channel(passes, 'var_grunge').std())
    raw = channel(passes, 'noise_calibration')
    off_errors = {}
    for node in g.nt.nodes:
        if node.type != 'OUTPUT_AOV' or node.name == 'noise_calibration':
            continue
        off = node.aov_name.endswith('_off') or (node.name.startswith('var_unit_') and node.name != 'var_unit_key')
        if off:
            neutral = 1 if any(word in node.name for word in ('tone', 'grunge', 'tint', 'bump')) else 0
            # Blender AOV names can themselves contain dots.
            data = next(v for k, v in passes.items() if k.endswith('.' + node.aov_name))
            off_errors[node.name] = float(np.max(np.abs(data[4:-4, 4:-4, :3] - neutral)))
    assert .04 <= sd <= .06, sd
    coverages = {str(c): float(np.mean(channel(passes, name) > 1e-6))
                 for c, name in ((.2, 'var_patchy_extent_20'), (.5, 'var_patchy_extent'),
                                 (.8, 'var_patchy_extent_80'))}
    assert all(abs(float(c)-v) <= .1 for c, v in coverages.items()), coverages
    assert off_errors and max(off_errors.values()) == 0, off_errors
    return dict(grunge_sd=sd, coverage=coverages, raw_mean=float(raw.mean()),
                raw_sd=float(raw.std()), off_errors=off_errors)


def _formula_comparison(out):
    # Prior surface measurements are comparison evidence, never a shader calibration table.
    measured = {(0., .6): .117403045296669, (2., .3): .08750655502080917,
                (2., .6): .06947463750839233, (2., 1.): .059531401842832565,
                (6., .6): .056337643414735794}
    rows = {}
    for (detail, rough), observed in measured.items():
        predicted = _moments(detail, rough)[1]
        rows[f'{detail},{rough}'] = dict(measured_sd=observed, formula_sd=predicted,
                                        relative_difference=predicted/observed-1)
    (out/'fbm-comparison.json').write_text(json.dumps(rows, indent=2))
    return rows


def _layout_evidence(out, name):
    layout = []
    for mat in bpy.data.materials:
        if not mat.node_tree:
            continue
        for frame in (n for n in mat.node_tree.nodes if n.type == 'FRAME'):
            nodes = [n for n in mat.node_tree.nodes if n.parent == frame]
            positions = [tuple(n.location) for n in nodes]
            assert len(positions) == len(set(positions)), (name, frame.label, positions)
            layout.append(dict(frame=frame.label, nodes=[dict(type=n.bl_idname, label=n.label,
                               location=list(n.location)) for n in nodes]))
    (out/(name+'-layout.json')).write_text(json.dumps(layout, indent=2))


def _unit_fixture(mat, source):
    if source == 'cell':
        plane(mat, 4)
        return
    if source == 'geometry':
        # Two boards welded along x = 0: one island, so only the stored face key tells them apart.
        mesh = bpy.data.meshes.new('boards')
        mesh.from_pydata([(x, y, 0) for y in (-.5, .5) for x in (-1.5, 0, 1.5)], [],
                         [(0, 1, 4, 3), (1, 2, 5, 4)])
        mesh.attributes.new('unit_key', 'INT', 'FACE').data.foreach_set('value', (3, 7))
        mesh.materials.append(mat)
        bpy.context.scene.collection.objects.link(bpy.data.objects.new('boards', mesh))
        return
    collection = bpy.data.collections.new('two_part_block')
    parts = []
    for x in (-.24, .24):
        ob = plane(mat, .44)
        ob.location.x = x
        parts.append(ob)
    if source == 'instancer':
        for ob in parts:
            bpy.context.scene.collection.objects.unlink(ob)
            collection.objects.link(ob)
        objects = []
        for x in (-1.5, -.5, .5, 1.5):
            ob = bpy.data.objects.new('block', None)
            ob.instance_type, ob.instance_collection = 'COLLECTION', collection
            ob.location.x = x
            bpy.context.scene.collection.objects.link(ob)
            objects.append(ob)
        set_unit_keys(objects)
        saved = [ob['unit_key'] for ob in objects]
        set_unit_keys(reversed(objects))
        assert saved == [ob['unit_key'] for ob in objects]
    else:
        for i, ob in enumerate(parts):
            ob.location.x = -.75 + i * 1.5
        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()


def units(out):
    metrics = {}
    centers = {'instancer': (13, 44, 77, 108, 141, 172, 205, 236), 'island': (76, 172),
               'geometry': (80, 176), 'cell': (32, 96, 160, 224)}
    for source in centers:
        black_scene(samples=4, res=256)
        mat, g = material(source)
        # The cell fixture is a 4 m plane: UV x in cells of 0.25 is four 1 m units.
        uv = g.node('ShaderNodeTexCoord', (-3600, -700)).outputs['UV']
        key = unit_key(g, source, vector=uv, size=(.25, 2, 2))
        emission(g, key)
        unit_values(g, key, tilt_deg=2)
        _unit_fixture(mat, source)
        ortho_camera(8, 4)
        passes = render(out, 'keys-' + source)
        data = channel(passes, 'Combined')
        row = data[data.shape[0]//2]
        assert all(float(data[data.shape[0]//2-2:data.shape[0]//2+3, x-2:x+3].std()) < 1e-6
                   for x in centers[source])
        values = [float(np.median(row[max(0, x-2):x+3])) for x in centers[source]]
        if source == 'instancer':
            assert all(abs(values[i]-values[i+1]) < 1e-6 for i in range(0, 8, 2)), values
            assert len(set(round(x, 5) for x in values[::2])) == 4, values
        else:
            assert all(abs(a-b) > .001 for a, b in zip(values, values[1:])), values
        metrics[source] = values
    return metrics


def graphs(out):
    from regress_cases import CASES
    from regress_rig import mods
    black_scene(samples=1, res=16)
    spec = importlib.util.spec_from_file_location('variation_before', out/'variation_before.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    before = graph(old.random_tone_material('R', (.1,)*3, (.2,)*3).node_tree)
    after = graph(random_tone_material('R', (.1,)*3, (.2,)*3).node_tree)
    for name, value in (('random-tone-before', before), ('random-tone-after', after)):
        (out/(name+'.json')).write_text(json.dumps(value, sort_keys=True, indent=2))
    assert before == after
    baselines = {}
    for name in ('anti_tile', 'unit_key', 'unit_values', 'macro_tone', 'grunge', 'patchy_extent'):
        bpy.ops.wm.read_homefile(use_empty=True)
        CASES[name](mods())
        _layout_evidence(out, name)
        baselines[name] = {m.name: graph(m.node_tree) for m in bpy.data.materials if m.node_tree}
    (out/'variation-baseline.json').write_text(json.dumps(baselines, sort_keys=True, indent=2))
    return dict(random_tone_identical=True, baseline_cases=list(baselines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--only', choices=('tiling', 'marks', 'units', 'graphs', 'coordinates'))
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.out.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, run in (('graphs', graphs), ('tiling', tiling), ('marks', marks), ('units', units), ('coordinates', coordinates)):
        if args.only and args.only != name:
            continue
        try:
            results[name] = run(args.out)
        except Exception:
            import traceback
            results[name] = {'ERROR': traceback.format_exc()}
        (args.out/('results-' + (args.only or 'all') + '.json')).write_text(json.dumps(results, indent=2))
    if not args.only or args.only == 'marks':
        results['fbm_formula'] = _formula_comparison(args.out)
    (args.out/('results-' + (args.only or 'all') + '.json')).write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if any('ERROR' in result for result in results.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
